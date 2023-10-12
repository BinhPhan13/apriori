from itertools import combinations
from typing import Iterable, Union

class Manager:
    def __init__(self, transactions:Iterable[Iterable[str]]):
        self._data = {} # item : set of transactions
        for i, row in enumerate(transactions):
            for item in row:
                self._data[item] = self._data.get(item, set())
                self._data[item].add(i)
        self._config()

    def _config(self):
        # dict is ordered in python > 3.6
        self._decoder = tuple(self._data.keys())
        self._data = tuple(self._data.values())
    
    @property
    def data(self):
        return self._data

    @property
    def decoder(self):
        return self._decoder
        
class Miner:
    def __init__(self, mng:Manager,
        L1:dict[int, set], maxsize:int=10,
        minsp:int=1
    ):
        # contain large itemsets mined by size
        self._mng = mng
        self._data = [L1]
        self._numiter = maxsize-1
        self._minsp = minsp

    def mine(self):
        for i in range(self._numiter):
            current_sets = list(self._data[-1].keys())
            joined_sets = self._join(current_sets)
            pruned_sets = self._prune(current_sets, joined_sets)

            Ck = {itemset : self._count(itemset)
                for itemset in pruned_sets
            }
            Lk = {k:v for k,v in Ck.items() if v >= self._minsp}

            if not Lk: break
            self._data.append(Lk)


    def _join(self, itemsets:list[tuple[int]]):
        N = len(itemsets)
        i = 0
        while i < N-1:
            *prev, last = itemsets[i]
            tails = [last]
            for j in range(i+1, N):
                *prv, lst = itemsets[j]
                if prv == prev: tails.append(lst)
                else: break

            i = j
            for cbn in combinations(tails, 2):
                yield tuple(prev + list(cbn))

    def _prune(self,
        prevsets:Iterable[tuple[int]],
        nextsets:Iterable[tuple[int]]
    ):
        base = set(prevsets) # for hash lookup
        for itemset in nextsets:
            for i in range(len(itemset)-2): # why..?
                subset = itemset[:i] + itemset[i+1:]
                # contain subset that is not common -> remove
                if subset not in base: break
            else: yield itemset

    def _count(self, itemset:tuple[int]):
        data = self._mng.data

        itemset = sorted(
            itemset,
            key=lambda item:len(data[item]),
            reverse=True)
        
        indices = None
        while itemset:
            item = itemset.pop()
            indices = data[item] if indices is None \
                else data[item] & indices
            if len(indices) < self._minsp: return 0

        return len(indices)

    @property
    def data(self):
        return tuple(self._data)

class Rule:
    def __init__(self,
        condition:set, result:set,
        confidence:float,
        support:float
    ):
        self._lhs = condition
        self._rhs = result
        self._cf = confidence
        self._sp = support

    def __str__(self):
        return f'{self._lhs} -> {self._rhs}'

    def __repr__(self):
        stats = f'confidence: {self._cf:.3f}, support: {self._sp:.3f}'
        return f'{self} ({stats})'

    @property
    def lhs(self):
        return tuple(self._lhs)

    @property
    def rhs(self):
        return tuple(self._rhs)

class Apriori:
    def __init__(self,
        transactions:Iterable[Iterable[str]],
        minsp:float, mincf:float
    ):
        self._manager = Manager(transactions)
        self._num_txns = len(transactions)
        assert 0 <= minsp <= 1 and 0 <= mincf <= 1
        self._minsp = self._num_txns * minsp
        self._mincf = mincf

    def solve(self):
        C1 = {(i,) : len(txns)
            for i, txns in enumerate(self._manager.data)
        }
        L1 = {k:v for k,v in C1.items() if v >= self._minsp}

        self._miner = Miner(self._manager, L1, minsp=self._minsp)
        self._miner.mine()

        self._orders = self._miner.data
        self._getallrules()

    def _getallrules(self):
        self._rules = []
        for i, L in enumerate(self._orders, 1):
            for size in range(1, i):
                self._rules += list(self._getrules(L, size))

    def _getrules(self, Lcur:dict[tuple[int],int], size:int):
        '''Yield rules: condition, result, confidence, support
        Lcur: current large itemsets to get rules
        size: size of condition
        '''
        Lref = self._orders[size-1]
        for itemset in Lcur:
            for subset in combinations(itemset, size):
                sp = Lcur[itemset]
                cf = sp / Lref[subset]
                assert 0 <= cf <= 1
                if cf < self._mincf: continue

                cdt, rst = self._repr_rule(subset, itemset)
                yield Rule(cdt, rst, cf, sp/self._num_txns)

    def _repr_rule(self, sub:tuple[int], sup:tuple[int]):
        # decode
        decoder = self._manager.decoder
        sub = tuple(decoder[x] for x in sub)
        sup = tuple(decoder[x] for x in sup)

        condition = set(sub)
        result = set(sup) - condition
        return condition, result

    @property
    def rules(self) -> Rule:
        try: return tuple(self._rules)
        except AttributeError: return None
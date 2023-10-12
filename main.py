from sys import argv
from apriori import Apriori

file = 'data/small_gc.txt'
transactions = []
f = open(file, 'r')
for line in f:
    line = line.strip('\n')
    transactions.append(line.split(','))
f.close()

minsp, mincf = 0.1, 0.8
apri = Apriori(transactions, minsp, mincf)
apri.solve()
# interactive mode
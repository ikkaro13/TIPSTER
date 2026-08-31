import sqlite3
c = sqlite3.connect('backend/tipster.db').cursor()
c.execute('SELECT id, pick FROM bets WHERE pick LIKE "%1x%" OR pick LIKE "%x2%"')
for r in c.fetchall(): print(r)

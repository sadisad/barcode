import sqlite3
c = sqlite3.connect("certificates.db")
res = c.execute("SELECT * FROM certificates WHERE nama LIKE '%Ridho%'").fetchall()
for r in res:
    print(r)

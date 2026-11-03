import sqlite3

con = sqlite3.connect("crm.db")

# Full CREATE statements
for (sql,) in con.execute("SELECT sql FROM sqlite_master WHERE type='table'"):
    print(sql, "\n")

# Column details per table
for (table,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
    print(f"--- {table} ---")
    for cid, name, ctype, notnull, default, pk in con.execute(f"PRAGMA table_info({table})"):
        print(f"{name:15} {ctype:10} {'PRIMARY KEY' if pk else ''}")
    print()
con.close()
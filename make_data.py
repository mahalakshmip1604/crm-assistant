import random, sqlite3
from faker import Faker

fake = Faker("en_GB")
Faker.seed(42); random.seed(42)

con = sqlite3.connect("crm.db")
con.executescript("""
DROP TABLE IF EXISTS interactions; DROP TABLE IF EXISTS contracts;
DROP TABLE IF EXISTS contacts;     DROP TABLE IF EXISTS accounts;

CREATE TABLE accounts (id INTEGER PRIMARY KEY, name TEXT, industry TEXT,
                       country TEXT, created_at DATE);
CREATE TABLE contacts (id INTEGER PRIMARY KEY, account_id INTEGER REFERENCES accounts(id),
                       name TEXT, role TEXT, email TEXT);
CREATE TABLE contracts (id INTEGER PRIMARY KEY, account_id INTEGER REFERENCES accounts(id),
                        product TEXT, monthly_value REAL, start_date DATE,
                        end_date DATE, status TEXT);
CREATE TABLE interactions (id INTEGER PRIMARY KEY, account_id INTEGER REFERENCES accounts(id),
                           contact_id INTEGER REFERENCES contacts(id),
                           type TEXT, date DATE, notes TEXT);
""")

industries = ["Retail", "Logistics", "Finance", "Healthcare", "Manufacturing", "Education"]
countries  = ["Belgium", "France", "Netherlands", "Luxembourg", "Spain"]
products   = ["Business Fibre", "Mobile Fleet", "Cloud PBX", "IoT Connectivity", "Cybersecurity"]
roles      = ["CEO", "IT Manager", "Procurement", "Finance Director", "Office Manager"]
types      = ["call", "email", "meeting", "support ticket"]
notes      = ["Asked about pricing for extra lines", "Complained about outage last week",
              "Interested in upgrading contract", "Renewal discussion started",
              "Requested a security audit", "Happy with service, no action needed"]

for a in range(1, 201):                                   # 200 accounts
    con.execute("INSERT INTO accounts VALUES (?,?,?,?,?)",
        (a, fake.company(), random.choice(industries), random.choice(countries),
         fake.date_between("-4y", "-1y").isoformat()))
    contact_ids = []
    for _ in range(random.randint(1, 4)):
        cur = con.execute("INSERT INTO contacts (account_id,name,role,email) VALUES (?,?,?,?)",
            (a, fake.name(), random.choice(roles), fake.email()))
        contact_ids.append(cur.lastrowid)
    for _ in range(random.randint(1, 3)):
        start = fake.date_between("-3y", "-1m")
        end = fake.date_between(start, "+2y")
        con.execute("""INSERT INTO contracts (account_id,product,monthly_value,start_date,end_date,status)
                       VALUES (?,?,?,?,?,?)""",
            (a, random.choice(products), round(random.uniform(50, 5000), 2),
             start.isoformat(), end.isoformat(), "active" if end > fake.date_object() else "expired"))
    for _ in range(random.randint(5, 15)):
        con.execute("""INSERT INTO interactions (account_id,contact_id,type,date,notes)
                       VALUES (?,?,?,?,?)""",
            (a, random.choice(contact_ids), random.choice(types),
             fake.date_between("-1y", "today").isoformat(), random.choice(notes)))
con.commit(); con.close()
print("crm.db created")
import sqlite3, pandas as pd

def run(sql):
    con = sqlite3.connect("crm.db")
    df = pd.read_sql(sql, con)
    con.close()
    return df

if __name__ == "__main__":
    #print(run("SELECT * FROM accounts LIMIT 5"))


    from explore import run
    df = run("SELECT a.industry, c.product, c.monthly_value FROM accounts a JOIN contracts c ON c.account_id=a.id")
    print(df.groupby(["industry","product"])["monthly_value"].mean().round(0).unstack())
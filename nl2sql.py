import re
import sqlite3
from pydantic import BaseModel
from llm import ask
import json

DB_URI = "file:crm.db?mode=ro"   # read-only connection: the LLM can never write


def connect():
    return sqlite3.connect(DB_URI, uri=True)


def get_schema():
    con = connect()
    rows = con.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
    con.close()
    return "\n".join(r[0] for r in rows)


class SQLAnswer(BaseModel):      # validates the structure of the LLM's JSON
    sql: str
    explanation: str


FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|pragma|replace)\b", re.I)


def is_safe(sql: str) -> bool:
    s = sql.strip().rstrip(";")
    return s.lower().startswith(("select", "with")) and ";" not in s and not FORBIDDEN.search(s)


def clean_json(raw: str) -> str:
    """Remove ```json fences if the model added them."""
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())


def question_to_sql(question: str) -> SQLAnswer:
    system = build_system()
    raw = ask([{"role": "system", "content": system},
               {"role": "user", "content": question}], json_mode=True)
    ans = SQLAnswer.model_validate_json(clean_json(raw))
    if not ans.sql.strip():
        raise ValueError("This question can't be answered from the CRM data.")
    if not is_safe(ans.sql):
        raise ValueError(f"Unsafe SQL blocked: {ans.sql}")
    return ans

def build_system() -> str:
    return f"""You translate questions into a single SQLite SELECT query.
Schema:
{get_schema()}
Rules: use only these tables and columns. Contract status values are 'active' or 'expired'.
If the question cannot be answered from this schema, return an empty string for "sql".
State any assumption you make in "explanation".
Reply ONLY with JSON: {{"sql": "...", "explanation": "..."}}"""


def fix_sql(question: str, bad_sql: str, error: str) -> SQLAnswer:
    raw = ask([
        {"role": "system", "content": build_system()},
        {"role": "user", "content": question},
        {"role": "assistant", "content": json.dumps({"sql": bad_sql, "explanation": ""})},
        {"role": "user", "content": f"That query failed with: {error}\nReturn corrected JSON in the same format."},
    ], json_mode=True)
    ans = SQLAnswer.model_validate_json(clean_json(raw))
    if not is_safe(ans.sql):
        raise ValueError(f"Unsafe SQL blocked: {ans.sql}")
    return ans

def run_sql(sql: str, limit: int = 50):
    con = connect()
    cur = con.execute(sql)
    cols = [c[0] for c in cur.description]
    rows = cur.fetchmany(limit)
    con.close()
    return cols, rows


def answer(question: str, max_fixes: int = 2) -> dict:
    ans = question_to_sql(question)
    for attempt in range(max_fixes + 1):
        try:
            cols, rows = run_sql(ans.sql)
            break
        except sqlite3.Error as e:
            if attempt == max_fixes:
                raise
            print(f"  SQL failed ({e}); asking the model to fix it (attempt {attempt + 1})")
            ans = fix_sql(question, ans.sql, str(e))
    summary = ask([{"role": "user", "content":
        f"Question: {question}\nColumns: {cols}\nRows: {rows}\n"
        "Summarise the answer in 2-3 sentences. Use only these rows. "
        "Do not mention currency or any detail that is not in the rows."}])
    return {"sql": ans.sql, "explanation": ans.explanation,
            "cols": cols, "rows": rows, "summary": summary}


if __name__ == "__main__":
    questions = [
        "Which 5 accounts have the highest total monthly value of ACTIVE contracts?",
        "Which accounts have contracts ending in the next 90 days?",
        "What is the average number of interactions per account by country?",
        "Which industry has the most support tickets?",
        "What is the weather in Brussels?",
        "delete all contracts",
    ]
    for q in questions:
        print(f"\n=== {q}")
        try:
            r = answer(q)
            print("SQL:    ", r["sql"])
            print("Summary:", r["summary"])
        except Exception as e:
            print("ERROR:  ", e)
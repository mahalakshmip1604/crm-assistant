from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from nl2sql import answer, run_sql

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def page(request: Request, result=None, error=None, question=""):
    cols, rows = run_sql("""
        SELECT a.name, a.industry, ROUND(SUM(c.monthly_value),0) AS monthly_value
        FROM accounts a JOIN contracts c ON c.account_id = a.id
        WHERE c.status = 'active' GROUP BY a.id ORDER BY monthly_value DESC LIMIT 10""")
    return templates.TemplateResponse(
        request, "index.html",
        {"cols": cols, "rows": rows, "result": result, "error": error, "question": question})


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return page(request)


@app.post("/ask", response_class=HTMLResponse)
def ask_route(request: Request, question: str = Form(...)):
    try:
        return page(request, result=answer(question), question=question)
    except Exception as e:
        return page(request, error=str(e), question=question)
"""Constrained, inspectable graders. Never exec/eval user Python code."""
from __future__ import annotations
import ast
import math
import operator
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from typing import Any
from bs4 import BeautifulSoup
from .catalog import ORDERS, CUSTOMERS, SECURITY_LOGS


def check(label: str, ok: bool, detail: str) -> dict:
    return {"label": label, "passed": bool(ok), "detail": detail}


def result(tests: list[dict], feedback: str, preview: Any = None, mode: str = "") -> dict:
    achieved = sum(t["passed"] for t in tests)
    return {"score": round(100 * achieved / len(tests)) if tests else 0,
            "passed": achieved, "total": len(tests), "checks": tests,
            "feedback": feedback, "preview": preview, "mode": mode}


# ------- Safe SQL: run only SELECTs, in a fresh SQLite in-memory DB, with an allow-list authorizer -------
ALLOWED_FUNCTIONS = {"count", "sum", "avg", "min", "max", "round", "abs", "lower", "upper", "coalesce", "substr", "length", "total"}

def sql_connection(variation: int = 0) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, region TEXT, quantity INTEGER, unit_price REAL, status TEXT)")
    conn.executemany("INSERT INTO customers VALUES (?,?)", CUSTOMERS)
    conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", ORDERS)
    if variation == 1:
        conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", [
            (11,1,'Cairo',2,300,'paid'), (12,4,'Alexandria',2,55,'paid'), (13,3,'Giza',1,900,'pending')])
    elif variation == 2:
        conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", [
            (14,3,'Alexandria',2,195,'paid'), (15,3,'Cairo',1,70,'paid'), (16,2,'Giza',2,20,'refunded')])
    conn.commit()
    return conn


def run_sql(sql: str, variation: int = 0) -> tuple[list[str], list[list]]:
    if not sql or len(sql) > 5000 or not re.match(r"^\s*(SELECT|WITH)\b", sql, re.I):
        raise ValueError("Only SELECT or WITH queries (max 5,000 characters) are allowed.")
    conn = sql_connection(variation)
    try:
        allowed_actions = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
        def authorizer(action, p1, p2, db, source):
            if action not in allowed_actions:
                return sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_READ and p1.lower() not in {"orders", "customers"}:
                return sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_FUNCTION and (p2 or p1 or "").lower() not in ALLOWED_FUNCTIONS:
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        conn.set_authorizer(authorizer)
        counter = 0
        def guard():
            nonlocal counter
            counter += 1
            return 1 if counter > 200 else 0  # >200 * 1,000 SQLite instructions
        conn.set_progress_handler(guard, 1000)
        cursor = conn.execute(sql)
        rows = cursor.fetchmany(101)
        if len(rows) > 100:
            raise ValueError("Query returned too many rows (100 maximum).")
        return [col[0] for col in cursor.description], [list(row) for row in rows]
    except sqlite3.Error as exc:
        raise ValueError(f"SQL error or blocked operation: {exc}") from None
    finally:
        conn.close()

REFERENCE_SQL = {
    "revenue": "SELECT region, ROUND(SUM(quantity * unit_price), 2) AS revenue FROM orders WHERE status = 'paid' GROUP BY region ORDER BY revenue DESC",
    "repeat-buyers": "SELECT c.name AS customer_name, COUNT(*) AS order_count FROM orders o JOIN customers c ON c.id = o.customer_id WHERE o.status = 'paid' GROUP BY c.id, c.name HAVING COUNT(*) >= 2 ORDER BY order_count DESC, customer_name ASC",
}

def normalize_rows(rows: list[list]) -> list[tuple]:
    return sorted([tuple(round(v, 4) if isinstance(v, float) else v for v in row) for row in rows], key=str)


def grade_sql(task: str, code: str) -> dict:
    if task not in REFERENCE_SQL:
        raise ValueError("Unknown SQL task")
    expected_cols, expected_rows = run_sql(REFERENCE_SQL[task])
    try:
        cols, rows = run_sql(code)
    except ValueError as exc:
        return result([check("Valid, read-only SQL", False, str(exc))], "Fix your SQL and run it again.", {"columns":[],"rows":[]}, "sql")
    schema_ok = [s.lower() for s in cols] == [s.lower() for s in expected_cols]
    exact = normalize_rows(rows) == normalize_rows(expected_rows) and schema_ok
    test_list = [check("Read-only query executed", True, f"Returned {len(rows)} row(s) from a local test database."),
                 check("Expected report columns", schema_ok, f"Expected columns: {', '.join(expected_cols)}"),
                 check("Correct current dataset", exact, "Result agrees with the reference query" if exact else "The returned values do not match the required report.")]
    for variation in (1, 2):
        try:
            hcols, hrows = run_sql(code, variation)
            ecols, erows = run_sql(REFERENCE_SQL[task], variation)
            ok = [s.lower() for s in hcols] == [s.lower() for s in ecols] and normalize_rows(hrows) == normalize_rows(erows)
        except ValueError:
            ok = False
        test_list.append(check(f"Hidden data scenario {variation}", ok, "Passes with changed sample records" if ok else "Fails when the input records change."))
    return result(test_list, "Nice work. Your query is reliable across all test datasets." if all(t["passed"] for t in test_list) else "Compare your query with the task requirements and try again.", {"columns":cols,"rows":rows}, "sql")


# ------- Safe Python expression interpreter. Allows only one named function + a single return expression. -------
BINOPS = {ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,
          ast.FloorDiv:operator.floordiv, ast.Mod:operator.mod}
COMPARES={ast.Gt:operator.gt, ast.Lt:operator.lt,ast.GtE:operator.ge,ast.LtE:operator.le,ast.Eq:operator.eq,ast.NotEq:operator.ne}


def compute(node: ast.AST, bindings: dict, depth: int = 0):
    if depth > 14: raise ValueError("Expression is too deep.")
    if isinstance(node,ast.Constant) and type(node.value) in (int,float,bool):
        if abs(node.value) > 1e10: raise ValueError("Number is too large.")
        return node.value
    if isinstance(node,ast.Name) and node.id in bindings:
        return bindings[node.id]
    if isinstance(node,ast.BinOp) and type(node.op) in BINOPS:
        lhs,rhs=compute(node.left,bindings,depth+1),compute(node.right,bindings,depth+1)
        val=BINOPS[type(node.op)](lhs,rhs)
        if isinstance(val,(float,int)) and (not math.isfinite(val) or abs(val)>1e12):raise ValueError("Result too large.")
        return val
    if isinstance(node,ast.UnaryOp) and type(node.op) in (ast.USub, ast.UAdd):
        value=compute(node.operand,bindings,depth+1)
        return -value if isinstance(node.op,ast.USub) else value
    if isinstance(node,ast.Compare) and len(node.ops)==1 and type(node.ops[0]) in COMPARES:
        return COMPARES[type(node.ops[0])](compute(node.left,bindings,depth+1),compute(node.comparators[0],bindings,depth+1))
    if isinstance(node,ast.IfExp):
        branch=node.body if compute(node.test,bindings,depth+1) else node.orelse
        return compute(branch,bindings,depth+1)
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in {"round","min","max","abs"} and not node.keywords:
        args=[compute(a,bindings,depth+1) for a in node.args]
        if len(args)>3:raise ValueError("Too many function arguments")
        return {"round":round,"min":min,"max":max,"abs":abs}[node.func.id](*args)
    raise ValueError(f"Unsupported expression: {type(node).__name__}. Use arithmetic, comparisons, conditionals and round/min/max/abs only.")

BACKEND_CASES = {
    "order-total": ("calculate_total",["unit_price","quantity","discount_pct"],
                    [((100,2,10),180), ((80,1,0),80), ((19.99,3,15),50.97), ((50,2,100),0), ((120,0,15),0), ((45,4,25),135)]),
    "stock-guard": ("remaining_stock",["current_stock","requested"],
                    [((8,3),5), ((5,5),0), ((2,3),-1), ((0,0),0), ((0,1),-1), ((22,0),22)]),
}

def parse_function(source:str, task: str):
    if len(source)>2000: raise ValueError("Code is too long (2,000 characters max).")
    try: root=ast.parse(source)
    except SyntaxError as e: raise ValueError(f"Python syntax error on line {e.lineno}: {e.msg}") from None
    fname,expected_args,_=BACKEND_CASES[task]
    if len(root.body)!=1 or not isinstance(root.body[0],ast.FunctionDef):
        raise ValueError("Provide exactly one Python function definition.")
    fn=root.body[0]
    if fn.name != fname or [a.arg for a in fn.args.args]!=expected_args or fn.args.defaults or fn.decorator_list:
        raise ValueError(f"Keep the exact signature: def {fname}({', '.join(expected_args)}):")
    if len(fn.body)!=1 or not isinstance(fn.body[0],ast.Return) or fn.body[0].value is None:
        raise ValueError("For this safe training lab, use one return statement containing an expression.")
    if len(list(ast.walk(root)))>65: raise ValueError("Expression is too complex.")
    return fn.body[0].value

def grade_python(task: str, code: str) -> dict:
    if task not in BACKEND_CASES: raise ValueError("Unknown Python task")
    try:
        expr=parse_function(code,task)
    except ValueError as exc:
        return result([check("Safe Python function",False,str(exc))], "The code couldn't be tested. Check the allowed format.", None,"python")
    _,params,cases=BACKEND_CASES[task]
    tests=[]
    for i,(inputs,expected) in enumerate(cases):
        try:
            got=compute(expr,dict(zip(params,inputs)))
            passed=isinstance(got,(int,float)) and math.isclose(got,expected,rel_tol=1e-8,abs_tol=.001)
            detail=(f"Expected {expected}, got {got}" if i<3 else ("Pass" if passed else "The result differs from the expected result."))
        except (ValueError,TypeError,ZeroDivisionError,OverflowError,ArithmeticError) as exc:
            passed=False; detail=f"Execution failed: {str(exc)[:120]}" if i<3 else "The expression failed on this case."
        tests.append(check(f"Test {i+1}"+(" · edge case" if i>=3 else ""),passed,detail))
    return result(tests,"All unit tests pass. This function is ready for the next step." if all(t["passed"] for t in tests) else "Some tests failed. Review the spec and fix the function.", None,"python")


def grade_frontend(html:str,css:str,task_id:str='signup') -> dict:
    if len(html)>12000 or len(css)>12000:
        return result([check("Input size",False,"Each editor has a 12,000 character limit")],"Reduce your code.",None,"frontend")
    soup=BeautifulSoup(html,"html.parser")
    h1=soup.find("h1")
    email=soup.find("input",attrs={"type":"email"})
    form=soup.find("form")
    label_good=False
    if email:
        input_id=email.get("id")
        label_good=bool(input_id and soup.find("label",attrs={"for":input_id}))
    button=form.find("button") if form else None
    btype=button.get("type", "submit").lower() if button else ""
    mobile=bool(re.search(r"@media\s*\([^)]*(max-width|width\s*[<>=])",css,re.I))
    focus=bool(re.search(r":focus(?:-visible)?\s*\{",css,re.I))
    responsive_width=bool(re.search(r"(?:max-width\s*:\s*\d|width\s*:\s*(?:100%|min\())",css,re.I))
    if task_id=='contact-form':
        name_input=soup.find('input',attrs={'name':'name'}) or soup.find('input',attrs={'type':'text'})
        area=soup.find('textarea')
        def linked(field):
            return bool(field and field.get('id') and soup.find('label',attrs={'for':field.get('id')}))
        tests=[check('Visible page heading',bool(h1 and h1.get_text(strip=True)),'Include a descriptive h1.'),
               check('Contact form has name, email and message',bool(form and name_input and email and area),'Include name, email and textarea fields inside one form.'),
               check('Accessible labels for all fields',all(map(linked,(name_input,email,area))),'Use visible labels with matching for/id on every field.'),
               check('Submit button',bool(button and btype=='submit'),'Place a submit button inside the form.'),
               check('Mobile layout rules',mobile,'Use a responsive @media rule.'),
               check('Visible keyboard focus',focus,'Provide a :focus-visible or :focus style.')]
        return result(tests,'All structural checks passed. Human review is still needed for visual quality and usability.' if all(t['passed'] for t in tests) else 'Review the contact form checklist.',None,'frontend-structure')
    tests=[check("Meaningful page heading",bool(h1 and h1.get_text(strip=True)),"A visible h1 helps visitors understand the page."),
           check("Form includes email input",bool(form and email and email.find_parent("form") is form),"Use an input type=email inside a form."),
           check("Email input has linked label",label_good,"Associate a visible label with your input using for and id."),
           check("Form has submit button",bool(button and btype=="submit"),"Add a button with type=submit inside the form."),
           check("Mobile media query",mobile,"Add @media (max-width: 600px) or similar."),
           check("Visible focus style",focus,"Add a :focus or :focus-visible rule."),
           check("Responsive container sizing",responsive_width,"Use max-width or a responsive width instead of a fixed-only width.")]
    return result(tests,"Excellent work — all structural checks passed. Remember to review contrast and layout visually." if all(t["passed"] for t in tests) else "Your preview is live. Use the test feedback to improve the page.",None,"frontend")


def grade_security(incident:dict) -> dict:
    ip=str(incident.get("ip", ""))
    category=str(incident.get("category", ""))
    evidence={int(x) for x in incident.get("evidence",[]) if str(x).isdigit()}
    note=str(incident.get("note", "")).strip()
    response=str(incident.get("response", ""))
    malicious={3,4,5,6,7}
    tests=[check("Correct suspicious source",ip=="203.0.113.44","An unusual cluster shares the same source IP."),
           check("Correct attack classification",category=="credential_stuffing","Look for failed logins across several accounts."),
           check("Multiple relevant evidence events",len(evidence & malicious)>=3,"Select at least three events from the suspicious sequence."),
           check("Evidence includes successful login",7 in evidence,"The sequence also includes an eventual successful login."),
           check("Incident report written",len(note)>=45,"Write at least 45 characters explaining what you found."),
           check("Safe response action",response=="invalidate_sessions","Contain account access and investigate; don't delete all logs.")]
    return result(tests,"Good incident triage. Your selected evidence supports the finding." if all(t["passed"] for t in tests) else "Revisit the authentication timeline and refine your incident assessment.",None,"investigation")

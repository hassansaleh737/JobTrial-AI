from fastapi.testclient import TestClient
from backend.main import app
from backend.engine import run_sql, grade_sql, grade_python,grade_frontend, grade_security
from backend.catalog import TRACKS
client=TestClient(app)


def test_health_and_catalog():
    assert client.get('/api/health').json()['ok']
    assert len(client.get('/api/catalog').json()['tracks'])==4


def test_backend_bug_and_fix():
    starter=TRACKS['backend']['tasks'][0]['starter']
    assert grade_python('order-total',starter)['score']<100
    fixed='def calculate_total(unit_price, quantity, discount_pct):\n    return round(unit_price * quantity * (1-discount_pct/100), 2)'
    assert grade_python('order-total',fixed)['score']==100
    assert grade_python('stock-guard','def remaining_stock(current_stock, requested):\n    return current_stock-requested if requested<=current_stock else -1')['score']==100


def test_block_untrusted_python():
    malicious='def calculate_total(unit_price, quantity, discount_pct):\n    return __import__("os").system("echo HACK")'
    assert grade_python('order-total',malicious)['score']==0
    assert grade_python('order-total','import os')['score']==0


def test_sql_reference_and_block_writes():
    from backend.engine import REFERENCE_SQL
    for key in REFERENCE_SQL:
        assert grade_sql(key,REFERENCE_SQL[key])['score']==100
    assert grade_sql('revenue','DELETE FROM orders')['score']==0
    assert grade_sql('revenue','SELECT * FROM sqlite_master')['score']==0
    assert len(run_sql('SELECT * FROM orders')[1])>0


def test_frontend_checker():
    html='<main><h1>Sign up</h1><form><label for="email">Email</label><input id="email" type="email"><button type="submit">Join</button></form></main>'
    css='.card { max-width: 480px } input:focus-visible { outline: 2px solid blue } @media (max-width: 600px) { .card { width: 100% } }'
    assert grade_frontend(html,css)['score']==100


def test_security_triage():
    incident={"ip":"203.0.113.44","category":"credential_stuffing","evidence":[3,4,5,7],"note":"A burst of login failures across multiple accounts was followed by a successful login.","response":"invalidate_sessions"}
    assert grade_security(incident)['score']==100


def test_analyze_and_persist():
    r=client.post('/api/analyze',json={"description":"Frontend developer internship. HTML CSS React accessibility."})
    assert r.status_code==200 and r.json()['track']=='frontend'
    r=client.post('/api/submit',json={"track":"backend","task_id":"stock-guard","code":"def remaining_stock(current_stock, requested):\n    return current_stock-requested"})
    assert r.status_code==200
    uid=r.json()['report_id']
    assert client.get('/api/report/'+uid).status_code==200
    assert client.get('/api/history').status_code==200


def test_text_upload():
    r=client.post('/api/extract',files={'file':('job.txt',b'Python backend internship: FastAPI, SQL and unit tests.', 'text/plain')})
    assert r.status_code==200 and 'FastAPI' in r.json()['text']

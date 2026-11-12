import os
from fastapi.testclient import TestClient
from backend.main import app
from backend.adaptive import build_job_trial, grade_local_python
from backend.docker_grader import render,grade_docker
client=TestClient(app)


def test_ai_role_does_not_fall_back_to_order_total():
    d=client.post('/api/analyze',json={'description':'AI Engineer internship. Python machine learning classification model evaluation and data science.'}).json()
    assert d['track']=='backend'
    assert d['dynamic_trial']['tasks'][0]['id'].startswith('pack:ml-easy:')


def test_python_multi_statement_solution():
    src='''def calculate_total(unit_price, quantity, discount_pct):
    subtotal = unit_price * quantity
    discount = subtotal * discount_pct / 100
    result = subtotal - discount
    return round(result, 2)
'''
    assert grade_local_python('gen:order-total:python',src)['score']==100


def test_python_loops_and_lists():
    code='''def classification_accuracy(actual, predicted):
    correct = 0
    for i in range(len(actual)):
        if actual[i] == predicted[i]:
            correct += 1
    return correct / len(actual)
'''
    assert grade_local_python('gen:ml-accuracy:python',code)['score']==100
    dedupe='''def unique_count(identifiers):
    seen = []
    for item in identifiers:
        if not item in seen:
            seen.append(item)
    return len(seen)
'''
    assert grade_local_python('gen:data-dedupe:python',dedupe)['score']==100


def test_python_unsupported_import_and_unsafe_code():
    code='''def calculate_total(unit_price, quantity, discount_pct):
    return __import__("os").system("whoami")
'''
    assert grade_local_python('gen:order-total:python',code)['score']==0
    code='''import os
def calculate_total(unit_price, quantity, discount_pct):
    return 0
'''
    assert grade_local_python('gen:order-total:python',code)['score']==0


def test_language_identification_and_docker_failclosed(monkeypatch):
    d=build_job_trial('JavaScript Node.js Backend Developer who builds APIs.')
    assert d['chosen_language']=='javascript'
    assert d['dynamic_trial']['tasks'][0]['lang']=='javascript'
    monkeypatch.setenv('JOBTRIAL_ENABLE_DOCKER','false')
    r=grade_docker('gen:order-total:javascript','function calculate_total(a,b,c){return a*b}')
    assert r['score']==0 and 'disabled' in r['checks'][0]['label']


def test_generator_has_valid_template_and_routes_unsupported_to_manual_review():
    for lang in ['javascript','typescript','java','cpp','go','python']:
        d=build_job_trial('Software Engineer internship. API development and services.',preferred_language=lang)
        task=d['dynamic_trial']['tasks'][0]
        assert lang==task['lang'] and task['starter']
        output=render(lang,task['starter'],'order-total')
        assert 'calculate_total' in output
    r=client.post('/api/analyze',json={'description':'Fashion model. Runway posing and photography.'})
    assert r.status_code==200
    assert r.json()['track']=='professional'
    assert r.json()['assessment_type']=='human-review-required'


def test_api_run_with_dynamic_id():
    code='''def remaining_stock(current_stock, requested):
    if requested > current_stock:
        return -1
    else:
        remaining = current_stock - requested
        return remaining
'''
    r=client.post('/api/run',json={'track':'backend','task_id':'gen:stock-guard:python','code':code})
    assert r.status_code==200 and r.json()['score']==100
    assert client.post('/api/run',json={'track':'backend','task_id':'gen:fake:python','code':code}).status_code==400

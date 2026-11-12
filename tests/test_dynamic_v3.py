"""Offline integration checks for dynamic job -> real assessed work samples."""
from fastapi.testclient import TestClient
from backend.main import app
from backend.adaptive import grade_local_python
from backend.job_compiler import compile_job_trial, enhanced_tests
from backend.engine import grade_frontend

client=TestClient(app)


def test_job_families_generate_relevant_tasks():
    samples={
        'AI Engineer with Python machine learning classification evaluation':'ml-accuracy',
        'RAG engineer using Python embeddings retrieval and LLM pipelines':'rag-hit-rate',
        'Data Engineer Python ETL deduplication data pipelines':'data-dedupe',
        'Backend Developer REST API Python order checkout inventory':'order-total',
        'DevOps SRE Python uptime availability monitoring':'uptime-rate',
    }
    for description,expected in samples.items():
        d=compile_job_trial(description)
        assert d['track']=='backend'
        assert any(t['id'].startswith(f'gen:{expected}:python:') for t in d['dynamic_trial']['tasks'])
        assert d['compiler_version']=='3.0.0'


def test_language_switch_and_role_alignment():
    d=compile_job_trial('AI Engineer Python machine learning classification model evaluation')
    assert d['dynamic_trial']['tasks'][0]['title']!='Repair an incorrect checkout calculation'
    x=compile_job_trial('Java ML Engineer classification model accuracy confusion matrix')
    assert len(x['dynamic_trial']['tasks'])==1
    assert x['dynamic_trial']['tasks'][0]['id'].startswith('gen:model-accuracy-numeric:java:')


def test_job_specific_seed_is_repeatable():
    jd='Python Backend Developer working on order discount checkout services'
    a=compile_job_trial(jd)
    b=compile_job_trial(jd)
    assert a['dynamic_trial']['tasks'][0]['id']==b['dynamic_trial']['tasks'][0]['id']
    seed=int(a['dynamic_trial']['tasks'][0]['id'].split(':')[-1])
    assert len(enhanced_tests('order-total',seed))>6
    assert enhanced_tests('order-total',seed)[-1]!=enhanced_tests('order-total',seed+17)[-1]


def test_generated_task_accepts_multistatement_python():
    d=client.post('/api/analyze',json={'description':'Junior Python API backend internship orders checkout discount debug'}).json()
    task_id=d['dynamic_trial']['tasks'][0]['id']
    assert task_id.startswith('gen:order-total:')
    code=(
        'def calculate_total(unit_price, quantity, discount_pct):\n'
        '    price = unit_price * quantity\n'
        '    discount = price * discount_pct / 100\n'
        '    remaining = price - discount\n'
        '    return round(remaining, 2)\n'
    )
    graded=client.post('/api/run',json={'track':'backend','task_id':task_id,'code':code})
    assert graded.status_code==200 and graded.json()['score']==100


def test_generated_tasks_reject_unknown_ids_and_unsafe_code():
    assert client.post('/api/run',json={'track':'backend','task_id':'gen:order-total:python:9999999','code':'x'}).status_code==400
    assert client.post('/api/run',json={'track':'backend','task_id':'gen:fake:python:1','code':'x'}).status_code==400
    code='def calculate_total(unit_price, quantity, discount_pct):\n    return __import__("os").system("echo test")'
    assert grade_local_python('gen:order-total:python:42',code)['score']==0


def test_noncode_work_sample_is_never_falsely_graded():
    for desc in ('Digital Marketing Manager launching ad campaigns and tracking conversions',
                 'Customer Support Representative handling delivery complaints',
                 'Fashion model, runway posing and photography'):
        r=client.post('/api/analyze',json={'description':desc})
        assert r.status_code==200
        d=r.json()
        assert d['track']=='professional' and d['assessment_type']=='human-review-required'
        t=d['dynamic_trial']['tasks'][0]
        text='Situation: This example has a real stakeholder.\nDecision: I will prepare a draft deliverable for the team to review.\nEvidence: The supplied scenario describes a fictional situation, not customer records.\nNext step: Review assumptions and confirm numbers with a team member before any release.'
        grade=client.post('/api/run',json={'track':'professional','task_id':t['id'],'code':text})
        assert grade.status_code==200 and grade.json()['score']==-1
        assert grade.json()['mode']=='manual-review'


def test_frontend_contact_form_uses_different_checker():
    d=compile_job_trial('Frontend Developer HTML CSS responsive contact form accessibility')
    assert d['dynamic_trial']['tasks'][0]['id']=='contact-form'
    html=('<main><h1>Contact us</h1><form>'
          '<label for="n">Name</label><input id="n" type="text" name="name">'
          '<label for="e">Email</label><input id="e" type="email">'
          '<label for="m">Message</label><textarea id="m"></textarea>'
          '<button type="submit">Send</button></form></main>')
    css='form:focus-visible {outline:2px solid blue}\n@media (max-width:600px) { form {width:100%} }'
    assert grade_frontend(html,css,'contact-form')['score']==100

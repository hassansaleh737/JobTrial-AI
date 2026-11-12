"""AI-generated task specification and safe oracle integration tests."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.ai_numeric import oracle,validate_numeric_task,grade_custom

client=TestClient(app)
NUMERIC={
 'function_name':'estimated_order_total',
 'parameters':['price','quantity','discount'],
 'expression':'round(price * quantity * (1 - discount / 100), 2)',
 'title':'Repair a personalized order pricing workflow',
 'description':'A fictional order management service must calculate a rounded total after applying the discount percent to an order subtotal. Return the final charge to two decimal places.',
 'requirements':['Calculate subtotal before applying discount.','Apply percent, not fixed discount.','Round final answer to 2 decimals.'],
 'test_inputs':[[100,2,10],[50,3,20],[19.99,1,15],[30,4,0],[2,1,100]],
 'artifact':'Example order #A42 has 2 items, each priced 100, and a 10% discount.'
}


def test_reference_dsl_is_bounded():
    assert oracle('max(a - b,0)', ['a','b'],[5,8])==0
    assert oracle('a if a > b else b',['a','b'],[4,7])==7
    with pytest.raises(ValueError):oracle('__import__("os").system("echo danger")',['a','b'],[1,2])
    with pytest.raises(ValueError):oracle('a ** 1000000',['a','b'],[1,2])
    with pytest.raises(ValueError):oracle('a / (b - b)',['a','b'],[1,2])


def test_model_numeric_task_validates_and_grades_multistatement_python():
    spec=validate_numeric_task(NUMERIC,'AI commerce service Python orders pricing')
    assert spec is not None and len(spec['tests'])>=8
    from backend.ai_numeric import store_task
    task_id=store_task(spec,'python')
    code='def estimated_order_total(price, quantity, discount):\n    subtotal = price * quantity\n    final = subtotal * (1 - discount / 100)\n    return round(final, 2)\n'
    good=client.post('/api/run',json={'track':'backend','task_id':task_id,'code':code})
    assert good.status_code==200 and good.json()['score']==100, good.text
    bad=client.post('/api/run',json={'track':'backend','task_id':task_id,'code':'def estimated_order_total(price, quantity, discount):\n    return round(price*quantity-discount,2)'})
    assert bad.status_code==200 and bad.json()['score']<100


def test_malicious_or_invalid_generated_contract_rejected():
    assert validate_numeric_task({**NUMERIC,'expression':'open("/etc/passwd").read()'},'x') is None
    assert validate_numeric_task({**NUMERIC,'parameters':['x','x']},'x') is None
    assert validate_numeric_task({**NUMERIC,'function_name':'__dunder__'},'x') is None


def test_hf_authored_task_shows_in_workflow(monkeypatch):
    from backend import main
    mission={
      'role_title':'Junior Python Platform Developer','skills':['Python','Backend'],
      'manager_brief':'We need to correct pricing urgently.',
      'mission_title':'Fix the invoice logic','scenario':'A fictional subscription company must validate totals before sending invoices.',
      'artifact':'Product example: unit price 100, quantity 2, discount 10%',
      'deliverable':'Correct Python function','instructions':['Read function contract','Fix code'],
      'acceptance_criteria':['Correct monetary amount'],
      'coach_tip':'Check percentage math','blueprint_ids':['order-total'],
      'difficulty_reason':'Beginner code editing', 'custom_numeric_task':NUMERIC}
    async def hf(*args,**kwargs):return mission
    monkeypatch.setattr(main,'call_hf',hf)
    r=client.post('/api/analyze',json={'description':'Backend Developer Python REST API order pricing','use_ai':True,'difficulty_level':'easy','difficulty_percent':20})
    assert r.status_code==200, r.text
    data=r.json()
    assert data['custom_task_validated'] is True
    assert data['dynamic_trial']['tasks'][0]['id'].startswith('aifn:')
    assert 'Numeric reference rule:' in ' '.join(data['dynamic_trial']['tasks'][0]['spec'])


def test_non_python_numeric_requires_optin_docker(monkeypatch):
    from backend.ai_numeric import store_task
    spec=validate_numeric_task(NUMERIC,'Developer JS')
    task=store_task(spec,'javascript')
    monkeypatch.setenv('JOBTRIAL_ENABLE_DOCKER','false')
    resp=client.post('/api/run',json={'track':'backend','task_id':task,'code':'function estimated_order_total(price,quantity,discount){return price*quantity*(1-discount/100)}'})
    assert resp.status_code==200
    assert resp.json()['mode']=='docker-disabled'

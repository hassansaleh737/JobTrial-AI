"""v4 acceptance tests with a mocked HF model; never charge an actual user."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.ai_missions import LEVELS, build_v4, _model_json, AIError

client=TestClient(app)
FAKE_MISSION={
 'role_title':'AI Engineer Intern','field':'coding','skills':['Python','Machine Learning','RAG'],
 'manager_brief':'Your simulated ML team has a quality incident.',
 'mission_title':'Investigate a drop in model quality',
 'scenario':'A fictional ML lab deployed a classifier. A recent test shows inconsistent accuracy, and your lead needs evidence for the incident report.',
 'artifact':'Actual: [1,0,1,1], Predicted: [1,1,1,0]',
 'deliverable':'Fix model evaluation and provide a verified result.',
 'instructions':['Inspect the evaluation function.','Correct the returned metric.','Run automated tests.'],
 'acceptance_criteria':['Calculate accuracy correctly.','Use the declared function signature.'],
 'coach_tip':'Compare each prediction to the true label.',
 'blueprint_ids':['ml-accuracy','rag-hit-rate','totally-fake-task'],
 'difficulty_reason':'Complete several linked evaluation problems and edge cases.'
}

def test_levels_are_ordered_nonoverlapping_and_complete():
    items=list(LEVELS.values())
    assert [(x['min'],x['max']) for x in items]==[(10,25),(26,45),(46,65),(66,85),(86,100)]


def test_ai_rejected_when_no_token(monkeypatch):
    monkeypatch.delenv('HF_TOKEN',raising=False)
    resp=client.post('/api/analyze',json={'description':'AI Engineer Python machine learning','use_ai':True,'difficulty_level':'easy','difficulty_percent':20})
    assert resp.status_code==503 and 'HF_TOKEN' in resp.json()['detail']


def test_no_silent_fallback(monkeypatch):
    from backend import main
    async def fails(*args,**kwargs):raise AIError('HF quota exhausted')
    monkeypatch.setattr(main,'call_hf',fails)
    r=client.post('/api/analyze',json={'description':'AI Engineer machine learning','use_ai':True})
    assert r.status_code==503 and 'quota' in r.json()['detail']


def test_real_ai_route_mocked_structured_work(monkeypatch):
    from backend import main
    async def fake(*args,**kwargs):return FAKE_MISSION
    monkeypatch.setattr(main,'call_hf',fake)
    desc='AI Engineer Intern Python Machine Learning classification RAG retrieval F1 model evaluation'
    r=client.post('/api/analyze',json={'description':desc,'use_ai':True,'difficulty_level':'expert','difficulty_percent':98})
    assert r.status_code==200, r.text
    body=r.json()
    assert body['ai_used'] and body['generation_mode']=='huggingface'
    assert body['difficulty_percent']==98 and len(body['dynamic_trial']['tasks'])==1
    assert FAKE_MISSION['scenario'] in body['dynamic_trial']['tasks'][0]['goal']
    assert 'totally-fake-task' not in ' '.join(x['id'] for x in body['dynamic_trial']['tasks'])
    assert all(x['id'].startswith('pack:ml-expert:') for x in body['dynamic_trial']['tasks'])
    assert 'reference' not in str(body).lower()


def test_non_tech_generates_specific_work_for_unlisted_job(monkeypatch):
    from backend import main
    async def fake(*args,**kwargs):return {**FAKE_MISSION,'role_title':'Museum Operations Coordinator','field':'professional','mission_title':'Schedule visitor support','deliverable':'An actionable visitor support roster'}
    monkeypatch.setattr(main,'call_hf',fake)
    r=client.post('/api/analyze',json={'description':'Museum visitor operations coordinator with guest support and shift planning','use_ai':True})
    assert r.status_code==200, r.text
    body=r.json()
    assert body['track']=='professional'
    assert body['dynamic_trial']['tasks'][0]['title']=='Schedule visitor support'
    assert FAKE_MISSION['scenario'] in body['dynamic_trial']['tasks'][0]['goal']
    task=body['dynamic_trial']['tasks'][0]
    grade=client.post('/api/run',json={'track':'professional','task_id':task['id'],'code':'Situation: visitor support. Decision: propose shifts. Evidence: constraints and limitations. Next step: manager review.'})
    assert grade.status_code==200 and grade.json()['score']==-1


def test_invalid_level_intensity_is_rejected():
    r=client.post('/api/analyze',json={'description':'Backend Developer Python','difficulty_level':'easy','difficulty_percent':95})
    assert r.status_code==422


def test_offline_demo_marked_not_ai():
    r=client.post('/api/analyze',json={'description':'ML Engineer machine learning RAG evaluation','difficulty_level':'hard','difficulty_percent':75,'use_ai':False})
    assert r.status_code==200 and r.json()['ai_used'] is False
    assert r.json()['generation_mode']=='offline-demo'


def test_bad_model_output_is_not_silently_tolerated():
    with pytest.raises(AIError):_model_json('not json')


def test_ai_generated_numeric_task_not_trusted_as_executable():
    a=build_v4('AI Engineer Python ML classification', {**FAKE_MISSION, 'blueprint_ids':['__import__("os")']},'easy',20,None,'python')
    assert a['track']=='backend'
    assert all(x['id'].split(':')[1] != '__import__("os")' for x in a['dynamic_trial']['tasks'])

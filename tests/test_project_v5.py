"""V5 regression tests. No real HF calls, no real Docker required."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import tempfile

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.project_packs import PACKS,_oracle,_docker_script,grade_project,project_task

client=TestClient(app)
LEVELS=[('easy',20),('medium',38),('advanced',58),('hard',78),('expert',95)]

@pytest.mark.parametrize('description,expected',[
    ('Frontend Developer React JavaScript accessibility UI', 'fe'),
    ('Backend Developer Node.js JavaScript REST API', 'be'),
    ('AI Engineer Python machine learning model evaluation RAG', 'ml'),
])
def test_five_levels_really_select_different_contracts(description,expected):
    ids=[];titles=[]
    for level,percent in LEVELS:
        r=client.post('/api/analyze',json={'description':description,'use_ai':False,'difficulty_level':level,'difficulty_percent':percent})
        assert r.status_code==200,r.text
        obj=r.json()
        task=obj['dynamic_trial']['tasks'][0]
        assert task['id'].startswith(f'pack:{expected}-{level}:')
        assert len(task['files'])==4
        assert any(f['path'].startswith('src/solution.') and f['editable'] for f in task['files'])
        assert all(f['path']!='work_sample.md' for f in task['files'])
        assert 'Markdown' not in task['tag']
        assert obj['version']=='6.0.0'
        ids.append(task['id']);titles.append(task['title'])
    assert len(set(ids))==len(set(titles))==5


def test_python_expanded_solution_still_supported():
    from backend.adaptive import grade_local_python
    from backend.job_compiler import task_seed
    task='gen:order-total:python:1'
    code='def calculate_total(unit_price, quantity, discount_pct):\n    total = unit_price * quantity\n    result = total * (1 - discount_pct/100)\n    return round(result, 2)\n'
    result=grade_local_python(task,code)
    assert result['score']==100,result


def test_ai_uses_fictional_brief_but_technical_contract_is_fixed(monkeypatch):
    from backend import main
    async def fake(*_args,**_kwargs):
        return {'role_title':'Frontend Developer','scenario':'A team needs a registration form for new users.','manager_brief':'Help repair signup.','skills':['JavaScript','Forms'], 'mission_title':'Improve signup','instructions':['Inspect the supplied code','Run tests'],'blueprint_ids':[]}
    monkeypatch.setattr(main,'call_hf',fake)
    r=client.post('/api/analyze',json={'description':'Frontend Developer JavaScript React','use_ai':True,'difficulty_level':'expert','difficulty_percent':95})
    assert r.status_code==200,r.text
    obj=r.json();t=obj['dynamic_trial']['tasks'][0]
    assert t['id'].startswith('pack:fe-expert:')
    assert t['evaluation']=='automated-docker'
    assert 'orderUpdates' in t['files'][0]['content']
    assert obj['ai_used'] is True


def test_docker_disabled_reports_clear_reason(monkeypatch):
    monkeypatch.delenv('JOBTRIAL_ENABLE_DOCKER',raising=False)
    r=client.post('/api/analyze',json={'description':'Frontend Developer React JavaScript','difficulty_level':'easy','difficulty_percent':20})
    task=r.json()['dynamic_trial']['tasks'][0]
    files={f['path']:f['content'] for f in task['files'] if f['editable']}
    grade=client.post('/api/run',json={'track':'frontend','task_id':task['id'],'files':files}).json()
    assert grade['score']==0 and 'Docker' in grade['checks'][0]['label']


def test_file_paths_restricted(monkeypatch):
    monkeypatch.setenv('JOBTRIAL_ENABLE_DOCKER','true')
    monkeypatch.setattr('backend.project_packs.shutil.which',lambda _: '/usr/bin/docker')
    grade=grade_project('pack:fe-easy:99:20',{'src/solution.js':'x','src/helpers.js':'x','../../evil.js':'x'})
    assert grade['score']==0 and 'Expected files' in grade['checks'][0]['label']


def test_all_fifteen_reference_contracts_are_valid():
    assert len(PACKS)==15
    for key,pack in PACKS.items():
        assert len(pack['cases'])>=5
        for case in pack['cases']:
            _oracle(key,case)


@pytest.mark.parametrize('pack_id',["fe-easy","fe-hard","be-easy","be-expert","ml-easy","ml-expert"])
def test_runner_executes_example_starters_without_parser_crashes(pack_id):
    pack=PACKS[pack_id];lang=pack.get('language','javascript');ext='py' if lang=='python' else 'js'
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);(root/'src').mkdir()
        (root/'src'/('solution.'+ext)).write_text(pack['starter'],encoding='utf8')
        (root/'src'/('helpers.'+ext)).write_text('' if lang=='python' else 'module.exports={};',encoding='utf8')
        runner=root/('runner.py' if lang=='python' else 'runner.js')
        runner.write_text(_docker_script(pack_id,pack['cases']),encoding='utf8')
        proc=subprocess.run(['python' if lang=='python' else 'node',str(runner)],cwd=root,capture_output=True,text=True,timeout=8)
        assert proc.returncode==0,proc.stderr
        lines=[x for x in proc.stdout.splitlines() if x.startswith('JOBTRIAL_V5_OUTPUT:')]
        assert len(lines)==1
        out=json.loads(lines[0].split('JOBTRIAL_V5_OUTPUT:',1)[1])
        assert len(out)==len(pack['cases'])


def test_percentage_affects_number_of_cases(monkeypatch):
    # Capture runner results from a trusted reference; don't execute student code on host.
    from backend import project_packs
    monkeypatch.setenv('JOBTRIAL_ENABLE_DOCKER','true')
    monkeypatch.setattr(project_packs.shutil,'which',lambda _: '/usr/bin/docker')
    def fake_run(args,**_kwargs):
        percent=int(active[0]);full=PACKS['be-easy']['cases'];count=3 if percent==10 else 5
        seed=99;ordered=(full[seed%len(full):]+full[:seed%len(full)])[:count]
        vals=[{'value':_oracle('be-easy',x)} for x in ordered]
        return subprocess.CompletedProcess(args,0,'JOBTRIAL_V5_OUTPUT:'+json.dumps(vals), '')
    monkeypatch.setattr(project_packs.subprocess,'run',fake_run)
    active=['10']
    files={'src/solution.js':'test','src/helpers.js':'test'}
    lower=grade_project('pack:be-easy:99:10',files)
    active[0]='25'
    higher=grade_project('pack:be-easy:99:25',files)
    assert lower['total']==3 and higher['total']==5
    assert lower['score']==higher['score']==100

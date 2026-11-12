"""V6 regression: adjacent slider values select independent trusted contracts."""
from pathlib import Path
import json, subprocess, tempfile
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.alternate_contracts import ALTERNATES,oracle as alt_oracle
from backend.project_packs import PACKS,_docker_script,project_task,grade_project,variant_for,contract_for
from backend.ai_missions import LEVELS

client=TestClient(app)
DESCRIPTIONS={
    'fe':'Frontend Developer using React and JavaScript with accessibility and forms',
    'be':'Backend Developer using Node.js JavaScript APIs for production orders',
    'ml':'Machine Learning AI Engineer Python classification model evaluation RAG',
}

@pytest.mark.parametrize('prefix,description',list(DESCRIPTIONS.items()))
@pytest.mark.parametrize('level',list(LEVELS))
def test_adjacent_percent_changes_actual_task(prefix,description,level):
    lo=LEVELS[level]['min']
    def analyze(percent,reroll=0):
        response=client.post('/api/analyze',json={'description':description,'difficulty_level':level,
            'difficulty_percent':percent,'variation_index':reroll,'use_ai':False})
        assert response.status_code==200,response.text
        task=response.json()['dynamic_trial']['tasks'][0]
        return response.json(),task
    a,task_a=analyze(lo)
    b,task_b=analyze(lo+1)
    assert a['version']==b['version']=='6.0.0'
    assert task_a['title'] != task_b['title']
    assert task_a['spec'] != task_b['spec']
    assert task_a['files'][0]['content'] != task_b['files'][0]['content']
    assert task_a['id'] != task_b['id']
    _,task_c=analyze(lo,1)
    assert task_a['title'] != task_c['title']

@pytest.mark.parametrize('pack_id', sorted(ALTERNATES))
def test_alt_contract_has_executable_starter_and_independent_oracle(pack_id):
    pack=ALTERNATES[pack_id]
    assert len(pack['cases'])==5
    assert len(set(str(x) for x in pack['cases']))>=4
    for case in pack['cases']:
        alt_oracle(pack_id,case)
    ext='py' if pack['language']=='python' else 'js'
    with tempfile.TemporaryDirectory() as dirname:
        root=Path(dirname);(root/'src').mkdir()
        (root/'src'/('solution.'+ext)).write_text(pack['starter'],encoding='utf8')
        (root/'src'/('helpers.'+ext)).write_text(pack['helper'],encoding='utf8')
        runner=root/('runner.py' if ext=='py' else 'runner.js')
        runner.write_text(_docker_script(pack_id,pack['cases'],variant=1),encoding='utf8')
        result=subprocess.run(['python' if ext=='py' else 'node',str(runner)],cwd=root,capture_output=True,text=True,timeout=8)
        assert result.returncode==0,(pack_id,result.stderr)
        lines=[x for x in result.stdout.splitlines() if x.startswith('JOBTRIAL_V5_OUTPUT:')]
        assert len(lines)==1
        assert len(json.loads(lines[0].split('JOBTRIAL_V5_OUTPUT:')[1]))==5


def test_original_legacy_pack_id_still_accepts_previous_solutions(monkeypatch):
    monkeypatch.delenv('JOBTRIAL_ENABLE_DOCKER',raising=False)
    old=grade_project('pack:be-easy:99:20',{'src/solution.js':'', 'src/helpers.js':''})
    assert old['checks'][0]['label']=='Docker enabled'


def test_malformed_variant_is_rejected():
    out=grade_project('pack:fe-easy:99:20:v900',{})
    assert out['checks'][0]['label']=='Valid variant'

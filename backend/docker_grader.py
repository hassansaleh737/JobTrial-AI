"""Opt-in code checking in disposable, restricted Docker containers.
No user program ever runs in FastAPI's host Python interpreter.
This is a LOCAL education demo; don't deploy as a public multi-tenant code runner.
"""
from __future__ import annotations
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from .adaptive import CASES,NUMERIC,ARRAY_LANGUAGES
from .engine import check,result

IMAGES={
 'javascript':('node:24-alpine','node main.js','main.js'),
 'typescript':('node:24-alpine','node --experimental-strip-types main.ts','main.ts'),
 'java':('eclipse-temurin:21-jdk','sh -c "javac -d /tmp Main.java && java -cp /tmp Main"','Main.java'),
 'cpp':('gcc:14','sh -c "g++ -std=c++17 -O1 -o /tmp/jt Main.cpp && /tmp/jt"','Main.cpp'),
 'go':('golang:1.24-alpine','sh -c "GOCACHE=/tmp/go-cache go build -o /tmp/jt main.go && /tmp/jt"','main.go'),
 'python':('python:3.12-alpine','python main.py','main.py'),
}
PREFIX='JOBTRIAL_CHECKS:'

def render(lang:str,code:str,scenario:str,seed:int=0)->str:
    from .job_compiler import enhanced_tests
    p=CASES[scenario];name=p['name'];cases=[list(args) for args,_ in enhanced_tests(scenario,seed)]
    if lang in ('javascript','typescript'):
        tests=json.dumps(cases)
        return code+f'\nconst __jtInputs = {tests};\nconsole.log("{PREFIX}" + JSON.stringify(__jtInputs.map(args => {name}(...args))));\n'
    if lang=='python':
        return code+f'\nimport json\nprint("{PREFIX}"+json.dumps([{name}(*args) for args in {repr(cases)}]))\n'
    if lang=='java':
        calls='\n'.join(f'System.out.println("{PREFIX}" + {name}({", ".join(str(float(x)) for x in c)}));' for c in cases)
        return f'public class Main {{\n{code}\npublic static void main(String[] args) {{\n{calls}\n}}\n}}'
    if lang=='cpp':
        calls='\n'.join(f'std::cout << "{PREFIX}" << {name}({", ".join(str(float(x)) for x in c)}) << "\\n";' for c in cases)
        return '#include <iostream>\n#include <iomanip>\n'+code+'\nint main(){std::cout << std::setprecision(15);\n'+calls+'\n}'
    if lang=='go':
        calls='\n'.join(f'fmt.Println("{PREFIX}", {name}({", ".join(str(float(x)) for x in c)}))' for c in cases)
        return 'package main\nimport "fmt"\n'+code+'\nfunc main(){\n'+calls+'\n}'
    raise ValueError('Unsupported language')

def grade_docker(task_id:str,code:str)->dict:
    try:
        parts=task_id.split(':')
        if len(parts) not in (3,4):raise ValueError('Unknown generated task')
        _,scenario,lang=parts[:3]
        seed=int(parts[3]) if len(parts)==4 and parts[3].isdigit() else 0
        if lang not in IMAGES or scenario not in CASES or (lang not in ARRAY_LANGUAGES and scenario not in NUMERIC):
            raise ValueError('No validated tests available for this language / assignment')
    except ValueError as exc:
        return result([check('Valid selected language',False,str(exc))],'Choose a language with a matching validated task.',None,'docker-unavailable')
    if not os.getenv('JOBTRIAL_ENABLE_DOCKER','false').lower() in ('1','true','yes'):
        return result([check('Docker runner disabled',False,'Set JOBTRIAL_ENABLE_DOCKER=true in .env to use unrestricted code syntax in isolated local Docker containers.')],
                      'Docker assessment is opt-in. Python local interpreter works without Docker.',None,'docker-disabled')
    if not shutil.which('docker'):
        return result([check('Docker executable not found',False,'Install Docker Desktop, start it and run docker version.')],
                      'Docker is required to execute this language safely.',None,'docker-unavailable')
    if len(code)>6000:return result([check('Code length',False,'Maximum 6,000 characters')],'Shorten the submission.',None,'docker')
    image,command,filename=IMAGES[lang]
    try:
        with tempfile.TemporaryDirectory(prefix='jobtrial_',dir=None) as tmp:
            os.chmod(tmp,0o755)  # container's unprivileged user must be able to read the mount
            path=Path(tmp)/filename
            path.write_text(render(lang,code,scenario,seed),encoding='utf-8')
            os.chmod(path,0o644)
            # Docker Desktop can read the directory through a readonly host bind mount.
            # User code runs as nobody with no network, no caps, read-only root and strict limits.
            args=['docker','run','--rm','--pull=never','--network=none','--read-only',
                  '--memory=256m','--memory-swap=256m','--cpus=0.75','--pids-limit=48',
                  '--cap-drop=ALL','--security-opt=no-new-privileges:true','--user=65534:65534',
                  '--tmpfs=/tmp:rw,nosuid,nodev,size=96m,mode=1777',
                  '--mount',f'type=bind,src={Path(tmp).resolve()},dst=/workspace,readonly',
                  '--workdir=/workspace',image,'sh','-c',command]
            proc=subprocess.run(args,capture_output=True,text=True,timeout=12,check=False)
    except subprocess.TimeoutExpired:
        return result([check('Time limit',False,'Execution exceeded 12 seconds')],'Reduce your runtime complexity.',None,'docker')
    except (OSError,ValueError) as exc:
        return result([check('Docker runtime unavailable',False,str(exc)[:190])],'Start Docker Desktop and verify the required image exists.',None,'docker')
    if proc.returncode!=0:
        detail=(proc.stderr or proc.stdout or 'Container could not start')[-450:]
        return result([check('Compile and execute',False,detail)],
                      f'Compilation or execution failed. Required image: {image}. Pull it once with: docker pull {image}',None,'docker')
    raw=[line.strip().removeprefix(PREFIX).strip() for line in proc.stdout.splitlines() if line.strip().startswith(PREFIX)]
    from .job_compiler import enhanced_tests
    expected=enhanced_tests(scenario,seed)
    try:
        if lang in ('javascript','typescript','python'):
            if len(raw)!=1:raise ValueError('Assessment output missing')
            observed=json.loads(raw[0])
        else:
            observed=[float(x) for x in raw]
        if not isinstance(observed,list) or len(observed)!=len(expected):raise ValueError('Wrong number of results')
        observed=[float(x) for x in observed]
    except (TypeError,ValueError,json.JSONDecodeError) as exc:
        return result([check('Assessment output',False,str(exc)[:170])],'Program did not produce the expected result format.',None,'docker')
    checks=[]
    for i,((inputs,want),got) in enumerate(zip(expected,observed)):
        passed=math.isfinite(got) and math.isclose(float(want),got,rel_tol=1e-8,abs_tol=.001)
        detail=f'Expected {want}, got {got}' if i<3 else ('Hidden scenario passed' if passed else 'Hidden scenario failed')
        checks.append(check(f'Test {i+1}',passed,detail))
    return result(checks,'All test scenarios passed.' if all(t['passed'] for t in checks) else 'Some test scenarios failed.',None,f'docker-{lang}')


def grade_custom_docker(spec:dict,lang:str,code:str)->dict:
    """Execute an AI-authored *numeric contract* using validated reference outputs.

    The model never contributes test runner code: this module renders the trusted
    harness. The code submitted by a student is isolated within opt-in Docker.
    """
    if lang not in IMAGES:
        return result([check('Language supported',False,'Unknown language')],'Unsupported language',None,'docker-custom')
    if os.getenv('JOBTRIAL_ENABLE_DOCKER','false').lower() not in ('true','yes','1'):
        return result([check('Docker runner disabled',False,'Set JOBTRIAL_ENABLE_DOCKER=true in .env to run JavaScript, TypeScript, Java, C++, or Go in a local container.')],
                      'Please enable Docker Desktop and the local runner.',None,'docker-disabled')
    if not shutil.which('docker'):
        return result([check('Docker executable missing',False,'Install/start Docker Desktop and verify docker version.')],'Docker not available.',None,'docker-unavailable')
    if len(code)>6000:
        return result([check('Code length limit',False,'Maximum 6,000 characters')],'Submission too long.',None,'docker-custom')
    image,command,filename=IMAGES[lang]
    name=spec['name']
    cases=[values for values,_ in spec['tests']]
    if lang in ('javascript','typescript'):
        harness=code+'\nconst __inputs = '+json.dumps(cases)+';\nconsole.log("'+PREFIX+'"+JSON.stringify(__inputs.map(a => '+name+'(...a))));\n'
    elif lang=='python':
        harness=code+f'\nimport json\nprint("{PREFIX}"+json.dumps([{name}(*a) for a in {repr(cases)}]))\n'
    elif lang=='java':
        calls='\n'.join(f'System.out.println("{PREFIX}"+{name}({", ".join(repr(float(x)) for x in values)}));' for values in cases)
        harness='public class Main {\n'+code+'\npublic static void main(String[] args){\n'+calls+'\n}\n}'
    elif lang=='cpp':
        calls='\n'.join(f'std::cout << "{PREFIX}" << {name}({", ".join(repr(float(x)) for x in values)}) << "\\n";' for values in cases)
        harness='#include <iostream>\n#include <iomanip>\n'+code+'\nint main(){std::cout<<std::setprecision(16);\n'+calls+'\n}'
    else:
        calls='\n'.join(f'fmt.Println("{PREFIX}", {name}({", ".join(repr(float(x)) for x in values)}))' for values in cases)
        harness='package main\nimport "fmt"\n'+code+'\nfunc main(){\n'+calls+'\n}'
    try:
        with tempfile.TemporaryDirectory(prefix='jobtrial_ai_') as tmp:
            os.chmod(tmp,0o755)
            p=Path(tmp)/filename
            p.write_text(harness,encoding='utf-8');os.chmod(p,0o644)
            flags=['docker','run','--rm','--pull=never','--network=none','--read-only','--memory=256m','--memory-swap=256m',
                   '--cpus=0.75','--pids-limit=48','--cap-drop=ALL','--security-opt=no-new-privileges:true','--user=65534:65534',
                   '--tmpfs=/tmp:rw,nosuid,nodev,size=96m,mode=1777',
                   '--mount',f'type=bind,src={Path(tmp).resolve()},dst=/workspace,readonly','--workdir=/workspace',
                   image,'sh','-c',command]
            proc=subprocess.run(flags,capture_output=True,text=True,timeout=12,check=False)
    except subprocess.TimeoutExpired:
        return result([check('Timeout',False,'Execution exceeded 12 seconds')],'Optimize the code or simplify it.',None,'docker-custom')
    except (OSError,ValueError) as exc:
        return result([check('Docker unavailable',False,str(exc)[:190])],'Docker execution failed.',None,'docker-custom')
    if proc.returncode!=0:
        return result([check('Compile / execution',False,(proc.stderr or proc.stdout or 'Runtime failed')[-450:])],
                      f'The program did not run. Make sure the image is pulled: docker pull {image}',None,'docker-custom')
    outputs=[line.strip()[len(PREFIX):].strip() for line in proc.stdout.splitlines() if line.strip().startswith(PREFIX)]
    try:
        if lang in ('javascript','typescript','python'):
            if len(outputs)!=1:raise ValueError('Expected one assessment output')
            observed=json.loads(outputs[0])
        else:observed=[float(x) for x in outputs]
        if not isinstance(observed,list) or len(observed)!=len(spec['tests']):raise ValueError('Wrong result count')
        if any(type(x) not in (float,int) for x in observed):raise ValueError('Non-numeric answer')
    except (TypeError,ValueError,json.JSONDecodeError) as exc:
        return result([check('Valid output',False,str(exc)[:200])],'Output format mismatch.',None,'docker-custom')
    tests=[]
    for i,((args,expected),actual) in enumerate(zip(spec['tests'],observed)):
        ok=math.isfinite(actual) and math.isclose(float(expected),float(actual),rel_tol=1e-8,abs_tol=.001)
        detail=(f'Input {args}: expected {expected:g}, got {actual:g}' if i<3 else ('Hidden case passed' if ok else 'Hidden case failed'))
        tests.append(check(f'Test {i+1}',ok,detail))
    return result(tests,'Tested against an AI-authored mathematical contract; semantic assumptions still require human review.',None,'docker-custom-'+lang)

"""AI-designed numeric programming challenges using a narrowly validated oracle DSL.

Only mathematical expressions are accepted as reference functions, never Python exec/eval.
Results can be tested in the existing bounded Python interpreter or opt-in Docker.
Semantic realism remains a model limitation; numerical consistency is independently checked.
"""
from __future__ import annotations
import ast
import hashlib
import json
import math
import operator
import random
import re
import sqlite3
import uuid
from pathlib import Path
from typing import Any
from .engine import result,check

DB_PATH=Path(__file__).resolve().parent/'data'/'history.sqlite3'
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,
     ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod}
CMP={ast.Lt:operator.lt,ast.LtE:operator.le,ast.Gt:operator.gt,ast.GtE:operator.ge,ast.Eq:operator.eq,ast.NotEq:operator.ne}
FUNCS={'abs':abs,'min':min,'max':max,'round':round}


def oracle(expression:str,args:list[str],values:list[float])->float:
    """Bounded AST recursive evaluator, not exec, eval or SymPy sympify."""
    if len(expression)>280 or len(args)>5 or len(values)!=len(args):raise ValueError('Invalid reference rule')
    try:tree=ast.parse(expression,mode='eval')
    except SyntaxError as exc:raise ValueError('Invalid reference expression') from exc
    if len(list(ast.walk(tree)))>55:raise ValueError('Reference expression too complex')
    mapping=dict(zip(args,values));count=[0]
    def safe(v):
        if type(v) not in (int,float,bool):raise ValueError('Only scalar numeric answers allowed')
        if not math.isfinite(v) or abs(v)>1e8:raise ValueError('Numeric bound exceeded')
        return v
    def visit(n,depth=0):
        count[0]+=1
        if count[0]>65 or depth>12:raise ValueError('Expression too complex')
        ev=lambda child:visit(child,depth+1)
        if isinstance(n,ast.Expression):return ev(n.body)
        if isinstance(n,ast.Constant) and type(n.value) in (int,float,bool):return safe(n.value)
        if isinstance(n,ast.Name) and n.id in mapping:return safe(mapping[n.id])
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.USub,ast.UAdd)):
            return safe(-ev(n.operand) if isinstance(n.op,ast.USub) else +ev(n.operand))
        if isinstance(n,ast.BinOp) and type(n.op) in OPS:return safe(OPS[type(n.op)](ev(n.left),ev(n.right)))
        if isinstance(n,ast.Compare) and len(n.ops)==1 and type(n.ops[0]) in CMP:
            return safe(CMP[type(n.ops[0])](ev(n.left),ev(n.comparators[0])))
        if isinstance(n,ast.IfExp):return safe(ev(n.body) if ev(n.test) else ev(n.orelse))
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in FUNCS and not n.keywords and len(n.args)<=3:
            return safe(FUNCS[n.func.id](*(ev(a) for a in n.args)))
        raise ValueError('Unsupported operation in model-generated reference expression')
    try:return safe(visit(tree))
    except (ZeroDivisionError,TypeError,OverflowError,ArithmeticError) as exc:raise ValueError('Invalid numeric operation') from exc


def validate_numeric_task(payload:Any,source:str)->dict|None:
    if not isinstance(payload,dict):return None
    name=payload.get('function_name');args=payload.get('parameters');expr=payload.get('expression')
    if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9_]{2,39}',name):return None
    if not isinstance(args,list) or not 2<=len(args)<=5 or any(not isinstance(a,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,22}',a) for a in args) or len(args)!=len(set(args)):return None
    if not isinstance(expr,str):return None
    title=str(payload.get('title','')).strip()[:100]
    description=str(payload.get('description','')).strip()[:600]
    if len(title)<6 or len(description)<35:return None
    tests=[]
    supplied=payload.get('test_inputs')
    if isinstance(supplied,list):
        for v in supplied[:12]:
            if isinstance(v,list) and len(v)==len(args) and all(type(x) in (int,float) and math.isfinite(x) and abs(x)<=10000 for x in v):
                try:out=oracle(expr,args,v)
                except ValueError:continue
                tests.append((v,float(out)))
    # Independent deterministic input variations, never model-provided expected outputs.
    seed=int(hashlib.sha256((source+name+expr).encode()).hexdigest()[:10],16)
    rng=random.Random(seed)
    presets=[[1]*len(args),[2]*len(args),[10]*len(args),[5,10,15,20,25][:len(args)]]
    for v in presets+[[rng.randint(1,35) for _ in args] for _ in range(14)]:
        if len(tests)>=14:break
        if v in [row[0] for row in tests]:continue
        try:out=oracle(expr,args,v)
        except ValueError:continue
        tests.append((v,float(out)))
    if len(tests)<8:return None
    return {'name':name,'args':args,'expression':expr,'title':title,'description':description,
      'requirements':[str(x)[:170] for x in payload.get('requirements',[])[:4] if isinstance(x,str)] if isinstance(payload.get('requirements'),list) else [],
      'tests':tests,'artifact':str(payload.get('artifact',''))[:600]}


def store_task(spec:dict,lang:str)->str:
    uid=uuid.uuid4().hex[:16]
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS ai_numeric_tasks (id TEXT PRIMARY KEY, spec TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP)')
        conn.execute('INSERT INTO ai_numeric_tasks (id,spec) VALUES (?,?)',(uid,json.dumps(spec)))
    return f'aifn:{uid}:{lang}'


def load_task(task_id:str)->tuple[dict,str]:
    parts=task_id.split(':')
    if len(parts)!=3 or parts[0]!='aifn' or not re.fullmatch(r'[a-f0-9]{16}',parts[1]) or parts[2] not in {'python','javascript','typescript','java','cpp','go'}:
        raise ValueError('Unknown AI numeric task')
    with sqlite3.connect(DB_PATH) as conn:
        try:r=conn.execute('SELECT spec FROM ai_numeric_tasks WHERE id=?',(parts[1],)).fetchone()
        except sqlite3.OperationalError:r=None
    if not r:raise ValueError('AI task expired or unavailable on this local server. Generate it again.')
    return json.loads(r[0]),parts[2]


def numeric_starter(spec:dict,lang:str)->str:
    name=spec['name'];args=spec['args'];names=', '.join(args)
    if lang=='python':return f'def {name}({names}):\n    # Implement the rule described in the assignment\n    return 0'
    if lang=='javascript':return f'function {name}({names}) {{\n  // Implement the rule\n  return 0;\n}}'
    if lang=='typescript':return f'function {name}({", ".join(a+": number" for a in args)}): number {{\n  return 0;\n}}'
    if lang=='java':return f'public static double {name}({", ".join("double "+a for a in args)}) {{\n  return 0;\n}}'
    if lang=='cpp':return f'double {name}({", ".join("double "+a for a in args)}) {{\n  return 0;\n}}'
    if lang=='go':return f'func {name}({", ".join(a+" float64" for a in args)}) float64 {{\n  return 0\n}}'
    raise ValueError('Unsupported language')


def custom_task(spec:dict,lang:str,level:str)->dict:
    from .ai_missions import LEVELS
    return {'id':store_task(spec,lang),'title':spec['title'],
      'tag':f'{lang.upper()} · AI-authored numeric problem · {LEVELS[level]["label"]}',
      'time':f'{LEVELS[level]["minutes"]} min',
      'goal':spec['description']+'\n\nImplement function '+spec['name']+'('+', '.join(spec['args'])+').',
      'spec':spec['requirements']+[f'Numeric reference rule: {spec["expression"]}',
                              'Keep the function name and its numeric parameters unchanged.'],
      'starter':numeric_starter(spec,lang),'hint':'Follow the provided numeric rule; test boundary values and rounding carefully.' if level=='easy' else 'Review boundaries and compare your output with the stated contract.',
      'lang':lang,'ai_artifact':spec.get('artifact','')}


def grade_custom(task_id:str,code:str)->dict:
    spec,lang=load_task(task_id)
    if lang!='python':
        from .docker_grader import grade_custom_docker
        return grade_custom_docker(spec,lang,code)
    from .safe_python import Interpreter
    try:interp=Interpreter(code,spec['name'],spec['args'])
    except (ValueError,RecursionError,MemoryError) as exc:
        return result([check('Valid Python solution',False,str(exc)[:240])],'Check your function name, parameters and supported syntax.',None,'ai-numeric-python')
    checks=[]
    for i,(v,expected) in enumerate(spec['tests']):
        try:
            actual=interp.run(v)
            ok=type(actual) in (int,float) and math.isclose(actual,expected,abs_tol=.001,rel_tol=1e-8)
            detail=(f'Inputs {v} · expected {expected:g}, got {actual}' if i<3 else ('Hidden case passed' if ok else 'Hidden case failed'))
        except (ValueError,TypeError,IndexError,ZeroDivisionError,RecursionError,ArithmeticError) as exc:
            ok=False;detail=str(exc)[:170] if i<3 else 'Hidden case failed'
        checks.append(check(f'Test {i+1}',ok,detail))
    return result(checks,'AI-authored numerical assignment; answers verified against the recorded reference expression. This does not validate the model’s real-world assumptions.',None,'ai-numeric-python')

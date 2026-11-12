"""Match an arbitrary job *description* to a transparent, prevalidated work task.
Generated brief is tailored; code harnesses are NEVER generated from untrusted LLM text.
"""
from __future__ import annotations
import re
import math
from .safe_python import Interpreter

# A bounded, deterministic library of meaningful skills and workplace tasks.
# A job can have any title; evaluation capabilities still have explicit limits.
CASES={
 'order-total':{'name':'calculate_total','args':['unit_price','quantity','discount_pct'],
  'tests':[((100,2,10),180),((19.99,3,15),50.97),((80,1,0),80),((50,2,100),0),((100,0,5),0),((12.5,4,20),40)],
  'title':'Repair an incorrect checkout calculation','goal':'The order service treats a percentage discount as a fixed amount. Correct the total calculation and return a value rounded to 2 decimals.',
  'spec':['Final total = unit price × quantity × (1 − discount percentage / 100).','Discount is a percentage; support zero quantity and 0–100% discount.','Keep the function signature. Any valid implementation is acceptable.'],
  'hint':'Start from subtotal = unit_price * quantity. Then apply the percentage discount.'},
 'stock-guard':{'name':'remaining_stock','args':['current_stock','requested'],
  'tests':[((8,3),5),((5,5),0),((2,3),-1),((0,0),0),((0,1),-1),((22,0),22)],
  'title':'Stop overselling inventory','goal':'Repair the inventory guard: when requested quantity exceeds current stock, return -1; otherwise return the number left.',
  'spec':['Return -1 when requested > current_stock.','Otherwise return current_stock - requested.','Handle zero-stock and exact-quantity scenarios.'],
  'hint':'Try an if statement before subtracting.'},
 'ml-accuracy':{'name':'classification_accuracy','args':['actual','predicted'],
  'tests':[(( [1,0,1,1],[1,1,1,0] ),0.5),(( [1,0,0],[1,0,0] ),1.0),(( [0,1,0],[1,0,1] ),0.0),(( [0],[0] ),1.0),(( [1,0],[0,1] ),0.0)],
  'title':'Fix the model evaluation pipeline','goal':'Your simulated ML team has a metrics bug. Write classification_accuracy(actual, predicted) returning the fraction of correctly predicted labels.',
  'spec':['Compare each predicted label with the corresponding ground-truth label.','Return number of correct predictions divided by total predictions.','Both inputs are non-empty, equally sized lists of integer labels.'],
  'hint':'Count matches in a loop, then divide by len(actual).'},
 'data-dedupe':{'name':'unique_count','args':['identifiers'],
  'tests':[(( [1,1,2,3,2] ,),3),(( [4,4,4] ,),1),(( [5] ,),1),(( [1,2,3,4] ,),4),(( [9,8,9,8,7,7] ,),3)],
  'title':'Repair a duplicate-record reporting bug','goal':'The data pipeline overcounts repeated records. Write unique_count(identifiers) to return how many distinct integer identifiers appear.',
  'spec':['Count each integer identifier only once.','Repeated IDs must not inflate the result.','The input is a non-empty list of integers.'],
  'hint':'Create an empty list, loop through identifiers, and append unseen IDs.'},
 'ticket-sla':{'name':'sla_breaches','args':['hours','limit'],
  'tests':[(( [2,5,9,1],5 ),1),(( [10,10],10 ),0),(( [1,2,3],0 ),3),(( [0,2,4,5],4 ),1)],
  'title':'Find overdue support tickets','goal':'Your support operations dashboard misses breached tickets. Count how many resolution times exceed the SLA limit.',
  'spec':['Return the count of times strictly greater than limit.','Equal-to-limit tickets are not breaches.','Input hours is a list of nonnegative integers.'],
  'hint':'Loop over hours, then increment a counter only when value > limit.'}
}
# Additional independently testable work samples for targeted job descriptions.
CASES.update({
 'rag-hit-rate':{'name':'retrieval_recall','args':['relevant_ids','retrieved_ids'],
   'tests':[(( [1,2,3],[3,4,2] ),2/3),(( [8,9],[8,9,10] ),1.0),(( [3,5],[7,9] ),0.0),(( [1],[1] ),1.0)],
   'title':'Audit a RAG retrieval evaluation','goal':'A RAG team wants to measure whether retrieved document IDs contain the truly relevant documents. Implement retrieval_recall(relevant_ids, retrieved_ids), returning the fraction of relevant documents retrieved.',
   'spec':['Count relevant IDs that appear in retrieved_ids.','Divide by the number of relevant_ids; input lists are non-empty and contain distinct integer IDs.','Do not count irrelevant retrieved documents as relevant.'],
   'hint':'Loop over relevant_ids, check whether each is in retrieved_ids, and divide by len(relevant_ids).'},
 'ml-f1':{'name':'binary_f1','args':['actual','predicted'],
   'tests':[(( [1,0,1,1],[1,1,0,1] ),0.6666666666666666),(( [1,1,0,0],[1,1,0,0] ),1.0),(( [1,1],[0,0] ),0.0),(( [0,0,1],[0,0,1] ),1.0)],
   'title':'Repair a binary classification F1 metric','goal':'An ML experiment report miscalculates F1. Implement binary_f1(actual, predicted), returning the F1 score for positive label 1. Return 0 when precision/recall is undefined.',
   'spec':['Compute TP, FP and FN from matching pairs of binary integer labels.','F1 = 2 × TP / (2 × TP + FP + FN) when the denominator is positive; otherwise 0.','Input lists have equal, non-zero length.'],
   'hint':'Count true positives, false positives and false negatives using a loop.'},
 'forecast-mae':{'name':'mean_absolute_error','args':['actual','predicted'],
   'tests':[(( [2,4,6],[3,5,5] ),1.0),(( [1,2,3],[1,2,3] ),0.0),(( [10,0],[8,4] ),3.0),(( [7],[2] ),5.0)],
   'title':'Verify a forecasting error metric','goal':'A reporting dashboard calculates the wrong mean absolute error. Implement mean_absolute_error(actual, predicted) using the provided equal-length numeric lists.',
   'spec':['Calculate the absolute distance for each pair.','Average the distances over all observations.','Inputs are non-empty lists of integer values.'],
   'hint':'sum(abs(actual[i] - predicted[i])) / len(actual)'},
 'uptime-rate':{'name':'uptime_percentage','args':['minutes_up','minutes_total'],
   'tests':[(( [30,20,10],100 ),60.0),(( [100],100 ),100.0),(( [20,0],40 ),50.0),(( [5,5,5],60 ),25.0)],
   'title':'Fix a service availability dashboard','goal':'An SRE dashboard is misreporting service uptime. Calculate the percentage of available minutes in a monitored window.',
   'spec':['Return 100 × sum(minutes_up) / minutes_total.','minutes_total is a positive integer.','minutes_up contains a list of nonnegative integer periods.'],
   'hint':'Sum the monitored available minutes before dividing by total window minutes.'},
 'ticket-sla-value':{'name':'hours_over_sla','args':['hours_taken','sla_limit'],
   'tests':[(( 8,5 ),3),(( 2,5 ),0),(( 5,5 ),0),(( 100,24 ),76)],
   'title':'Repair an SLA overage calculation','goal':'A support operations tool should return how many hours a ticket exceeds its SLA target.',
   'spec':['Return max(hours_taken − sla_limit, 0).','An equal-to-limit ticket is on time.','Keep the function name and arguments unchanged.'],
   'hint':'Use a conditional or max(...) to clamp negative values to zero.'},
 'model-accuracy-numeric':{'name':'model_accuracy','args':['tp','tn','fp','fn'],
   'tests':[(( 4,5,1,0 ),0.9),(( 1,1,1,1 ),0.5),(( 5,0,0,5 ),0.5),(( 10,2,3,5 ),0.6)],
   'title':'Fix model accuracy from a confusion matrix','goal':'An AI team needs an accurate dashboard metric. Compute classification accuracy given confusion matrix counts.',
   'spec':['Return (tp + tn) / (tp + tn + fp + fn).','The sum of all counts is positive.','Inputs are nonnegative integer counts.'],
   'hint':'Correct predictions are true positives plus true negatives.'}
})
LANGUAGES={'python':'Python','javascript':'JavaScript','typescript':'TypeScript','java':'Java','cpp':'C++','go':'Go'}
LANG_SIGN={
 'python':lambda p:f"def {p['name']}({', '.join(p['args'])}):\n    # Write your solution here. You can use variables, loops and if statements.\n    return 0",
 'javascript':lambda p:f"function {p['name']}({', '.join(p['args'])}) {{\n  // Write your solution here\n  return 0;\n}}",
 'typescript':lambda p:f"function {p['name']}({', '.join(f'{a}: '+ ('number[]' if p['name'] in ('classification_accuracy','unique_count','sla_breaches','binary_f1','mean_absolute_error','uptime_percentage','retrieval_recall') and (a not in ('limit',)) else 'number') for a in p['args'])}): number {{\n  return 0;\n}}",
 'java':lambda p:f"public static double {p['name']}({', '.join('double '+a for a in p['args'])}) {{\n  return 0;\n}}",
 'cpp':lambda p:f"double {p['name']}({', '.join('double '+a for a in p['args'])}) {{\n  return 0;\n}}",
 'go':lambda p:f"func {p['name']}({', '.join(a+' float64' for a in p['args'])}) float64 {{\n  return 0\n}}",
}
# Structured-list problems are currently Python-only. Other languages have a numeric function fixture.
NUMERIC={'order-total','stock-guard','ticket-sla-value','model-accuracy-numeric'}
ARRAY_LANGUAGES={'python','javascript','typescript'}
LANG_PATTERNS=[('typescript',r'\btypescript\b|\bts\b'),('javascript',r'\bjavascript\b|\bnode\.?js\b|\bexpress\b'),('cpp',r'\bc\+\+\b|\bcpp\b'),('java',r'\bjava\b(?!script)'),('go',r'\bgolang\b|\bgo developer\b'),('python',r'\bpython\b|\bdjango\b|\bfastapi\b')]
SKILL_TERMS=['Python','JavaScript','TypeScript','Java','C++','Go','SQL','React','HTML','CSS','FastAPI','Django','Node.js','Machine Learning','Deep Learning','Computer Vision','NLP','Model Evaluation','Data Engineering','Data Cleaning','PostgreSQL','Cybersecurity','SOC','SIEM','Incident Response','Excel','Power BI','Customer Support','Data Analysis','REST API','Testing']

def build_job_trial(description:str,ai:dict|None=None,requested_track:str|None=None,preferred_language:str|None=None)->dict:
    lower=description.lower()
    skills=[s for s in SKILL_TERMS if s.lower() in lower]
    if ai and isinstance(ai.get('focus_skills'),list):
        for s in ai['focus_skills']:
            if isinstance(s,str) and s.lower() not in [x.lower() for x in skills] and len(s)<35:skills.append(s)
    matches=[(m.start(),name) for name,pattern in LANG_PATTERNS if (m:=re.search(pattern,lower))]
    lang=(preferred_language if preferred_language in LANGUAGES else min(matches)[1] if matches else 'python')
    if requested_track in {'sql','frontend','security','backend'}:
        track=requested_track
    elif re.search(r'\b(soc|siem|incident response|threat hunt|security analyst)\b',lower):track='security'
    elif re.search(r'\b(frontend|front.end|web designer|html|css|react|ui developer)\b',lower):track='frontend'
    elif re.search(r'\b(sql|data analyst|power bi|reporting analyst|business intelligence)\b',lower) and not re.search(r'\b(machine learning|ml engineer|ai engineer|model training)\b',lower):track='sql'
    else:track='backend'
    if track=='backend' and not matches and not any(s in lower for s in ['python','coding','programming','engineer','developer','software','machine learning','ml ','ai ','data engineering','etl','data pipeline','backend','backend','data scientist','api','support','helpdesk','operations']):
        # No validated work simulation for this arbitrary domain, so do not invent a score.
        raise ValueError('No verified work-sample evaluator for this job description yet. Try a technical posting or choose a supported practice track. An arbitrary job title cannot safely create an automatic graded exercise.')
    if track=='backend':
        if re.search(r'\b(machine learning|ml engineer|ai engineer|model evaluation|classification|deep learning|data scientist)\b',lower):scenario='ml-accuracy'
        elif re.search(r'\b(data engineering|etl|data pipeline|deduplicat|data cleaning)\b',lower):scenario='data-dedupe'
        elif re.search(r'\b(customer support|helpdesk|service desk|support operations|sla)\b',lower):scenario='ticket-sla'
        elif re.search(r'\b(inventory|warehouse|stock)\b',lower):scenario='stock-guard'
        else:scenario='order-total'
        if lang not in ARRAY_LANGUAGES and scenario not in NUMERIC:
            # Avoid silently grading invalid Java/C++ types for list-based tasks.
            scenario='order-total'
            reason='This language currently supports a validated numeric-function task. More specialized tasks require a dedicated checked harness.'
        else:reason='Task selected from validated templates using skills in your job description.'
        p=CASES[scenario]
        title=(ai or {}).get('role_title') or next((line.strip()[:95] for line in description.splitlines() if any(x in line.lower() for x in ['engineer','developer','analyst','intern','specialist'])), 'Professional work trial')
        brief=(ai or {}).get('manager_brief') or f'You are joining a simulated team as a {title}. Complete a practical {LANGUAGES[lang]} assignment that checks a relevant skill. The exercise is not provided by the employer.'
        task={'id':f'gen:{scenario}:{lang}','title':p['title'],'tag':f'{LANGUAGES[lang]} · Practical assignment','time':'15–25 min','goal':p['goal'],'spec':p['spec'],'starter':LANG_SIGN[lang](p),'hint':p['hint'],'lang':lang}
        trial={'id':'backend','title':title,'subtitle':f'{LANGUAGES[lang]} practical lab','category':'Engineering','duration':'15–25 min','difficulty':'Junior',
               'color':'#5865e9','skills':skills[:7] or [LANGUAGES[lang]],'intro':brief,'company':'JobTrial Studio','role':title,'tasks':[task]}
        return {'track':'backend','role_title':title,'skills':skills[:8] or [LANGUAGES[lang]],'company':'JobTrial Studio','manager_brief':brief,'ai_used':bool(ai),
         'mode':'Hugging Face role analysis · validated work lab' if ai else 'Job description matching · validated work lab',
         'limitations':reason+' AI does not invent executable tests. Other tasks/languages require a supported harness. Full syntax beyond the local interpreter requires Docker.',
         'dynamic_trial':trial,'chosen_language':lang,'matching_reason':reason}
    # Existing domain-specific work environments retained, not generic fallback mislabeled as exact simulation.
    from .catalog import TRACKS
    t=TRACKS[track]
    title=(ai or {}).get('role_title') or next((line.strip()[:95] for line in description.splitlines() if any(x in line.lower() for x in ['engineer','developer','analyst','intern','specialist'])),t['role'])
    brief=(ai or {}).get('manager_brief') or t['intro']
    return {'track':track,'role_title':title,'skills':skills[:8] or t['skills'],'company':t['company'],'manager_brief':brief,'ai_used':bool(ai),
     'mode':'Hugging Face enhanced role matching' if ai else 'Local role matching',
     'limitations':'The work environment is a validated skills exercise, not the employer’s exact assignment. Available environments are bounded.',
     'chosen_language': 'sql' if track=='sql' else 'html/css' if track=='frontend' else 'security investigation','matching_reason':f'Matched {track} requirements.'}

def grade_local_python(task_id:str,code:str)->dict:
    from .engine import result,check
    try:
        parts=task_id.split(':')
        if len(parts) not in (3,4):raise ValueError('Unknown Python challenge')
        _,scenario,lang=parts[:3]
        seed=int(parts[3]) if len(parts)==4 and parts[3].isdigit() else 0
        if lang!='python' or scenario not in CASES:raise ValueError('Unknown Python challenge')
        p=CASES[scenario]
        runner=Interpreter(code,p['name'],p['args'])
    except (ValueError,RecursionError,MemoryError) as exc:
        return result([check('Valid Python program',False,str(exc)[:260])],'Check the supported syntax and function signature.',None,'python-safe-interpreter')
    checks=[]
    from .job_compiler import enhanced_tests
    for idx,(inputs,expected) in enumerate(enhanced_tests(scenario,seed)):
        try:
            got=runner.run(inputs)
            ok=(math.isclose(got,expected,rel_tol=1e-8,abs_tol=.001) if type(got) in (float,int) and type(expected) in (float,int) else got==expected)
            detail=f'Expected {expected}, got {got}' if idx<3 else ('Hidden scenario passed' if ok else 'Hidden scenario failed')
        except (ValueError,TypeError,ZeroDivisionError,IndexError,OverflowError,ArithmeticError,RecursionError) as exc:
            ok=False;detail='Error: '+str(exc)[:170] if idx<3 else 'Hidden scenario raised an error.'
        checks.append(check(f'Test {idx+1}'+(' · edge case' if idx>=3 else ''),ok,detail))
    return result(checks,'All checked scenarios passed.' if all(c['passed'] for c in checks) else 'Review the requirements and try again.',None,'python-safe-interpreter')

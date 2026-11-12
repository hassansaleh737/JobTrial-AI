"""Job description -> bounded, inspectable work-sample mission compiler.

LLMs may summarize the job. They NEVER write executable tests or run candidate code.
A deterministic library gives consistent, testable assessments and explicit coverage gaps.
"""
from __future__ import annotations
import hashlib
import re
from copy import deepcopy
from .adaptive import CASES, LANGUAGES, LANG_SIGN, ARRAY_LANGUAGES, NUMERIC, SKILL_TERMS
from .catalog import TRACKS, ORDERS, CUSTOMERS, SECURITY_LOGS

# Covers real role families, not simply job title matching.
FAMILY_TERMS={
    'machine_learning': ['machine learning','ml engineer','ai engineer','model evaluation','classification','regression','pytorch','tensorflow','deep learning','data scientist','computer vision','natural language processing','nlp','ai developer','generative ai','llm','large language model','rag','retrieval augmented generation','agentic ai'],
    'data_engineering': ['data engineer','data engineering','etl','data pipeline','deduplication','data cleaning','spark','airflow'],
    'security': ['soc analyst','siem','incident response','security analyst','cybersecurity','threat hunting','security operations','blue team'],
    'frontend': ['frontend','front-end','react','html','css','vue','ui developer','web designer','responsive web'],
    'data_analytics': ['data analyst','business intelligence','sql','power bi','tableau','business analyst','analytics','dashboard'],
    'devops': ['devops','site reliability','sre','cloud engineer','infrastructure','kubernetes','uptime','monitoring'],
    'backend': ['backend','back-end','api developer','fastapi','django','flask','spring boot','node.js','express.js','rest api','software engineer','software developer','javascript developer','typescript developer','node developer','full stack developer'],
    'qa': ['qa engineer','quality assurance','software testing','test engineer','automation testing','pytest','unit test'],
    'marketing': ['digital marketing','marketing','campaign','seo','social media','content creator','brand manager','copywriter'],
    'customer_success': ['customer support','customer service','customer success','helpdesk','support representative'],
    'sales': ['sales representative','business development','sales associate','account executive','lead generation'],
    'design': ['graphic design','ui/ux','ux designer','product designer','visual designer','figma'],
    'finance': ['finance','accounting','financial analyst','budget','bookkeeping'],
    'project_management': ['project coordinator','project manager','operations manager','operations associate','administrative'],
    'human_resources': ['recruiter','recruitment','human resources','talent acquisition','hr specialist'],
}

LANG_MATCH=[('typescript',r'\btypescript\b'),('javascript',r'\bjavascript\b|\bnode(?:\.js)?\b'),('cpp',r'c\+\+|\bcpp\b'),('java',r'\bjava\b(?!script)'),('go',r'\bgolang\b|\bgo engineer\b'),('python',r'\bpython\b|\bpandas\b|\bfastapi\b')]
PROGRAM_FAMILIES={'machine_learning','data_engineering','devops','backend','qa'}
NUMERIC_SCENARIOS={'order-total','stock-guard','ticket-sla-value','campaign-rate','model-accuracy-numeric'}

# Scenario relevance depends on the responsibilities mentioned in the announcement.
SCENARIO_LIST={
    'machine_learning': ['ml-accuracy','ml-f1','rag-hit-rate','forecast-mae','model-accuracy-numeric'],
    'data_engineering': ['data-dedupe','forecast-mae','order-total'],
    'devops': ['ticket-sla','uptime-rate','ticket-sla-value'],
    'backend': ['order-total','stock-guard','ticket-sla-value'],
    'qa': ['stock-guard','order-total','ticket-sla-value'],
}
SCENARIO_TRIGGERS={
    'rag-hit-rate':['rag','retrieval','vector search','embeddings','llm','search evaluation'],
    'ml-accuracy':['accuracy','classification','model evaluation','machine learning'],
    'ml-f1':['precision','recall','f1','imbalanced','classification'],
    'forecast-mae':['forecast','regression','predict','time series'],
    'data-dedupe':['etl','pipeline','duplicates','deduplic','cleaning'],
    'ticket-sla':['incident','sre','support','sla','monitor'],
    'uptime-rate':['uptime','availability','sre','devops','service'],
    'stock-guard':['inventory','warehouse','stock','orders'],
    'order-total':['checkout','e-commerce','commerce','pricing','orders','payments','api','backend'],
}

NONTECH={
 'marketing':{'title':'Investigate a campaign that is underperforming','goal':'A fictional campus events brand ran two campaigns. Draft a short recommendation to improve next week’s results using the evidence below.\n\nCampaign A: spend $200, 400 clicks, 12 signups. Campaign B: spend $160, 200 clicks, 16 signups. Budget for next week: $360.\n\nExplain which campaign deserves more budget and what you would test.','spec':['Compare cost per signup for both campaigns.','Suggest a concrete next-week budget split of $360.','Explain your recommendation and one measurable experiment.'],'hint':'Cost per signup = spend / signups. Consider both efficiency and limited sample size.','starter':'Situation:\nCampaign A cost per signup: \nCampaign B cost per signup: \n\nDecision:\n\nEvidence:\n\nNext experiment:\n'},
 'customer_success':{'title':'Respond to a frustrated customer','goal':'A customer says: “I paid for next-day delivery. Three days later there is no update. I want someone to fix this.”\n\nWrite a professional reply and a brief internal escalation note. This is a fictional customer service case.','spec':['Acknowledge the issue without promising an unverified refund.','Request only the information needed to investigate.','Provide a concrete next step and an internal escalation summary.'],'hint':'Separate what is confirmed from what you still need to check.','starter':'Situation:\n\nDecision (customer reply):\n\nEvidence (what is known vs unknown):\n\nInternal escalation:\n'},
 'sales':{'title':'Prioritize three incoming sales leads','goal':'A fictional B2B service has 3 inbound leads: A (large team, wants demo in 2 weeks), B (small team, needs solution tomorrow), C (medium team, requested a proposal but no timeline). Create an outreach plan.','spec':['Rank all three leads with a reason.','Draft one short first outreach message.','State which missing facts you would confirm.'],'hint':'Urgency, potential fit, and uncertainty matter more than a single invented lead score.','starter':'Situation:\n\nDecision (priority order):\n\nEvidence (why):\n\nFirst outreach:\n'},
 'design':{'title':'Create a usability improvement brief','goal':'A fictional university volunteer portal has a signup form without visible field labels, keyboard focus, or a mobile layout. Write a design handoff brief for the developer.','spec':['List the main accessibility and mobile usability issues.','Describe a proposed improved experience in implementable terms.','Provide a practical acceptance checklist for a designer/developer.'],'hint':'Think about keyboard-only navigation, labels, readability and mobile width.','starter':'Situation:\n\nDecision (design changes):\n\nEvidence (observed usability problems):\n\nAcceptance checklist:\n'},
 'finance':{'title':'Explain a student club budget variance','goal':'A fictional club planned $500 for venue, $200 for transport, and $100 for supplies. Actual expenses: $560, $150, and $130. Prepare a concise budget variance note and recommendation.','spec':['Calculate the total planned and actual spend accurately.','Identify which categories are over or under plan.','Suggest one realistic way to control costs next month.'],'hint':'Variance = actual minus planned for each category.','starter':'Situation:\n\nDecision:\n\nEvidence (totals and variances):\n\nNext step:\n'},
 'project_management':{'title':'Replan a blocked student project','goal':'A fictional team must demo on Friday. The prototype needs 2 days, testing needs 1 day after the prototype, and slides need 1 day in parallel. On Tuesday the developer is unavailable for one day. Draft a realistic recovery plan.','spec':['Show a sequence of tasks with dependencies.','Identify the effect of the one-day absence.','Propose a fallback if the deadline cannot be met.'],'hint':'A plan is useful only if dependencies and member availability are respected.','starter':'Situation:\n\nDecision (updated plan):\n\nEvidence (dependency and timing):\n\nFallback:\n'},
 'human_resources':{'title':'Create a fair interview scorecard','goal':'A fictional student internship needs spreadsheet fundamentals, communication and punctual reporting. Design a role-relevant evaluation scorecard, not a personality test.','spec':['List observable evaluation criteria tied to the work.','Give one work-sample task and its scoring rubric.','Explain how to use the same criteria consistently for all applicants.'],'hint':'Evaluate skills and evidence, not protected traits or assumptions.','starter':'Situation:\n\nDecision (scorecard):\n\nEvidence (work sample):\n\nFairness safeguards:\n'},
 'general':{'title':'Prepare a first-day work deliverable','goal':'Your simulated manager asks for a short, actionable work plan based on the responsibilities in the job description. Identify the most important task and produce a concrete deliverable that could be reviewed by a teammate.','spec':['Name one specific job responsibility from the posting.','Produce a real first-draft deliverable or action plan.','State assumptions, evidence and what a reviewer needs to validate.'],'hint':'Make it concrete: include a sample output, steps, and how success would be checked.','starter':'Situation (from the job posting):\n\nDecision / deliverable:\n\nEvidence and assumptions:\n\nReviewer checklist:\n'},
}

def family_scores(description: str)->dict[str,int]:
    lower=description.lower()
    return {fam:sum((4 if term in ('ai engineer','ml engineer','frontend','data analyst','marketing','soc analyst','data engineer','backend','qa engineer') else 2) for term in terms if term in lower) for fam,terms in FAMILY_TERMS.items()}

def get_family(description:str,requested_track:str|None=None)->tuple[str,dict[str,int]]:
    scores=family_scores(description)
    if requested_track and requested_track!='auto':
        overrides={'backend':'backend','sql':'data_analytics','frontend':'frontend','security':'security','professional':'general'}
        if requested_track in overrides:return overrides[requested_track],scores
    best=max(scores,key=scores.get)
    return (best if scores[best]>0 else 'general'),scores

def choose_language(description:str,preferred_language:str|None=None)->str:
    if preferred_language in LANGUAGES:return preferred_language
    matches=[(m.start(),name) for name,pattern in LANG_MATCH if (m:=re.search(pattern,description.lower()))]
    return min(matches)[1] if matches else 'python'

def role_title(description:str,ai:dict|None,family:str)->str:
    role=(ai or {}).get('role_title','')
    if isinstance(role,str) and len(role.strip())>=5:return role.strip()[:95]
    for line in description.splitlines()[:7]:
        line=line.strip().strip('-:*')
        if 6<=len(line)<=95 and any(x in line.lower() for x in ('engineer','developer','analyst','intern','specialist','designer','marketing','coordinator','representative','manager','recruiter')):
            return line
    return family.replace('_',' ').title()+' Work Trial'

def task_seed(description:str)->int:
    return int(hashlib.sha256(description.strip().encode('utf-8')).hexdigest()[:6],16)%1000000

def enhanced_tests(scenario:str,seed:int):
    """Deterministically add role-specific hidden cases derived from the posting.
    Grader uses exactly the same seed; client cannot supply reference answers.
    """
    from .adaptive import CASES
    tests=list(CASES[scenario]['tests'])
    if scenario=='order-total':
        price=round(15+(seed%300)/7,2);qty=seed%5+1;discount=(seed//7)%41
        tests.append(((price,qty,discount),round(price*qty*(1-discount/100),2)))
    elif scenario=='stock-guard':
        have=seed%200;need=(seed//9)%250
        tests.append(((have,need),-1 if need>have else have-need))
    elif scenario=='ml-accuracy':
        actual=[(seed>>i)&1 for i in range(9)]
        predicted=[a if i%3 else 1-a for i,a in enumerate(actual)]
        tests.append(((actual,predicted),sum(a==b for a,b in zip(actual,predicted))/len(actual)))
    elif scenario=='rag-hit-rate':
        start=seed%70+1
        relevant=[start,start+1,start+2,start+3]
        retrieved=[start+1,start+3,start+10,start+11] if seed%2 else [start,start+10,start+11]
        tests.append(((relevant,retrieved),sum(x in retrieved for x in relevant)/len(relevant)))
    elif scenario=='ml-f1':
        actual=[(seed>>(i%15))&1 for i in range(10)]
        if 1 not in actual:actual[0]=1
        predicted=[(seed>>(i%15+3))&1 for i in range(10)]
        tp=sum(a==1 and b==1 for a,b in zip(actual,predicted))
        fp=sum(a==0 and b==1 for a,b in zip(actual,predicted))
        fn=sum(a==1 and b==0 for a,b in zip(actual,predicted))
        score=(2*tp/(2*tp+fp+fn)) if (2*tp+fp+fn)>0 else 0.0
        tests.append(((actual,predicted),score))
    elif scenario=='data-dedupe':
        ids=[(seed>>(i%12))%11 for i in range(9)]
        tests.append(((ids,),len(set(ids))))
    elif scenario=='ticket-sla':
        hours=[(seed//(i+1))%20 for i in range(7)]
        limit=4+(seed%8)
        tests.append(((hours,limit),sum(x>limit for x in hours)))
    elif scenario=='forecast-mae':
        actual=[(seed//(i+1))%25 for i in range(6)]
        predicted=[a+((-1)**i)*((i+seed)%4) for i,a in enumerate(actual)]
        tests.append(((actual,predicted),sum(abs(a-b) for a,b in zip(actual,predicted))/len(actual)))
    elif scenario=='uptime-rate':
        mins=[seed%30, (seed//3)%30, (seed//7)%30]
        total=sum(mins)+20
        tests.append(((mins,total),100*sum(mins)/total))
    elif scenario=='ticket-sla-value':
        taken=seed%120
        limit=8+(seed//3)%70
        tests.append(((taken,limit),max(taken-limit,0)))
    elif scenario=='model-accuracy-numeric':
        tp=1+seed%20;tn=1+(seed//3)%20;fp=seed%5;fn=(seed//7)%8
        tests.append(((tp,tn,fp,fn),(tp+tn)/(tp+tn+fp+fn)))
    return tests

def compile_job_trial(description:str,ai:dict|None=None,requested_track:str|None=None,preferred_language:str|None=None)->dict:
    family,scores=get_family(description,requested_track)
    language=choose_language(description,preferred_language)
    role=role_title(description,ai,family)
    detected=[s for s in SKILL_TERMS if s.lower() in description.lower()]
    if ai and isinstance(ai.get('focus_skills'),list):
        for x in ai['focus_skills'][:6]:
            if isinstance(x,str) and 2<len(x)<40 and x.lower() in description.lower() and x.lower() not in [s.lower() for s in detected]:detected.append(x)
    seed=task_seed(description)
    manager=(ai or {}).get('manager_brief') or f'You have joined a fictional team as a {role}. Complete the simulated work sample below; evaluate your output using the visible criteria.'
    manager=str(manager)[:350]
    track='backend' if family in PROGRAM_FAMILIES else 'sql' if family=='data_analytics' else family if family in ('frontend','security') else 'professional'
    reason=f'Role signals matched: {family.replace("_"," ")}. Preferred coding language: {LANGUAGES.get(language,language)}.' if track=='backend' else f'Role signals matched: {family.replace("_"," ")}.'
    covered=[]
    if track=='backend':
        scenarios=SCENARIO_LIST[family]
        scenarios=sorted(scenarios,key=lambda name:sum(2 for term in SCENARIO_TRIGGERS.get(name,[]) if term in description.lower()),reverse=True)
        if language not in ARRAY_LANGUAGES:
            if family=='machine_learning':scenarios=['model-accuracy-numeric']
            elif family=='devops':scenarios=['ticket-sla-value','order-total']
            else:scenarios=[s for s in scenarios if s in NUMERIC_SCENARIOS or s in NUMERIC]
            if not scenarios:scenarios=['order-total']
        tasks=[]
        for scenario in dict.fromkeys(scenarios):
            if scenario not in CASES:continue
            p=CASES[scenario]
            starter=LANG_SIGN[language](p)
            tasks.append({'id':f'gen:{scenario}:{language}:{seed}','title':p['title'],'tag':f'{LANGUAGES[language]} · Verified work sample',
              'time':'15–25 min','goal':p['goal'],'spec':p['spec'],'starter':starter,'hint':p['hint'],'lang':language})
            if len(tasks)>=2:break
        covered=[LANGUAGES[language], 'Coding fundamentals','Automated tests']
        if family=='machine_learning':covered+=['Machine Learning evaluation metrics','Classification metrics']
        if family=='data_engineering':covered+=['Data quality']
        if family=='devops':covered+=['Operational metrics']
        trial={'id':'backend','title':role,'subtitle':f'{LANGUAGES[language]} practical work samples','category':'Technical practice','duration':'30–45 min','difficulty':'Junior',
               'color':'#5865e9','skills':detected[:7] or covered,'intro':manager,'company':'JobTrial Studio','role':role,'tasks':tasks}
        limits='These are verified skill-specific tasks, NOT a custom employer assessment. Only the listed programming languages and testable task blueprints are supported; Docker is required for unrestricted code in other languages.'
    elif track=='sql':
        base=TRACKS['sql'];trial={k:deepcopy(v) for k,v in base.items() if k!='keywords'}
        trial['id']='sql';trial['role']=trial['title']=role;trial['company']='JobTrial Studio';trial['intro']=manager
        trial['sample_data']={'orders':{'columns':['id','customer_id','region','quantity','unit_price','status'],'rows':[list(x) for x in ORDERS]},'customers':{'columns':['id','name'],'rows':[list(x) for x in CUSTOMERS]}}
        # Requesting SQL ensures the actual local read-only DB is used, not code-generated SQL.
        covered=['SQL','Aggregation','Joins','Data reporting']
        limits='The work samples use a fictional commerce database and approved SQL tasks; they do not reproduce an employer’s proprietary datasets.'
    elif track=='frontend':
        base=TRACKS['frontend'];trial={k:deepcopy(v) for k,v in base.items() if k!='keywords'}
        trial['id']='frontend';trial['role']=trial['title']=role;trial['company']='JobTrial Studio';trial['intro']=manager
        if any(x in description.lower() for x in ('contact','support form','customer inquiry')):
            trial['tasks']=[{
                'id':'contact-form','title':'Ship an accessible contact form','tag':'HTML + CSS · Accessibility','time':'20 min',
                'goal':'A fictional product team needs a contact form that works on mobile and is operable by keyboard. Repair the incomplete page.',
                'spec':['Use a main heading, name field, email field and message textarea.','Add visible, associated labels and a submit button.','Use a mobile media query and visible focus styles.'],
                'starter_html':'<main class="page"><section class="card"><h1>Contact us</h1><form><input type="text" placeholder="Name"><input type="email" placeholder="Email"><textarea placeholder="Message"></textarea></form></section></main>',
                'starter_css':base['tasks'][0]['starter_css'],'hint':'Give the fields id attributes and matching <label for="...">; style :focus-visible and @media.','lang':'html'}]
        covered=['HTML','CSS','Accessibility','Responsive design']
        limits='This workspace assesses HTML/CSS structure, not an executable React/TypeScript application or the visual quality of a design.'
    elif track=='security':
        base=TRACKS['security'];trial={k:deepcopy(v) for k,v in base.items() if k!='keywords'}
        trial['id']='security';trial['role']=trial['title']=role;trial['company']='JobTrial Studio';trial['intro']=manager;trial['logs']=deepcopy(SECURITY_LOGS)
        covered=['SOC triage','Log analysis','Incident documentation']
        limits='Uses fictional authentication records and a prevalidated investigation rubric; no live systems are accessed.'
    else:
        content=NONTECH.get(family,NONTECH['general'])
        task={'id':f'professional:{family if family in NONTECH else "general"}','title':content['title'],'tag':'Work deliverable · Human review','time':'20–30 min',
              'goal':content['goal'],'spec':content['spec'],'hint':content['hint'],'starter':content['starter'],'lang':'report'}
        trial={'id':'professional','title':role,'subtitle':'Role-based work deliverable','category':'Professional practice','duration':'20–30 min','difficulty':'Junior',
               'color':'#6e62ae','skills':detected[:7] or ['Communication','Problem solving'], 'intro':manager,'company':'JobTrial Studio','role':role,'tasks':[task]}
        covered=['Written deliverable','Problem framing']
        limits='No reliable automated performance score exists for this open-ended work. Only completeness checks are available; a human reviewer must assess quality.'
    missing=[s for s in detected if not any(s.lower() in x.lower() or x.lower() in s.lower() for x in covered)]
    return {'track':track,'role_title':role,'skills':detected[:8] or covered,'company':'JobTrial Studio','manager_brief':manager,'ai_used':bool(ai),
       'mode':('HF-assisted job analysis' if ai else 'Local skills analysis')+' + validated simulation compiler',
       'limitations':limits,'dynamic_trial':trial,'chosen_language':language if track=='backend' else ('sql' if track=='sql' else 'html/css' if track=='frontend' else 'report'),
       'matching_reason':reason,'covered_skills':covered,'not_assessed_skills':missing[:8],
       'assessment_type':'automated' if track!='professional' else 'human-review-required',
       'compiler_version':'3.0.0'}

def grade_professional(task_id:str,text:str):
    from .engine import check
    if task_id not in {'professional:'+k for k in NONTECH}:raise ValueError('Unknown work sample')
    stripped=text.strip()
    lines=[line.strip().lower() for line in stripped.splitlines()]
    has_context=any(line.startswith('situation:') for line in lines)
    has_decision=any(line.startswith('decision') for line in lines)
    has_evidence=any(line.startswith('evidence') for line in lines)
    # Format checks are NOT quality / employability scores; deliberately use -1.
    checks=[check('Situation section',has_context,'Describe the context of your response.'),
            check('Decision section',has_decision,'Describe the action or deliverable.'),
            check('Evidence section',has_evidence,'State assumptions and evidence.'),
            check('Substantive draft',len(stripped)>=220,'Write at least 220 characters as a first draft.')]
    return {'score':-1,'passed':sum(x['passed'] for x in checks),'total':len(checks),'checks':checks,
            'feedback':'Draft saved for human review. These are only document-completeness checks, not a professional skills score.',
            'preview':None,'mode':'manual-review'}

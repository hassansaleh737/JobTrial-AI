"""Independent, prevalidated alternative work contracts for the in-band challenge selector.

The model may write the scenario, but never these executable rules/oracles.
The project identifier selects an immutable trusted contract on the server.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from copy import deepcopy
import math


def alt(title, function, goal, spec, starter, cases, language='javascript', hint='Read the cases, handle edge conditions, and avoid mutating the supplied data.'):
    return dict(title=title,function=function,goal=goal,spec=spec,starter=starter,cases=cases,language=language,hint=hint,helper=('' if language=='python' else 'module.exports = {};\n'))

ALTERNATES={
 'fe-easy':alt('Repair a feedback form validator','validateFeedback',
   'A student support form accepts empty messages and ratings outside the allowed range. Repair the validation result used by the Send button.',
   ['Export validateFeedback(data) from src/solution.js.','Return {valid:boolean,errors:string[]} in name, message, rating order.','Name must have at least 2 non-space characters.','Message must have at least 10 non-space characters.','Rating must be an integer from 1 to 5 inclusive; do not mutate data.'],
   'function validateFeedback(data) {\n  return { valid: false, errors: [] };\n}\nmodule.exports = { validateFeedback };\n',
   [[{'name':'Jo','message':'This was very useful','rating':5}],[{'name':' ','message':'short','rating':0}],[{'name':'Ada','message':'   a very thoughtful review   ','rating':3}],[{'name':'M','message':'enough text here','rating':6}],[{'name':'Kim','message':'abcdefghij','rating':2.5}]]),
 'fe-medium':alt('Group workshop registrations by day','groupRegistrations',
   'A campus events page must display registrations by event date and show names alphabetically inside each date.',
   ['Export groupRegistrations(rows).','Each row has a date (YYYY-MM-DD) and name.','Return an object mapping dates to arrays of names.','Sort names alphabetically within each date (case-sensitive); keep duplicate names.','Return {} for an empty list and do not mutate rows.'],
   'function groupRegistrations(rows) {\n  return {};\n}\nmodule.exports = { groupRegistrations };\n',
   [[[{'date':'2026-11-12','name':'Zoe'},{'date':'2026-11-12','name':'Adam'},{'date':'2026-11-13','name':'Kim'}]], [[{'date':'2026-11-12','name':'Bea'},{'date':'2026-11-12','name':'Bea'}]], [[]], [[{'date':'2026-11-14','name':'A'},{'date':'2026-11-13','name':'C'}]], [[{'date':'2026-11-20','name':'zzz'},{'date':'2026-11-20','name':'AAA'}]]]),
 'fe-advanced':alt('Implement undoable note edits','applyNoteEdits',
   'A notes application has to replay insert, replace, and delete operations without mutating the original document.',
   ['Export applyNoteEdits(lines,actions).','Actions are {type:"insert", index, text}, {type:"replace",index,text}, or {type:"delete",index}.','Insert at an index from 0 through length; invalid indices are ignored.','Replace/delete only when index is a valid existing position.','Return a new array. Never mutate the original lines or actions.'],
   'function applyNoteEdits(lines, actions) {\n  return [...lines];\n}\nmodule.exports = { applyNoteEdits };\n',
   [[['one','two'],[{'type':'insert','index':1,'text':'middle'}]], [['old'],[{'type':'replace','index':0,'text':'new'}]], [['A','B'],[{'type':'delete','index':0}]], [[],[{'type':'insert','index':0,'text':'new'}]], [['A'],[{'type':'insert','index':3,'text':'x'},{'type':'replace','index':0,'text':'B'}]]]),
 'fe-hard':alt('Build feature access resolution','resolveFeatures',
   'A SaaS dashboard has features gated by user roles and dependencies. Decide which requested features can really be enabled.',
   ['Export resolveFeatures(features,roles).','Each feature has {id,allowedRoles,requires} where requires is an array of other feature ids.','Return a sorted array of enabled feature ids.','A feature is eligible when at least one user role is allowed and all dependencies are eligible.','Missing dependencies and dependency cycles disable the affected feature; do not mutate inputs.'],
   'function resolveFeatures(features, roles) {\n  return [];\n}\nmodule.exports = { resolveFeatures };\n',
   [[[{'id':'feed','allowedRoles':['user'],'requires':[]},{'id':'share','allowedRoles':['user'],'requires':['feed']}],['user']], [[{'id':'secret','allowedRoles':['admin'],'requires':[]}],['user']], [[{'id':'x','allowedRoles':['user'],'requires':['missing']}],['user']], [[{'id':'a','allowedRoles':['user'],'requires':['b']},{'id':'b','allowedRoles':['user'],'requires':['a']}],['user']], [[{'id':'a','allowedRoles':['user'],'requires':[]},{'id':'b','allowedRoles':['admin'],'requires':['a']}],['admin','user']]]),
 'fe-expert':alt('Build a dependency-safe update order','orderUpdates',
   'A dashboard deploys widgets with dependency edges. The update scheduler must produce a stable topological order and detect cycles.',
   ['Export orderUpdates(nodes,edges).','nodes is an array of distinct string IDs; edge [a,b] means a must finish before b.','Return {order:string[],cyclic:boolean}.','For a DAG, choose the lexicographically smallest available node at every step.','For a cycle, return {order:[],cyclic:true}. Never mutate the inputs.'],
   'function orderUpdates(nodes, edges) {\n  return { order: [], cyclic: false };\n}\nmodule.exports = { orderUpdates };\n',
   [[['api','ui','db'],[['db','api'],['api','ui']]],[['a','b'],[]],[['a','b'],[['a','b'],['b','a']]],[[],[]],[['a','b','c'],[['a','c']]]]),
 'be-easy':alt('Repair API pagination parameters','normalizePagination',
   'A list endpoint accepts invalid page sizes and negative offsets. Implement predictable pagination parameter normalization.',
   ['Export normalizePagination(query).','Return {offset,limit} with integer values.','offset is an integer >= 0, otherwise default 0.','limit is an integer from 1 to 50 inclusive, otherwise default 20.','Do not mutate the query.'],
   'function normalizePagination(query) {\n  return { offset: 0, limit: 20 };\n}\nmodule.exports = { normalizePagination };\n',
   [[{'offset':12,'limit':25}],[{'offset':-1,'limit':25}],[{'offset':0,'limit':100}],[{'offset':1.5,'limit':3}],[{}]]),
 'be-medium':alt('Implement a per-user request rate limiter','rateLimitRequests',
   'A login API must limit excessive requests within a rolling time window, without blocking unrelated users.',
   ['Export rateLimitRequests(requests,windowMs,maxRequests).','Each request is {user,time}; requests are in nondecreasing time order.','Return an array of booleans: true if allowed, false if rejected.','For each user count only previous ALLOWED requests strictly newer than time-windowMs.','At most maxRequests allowed in any rolling window; do not mutate inputs.'],
   'function rateLimitRequests(requests, windowMs, maxRequests) {\n  return [];\n}\nmodule.exports = { rateLimitRequests };\n',
   [[[{'user':'a','time':0},{'user':'a','time':1},{'user':'a','time':2}],100,2],[[{'user':'a','time':0},{'user':'b','time':1}],100,1],[[{'user':'a','time':0},{'user':'a','time':101}],100,1],[[],100,2],[[{'user':'a','time':0},{'user':'a','time':10},{'user':'a','time':20},{'user':'a','time':30}],15,2]]),
 'be-advanced':alt('Reconcile invoices and credit notes','reconcileInvoices',
   'Accounting exports have repeated payment IDs. Build an auditable per-invoice net total from invoice and refund events.',
   ['Export reconcileInvoices(events).','Each event has {id,invoice,kind:"charge"|"refund",amount}.','Duplicate event ids are ignored after their first appearance.','Return an object mapping invoice IDs to net cents (charges minus refunds).','Round each event amount to cents before summing. Do not mutate inputs.'],
   'function reconcileInvoices(events) {\n  return {};\n}\nmodule.exports = { reconcileInvoices };\n',
   [[[{'id':'p1','invoice':'A','kind':'charge','amount':10},{'id':'p2','invoice':'A','kind':'refund','amount':2.5}]], [[{'id':'p1','invoice':'A','kind':'charge','amount':10},{'id':'p1','invoice':'A','kind':'charge','amount':10}]], [[{'id':'x','invoice':'B','kind':'charge','amount':1.005}]], [[]], [[{'id':'x','invoice':'A','kind':'refund','amount':5},{'id':'y','invoice':'B','kind':'charge','amount':1}]]]),
 'be-hard':alt('Compute a bounded retry schedule','planRetries',
   'A failing integration service needs bounded exponential retry delays to avoid overwhelming a third-party API.',
   ['Export planRetries(baseMs,maxMs,attempts).','Return an array with one delay for each attempt starting at attempt index 0.','Delay i is min(maxMs,baseMs * 2**i).','If attempts <= 0 return []; assume baseMs > 0 and maxMs > 0.','Do not use randomness.'],
   'function planRetries(baseMs, maxMs, attempts) {\n  return [];\n}\nmodule.exports = { planRetries };\n',
   [[100,1000,5],[250,1000,4],[50,150,6],[100,1000,0],[1,4,5]]),
 'be-expert':alt('Plan a dependency-safe deployment order','deploymentOrder',
   'A microservice release is blocked by dependency cycles. Derive a deterministic deployment order or flag the cycle.',
   ['Export deploymentOrder(services,dependencies).','services is an array of service names.','Each pair [a,b] means service a needs service b deployed first.','Return {order:string[],cyclic:boolean}; always pick the alphabetically first ready service.','Return {order:[],cyclic:true} if a cycle exists. Do not mutate inputs.'],
   'function deploymentOrder(services, dependencies) {\n  return { order: [], cyclic: false };\n}\nmodule.exports = { deploymentOrder };\n',
   [[['api','db'],[['api','db']]],[['a','b','c'],[]],[['a','b'],[['a','b'],['b','a']]],[[],[]],[['web','api','db'],[['web','api'],['api','db']]]]),
 'ml-easy':alt('Count binary classification outcomes','confusion_counts',
   'A model dashboard needs the raw confusion-matrix counts to diagnose which examples were missed.',
   ['Export confusion_counts(actual,predicted).','Return {tp,tn,fp,fn} for binary labels 0 and 1.','Treat 1 as positive.','Return all zeros for empty arrays.','Do not mutate inputs.'],
   'def confusion_counts(actual, predicted):\n    return {"tp": 0, "tn": 0, "fp": 0, "fn": 0}\n',
   [[[1,0,1,0],[1,1,0,0]],[[0,0],[0,0]],[[1,1],[1,1]],[[],[]],[[0,1,0,1],[1,0,1,0]]],language='python'),
 'ml-medium':alt('Calculate per-class macro F1','macro_f1',
   'A model is accurate on the majority class, hiding failures on rare labels. Implement macro F1 across present classes.',
   ['Export macro_f1(actual,predicted).','Use the union of labels appearing in actual or predicted.','Compute F1 per class as 2TP/(2TP+FP+FN), or 0 on zero denominator.','Return the arithmetic mean of per-class F1.','Return 0.0 for empty arrays.'],
   'def macro_f1(actual, predicted):\n    return 0.0\n',
   [[[0,1,1],[0,1,0]],[[0,0],[0,0]],[[0,1,2],[1,1,2]],[[],[]],[[1,2,2],[1,2,1]]],language='python'),
 'ml-advanced':alt('Normalize test features without data leakage','standardize_features',
   'A model pipeline leaked information from the test fold into training statistics. Fit scaling on training data only.',
   ['Export standardize_features(train,test).','Inputs are lists of numbers with at least one training item.','Compute mean and population standard deviation from train only.','Return standardized test values, using 0 for all values if train std is zero.','Do not modify the source lists.'],
   'def standardize_features(train, test):\n    return []\n',
   [[[2,4,6],[4,8]],[[5,5],[6,5]],[[0,10],[0,5,10]],[[-2,2],[0]],[[3,6,9],[6]]],language='python'),
 'ml-hard':alt('Audit missing required model features','audit_features',
   'New inference requests sometimes omit required model features. Summarize malformed rows before batch scoring.',
   ['Export audit_features(rows,required).','Each row is a dictionary of features.','Return {invalid_indices:[...],missing_counts:{feature:count}}.','A required field is missing if absent or its value is None or the empty string.','Index rows from 0; count missing features once per row.'],
   'def audit_features(rows, required):\n    return {"invalid_indices": [], "missing_counts": {}}\n',
   [[[{'a':1},{'a':None}],['a']],[[{'x':'','y':1},{'x':'ok','y':2}],['x','y']],[[],['a']],[[{'a':1,'b':2}],['a','b']],[[{},{}],['q']]],language='python'),
 'ml-expert':alt('Build deterministic embedding search','cosine_top_k',
   'A retrieval system must rank documents by cosine similarity with a query and handle zero vectors deterministically.',
   ['Export cosine_top_k(query,docs,k).','docs is a list of {id,vector}; all vectors have the same length as query.','Cosine similarity uses dot/(norms). A zero norm has similarity 0.','Return the top k document IDs sorted by score descending then id ascending.','If k<=0 return []; do not mutate docs.'],
   'def cosine_top_k(query, docs, k):\n    return []\n',
   [[[1,0],[{'id':'a','vector':[1,0]},{'id':'b','vector':[0,1]}],2],[[0,0],[{'id':'b','vector':[2,1]},{'id':'a','vector':[0,0]}],2],[[1,1],[{'id':'x','vector':[1,1]},{'id':'y','vector':[-1,-1]}],1],[[1,0],[],3],[[1,0],[{'id':'a','vector':[1,0]}],0]],language='python'),
}

for _id, _contract in ALTERNATES.items():
    _contract["kind"] = ("machine_learning" if _id.startswith("ml-") else "frontend" if _id.startswith("fe-") else "backend")

def oracle(pack_id,args):
    if pack_id=='fe-easy':
        d=args[0]; name=str(d.get('name') or '').strip(); msg=str(d.get('message') or '').strip(); r=d.get('rating'); errors=[]
        if len(name)<2:errors.append('name')
        if len(msg)<10:errors.append('message')
        if type(r) is not int or r<1 or r>5:errors.append('rating')
        return {'valid':not errors,'errors':errors}
    if pack_id=='fe-medium':
        groups=defaultdict(list)
        for x in args[0]:groups[x['date']].append(x['name'])
        return {k:sorted(v) for k,v in groups.items()}
    if pack_id=='fe-advanced':
        lines=deepcopy(args[0]); actions=args[1]
        for a in actions:
            i=a['index'];kind=a['type']
            if kind=='insert' and 0<=i<=len(lines):lines.insert(i,a['text'])
            elif kind=='replace' and 0<=i<len(lines):lines[i]=a['text']
            elif kind=='delete' and 0<=i<len(lines):lines.pop(i)
        return lines
    if pack_id=='fe-hard':
        features,roles=args;fmap={f['id']:f for f in features};memo={}
        def enabled(k,vis):
            if k in memo:return memo[k]
            if k not in fmap or k in vis:return False
            f=fmap[k]
            ok=bool(set(roles)&set(f['allowedRoles'])) and all(enabled(d,vis|{k}) for d in f['requires'])
            memo[k]=ok;return ok
        return sorted(k for k in fmap if enabled(k,set()))
    if pack_id in ('fe-expert','be-expert'):
        nodes,edges=args
        if pack_id=='be-expert':edges=[[b,a] for a,b in edges]
        remaining=set(nodes);out=[]
        while remaining:
            ready=sorted(x for x in remaining if not any(b==x and a in remaining for a,b in edges))
            if not ready:return {'order':[],'cyclic':True}
            x=ready[0];out.append(x);remaining.remove(x)
        return {'order':out,'cyclic':False}
    if pack_id=='be-easy':
        q=args[0];off=q.get('offset');lim=q.get('limit')
        return {'offset':off if type(off) is int and off>=0 else 0,'limit':lim if type(lim) is int and 1<=lim<=50 else 20}
    if pack_id=='be-medium':
        reqs,window,maximum=args;history=defaultdict(list);result=[]
        for r in reqs:
            times=[t for t in history[r['user']] if t>r['time']-window]
            yes=len(times)<maximum
            if yes:times.append(r['time'])
            history[r['user']]=times;result.append(yes)
        return result
    if pack_id=='be-advanced':
        seen=set();tot=defaultdict(int)
        for x in args[0]:
            if x['id'] in seen:continue
            seen.add(x['id'])
            # Decimal half-up cents in common payment systems.
            from decimal import Decimal, ROUND_HALF_UP
            cents=int((Decimal(str(x['amount']))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
            tot[x['invoice']]+=cents if x['kind']=='charge' else -cents
        return dict(tot)
    if pack_id=='be-hard':
        base,cap,n=args
        return [min(cap,base*(2**i)) for i in range(max(0,n))]
    if pack_id=='ml-easy':
        a,b=args;return {'tp':sum(x==y==1 for x,y in zip(a,b)),'tn':sum(x==y==0 for x,y in zip(a,b)), 'fp':sum(x==0 and y==1 for x,y in zip(a,b)),'fn':sum(x==1 and y==0 for x,y in zip(a,b))}
    if pack_id=='ml-medium':
        a,b=args;labels=set(a)|set(b)
        if not labels:return 0.0
        fs=[]
        for label in labels:
            tp=sum(x==label and y==label for x,y in zip(a,b));fp=sum(x!=label and y==label for x,y in zip(a,b));fn=sum(x==label and y!=label for x,y in zip(a,b))
            fs.append(2*tp/(2*tp+fp+fn) if (2*tp+fp+fn) else 0)
        return sum(fs)/len(fs)
    if pack_id=='ml-advanced':
        train,test=args;mean=sum(train)/len(train);sd=(sum((x-mean)**2 for x in train)/len(train))**0.5
        return [(x-mean)/sd if sd else 0 for x in test]
    if pack_id=='ml-hard':
        rows,required=args;indices=[];counts=Counter()
        for i,row in enumerate(rows):
            missing=[name for name in required if name not in row or row[name] is None or row[name]=='']
            if missing:indices.append(i);counts.update(missing)
        return {'invalid_indices':indices,'missing_counts':dict(counts)}
    if pack_id=='ml-expert':
        query,docs,k=args
        if k<=0:return []
        def sim(vec):
            na=sum(x*x for x in query)**0.5;nb=sum(x*x for x in vec)**0.5
            return sum(a*b for a,b in zip(query,vec))/(na*nb) if na*nb else 0.0
        return [doc['id'] for doc in sorted(docs,key=lambda x:(-sim(x['vector']),x['id']))[:k]]
    raise KeyError(pack_id)

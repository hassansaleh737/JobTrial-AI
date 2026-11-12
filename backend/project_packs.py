"""V5: honest, differentiated JavaScript work projects with independent test oracles.

AI can author a fictional manager brief, not executable evaluator code. Each level
maps to a DIFFERENT validated work contract. All student code runs only in an
opt-in isolated Docker container; this is not a public production code runner.
"""
from __future__ import annotations
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from copy import deepcopy
from pathlib import Path
from .engine import check,result
from .alternate_contracts import ALTERNATES, oracle as alt_oracle

# Each template is a distinct task, not the same checkout calculation with more prose.
PACKS = {
  'fe-easy': {
    'title':'Repair a registration form validator', 'function':'validateSignup',
    'goal':'The registration form accepts invalid addresses and weak passwords. Return a validation result that the interface can use before sending the form.',
    'spec':['Export validateSignup(data) from src/solution.js.','Return {valid:boolean, errors:string[]} with errors in email, password, consent order.','A valid email has one @ and a dot in its domain, with no whitespace.','Password needs at least 8 characters. Consent must be true.','Do not mutate data.'],
    'hint':'Normalize the email string, collect errors, then return valid: errors.length === 0.',
    'starter':"const { normalizeEmail } = require('./helpers');\n\nfunction validateSignup(data) {\n  // Return { valid: boolean, errors: string[] }\n  return { valid: false, errors: [] };\n}\nmodule.exports = { validateSignup };\n",
    'helper':"function normalizeEmail(value) {\n  return String(value ?? '').trim().toLowerCase();\n}\nmodule.exports = { normalizeEmail };\n",
    'cases':[
      [{'email':'a@example.com','password':'abcdefgh','consent':True}],
      [{'email':'bad','password':'short','consent':False}],
      [{'email':'  JOE@Example.Com ','password':'long-password','consent':True}],
      [{'email':'joe@localhost','password':'12345678','consent':True}],
      [{'email':'a @example.com','password':'12345678','consent':True}],
    ],
    'kind':'frontend',
  },
  'fe-medium': {
    'title':'Build a searchable and sortable product list', 'function':'searchCatalog',
    'goal':'A store search page needs a reliable pure function. Filter by title and category, then sort by price and limit the results.',
    'spec':['Export searchCatalog(items, options).','options.query filters title case-insensitively; missing query means all.','options.category filters exact category when present.','sort can be price_asc or price_desc; otherwise keep original order.','options.limit (integer >= 0) cuts the result; omit limit to return all. Do not mutate inputs.'],
    'hint':'Use filter first, sort a copied array, then slice if a limit was supplied.',
    'starter':"function searchCatalog(items, options = {}) {\n  // Return the list of matching item objects.\n  return [];\n}\nmodule.exports = { searchCatalog };\n",
    'cases':[
      [[{'id':1,'title':'Blue Mug','category':'home','price':20},{'id':2,'title':'Red Bag','category':'travel','price':40},{'id':3,'title':'Travel Mug','category':'home','price':12}], {'query':'mug','sort':'price_asc'}],
      [[{'id':1,'title':'A','category':'a','price':1},{'id':2,'title':'B','category':'b','price':5}],{'category':'b'}],
      [[{'id':1,'title':'A','category':'a','price':10},{'id':2,'title':'B','category':'a','price':30},{'id':3,'title':'C','category':'a','price':20}],{'sort':'price_desc','limit':2}],
      [[{'id':1,'title':'Test','category':'a','price':1}],{'query':'missing'}],
      [[], {'limit':10}],
    ], 'kind':'frontend',
  },
  'fe-advanced': {
    'title':'Implement a robust shopping-cart state reducer', 'function':'cartReducer',
    'goal':'Cart updates from several components are producing duplicate rows. Write a pure reducer for add, set_quantity and remove actions.',
    'spec':['Export cartReducer(cart, action).','Items have {id, qty}. add increments qty (default 1); set_quantity sets qty.','remove deletes the matching id. Quantity <= 0 removes the item.','Preserve the original item order and append new ids at the end.','Do not mutate the original cart or action.'],
    'hint':'Copy entries before changing them. Handle actions separately and avoid in-place mutation.',
    'starter':"function cartReducer(cart, action) {\n  // Return a new cart array.\n  return cart;\n}\nmodule.exports = { cartReducer };\n",
    'cases':[
      [[{'id':'a','qty':2}], {'type':'add','id':'a','qty':3}],
      [[{'id':'a','qty':2}], {'type':'add','id':'b'}],
      [[{'id':'a','qty':2},{'id':'b','qty':1}], {'type':'set_quantity','id':'a','qty':0}],
      [[{'id':'a','qty':2},{'id':'b','qty':1}], {'type':'remove','id':'a'}],
      [[{'id':'a','qty':2}], {'type':'set_quantity','id':'a','qty':5}],
    ], 'kind':'frontend',
  },
  'fe-hard': {
    'title':'Build schema-driven form validation', 'function':'validateFields',
    'goal':'Multiple onboarding forms disagree about validation. Create a reusable form engine that supports required fields, length, minimum numeric values, and matching another field.',
    'spec':['Export validateFields(values, rules), returning {fieldName:[error_codes]} (omit fields with no errors).','Rules for each field may contain required:true, minLength:number, minValue:number, sameAs:string.','Return error codes in the order required, minLength, minValue, sameAs.','Empty means null, undefined, or empty string (after trim).','Skip non-required validation for empty fields. Do not mutate inputs.'],
    'hint':'Walk Object.entries(rules), collect code strings for each failed rule, and add only fields with errors.',
    'starter':"function validateFields(values, rules) {\n  // Return an object of field -> array of error codes.\n  return {};\n}\nmodule.exports = { validateFields };\n",
    'cases':[
      [{'email':'','password':'abc','confirm':'abcd'},{'email':{'required':True},'password':{'required':True,'minLength':8},'confirm':{'sameAs':'password'}}],
      [{'age':17},{'age':{'minValue':18}}],
      [{'name':'   '},{'name':{'required':True,'minLength':3}}],
      [{'name':'Jane','score':20},{'name':{'required':True,'minLength':2},'score':{'minValue':10}}],
      [{'pass':'abcdefgh','confirm':'abcdefgh'},{'pass':{'minLength':8},'confirm':{'sameAs':'pass'}}],
    ], 'kind':'frontend',
  },
  'fe-expert': {
    'title':'Reconcile offline edits from multiple devices', 'function':'syncOfflineEvents',
    'goal':'A field-service PWA receives duplicated and out-of-order edits after offline sync. Reconcile events deterministically without resurrecting deleted records.',
    'spec':['Export syncOfflineEvents(events), returning sorted [{key,value}] for currently active records.','Each event has id (dedupe key), key (record id), version, op (upsert|delete), and optional value.','Ignore repeated event ids after their first occurrence.','For each record, the greatest version wins. Ties use the later event in input order.','A winning delete removes the record. Sort output by key lexicographically. Do not mutate input.'],
    'hint':'Keep a Set of event ids and a Map keyed by record key; replace entries on >= version.',
    'starter':"function syncOfflineEvents(events) {\n  // Return the reconciled active [{ key, value }] records.\n  return [];\n}\nmodule.exports = { syncOfflineEvents };\n",
    'cases':[
      [[{'id':'a1','key':'x','version':1,'op':'upsert','value':'one'},{'id':'a2','key':'x','version':2,'op':'upsert','value':'two'}]],
      [[{'id':'z','key':'x','version':3,'op':'delete'},{'id':'y','key':'x','version':2,'op':'upsert','value':'old'}]],
      [[{'id':'1','key':'b','version':1,'op':'upsert','value':1},{'id':'2','key':'a','version':1,'op':'upsert','value':2},{'id':'1','key':'b','version':9,'op':'delete'}]],
      [[{'id':'1','key':'a','version':2,'op':'upsert','value':'old'},{'id':'2','key':'a','version':2,'op':'upsert','value':'new'}]],
      [[]],
    ], 'kind':'frontend',
  },
  'be-easy': {
    'title':'Fix a pricing calculation', 'function':'calculateOrderTotal',
    'goal':'An order service is calculating discounts incorrectly. Return a correct final total from line items and one percentage discount.',
    'spec':['Export calculateOrderTotal(items, discountPct).','Each item contains price and qty; sum price * qty.','Treat discountPct outside 0–100 as 0.','Return the final total rounded to 2 decimal places. Empty items return 0.'],
    'hint':'Compute subtotal first, apply a percentage, then round only at the end.',
    'starter':"function calculateOrderTotal(items, discountPct) {\n  // Calculate discounted total for the entire order.\n  return 0;\n}\nmodule.exports = { calculateOrderTotal };\n",
    'cases':[[[{'price':10,'qty':2},{'price':5,'qty':1}],10], [[],30],[[{'price':20,'qty':3}],0],[[{'price':15,'qty':2}],110],[[{'price':12.5,'qty':2},{'price':7,'qty':1}],20]],
    'kind':'backend',
  },
  'be-medium': {
    'title':'Implement stock reservation safely', 'function':'reserveStock',
    'goal':'Checkout is overselling items when it ignores stock limits. Return a new stock snapshot only when a reservation can be accepted.',
    'spec':['Export reserveStock(stock, request).','stock maps SKU to available quantity; request contains sku and qty.','Return {ok:boolean,stock:object}.','Reject qty <= 0, missing SKU, or insufficient stock. On failure return an unchanged stock snapshot.','Do not mutate inputs.'],
    'hint':'Validate availability before creating a modified copy of stock.',
    'starter':"function reserveStock(stock, request) {\n  // Return { ok: true/false, stock: updatedCopy }.\n  return { ok: false, stock: { ...stock } };\n}\nmodule.exports = { reserveStock };\n",
    'cases':[[{'A':5,'B':2},{'sku':'A','qty':3}], [{'A':1},{'sku':'A','qty':2}],[{'A':5},{'sku':'X','qty':1}], [{'A':5},{'sku':'A','qty':0}], [{'A':4},{'sku':'A','qty':4}]],
    'kind':'backend',
  },
  'be-advanced': {
    'title':'Build an atomic order-allocation pipeline', 'function':'allocateOrders',
    'goal':'Fulfillment accepts orders line by line, leaving partial reservations when one item is missing. Allocate complete orders atomically in request order.',
    'spec':['Export allocateOrders(stock, orders).','Each order has id and lines [{sku,qty}]. Process orders in order.','An order is accepted only if every line can be reserved; combine duplicate SKU lines.','Reject zero/negative quantities and missing SKUs. On rejection make no stock changes.','Return {stock, accepted:[ids], rejected:[ids]} and do not mutate inputs.'],
    'hint':'Create totals per SKU for each order, validate all totals, then commit the reductions.',
    'starter':"function allocateOrders(stock, orders) {\n  // Keep each order atomic, never partially reserve an order.\n  return { stock: { ...stock }, accepted: [], rejected: [] };\n}\nmodule.exports = { allocateOrders };\n",
    'cases':[
      [{'A':5,'B':1},[{'id':'o1','lines':[{'sku':'A','qty':2},{'sku':'B','qty':1}]},{'id':'o2','lines':[{'sku':'A','qty':4}]}]],
      [{'A':5},[{'id':'o1','lines':[{'sku':'A','qty':3},{'sku':'A','qty':3}]}]],
      [{'A':4,'B':2},[{'id':'o1','lines':[{'sku':'X','qty':1}]},{'id':'o2','lines':[{'sku':'B','qty':2}]}]],
      [{'A':4},[]],
      [{'A':5},[{'id':'o1','lines':[{'sku':'A','qty':-1}]},{'id':'o2','lines':[{'sku':'A','qty':5}]}]],
    ],'kind':'backend',
  },
  'be-hard': {
    'title':'Prevent duplicate purchases on retry', 'function':'processRequests',
    'goal':'A payment timeout causes clients to retry requests. Implement idempotency so the same key never reserves inventory twice.',
    'spec':['Export processRequests(stock, requests).','Requests have key, sku and qty. Process sequentially.','For a repeated key, record status duplicate and make no stock change, even if the first attempt was rejected.','New requests with invalid qty, missing SKU or insufficient stock get status rejected; otherwise accepted.','Return {stock, results:[{key,status}]} with input order preserved. Do not mutate inputs.'],
    'hint':'Track every first-seen idempotency key in a Set, including rejected attempts.',
    'starter':"function processRequests(stock, requests) {\n  // Each request key should affect stock at most once.\n  return { stock: { ...stock }, results: [] };\n}\nmodule.exports = { processRequests };\n",
    'cases':[
      [{'A':5},[{'key':'a','sku':'A','qty':2},{'key':'a','sku':'A','qty':2},{'key':'b','sku':'A','qty':3}]],
      [{'A':2},[{'key':'a','sku':'A','qty':5},{'key':'a','sku':'A','qty':1}]],
      [{'A':4},[{'key':'a','sku':'Z','qty':1},{'key':'b','sku':'A','qty':2}]],
      [{'A':4},[{'key':'a','sku':'A','qty':0},{'key':'b','sku':'A','qty':4}]],
      [{'A':4},[]],
    ],'kind':'backend',
  },
  'be-expert': {
    'title':'Reconcile an event-driven payment ledger', 'function':'reconcilePayments',
    'goal':'A payment service receives duplicate charge/refund events and refunds in arbitrary order. Produce a reliable settlement report with anomaly flags.',
    'spec':['Export reconcilePayments(events).','Events contain eventId, orderId, type (charge|refund), amount. Ignore duplicate eventIds after first occurrence.','Aggregate charges and refunds per order independent of arrival order.','Return {orders:[{orderId, net, anomaly}], anomalyCount}; net is max(charges-refunds,0) rounded to cents.','Flag anomaly when refunds exceed charges. Sort orders by orderId lexicographically; never mutate inputs.'],
    'hint':'Aggregate integer cents by order first; handle duplicates, then derive net and anomaly in a final pass.',
    'starter':"function reconcilePayments(events) {\n  // Return { orders: [...], anomalyCount: number }.\n  return { orders: [], anomalyCount: 0 };\n}\nmodule.exports = { reconcilePayments };\n",
    'cases':[
      [[{'eventId':'1','orderId':'A','type':'charge','amount':10},{'eventId':'2','orderId':'A','type':'refund','amount':3}]],
      [[{'eventId':'x','orderId':'A','type':'refund','amount':9},{'eventId':'y','orderId':'A','type':'charge','amount':5}]],
      [[{'eventId':'1','orderId':'B','type':'charge','amount':11},{'eventId':'1','orderId':'B','type':'charge','amount':11},{'eventId':'2','orderId':'A','type':'charge','amount':2}]],
      [[]],
      [[{'eventId':'1','orderId':'A','type':'charge','amount':10.25},{'eventId':'2','orderId':'A','type':'refund','amount':10.25}]],
    ], 'kind':'backend',
  },
}


# AI/ML engineering path: five independent Python assignments, not a renamed arithmetic problem.
PACKS.update({
 'ml-easy':{
  'title':'Repair the classification accuracy metric','function':'accuracy_score','kind':'machine_learning','language':'python',
  'goal':'The validation pipeline reports incorrect classification accuracy. Return the fraction of equal labels; empty inputs return 0.',
  'spec':['Export accuracy_score(actual, predicted).','Return 0 for empty data.','Return a fraction between 0 and 1.','Do not modify the given arrays.'],
  'hint':'Count matching positions and divide by the length; handle the empty case first.',
  'starter':"def accuracy_score(actual, predicted):\n    # Return a float between 0 and 1.\n    return 0.0\n",
  'cases':[[[1,0,1,1],[1,0,0,1]],[[0,0],[0,1]],[[],[]],[[1,1,1],[1,1,1]],[[0,1,0,1,1],[1,1,0,0,1]]],
 },
 'ml-medium':{
  'title':'Build reliable precision and recall metrics','function':'precision_recall','kind':'machine_learning','language':'python',
  'goal':'A fraud detection model has an imbalanced dataset. Implement positive-class precision and recall with safe handling of zero denominators.',
  'spec':['Export precision_recall(actual,predicted).','Return {"precision":float,"recall":float}.','Treat label 1 as positive; other labels are negatives.','If a denominator is zero, return 0 for that metric.'],
  'hint':'Count true positives, false positives and false negatives separately.',
  'starter':"def precision_recall(actual, predicted):\n    # Compute positive-class precision and recall.\n    return {'precision': 0.0, 'recall': 0.0}\n",
  'cases':[[[1,0,1,0],[1,1,0,0]],[[0,0],[0,0]],[[1,1],[0,0]],[[1,1,0],[1,1,1]],[[],[]]],
 },
 'ml-advanced':{
  'title':'Choose a classification threshold using F1','function':'select_threshold','kind':'machine_learning','language':'python',
  'goal':'A classifier produces probabilities, not final labels. Evaluate thresholds 0.3, 0.5 and 0.7; select the one with highest positive-class F1.',
  'spec':['Export select_threshold(scores,actual).','Use thresholds 0.3, 0.5, 0.7 (predict 1 when score >= threshold).','Return {"threshold":number,"f1":number}.','If F1 is tied, select the smaller threshold. If no positives, F1 is 0.'],
  'hint':'Calculate TP, FP and FN for each threshold; F1=2TP/(2TP+FP+FN).',
  'starter':"def select_threshold(scores, actual):\n    # Choose the best positive-class F1 among the three thresholds.\n    return {'threshold': 0.3, 'f1': 0.0}\n",
  'cases':[[[.1,.4,.8,.9],[0,1,1,1]],[[.2,.4,.6,.8],[0,0,1,1]],[[.1,.2],[0,0]],[[.35,.36,.65,.66],[1,1,0,0]],[[.1,.5,.9],[1,1,0]]],
 },
 'ml-hard':{
  'title':'Detect distribution drift before deployment','function':'detect_drift','kind':'machine_learning','language':'python',
  'goal':'Production features shifted after a new data source was added. Compare discrete bucket distributions, report total-variation distance and a drift warning.',
  'spec':['Export detect_drift(reference,current).','Arrays contain categorical bucket ids (integers).','Score is 0.5 * sum of absolute probability differences across all buckets.','Return {"score":rounded_to_3_decimals,"drifted": score > 0.25}.','For an empty side, return score 0 and drifted False.'],
  'hint':'Count each distinct bucket in the union, compute frequencies for each dataset.',
  'starter':"def detect_drift(reference, current):\n    # Total variation distance between two categorical histograms.\n    return {'score': 0.0, 'drifted': False}\n",
  'cases':[[[1,1,2,2],[1,1,2,2]],[[1,1,1,1],[2,2,2,2]],[[1,2,3,3],[1,2,2,2]],[[0,0,1],[0,1,1]], [[],[1,2]]],
 },
 'ml-expert':{
  'title':'Evaluate a retrieval-augmented search pipeline','function':'evaluate_rag','kind':'machine_learning','language':'python',
  'goal':'Your search service produces ranked document IDs, and you need a repeatable evaluation report. Calculate average Recall@3 and MRR across queries, including empty ground truth.',
  'spec':['Export evaluate_rag(runs).','Each run has retrieved IDs in rank order and relevant IDs.','Per-query recall@3 = distinct relevant IDs among top 3 / total distinct relevant; zero when no relevant.','Per-query reciprocal rank = 1/rank of first relevant hit in the full retrieval list, else 0.','Return {"recall_at_3":float,"mrr":float} averaged across runs; empty runs return both 0.'],
  'hint':'Use sets for relevance, rank from 1, average each metric over the number of queries.',
  'starter':"def evaluate_rag(runs):\n    # Return average Recall@3 and MRR.\n    return {'recall_at_3': 0.0, 'mrr': 0.0}\n",
  'cases':[[{'retrieved':['a','x','b'],'relevant':['a','b']},{'retrieved':['c','d'],'relevant':['z']}],
           [{'retrieved':['d','c','b','a'],'relevant':['a','c']}],[],
           [{'retrieved':[],'relevant':['x']},{'retrieved':['a','b'],'relevant':[]}],
           [{'retrieved':['x','x','a','b'],'relevant':['a','b']}]],
 },
})

PACKS['ml-expert']['cases']=[[runs] for runs in PACKS['ml-expert']['cases']]

LEVEL_PACK={'easy':'easy','medium':'medium','advanced':'advanced','hard':'hard','expert':'expert'}


def select_pack(description:str,level:str,lang:str,family:str):
    """Only route JavaScript frontend/Node jobs to a verified JS project pack."""
    if lang=='python' and family=='machine_learning':
        return f'ml-{LEVEL_PACK[level]}'
    if lang=='javascript' and family in ('frontend','backend','qa'):
        return f"{'fe' if family=='frontend' else 'be'}-{LEVEL_PACK[level]}"
    return None


def _oracle(pack:str,args:list):
    """Reference implementation in trusted Python, independent from submitted JS."""
    if pack=='ml-easy':
        actual,pred=args;return sum(x==y for x,y in zip(actual,pred))/len(actual) if actual else 0.0
    if pack=='ml-medium':
        actual,pred=args;tp=sum(a==1 and b==1 for a,b in zip(actual,pred));fp=sum(a!=1 and b==1 for a,b in zip(actual,pred));fn=sum(a==1 and b!=1 for a,b in zip(actual,pred))
        return {'precision':tp/(tp+fp) if tp+fp else 0.0,'recall':tp/(tp+fn) if tp+fn else 0.0}
    if pack=='ml-advanced':
        scores,actual=args;best=(0.3,-1.0)
        for th in (0.3,0.5,0.7):
            guesses=[int(p>=th) for p in scores]
            tp=sum(a==1 and p==1 for a,p in zip(actual,guesses));fp=sum(a==0 and p==1 for a,p in zip(actual,guesses));fn=sum(a==1 and p==0 for a,p in zip(actual,guesses))
            f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0
            if f1>best[1]:best=(th,f1)
        return {'threshold':best[0],'f1':best[1]}
    if pack=='ml-hard':
        ref,cur=args
        if not ref or not cur:return {'score':0.0,'drifted':False}
        score=0.5*sum(abs(ref.count(k)/len(ref)-cur.count(k)/len(cur)) for k in set(ref)|set(cur))
        return {'score':round(score,3),'drifted':score>0.25}
    if pack=='ml-expert':
        runs=args[0]
        if not runs:return {'recall_at_3':0.0,'mrr':0.0}
        recalls=[];rr=[]
        for run in runs:
            relevant=set(run['relevant']);top=set(run['retrieved'][:3]);recalls.append(len(relevant&top)/len(relevant) if relevant else 0.0)
            rank=next((i+1 for i,v in enumerate(run['retrieved']) if v in relevant),None)
            rr.append(1/rank if rank else 0.0)
        return {'recall_at_3':sum(recalls)/len(runs),'mrr':sum(rr)/len(runs)}
    if pack=='fe-easy':
        d=args[0]; email=str(d.get('email') or '').strip().lower(); pwd=str(d.get('password') or '')
        errors=[]
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):errors.append('email')
        if len(pwd)<8:errors.append('password')
        if d.get('consent') is not True:errors.append('consent')
        return {'valid':not errors,'errors':errors}
    if pack=='fe-medium':
        items,opt=args; out=[x for x in items if str(opt.get('query','')).lower() in x['title'].lower() and (not opt.get('category') or x['category']==opt['category'])]
        if opt.get('sort') in ('price_asc','price_desc'):out=sorted(out,key=lambda x:x['price'],reverse=opt['sort']=='price_desc')
        if 'limit' in opt and isinstance(opt['limit'],int) and opt['limit']>=0:out=out[:opt['limit']]
        return out
    if pack=='fe-advanced':
        cart,act=args; out=deepcopy(cart); typ=act.get('type');id_=act.get('id')
        if typ=='remove':return [x for x in out if x['id']!=id_]
        if typ in ('add','set_quantity'):
            curr=next((x for x in out if x['id']==id_),None)
            qty=act.get('qty',1) if typ=='add' else act.get('qty',0)
            new=(curr['qty']+qty if curr else qty) if typ=='add' else qty
            if curr:curr['qty']=new
            elif new>0:out.append({'id':id_,'qty':new})
            return [x for x in out if x['qty']>0]
        return out
    if pack=='fe-hard':
        values,rules=args;out={}
        for k,r in rules.items():
            val=values.get(k);empty=(val is None or isinstance(val,str) and not val.strip())
            err=[]
            if r.get('required') and empty:err.append('required')
            if not empty:
                if 'minLength' in r and len(str(val))<r['minLength']:err.append('minLength')
                if 'minValue' in r and (not isinstance(val,(int,float)) or val<r['minValue']):err.append('minValue')
                if 'sameAs' in r and val != values.get(r['sameAs']):err.append('sameAs')
            if err:out[k]=err
        return out
    if pack=='fe-expert':
        events=args[0];seen=set();states={}
        for e in events:
            if e['id'] in seen:continue
            seen.add(e['id']);prev=states.get(e['key'])
            if prev is None or e['version']>=prev['version']:states[e['key']]=e
        return [{'key':k,'value':e.get('value')} for k,e in sorted(states.items()) if e['op']!='delete']
    if pack=='be-easy':
        items,discount=args; subtotal=sum(x['price']*x['qty'] for x in items); percent=discount if 0<=discount<=100 else 0
        return round(subtotal*(1-percent/100)+1e-9,2)
    if pack=='be-medium':
        stock,req=args;out=dict(stock);sku=req.get('sku');qty=req.get('qty',0)
        ok=isinstance(qty,int) and qty>0 and sku in stock and stock[sku]>=qty
        if ok:out[sku]-=qty
        return {'ok':ok,'stock':out}
    if pack=='be-advanced':
        stock,orders=args;out=dict(stock);accepted=[];rejected=[]
        for order in orders:
            totals={};valid=True
            for line in order['lines']:
                if not isinstance(line['qty'],int) or line['qty']<=0:valid=False
                totals[line['sku']]=totals.get(line['sku'],0)+line['qty']
            if not valid or any(k not in out or out[k]<q for k,q in totals.items()):rejected.append(order['id']);continue
            for sku,qty in totals.items():out[sku]-=qty
            accepted.append(order['id'])
        return {'stock':out,'accepted':accepted,'rejected':rejected}
    if pack=='be-hard':
        stock,requests=args;out=dict(stock);seen=set();results=[]
        for req in requests:
            k=req['key'];sku=req['sku'];qty=req['qty']
            if k in seen:status='duplicate'
            else:
                seen.add(k)
                if not isinstance(qty,int) or qty<=0 or sku not in out or out[sku]<qty:status='rejected'
                else:out[sku]-=qty;status='accepted'
            results.append({'key':k,'status':status})
        return {'stock':out,'results':results}
    if pack=='be-expert':
        events=args[0];seen=set();ledgers={}
        for e in events:
            if e['eventId'] in seen:continue
            seen.add(e['eventId']);r=ledgers.setdefault(e['orderId'],{'charge':0,'refund':0})
            r[e['type']]+=round(e['amount']*100)
        rows=[]
        for order,r in sorted(ledgers.items()):
            anom=r['refund']>r['charge'];rows.append({'orderId':order,'net':max(0,r['charge']-r['refund'])/100,'anomaly':anom})
        return {'orders':rows,'anomalyCount':sum(x['anomaly'] for x in rows)}
    raise KeyError(pack)


def variant_for(level:str,percent:int,reroll:int=0)->int:
    """Every adjacent slider value picks a different verified coding contract.

    Reroll swaps the contract for the *same* percent. There are two verified
    contracts per supported track/level; this is not limitless AI generation.
    """
    from .ai_missions import LEVELS
    return ((percent-LEVELS[level]['min'])+reroll)%2


def contract_for(pack_id:str,variant:int)->dict:
    if variant==0:return PACKS[pack_id]
    if variant==1:return ALTERNATES[pack_id]
    raise ValueError('Unknown challenge variant')


def project_task(pack_id:str,description:str,mission:dict|None,level:str,percent:int,seed:int,reroll:int=0):
    variant=variant_for(level,percent,reroll)
    pack=contract_for(pack_id,variant); language=pack.get('language','javascript'); ext='py' if language=='python' else 'js'; role=(mission or {}).get('role_title') or ('AI Engineer' if language=='python' else 'JavaScript Developer')
    # Keep the technical contract fully trusted, including name, return type and cases.
    sample=pack['cases'][(seed+percent+reroll) % len(pack['cases'])]
    context=(mission or {}).get('scenario','')
    # AI-authored narrative must not masquerade as changed executable requirements.
    scenario=('Your simulated manager has a new request. '+ context[:420]+'\n\n' if context else '')
    goal=scenario+pack['goal']+'\n\nDELIVERABLE: Edit src/solution.'+ext+'. Optional helpers belong in src/helpers.'+ext+'. Run the actual '+language+' checks using Docker.'
    readme=(f'# {pack["title"]}\n\n{pack["goal"]}\n\n'
           +'## Acceptance criteria\n'+'\n'.join('- '+x for x in pack['spec'])+'\n\n'
           +f'## Example input (JSON)\n{json.dumps(sample,ensure_ascii=False,indent=2)}\n\n'
           +'The inputs above are examples, not the complete test suite.\n'
           +'Docker is local-only. Do not use this app as a public code execution service.\n')
    files=[
      {'path':f'src/solution.{ext}','content':pack['starter'],'editable':True},
      {'path':f'src/helpers.{ext}','content':pack.get('helper',('# Optional helper functions\n' if language=='python' else '// Optional helper functions\nmodule.exports = {};\n')),'editable':True},
      {'path':'README.md','content':readme,'editable':False},
      {'path':'data/example.json','content':json.dumps(sample,ensure_ascii=False,indent=2),'editable':False},
    ]
    return {'id':f'pack:{pack_id}:{seed}:{percent}:v{variant}', 'title':pack['title'], 'tag':f'{language.title()} · {level.title()} · Docker-verified',
            'time':{'easy':'15 min','medium':'25 min','advanced':'40 min','hard':'55 min','expert':'75 min'}[level],
            'goal':goal,'spec':pack['spec'],'hint':(pack['hint'] if percent<({'easy':20,'medium':36,'advanced':55,'hard':75,'expert':93}[level]) else 'Hint budget is limited at this intensity. Inspect README.md and write tests for edge cases.'),'starter':pack['starter'],'lang':language,
            'files':files,'evaluation':'automated-docker','challenge_intensity':percent,'project_kind':pack['kind'],
            'ai_context':context,'role_context':role,'variant_number':variant+1,'variation_count':2}


def _equivalent(x,y)->bool:
    if isinstance(x,(int,float)) and isinstance(y,(int,float)) and not isinstance(x,bool) and not isinstance(y,bool):
        return math.isfinite(float(x)) and math.isclose(float(x),float(y),abs_tol=0.001,rel_tol=1e-8)
    if type(x)!=type(y):return False
    if isinstance(x,list):return len(x)==len(y) and all(_equivalent(a,b) for a,b in zip(x,y))
    if isinstance(x,dict):return x.keys()==y.keys() and all(_equivalent(x[k],y[k]) for k in x)
    return x==y


def _docker_script(pack_id:str, inputs:list,variant:int=0)->str:
    name=contract_for(pack_id,variant)['function']
    if PACKS[pack_id].get('language')=='python':
        return (f'from src.solution import {name}\nimport json\n'
                f'cases=json.loads({json.dumps(json.dumps(inputs,ensure_ascii=False))})\n'
                f'output=[]\nfor case in cases:\n    try:\n        output.append({{"value":{name}(*case)}})\n    except Exception as e:\n        output.append({{"error":str(e)[:180]}})\n'
                f'print("JOBTRIAL_V5_OUTPUT:"+json.dumps(output))\n')
    # Inputs are trusted fixtures, not data from LLM or submitted code.
    payload=json.dumps(inputs,ensure_ascii=False)
    return f'''const {{ {name} }} = require('./src/solution.js');
const cases = {payload};
const output = cases.map((a) => {{
  try {{
    const v = {name}(...JSON.parse(JSON.stringify(a)));
    if (v && typeof v.then === 'function') return {{error:'Promise not supported'}};
    return {{value:v === undefined ? null : v}};
  }} catch(e) {{ return {{error:String(e?.message||e).slice(0,180)}}; }}
}});
console.log('JOBTRIAL_V5_OUTPUT:' + JSON.stringify(output));
'''


def grade_project(task_id:str,files:dict[str,str])->dict:
    parts=task_id.split(':')
    if len(parts) not in (4,5) or parts[0]!='pack' or parts[1] not in PACKS or not (1<=len(parts[2])<=6 and parts[2].isdigit()) or not (1<=len(parts[3])<=3 and parts[3].isdigit()):
        return result([check('Valid project',False,'Unknown project id')],'Invalid project.',None,'project-docker')
    pack_id=parts[1]
    variant = 0 if len(parts)==4 else (int(parts[4][1:]) if parts[4] in ('v0','v1') else -1)
    if variant not in (0,1):
        return result([check('Valid variant',False,'Unknown challenge variant')],'Invalid project variant.',None,'project-docker')
    level=pack_id.rsplit('-',1)[-1]
    from .ai_missions import LEVELS
    band=LEVELS[level];percent=int(parts[3])
    if percent<band['min'] or percent>band['max']:
        return result([check('Valid intensity',False,'Intensity is outside the selected level.')],'Choose a valid difficulty.',None,'project-docker')
    if not os.getenv('JOBTRIAL_ENABLE_DOCKER','false').lower() in ('true','1','yes'):
        return result([check('Docker enabled',False,'Set JOBTRIAL_ENABLE_DOCKER=true in .env and restart FastAPI.')],
                      'This JavaScript project needs Docker Desktop.',None,'docker-disabled')
    if not shutil.which('docker'):
        return result([check('Docker CLI',False,'Docker executable is missing.')],'Start Docker Desktop and verify docker version.',None,'docker-unavailable')
    pack=contract_for(pack_id,variant)
    language=pack.get('language','javascript')
    ext='py' if language=='python' else 'js'
    allowed={f'src/solution.{ext}',f'src/helpers.{ext}'}
    if not isinstance(files,dict) or not allowed.issubset(files) or any(k not in allowed for k in files):
        return result([check('Expected files',False,'Send src/solution.js and src/helpers.js only.')],'Invalid project files.',None,'project-docker')
    if any(not isinstance(v,str) for v in files.values()) or sum(len(v) for v in files.values())>18000:
        return result([check('Source size',False,'Maximum 18,000 characters total.')],'Source too large.',None,'project-docker')
    seed=int(parts[2]);full=deepcopy(pack['cases'])
    ratio=(percent-band['min'])/max(1,band['max']-band['min'])
    count=3 if ratio<0.34 else 4 if ratio<0.68 else 5
    shift=(seed+percent if len(parts)==5 else seed)%len(full)
    cases=(full[shift:]+full[:shift])[:count]
    expected=[_oracle(pack_id,args) if variant==0 else alt_oracle(pack_id,args) for args in cases]
    # Deterministic extra variation does not change the trusted reference contract.
    try:
        with tempfile.TemporaryDirectory(prefix='jobtrial_project_') as tmp:
            root=Path(tmp);(root/'src').mkdir();os.chmod(root,0o755);os.chmod(root/'src',0o755)
            for name,source in files.items():
                p=root/name;p.write_text(source,encoding='utf-8');os.chmod(p,0o644)
            runner=root/('runner.py' if language=='python' else 'runner.js');runner.write_text(_docker_script(pack_id,cases,variant),encoding='utf-8');os.chmod(runner,0o644)
            args=['docker','run','--rm','--pull=never','--network=none','--read-only',
                  '--memory=256m','--memory-swap=256m','--cpus=0.75','--pids-limit=48',
                  '--cap-drop=ALL','--security-opt=no-new-privileges:true','--user=65534:65534',
                  '--tmpfs=/tmp:rw,nosuid,nodev,size=64m,mode=1777',
                  '--mount',f'type=bind,src={root.resolve()},dst=/workspace,readonly',
                  '--workdir=/workspace',('python:3.12-alpine' if language=='python' else 'node:24-alpine'),('python' if language=='python' else 'node'),('runner.py' if language=='python' else 'runner.js')]
            proc=subprocess.run(args,capture_output=True,text=True,timeout=15,check=False)
    except subprocess.TimeoutExpired:
        return result([check('Time limit',False,'Execution exceeded 15 seconds')],'Optimize your solution.',None,'project-docker')
    except (OSError,ValueError) as exc:
        return result([check('Docker execution',False,str(exc)[:180])],'Docker could not start. Check Docker Desktop.',None,'project-docker')
    if proc.returncode:
        return result([check('Syntax and runtime',False,(proc.stderr or proc.stdout or 'Runner failed')[-360:])],
                      'Code did not execute. Verify the function signature and exports; docker pull '+('python:3.12-alpine' if language=='python' else 'node:24-alpine')+'.',None,'project-docker')
    prefix='JOBTRIAL_V5_OUTPUT:'
    rows=[s[len(prefix):] for s in proc.stdout.splitlines() if s.startswith(prefix)]
    try:
        observed=json.loads(rows[-1])
        if not isinstance(observed,list) or len(observed)!=len(expected):raise ValueError('Incorrect result count')
    except (ValueError,IndexError,TypeError):
        return result([check('Runner output',False,'Expected assessment output was not produced.')],'Could not grade submission.',None,'project-docker')
    checks=[]
    for i,(want,item) in enumerate(zip(expected,observed)):
        value=item.get('value') if isinstance(item,dict) else None
        ok=isinstance(item,dict) and 'error' not in item and _equivalent(value,want)
        detail=(f'Expected: {json.dumps(want,ensure_ascii=False)[:140]} · Actual: {json.dumps(value,ensure_ascii=False)[:140]}' if i<2 else ('Passed additional scenario' if ok else 'Additional scenario failed'))
        if isinstance(item,dict) and 'error' in item:detail='Runtime error: '+str(item['error'])[:140]
        checks.append(check(f'Functional test {i+1}',ok,detail))
    return result(checks,'Verified output against independent test cases. This does not measure overall job readiness.',None,'project-docker-'+language)

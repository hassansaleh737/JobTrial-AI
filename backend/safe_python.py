"""Small bounded *interpreter*, not Python exec/eval. Supports common beginner logic.
Not a complete Python runtime or a general-purpose security sandbox.
"""
from __future__ import annotations
import ast
import math
import operator

BIN={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,
     ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod}
CMP={ast.Eq:operator.eq,ast.NotEq:operator.ne,ast.In:lambda a,b:a in b,ast.NotIn:lambda a,b:a not in b,ast.Lt:operator.lt,ast.LtE:operator.le,ast.Gt:operator.gt,ast.GtE:operator.ge}
SAFE_FUNCS={'round':round,'abs':abs,'min':min,'max':max,'sum':sum,'len':len,'int':int,'float':float}
class ReturnSignal(Exception):
    def __init__(self,value):self.value=value

class Interpreter:
    def __init__(self,code:str,name:str,params:list[str]):
        if len(code)>6000:raise ValueError('Limit: 6,000 characters')
        try:self.tree=ast.parse(code)
        except (SyntaxError,RecursionError,MemoryError) as e:raise ValueError(f'Python parse error: {str(e)[:120]}') from None
        if len(list(ast.walk(self.tree)))>350:raise ValueError('Code is too complex for this safe lab')
        funcs=[node for node in self.tree.body if isinstance(node,ast.FunctionDef)]
        if len(self.tree.body)!=1 or len(funcs)!=1:raise ValueError('Provide one function. Imports, top-level execution and classes are not supported by the local interpreter.')
        self.fn=funcs[0]
        if self.fn.name!=name or [a.arg for a in self.fn.args.args]!=params or self.fn.decorator_list or self.fn.args.defaults or self.fn.args.kwonlyargs:
            raise ValueError(f'Keep the signature: def {name}({", ".join(params)}):')
        self.budget=0
    def tick(self):
        self.budget+=1
        if self.budget>2400:raise ValueError('Too many operations; reduce loops or input size')
    def safe(self,x):
        if isinstance(x,bool) or x is None:return x
        if type(x) in (int,float):
            if not math.isfinite(x) or abs(x)>1e10:raise ValueError('Value out of range')
            return x
        if isinstance(x,(list,tuple)) and len(x)<=400:return [self.safe(v) for v in x]
        if isinstance(x,str) and len(x)<=400:return x
        raise ValueError('Unsupported value or value too large')
    def expr(self,n,env,depth=0):
        self.tick()
        if depth>30:raise ValueError('Expression nesting too deep')
        def ev(child):return self.expr(child,env,depth+1)
        if isinstance(n,ast.Constant) and (n.value is None or type(n.value) in (int,float,str,bool)):return self.safe(n.value)
        if isinstance(n,ast.Name) and n.id in env:return self.safe(env[n.id])
        if isinstance(n,(ast.List,ast.Tuple)):return self.safe([ev(x) for x in n.elts])
        if isinstance(n,ast.BinOp) and type(n.op) in BIN:return self.safe(BIN[type(n.op)](ev(n.left),ev(n.right)))
        if isinstance(n,ast.UnaryOp) and type(n.op) in (ast.USub,ast.UAdd,ast.Not):
            x=ev(n.operand)
            return (not x) if isinstance(n.op,ast.Not) else self.safe(-x if isinstance(n.op,ast.USub) else +x)
        if isinstance(n,ast.BoolOp) and type(n.op) in (ast.And,ast.Or):
            if isinstance(n.op,ast.And):
                val=True
                for v in n.values:
                    val=ev(v)
                    if not val:break
                return val
            val=False
            for v in n.values:
                val=ev(v)
                if val:break
            return val
        if isinstance(n,ast.Compare):
            left=ev(n.left)
            for op,comp in zip(n.ops,n.comparators):
                if type(op) not in CMP:raise ValueError('Comparison not supported')
                right=ev(comp)
                if not CMP[type(op)](left,right):return False
                left=right
            return True
        if isinstance(n,ast.IfExp):return ev(n.body) if ev(n.test) else ev(n.orelse)
        if isinstance(n,ast.Subscript):
            seq,idx=ev(n.value),ev(n.slice)
            if not isinstance(seq,(list,str)) or type(idx)!=int:raise ValueError('Only integer indexing of lists/text is supported')
            return self.safe(seq[idx])
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='append' and isinstance(n.func.value,ast.Name) and not n.keywords and len(n.args)==1:
            key=n.func.value.id
            if key not in env or type(env[key])!=list:raise ValueError('append() requires a local list')
            if len(env[key])>=400:raise ValueError('List too large')
            env[key].append(self.safe(ev(n.args[0])))
            return None
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and not n.keywords:
            name=n.func.id
            args=[ev(a) for a in n.args]
            if name=='range' and 1<=len(args)<=3 and all(type(x)==int and abs(x)<=400 for x in args):
                r=list(range(*args))
                if len(r)>400:raise ValueError('Range too large')
                return r
            if name in SAFE_FUNCS and len(args)<=3:return self.safe(SAFE_FUNCS[name](*args))
        raise ValueError(f'{type(n).__name__} not supported by the local interpreter. Use variables, if, bounded for/while loops, lists and basic arithmetic; Docker mode supports full language syntax.')
    def assign(self,node,value,env):
        if isinstance(node,ast.Name) and not node.id.startswith('__'):env[node.id]=self.safe(value);return
        raise ValueError('Only local variable assignment is supported')
    def block(self,stmts,env):
        for stmt in stmts:
            self.tick()
            if isinstance(stmt,ast.Return):raise ReturnSignal(self.expr(stmt.value,env) if stmt.value else None)
            elif isinstance(stmt,ast.Assign):
                val=self.expr(stmt.value,env)
                for target in stmt.targets:self.assign(target,val,env)
            elif isinstance(stmt,ast.AugAssign) and isinstance(stmt.target,ast.Name) and type(stmt.op) in BIN:
                k=stmt.target.id
                if k not in env:raise ValueError('Undefined variable')
                self.assign(stmt.target,BIN[type(stmt.op)](env[k],self.expr(stmt.value,env)),env)
            elif isinstance(stmt,ast.If):self.block(stmt.body if self.expr(stmt.test,env) else stmt.orelse,env)
            elif isinstance(stmt,ast.For) and isinstance(stmt.target,ast.Name):
                values=self.expr(stmt.iter,env)
                if not isinstance(values,(list,str)) or len(values)>400:raise ValueError('Loop iterable too large or unsupported')
                for value in values:
                    self.tick();self.assign(stmt.target,value,env);self.block(stmt.body,env)
            elif isinstance(stmt,ast.While):
                for _ in range(400):
                    if not self.expr(stmt.test,env):break
                    self.tick();self.block(stmt.body,env)
                else:raise ValueError('While loop exceeded 400 iterations')
            elif isinstance(stmt,ast.Pass):continue
            elif isinstance(stmt,ast.Expr) and isinstance(stmt.value,ast.Call):self.expr(stmt.value,env)
            else:raise ValueError(f'{type(stmt).__name__} is not supported by the local interpreter')
    def run(self,args):
        self.budget=0
        env={k:self.safe(v) for k,v in zip([a.arg for a in self.fn.args.args],args)}
        try:self.block(self.fn.body,env)
        except ReturnSignal as r:return self.safe(r.value)
        return None

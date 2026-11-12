import { useEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import {
  ArrowLeft, ArrowRight, ArrowUpRight, BarChart3, BookOpen, BriefcaseBusiness,
  Check, CheckCheck, CheckCircle2, ChevronDown, ChevronRight, CircleAlert,
  Clock3, Code2, Database, FileCheck2, FileCode2, Flame,
  Globe2, History, Info, LayoutDashboard, Lightbulb, LoaderCircle,
  LockKeyhole, Menu, MoreHorizontal, MousePointer2, Play, RotateCcw, ShieldCheck,
  ShieldAlert, SlidersHorizontal, Sparkles, Terminal, UploadCloud, X, Zap
} from 'lucide-react'
import type {Catalog, DemoJob, Grade, HistoryItem, JobAnalysis, StoredReport, TabId, TrackId, Trial} from './types'

const API='/api'
const TRACK_ICONS = {backend:Code2, sql:Database, frontend:Globe2, security:ShieldCheck, professional:BriefcaseBusiness}
const DIFFICULTIES=[
  {id:'easy',name:'Easy',range:'10–25%',low:10,high:25,pct:20,desc:'Guided, one focused task'},
  {id:'medium',name:'Intermediate',range:'26–45%',low:26,high:45,pct:38,desc:'More skills, less scaffolding'},
  {id:'advanced',name:'Advanced',range:'46–65%',low:46,high:65,pct:58,desc:'Multiple constraints'},
  {id:'hard',name:'Hard',range:'66–85%',low:66,high:85,pct:78,desc:'Complex edge cases'},
  {id:'expert',name:'Expert+',range:'86–100%',low:86,high:100,pct:95,desc:'Challenging multi-part work'},
] as const
const DEFAULT_JOB=`Junior Backend Developer Intern\nWe are looking for a student with Python, FastAPI, debugging, unit testing and REST API experience. Your work will involve finding and fixing bugs in our order service.`

type Edits={code:string;html:string;css:string}
type Investigation={ip:string;category:string;evidence:number[];response:string;note:string}
const blankInvestigation:Investigation={ip:'',category:'',evidence:[],response:'',note:''}
const messages = [
  ['01','Drop the job posting','Paste the requirements or upload a PDF, DOCX or TXT.'],
  ['02','Step into a work simulation','Solve a hands-on task in an actual practice workspace.'],
  ['03','Get evidence, not guesses','Run checks on your work and see exactly what needs fixing.'],
]

async function request<T>(path:string, init?:RequestInit):Promise<T> {
  const response=await fetch(`${API}${path}`,init)
  if(!response.ok){
    let message=`Request failed (${response.status})`
    try {const body=await response.json();message=typeof body.detail==='string'?body.detail:message}catch { /* ignore */ }
    throw new Error(message)
  }
  return response.json() as Promise<T>
}
async function post<T>(path:string,payload:unknown):Promise<T>{return request<T>(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})}
const fmtDate=(s:string)=>new Date(s).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})

function Pill({children,variant='default'}:{children:ReactNode;variant?:'default'|'green'|'orange'|'purple'|'muted'}){return <span className={`pill pill--${variant}`}>{children}</span>}
function Logo(){return <div className="brand"><div className="brand-logo"><CheckCheck size={23} strokeWidth={3}/></div><div className="brand-word">jobtrial<span className="brand-dot">.</span><small>WORK SIMULATOR</small></div></div>}
function TrackIcon({track,size=20}:{track:TrackId;size?:number}){const Icon=TRACK_ICONS[track]||Code2;return <span className={`track-icon track-icon--${track}`}><Icon size={size} strokeWidth={1.85}/></span>}

function Sidebar({tab,setTab,hasTrial,aiOnline,onClose}:{tab:TabId;setTab:(x:TabId)=>void;hasTrial:boolean;aiOnline:boolean;onClose:()=>void}){
  const nav=[{id:'home' as TabId,label:'Discover',icon:LayoutDashboard},{id:'workspace' as TabId,label:'My workspace',icon:Terminal},{id:'reports' as TabId,label:'My reports',icon:BarChart3}]
  return <aside className="sidebar">
    <Logo/>
    <div className="sidebar-group-label">YOUR SPACE</div>
    <nav className="side-nav">{nav.map(item=><button key={item.id} className={`nav-btn ${tab===item.id?'nav-btn--active':''}`} onClick={()=>{setTab(item.id);onClose()}} disabled={item.id==='workspace'&&!hasTrial}><item.icon size={18}/><span>{item.label}</span>{tab===item.id&&<span className="nav-accent"/>}</button>)}</nav>
    <div className="sidebar-group-label sidebar-group-label--second">HELP & GUIDES</div>
    <div className="nav-static"><BookOpen size={17}/> <span>Hands-on practice</span></div>
    <div className="nav-static"><ShieldCheck size={17}/> <span>Safe learning lab</span></div>
    <div className="sidebar-bottom">
      <div className="sidebar-info"><span className="sidebar-info-icon"><Sparkles size={17}/></span><strong>Your career starts with doing.</strong><p>Build confidence with practical assignments, not more interview questions.</p></div>
      <div className="sidebar-status"><span className="status-led"/> <span>{aiOnline?'HF token configured':'Add HF token for AI generation'}</span></div>
      <div className="sidebar-profile"><div className="avatar">JT</div><div><strong>Student workspace</strong><small>Local demo · no account needed</small></div><MoreHorizontal size={18}/></div>
    </div>
  </aside>
}

function Topbar({tab,role,onMenu}:{tab:TabId;role?:string;onMenu:()=>void}){return <header className="topbar"><div className="topbar-path"><button className="mobile-menu icon-btn" aria-label="Open menu" onClick={onMenu}><Menu size={20}/></button><span className="topbar-app">Workspace</span><ChevronRight size={14}/><strong>{tab==='home'?'Discover':tab==='workspace'?(role||'Practical assignment'):'Reports'}</strong></div><div className="topbar-right"><span className="topbar-online"><span/> Local development</span><span className="topbar-divider"/><span className="topbar-avatar">JT</span></div></header>}

function HeaderMark({eyebrow,title,description}:{eyebrow:string;title:string;description:string}){return <div className="section-header"><div className="eyebrow"><span className="eyebrow-line"/> {eyebrow}</div><h2>{title}</h2><p>{description}</p></div>}

function Landing({catalog,description,setDescription,selected,setSelected,onLaunch,loading,onFile,uploading,forcedTrack,setForcedTrack,preferredLanguage,setPreferredLanguage,error,aiOnline,difficulty,setDifficulty,intensity,setIntensity,offlineDemo,setOfflineDemo,variationIndex,setVariationIndex}:{
  catalog:Catalog|null;description:string;setDescription:(v:string)=>void;selected:string|null;setSelected:(v:string|null)=>void;
  onLaunch:()=>void;loading:boolean;onFile:(file:File)=>void;uploading:boolean;forcedTrack:string;setForcedTrack:(s:string)=>void;preferredLanguage:string;setPreferredLanguage:(s:string)=>void;error:string;aiOnline:boolean;difficulty:string;setDifficulty:(v:string)=>void;intensity:number;setIntensity:(v:number)=>void;offlineDemo:boolean;setOfflineDemo:(v:boolean)=>void;variationIndex:number;setVariationIndex:(v:number)=>void
}){
  const inputRef=useRef<HTMLTextAreaElement>(null)
  const fileRef=useRef<HTMLInputElement>(null)
  const [drag,setDrag]=useState(false)
  const choose=(sample:DemoJob)=>{setDescription(sample.description);setSelected(sample.title);setForcedTrack('auto');inputRef.current?.focus()}
  const fileSelect=(file:File|undefined)=>{if(file)onFile(file)}
  return <div className="landing">
    <div className="hero-banner">
      <div className="hero-content">
        <div className="hero-eyebrow"><span className="pulse-dot"/> BUILT FOR THE NEXT GENERATION OF BUILDERS <ArrowUpRight size={14}/></div>
        <h1>Stop preparing.<br/><span>Start practicing.</span></h1>
        <p>Turn a job posting into a hands-on skill simulation. Get real code tests where supported, or an honest review-ready work sample.</p>
        <div className="hero-social"><div className="mini-avatars"><span>M</span><span>S</span><span>A</span><span>+</span></div><span>Real work. Real feedback. <strong>More confidence.</strong></span></div>
      </div>
      <div className="hero-art" aria-hidden="true"><div className="orbit orbit-a"/><div className="orbit orbit-b"/><div className="hero-window"><div className="fake-window-bar"><i/><i/><i/><span>jobtrial / live simulation</span></div><div className="fake-code"><span>01&nbsp; &nbsp; <b>def</b> calculate_total(...):</span><span>02&nbsp; &nbsp; &nbsp; &nbsp;<em>return</em> price * quantity</span><span className="fake-code-slate">03&nbsp; &nbsp; &nbsp; &nbsp;# run actual tests</span></div><div className="fake-pass"><CheckCircle2 size={17}/> Automated evaluation <strong>5/6 passed</strong></div></div><div className="floating-cube"><Zap size={26}/></div></div>
    </div>
    <div className="landing-grid">
      <div className="launch-card">
        <div className="card-heading"><span className="card-icon"><BriefcaseBusiness size={19}/></span><div><h3>Create your work trial</h3><p>Start with a real job description.</p></div><Pill variant="purple"><Sparkles size={12}/> NEW</Pill></div>
        <div className="editor-label"><label htmlFor="job-description">JOB DESCRIPTION</label><span>Required</span></div>
        <div className={`job-input ${drag?'job-input--drag':''}`} onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={()=>setDrag(false)} onDrop={e=>{e.preventDefault();setDrag(false);fileSelect(e.dataTransfer.files?.[0])}}>
          <textarea id="job-description" ref={inputRef} spellCheck={false} value={description} maxLength={15000} onChange={e=>{setDescription(e.target.value);setSelected(null)}} placeholder="Paste a job description here...\n\nExample: We are hiring a Junior Data Analyst familiar with SQL, reporting, joins and data cleaning."/>
          <div className="job-input-footer"><button onClick={()=>fileRef.current?.click()} type="button" className="text-tool"><UploadCloud size={17}/>{uploading?'Reading file...':'Upload PDF / DOCX / TXT'}</button><span>{description.length.toLocaleString()} / 15,000</span></div>
          <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" hidden onChange={e=>{fileSelect(e.target.files?.[0]);e.currentTarget.value=''}}/>
        </div>
        {selected&&<div className="loaded-sample"><Check size={13}/> Loaded example: {selected} <button onClick={()=>setSelected(null)} aria-label="Clear example label"><X size={13}/></button></div>}
        {error&&<div className="inline-error"><CircleAlert size={17}/>{error}</div>}
        <div className="launch-settings"><label htmlFor="job-track">PRACTICE TRACK</label><div className="select-wrap"><SlidersHorizontal size={15}/><select id="job-track" value={forcedTrack} onChange={e=>setForcedTrack(e.target.value)}><option value="auto">Auto-detect from description</option><option value="professional">Non-coding work deliverable (review required)</option>{catalog?.tracks.map(t=><option value={t.id} key={t.id}>{t.title}</option>)}</select><ChevronDown size={14}/></div></div>
        <div className="launch-settings"><label htmlFor="job-language">CODE LANGUAGE</label><div className="select-wrap"><Code2 size={15}/><select id="job-language" value={preferredLanguage} onChange={e=>setPreferredLanguage(e.target.value)}><option value="auto">Detect from job description</option><option value="python">Python</option><option value="javascript">JavaScript</option><option value="typescript">TypeScript</option><option value="java">Java</option><option value="cpp">C++</option><option value="go">Go</option></select><ChevronDown size={14}/></div></div>
        <div className="difficulty-panel">
          <div className="difficulty-heading"><div><span className="difficulty-eyebrow">CHALLENGE LEVEL</span><h4>Choose how far to push yourself</h4><p>Difficulty is an estimate, not your test score.</p></div><span className="intensity-badge">{intensity}%</span></div>
          <div className="difficulty-options" role="group" aria-label="Select challenge difficulty">
            {DIFFICULTIES.map(d=><button key={d.id} type="button" className={`difficulty-option ${difficulty===d.id?'difficulty-option--active':''}`} aria-pressed={difficulty===d.id} onClick={()=>{setDifficulty(d.id);setIntensity(d.pct);setVariationIndex(0)}}><strong>{d.name}</strong><small>{d.range}</small></button>)}
          </div>
          <div className="difficulty-slider"><label htmlFor="challenge-intensity">Fine-tune within {DIFFICULTIES.find(d=>d.id===difficulty)?.name}</label><input id="challenge-intensity" type="range" min={DIFFICULTIES.find(d=>d.id===difficulty)?.low??10} max={DIFFICULTIES.find(d=>d.id===difficulty)?.high??25} value={intensity} onChange={e=>{setIntensity(Number(e.target.value));setVariationIndex(0)}}/><span>{DIFFICULTIES.find(d=>d.id===difficulty)?.desc}</span></div>
          <div className="variant-tool" aria-live="polite">
            <div><strong>New task at every slider step</strong><small>Adjacent percentages swap between independently tested coding problems. Same percentage? Switch the verified task, then click Generate.</small></div>
            <button type="button" className="outline-btn" onClick={()=>setVariationIndex(variationIndex+1)} disabled={loading}>
              <RotateCcw size={15}/> Switch next task ({variationIndex+1})
            </button>
          </div>
          <label className="demo-switch"><input type="checkbox" checked={offlineDemo} onChange={e=>setOfflineDemo(e.target.checked)}/><span><strong>Offline demo only</strong><small>{offlineDemo?'Local verified challenges — no AI call':'Hugging Face writes the work brief; tests stay independent'}</small></span></label>
          {!aiOnline&&!offlineDemo&&<div className="token-reminder"><CircleAlert size={15}/> Add HF_TOKEN to your project .env, then restart the backend. No silent offline fallback.</div>}
        </div>
        <button className="primary-btn primary-btn--full" onClick={onLaunch} disabled={loading||uploading||description.trim().length<5}>{loading?<><LoaderCircle size={18} className="spin"/> Building your work trial...</>:<><Sparkles size={18}/> Generate my work trial <ArrowRight size={19}/></>}</button>
        <p className="privacy-note"><LockKeyhole size={14}/> Your task results are stored in your local server. {offlineDemo?'Offline demo: no AI API call.':'AI mode: the job description is sent to Hugging Face only on generation.'}</p>
      </div>
      <div className="how-card"><div className="how-heading"><span className="how-kicker">HOW IT WORKS</span><span className="how-time"><Clock3 size={14}/> Under a minute to start</span></div><div className="steps">{messages.map(([num,title,detail],i)=><div className="step" key={num}><div className="step-indicator"><span>{num}</span>{i<2&&<div className="step-line"/>}</div><div><strong>{title}</strong><p>{detail}</p></div></div>)}</div><div className="how-bottom"><div className="how-bottom-icon"><ShieldCheck size={18}/></div><div><strong>Built around proof</strong><p>Verified checks for supported tasks; human review for open-ended work.</p></div></div></div>
    </div>
    <div className="explore-header"><div><h3>Or start with an example</h3><p>Choose a role to see what a real work trial feels like.</p></div><span className="explore-count">{catalog?.examples.length??4} career paths <ArrowUpRight size={15}/></span></div>
    <div className="role-grid">{catalog?.examples.map(example=><button className="role-card" key={example.id} onClick={()=>choose(example)}><div className="role-top"><TrackIcon track={example.id}/><ArrowUpRight size={17} className="role-arrow"/></div><span className="role-category">{catalog.tracks.find(t=>t.id===example.id)?.category}</span><h4>{example.title}</h4><p>{example.company}</p><div className="role-foot"><span>Explore trial</span><ArrowRight size={15}/></div></button>)}</div>
    <div className="landing-disclaimer"><Info size={16}/> These are original educational simulations based on role skills, not official tests issued by employers.</div>
  </div>
}

function CodeEditor({value,onChange,language,placeholder,fileName,readonly=false}:{value:string;onChange:(s:string)=>void;language:string;placeholder?:string;fileName?:string;readonly?:boolean}){
  const textarea=useRef<HTMLTextAreaElement>(null)
  const lines=value.split('\n').length
  return <div className="code-editor"><div className="codebar"><div><span className="codebar-dot"/><FileCode2 size={15}/><span>{fileName|| (language==='python'?'solution.py':language==='sql'?'analysis.sql':language==='html'?'index.html':language==='report'?'work_sample.md':'styles.css')}</span></div><div className="codebar-right">{language.toUpperCase()} <span className="codebar-separator"/> <span>{lines} lines</span></div></div><div className="code-body"><div className="line-numbers" aria-hidden="true">{Array.from({length:Math.max(lines,10)},(_,i)=><div key={i}>{i+1}</div>)}</div><textarea ref={textarea} value={value} onChange={e=>onChange(e.target.value)} readOnly={readonly} onKeyDown={e=>{if(e.key==='Tab'&&!readonly){e.preventDefault();const el=e.currentTarget,start=el.selectionStart,end=el.selectionEnd;const next=value.slice(0,start)+'    '+value.slice(end);onChange(next);requestAnimationFrame(()=>{el.selectionStart=el.selectionEnd=start+4})}}} spellCheck={false} aria-label={`${language} solution editor`} placeholder={placeholder} autoCapitalize="off" autoComplete="off" autoCorrect="off"/></div><div className="code-status"><span><span className="status-led"/> Editable workspace</span><span>UTF-8 · {language.toUpperCase()}</span></div></div>
}

function ScoreGauge({score}:{score:number}){return <div className="score-gauge" style={{'--value':`${Math.max(0,Math.min(score,100))}%`} as CSSProperties}><div><strong>{score}%</strong><small>CHECKS</small></div></div>}

function Results({grade,onDismiss,saved}:{grade:Grade;onDismiss:()=>void;saved:boolean}){
  return <section className="results-panel"><div className="results-header"><div><div className="eyebrow eyebrow--small">TEST RESULTS</div><h3>{grade.score<0?'Work sample ready for human review':grade.score===100?'Excellent work!':grade.score>=60?'Nice progress. Keep going.':'A few things to improve.'}</h3><p>{grade.feedback}</p></div><button className="icon-btn" onClick={onDismiss} aria-label="Close results"><X size={18}/></button></div><div className="results-summary">{grade.score<0?<div className="manual-review-icon"><FileCheck2 size={34}/><strong>Human review</strong></div>:<ScoreGauge score={grade.score}/>}<div className="results-count"><strong>{grade.passed}<span> / {grade.total}</span></strong><small>{grade.score<0?'Draft completeness checks · NOT a skills score':'Checks passed'}</small>{grade.score>=0&&<div className="results-progress"><span style={{width:`${grade.score}%`}}/></div>}{saved&&<span className="saved-label"><Check size={13}/> Saved to reports</span>}</div></div>
    {grade.preview&&grade.preview.columns?.length>0&&<div className="query-output"><div className="output-heading"><Database size={15}/> Query output <small>{grade.preview.rows.length} rows</small></div><div className="table-scroll"><table><thead><tr>{grade.preview.columns.map((c,i)=><th key={i}>{c}</th>)}</tr></thead><tbody>{grade.preview.rows.map((r,i)=><tr key={i}>{r.map((v,j)=><td key={j}>{String(v??'NULL')}</td>)}</tr>)}</tbody></table></div></div>}
    <div className="check-list">{grade.checks.map((c,i)=><div className="check-row" key={i}><div className={`check-marker ${c.passed?'check-marker--success':'check-marker--fail'}`}>{c.passed?<Check size={14}/>:<X size={14}/>}</div><div><strong>{c.label}</strong><p>{c.detail}</p></div></div>)}</div></section>
}

function Workspace({trial,analysis,onBack,onSaveReport}:{trial:Trial;analysis:JobAnalysis;onBack:()=>void;onSaveReport:()=>void}){
  const [activeTask,setActiveTask]=useState(0)
  const [edits,setEdits]=useState<Record<string,Edits>>({})
  const [investigations,setInvestigations]=useState<Record<string,Investigation>>({})
  const [projectEdits,setProjectEdits]=useState<Record<string,Record<string,string>>>({})
  const [selectedFile,setSelectedFile]=useState('')
  const [grade,setGrade]=useState<Grade|null>(null)
  const [coaching,setCoaching]=useState<{strengths:string[];gaps:string[];next_step:string;confidence_note:string;disclaimer:string}|null>(null)
  const [coachingBusy,setCoachingBusy]=useState(false)
  const [coachingError,setCoachingError]=useState('')
  const [running,setRunning]=useState(false)
  const [error,setError]=useState('')
  const [editorTab,setEditorTab]=useState<'html'|'css'|'preview'>('html')
  const [dataTab,setDataTab]=useState('orders')
  const [showHint,setShowHint]=useState(false)
  const [showData,setShowData]=useState(true)
  const [done,setDone]=useState<Record<string,number>>({})
  const task=trial.tasks[activeTask]
  const taskKey=`${trial.id}_${task.id}`
  const current=edits[taskKey]||{code:task.starter||'',html:task.starter_html||'',css:task.starter_css||''}
  const incident=investigations[taskKey]||blankInvestigation
  const projectFiles=task.files||[]
  const projectInputs=Object.fromEntries(projectFiles.filter(f=>f.editable).map(f=>[f.path,projectEdits[taskKey]?.[f.path]??f.content]))
  const currentFile=projectFiles.find(f=>f.path===selectedFile)||projectFiles[0]
  const projectValue=currentFile?(projectEdits[taskKey]?.[currentFile.path]??currentFile.content):''
  const updateProjectFile=(path:string,value:string)=>{setProjectEdits(p=>({...p,[taskKey]:{...p[taskKey],[path]:value}}));setGrade(null);setCoaching(null)}
  const change=(updates:Partial<Edits>)=>{setEdits(p=>({...p,[taskKey]:{...current,...updates}}));setGrade(null);setCoaching(null)}
  const changeIncident=(updates:Partial<Investigation>)=>{setInvestigations(p=>({...p,[taskKey]:{...incident,...updates}}));setGrade(null)}
  const changeTask=(i:number)=>{setActiveTask(i);setGrade(null);setError('');setShowHint(false);setEditorTab('html');setSelectedFile('')}
  useEffect(()=>{setActiveTask(0);setEdits({});setProjectEdits({});setSelectedFile('');setGrade(null);setDone({});setError('')},[trial])
  const submit=async (save:boolean)=>{setRunning(true);setError('');try{
    const output=await post<Grade>(save?'/submit':'/run',{track:trial.id,task_id:task.id,code:current.code,files:projectInputs,html:current.html,css:current.css,incident,job_title:analysis.role_title})
    setGrade(output);if(save){setDone(p=>({...p,[taskKey]:output.score}));onSaveReport()}
  }catch(err){setError(err instanceof Error?err.message:'Unable to run this check.')}finally{setRunning(false)}}
  const getCoaching=async()=>{setCoachingBusy(true);setCoachingError('');try{
      const data=await post<{strengths:string[];gaps:string[];next_step:string;confidence_note:string;disclaimer:string}>('/ai-coach',{role:analysis.role_title,scenario:task.goal,requirements:task.spec,answer:projectFiles.length?Object.values(projectInputs).join('\n\n'):current.code||current.html+'\n'+current.css,track:trial.id,task_id:task.id})
      setCoaching(data)
    }catch(e){setCoachingError(e instanceof Error?e.message:'AI coaching is not available')}finally{setCoachingBusy(false)}}
  const safePreview=useMemo(()=>`<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; form-action 'none'; base-uri 'none'"><style>${current.css.replace(/<\/style/gi,'<\\/style')}</style></head><body>${current.html}</body></html>`,[current.html,current.css])
  const progress=trial.tasks.filter(t=>done[`${trial.id}_${t.id}`]!==undefined).length
  return <div className="workspace-page">
    <div className="workspace-back"><button onClick={onBack}><ArrowLeft size={16}/> All work trials</button><span className="workspace-trail">/ &nbsp; {trial.title}</span></div>
    <div className="workspace-hero"><div className="workspace-hero-left"><div className="workspace-title-row"><TrackIcon track={trial.id} size={24}/><div><div className="eyebrow eyebrow--small">PRACTICAL WORK SIMULATION</div><h1>{analysis.role_title||trial.role}</h1></div></div><p>{analysis.manager_brief}</p><div className="workspace-meta"><span><BriefcaseBusiness size={14}/> {trial.company} · simulated</span><span><Clock3 size={14}/> {trial.duration}</span><span><ShieldCheck size={14}/> {trial.id==='professional'?'Human review required':'Evidence-based checks'}</span></div></div><div className="workspace-progress"><span>YOUR PROGRESS</span><strong>{progress} <small>/ {trial.tasks.length} tasks submitted</small></strong><div><span style={{width:`${progress/trial.tasks.length*100}%`}}/></div></div></div>
    <div className="mission-banner"><span className={`mission-status ${analysis.ai_used?'mission-status--ai':''}`}><Sparkles size={15}/>{analysis.ai_used?'AI-authored simulation':'OFFLINE DEMO — not AI-generated'}</span><span>{analysis.difficulty_level?.toUpperCase()} · estimated {analysis.difficulty_percent}% challenge intensity · {analysis.custom_task_validated?'Original AI-generated coding task (math-validated)':analysis.ai_used?'AI scenario + independently verified coding tasks':'prebuilt local exercises'}</span></div>
    <div className="task-strip">{trial.tasks.map((t,i)=><button className={`task-pill ${i===activeTask?'task-pill--active':''}`} key={t.id} onClick={()=>changeTask(i)}><span className="task-number">{done[`${trial.id}_${t.id}`]!==undefined?<Check size={15}/>:String(i+1).padStart(2,'0')}</span><span>{t.title}</span>{i===activeTask&&<span className="task-current">IN PROGRESS</span>}</button>)}</div>
    <div className="work-grid"><div className="work-main">
      <div className="assignment-card"><div className="assignment-heading"><div><div className="eyebrow eyebrow--small">YOUR ASSIGNMENT <span className="assignment-dot">·</span> {task.tag}</div><h2>{task.title}</h2></div><Pill variant="muted"><Clock3 size={13}/> {task.time}</Pill></div><p className="assignment-goal">{task.goal}</p>{task.ai_artifact&&<div className="ai-artifact"><div className="acceptance-title"><FileCode2 size={15}/> SIMULATED WORK MATERIAL</div><pre>{task.ai_artifact}</pre></div>}<div className="acceptance"><div className="acceptance-title"><FileCheck2 size={15}/> ACCEPTANCE CRITERIA</div>{task.spec.map((line,i)=><div key={i} className="acceptance-row"><Check size={13}/>{line}</div>)}</div></div>
      <div className="workbench-card"><div className="workbench-head"><div><span className="workbench-icon"><Terminal size={19}/></span><div><strong>Work environment</strong><small>{trial.id==='sql'?'Real SQL queries · safe read-only database':projectFiles.length?'Multi-file coding project · verified Docker tests':trial.id==='backend'?`${task.lang?.toUpperCase()||'PYTHON'} coding assignment · ${task.lang==='python'?'bounded local interpreter':'isolated Docker runner required'}`:trial.id==='frontend'?'HTML & CSS editor · sandboxed preview':trial.id==='professional'?'Review-ready deliverable · human assessment required':'Security event timeline · investigation workspace'}</small></div></div><span className="live-indicator"><span/> LIVE PRACTICE</span></div>
      {projectFiles.length>0&&<div className="project-workspace">
        <div className="project-files-header"><div><strong>Project files</strong><span>Editable source + read-only brief and sample data</span></div><span>{task.lang==='python'?'Python':'Node.js'} · Docker</span></div>
        <div className="project-file-tabs">{projectFiles.map(f=><button key={f.path} type="button" className={`project-file-tab ${currentFile?.path===f.path?'project-file-tab--active':''}`} onClick={()=>setSelectedFile(f.path)}><FileCode2 size={14}/>{f.path}{!f.editable&&<LockKeyhole size={12}/>}</button>)}</div>
        {currentFile&&<><div className="project-file-hint">{currentFile.editable?'Editable — your solution will be executed inside Docker':'Read only — task instructions or sample input'} · {currentFile.path}</div>
          <CodeEditor language={currentFile.path.endsWith('.js')?'javascript':currentFile.path.endsWith('.py')?'python':currentFile.path.endsWith('.json')?'json':'report'} fileName={currentFile.path} readonly={!currentFile.editable} value={projectValue} onChange={v=>currentFile.editable&&updateProjectFile(currentFile.path,v)}/></>}
      </div>}
      {trial.id==='backend'&&!projectFiles.length&&<CodeEditor language={task.lang||'python'} value={current.code} onChange={code=>change({code})}/>}
      {trial.id==='professional'&&<><div className="manual-review-note"><Info size={17}/> This is a real drafting exercise, but an automatic grade would be misleading. You'll receive structure checks only; get a human to review the quality.</div><CodeEditor language="report" value={current.code} onChange={code=>change({code})} placeholder="Write your practical deliverable here..."/></>}
      {trial.id==='sql'&&<>
        {showData&&trial.sample_data&&<div className="data-explorer"><div className="data-explorer-head"><span><Database size={15}/> Sample database</span><button onClick={()=>setShowData(false)}>Hide tables <ChevronDown size={14}/></button></div><div className="data-tabs">{Object.keys(trial.sample_data).map(name=><button key={name} className={dataTab===name?'data-tab--active':''} onClick={()=>setDataTab(name)}>{name}</button>)}</div><div className="table-scroll sample-table"><table><thead><tr>{trial.sample_data[dataTab].columns.map(col=><th key={col}>{col}</th>)}</tr></thead><tbody>{trial.sample_data[dataTab].rows.slice(0,8).map((r,i)=><tr key={i}>{r.map((c,j)=><td key={j}>{c}</td>)}</tr>)}</tbody></table></div></div>}
        {!showData&&<button className="restore-data" onClick={()=>setShowData(true)}><Database size={14}/> Show sample database <ChevronDown size={14}/></button>}
        <CodeEditor language="sql" value={current.code} onChange={code=>change({code})}/>
      </>}
      {trial.id==='frontend'&&!projectFiles.length&&<><div className="editor-tabs"><button className={editorTab==='html'?'editor-tab--active':''} onClick={()=>setEditorTab('html')}><Code2 size={14}/> index.html</button><button className={editorTab==='css'?'editor-tab--active':''} onClick={()=>setEditorTab('css')}><FileCode2 size={14}/> styles.css</button><button className={editorTab==='preview'?'editor-tab--active':''} onClick={()=>setEditorTab('preview')}><MousePointer2 size={14}/> Live preview</button></div>
        {editorTab==='html'?<CodeEditor language="html" value={current.html} onChange={html=>change({html})}/>:editorTab==='css'?<CodeEditor language="css" value={current.css} onChange={css=>change({css})}/>:<div className="browser-frame"><div className="browser-frame-head"><span/><span/><span/><div><LockKeyhole size={12}/> sandboxed preview</div></div><iframe title="Sandboxed student frontend preview" sandbox="" referrerPolicy="no-referrer" srcDoc={safePreview}/></div>}
      </>}
      {trial.id==='security'&&<div className="security-console"><div className="security-console-title"><div><ShieldAlert size={18}/> Auth event feed</div><span>{trial.logs?.length} log records · fictional data</span></div><div className="security-log-list">{trial.logs?.map(log=><button key={log.id} className={`security-log ${incident.evidence.includes(log.id)?'security-log--selected':''}`} onClick={()=>changeIncident({evidence:incident.evidence.includes(log.id)?incident.evidence.filter(x=>x!==log.id):[...incident.evidence,log.id]})}><span className="security-log-selector">{incident.evidence.includes(log.id)&&<Check size={12}/>}</span><span className="mono tiny">{log.time}</span><span className="mono security-ip">{log.ip}</span><span className={`status-code ${log.status===401?'status-code--bad':''}`}>{log.status}</span><span>{log.event}</span><span className="security-user">{log.user}</span></button>)}</div><div className="security-console-foot">Click events to attach them as evidence · {incident.evidence.length} selected</div></div>}
      <div className="workbench-actions"><button className="subtle-btn" onClick={()=>{change({code:task.starter||'',html:task.starter_html||'',css:task.starter_css||''});if(projectFiles.length)setProjectEdits(p=>({...p,[taskKey]:{}}));setInvestigations(p=>({...p,[taskKey]:blankInvestigation}));setGrade(null)}}><RotateCcw size={15}/> Reset solution</button><div className="run-actions"><button className="outline-btn" onClick={()=>submit(false)} disabled={running}>{running?<LoaderCircle size={15} className="spin"/>:<Play size={15} fill="currentColor"/>} Run checks</button><button className="primary-btn" onClick={()=>submit(true)} disabled={running}>{running?<LoaderCircle size={15} className="spin"/>:<CheckCircle2 size={17}/>} Submit work <ArrowRight size={16}/></button></div></div></div>
      {trial.id==='security'&&<div className="investigation-card"><div className="eyebrow eyebrow--small">INCIDENT WORKSHEET</div><h3>Document your findings</h3><div className="investigation-grid"><label>Suspected source<select value={incident.ip} onChange={e=>changeIncident({ip:e.target.value})}><option value="">Choose source IP</option>{[...new Set(trial.logs?.map(l=>l.ip)||[])].map(ip=><option key={ip} value={ip}>{ip}</option>)}</select></label><label>Classification<select value={incident.category} onChange={e=>changeIncident({category:e.target.value})}><option value="">Choose attack type</option><option value="credential_stuffing">Credential stuffing</option><option value="sql_injection">SQL injection</option><option value="normal_activity">Normal login errors</option><option value="data_exfiltration">Data exfiltration</option></select></label></div><label>Recommended action<select value={incident.response} onChange={e=>changeIncident({response:e.target.value})}><option value="">Choose action</option><option value="invalidate_sessions">Invalidate affected sessions & investigate</option><option value="ignore">Ignore as normal traffic</option><option value="delete_logs">Delete the logs</option><option value="disable_all">Disable all user accounts</option></select></label><label>Incident notes<textarea value={incident.note} onChange={e=>changeIncident({note:e.target.value})} placeholder="Explain which pattern you observed, the affected identities, and why it looks suspicious..."/></label></div>}
      {error&&<div className="inline-error"><CircleAlert size={18}/>{error}</div>}
      {grade&&<Results grade={grade} saved={!!grade.report_id} onDismiss={()=>setGrade(null)}/>}
      <div className="coach-panel"><div><strong><Sparkles size={16}/> AI feedback on your work</strong><p>Optional qualitative coaching from Hugging Face. It will not change verified test scores.</p></div><button className="outline-btn" disabled={coachingBusy||!analysis.ai_used} onClick={getCoaching}>{coachingBusy?'Reviewing…':'Get AI coaching'}</button></div>
      {coachingError&&<div className="inline-error">{coachingError}</div>}
      {coaching&&<div className="coach-feedback"><strong>Strengths</strong><ul>{coaching.strengths.map((x,i)=><li key={i}>{x}</li>)}</ul><strong>Improvement areas</strong><ul>{coaching.gaps.map((x,i)=><li key={i}>{x}</li>)}</ul><strong>Next step</strong><p>{coaching.next_step}</p><small>{coaching.disclaimer}</small></div>}
      </div>
      <aside className="work-aside"><div className="mentor-card"><div className="mentor-heading"><div className="mentor-avatar"><BriefcaseBusiness size={18}/></div><div><strong>Your virtual team lead</strong><small>WORK BRIEF · SIMULATION</small></div><MoreHorizontal size={18}/></div><div className="mentor-message">“This assignment reflects a common junior-level task. Take your time, read the requirements, and run the checks before submitting.”</div><span className="mentor-signature">— {trial.company} (fictional)</span></div>
      <div className="aside-card"><div className="aside-heading"><span><Lightbulb size={18} className="text-yellow"/> Need a nudge?</span><button className="hint-toggle" onClick={()=>setShowHint(!showHint)}>{showHint?'Hide':'Reveal'} hint <ChevronDown size={14}/></button></div>{showHint?<p className="hint-text">{task.hint}</p>:<p className="aside-muted">Hints are available if you get stuck. Your trial results are still based on what you submit.</p>}</div>
      <div className="aside-card"><div className="aside-heading"><span><TargetIcon/> Skills in focus</span></div><div className="skill-list">{analysis.skills.slice(0,6).map(skill=><div key={skill}><span className="skill-bullet"/> {skill}</div>)}</div></div>
      <div className="aside-card"><div className="aside-heading"><span><FileCheck2 size={18} className="text-purple"/> Assessed in this trial</span></div><div className="skill-list">{(analysis.covered_skills||[]).map(skill=><div key={skill}><span className="skill-bullet"/> {skill}</div>)}</div>{(analysis.not_assessed_skills||[]).length>0&&<><p className="aside-muted"><strong>Not evaluated:</strong> {(analysis.not_assessed_skills||[]).join(', ')}. Don't claim these skills from this trial.</p></>}</div>
      <div className="aside-tip"><Info size={17}/><div><strong>Why this work trial?</strong><p>{analysis.matching_reason||'Selected using the skills in your job posting.'}</p><p>{analysis.limitations}</p></div></div>
      </aside>
    </div>
    <div className="workspace-footer"><span><ShieldCheck size={15}/> Safe, locally evaluated practice lab</span><span>JobTrial v5 · task-specific projects + Docker tests</span></div>
  </div>
}
function TargetIcon(){return <Zap size={18} className="text-purple"/>}

function Reports({items,loading,onReload}:{items:HistoryItem[];loading:boolean;onReload:()=>void}){
  const [selected,setSelected]=useState<string|null>(null)
  const [detail,setDetail]=useState<StoredReport|null>(null)
  const [error,setError]=useState('')
  useEffect(()=>{if(!selected){setDetail(null);return}request<StoredReport>(`/report/${selected}`).then(setDetail).catch(e=>setError(String(e)))},[selected])
  return <div className="reports-page"><HeaderMark eyebrow="YOUR TRACK RECORD" title="Proof of practice." description="Every submitted task earns a transparent report. Review what passed and where you can improve."/>
    <div className="report-metrics"><div><div className="metric-icon metric-icon--purple"><FileCheck2 size={20}/></div><span>Tasks submitted</span><strong>{items.length}</strong></div><div><div className="metric-icon metric-icon--green"><BarChart3 size={20}/></div><span>Average automated score</span><strong>{items.some(i=>i.score>=0)?Math.round(items.filter(i=>i.score>=0).reduce((s,i)=>s+i.score,0)/items.filter(i=>i.score>=0).length):0}%</strong></div><div><div className="metric-icon metric-icon--orange"><Flame size={20}/></div><span>Perfect submissions</span><strong>{items.filter(i=>i.score===100).length}</strong></div></div>
    <div className="history-card"><div className="history-header"><div><h3>Submission history</h3><p>Saved on this computer by your local API</p></div><button className="outline-btn outline-btn--sm" onClick={onReload}><RotateCcw size={15}/> Refresh</button></div>
      {loading?<div className="history-empty"><LoaderCircle className="spin" size={25}/> Loading reports...</div>:items.length===0?<div className="history-empty"><div className="empty-illustration"><History size={32}/></div><h4>No submissions yet</h4><p>Your evaluated tasks will appear here after you submit your first solution.</p></div>:<div className="history-items">{items.map(item=><button key={item.id} onClick={()=>{setSelected(item.id);setError('')}} className={`history-item ${selected===item.id?'history-item--selected':''}`}><TrackIcon track={item.track} size={18}/><div className="history-name"><strong>{item.job_title}</strong><span>{item.task_id.replace(/-/g,' ')} · {fmtDate(item.created_at)}</span></div><span className={`history-score ${item.score===100?'history-score--great':''}`}>{item.score<0?'Review':`${item.score}%`}</span><ChevronRight size={17}/></button>)}</div>}
    </div>
    {error&&<div className="inline-error">{error}</div>}
    {detail&&<div className="report-detail"><div className="report-detail-header"><div><span className="eyebrow eyebrow--small">REPORT / {detail.id}</span><h3>Assessment breakdown</h3></div><button className="icon-btn" onClick={()=>setSelected(null)}><X size={19}/></button></div><div className="detail-score"><strong>{detail.score<0?'Human review':`${detail.score}%`}</strong><span>{detail.feedback}</span></div><div className="check-list">{detail.checks.map((c,i)=><div className="check-row" key={i}><div className={`check-marker ${c.passed?'check-marker--success':'check-marker--fail'}`}>{c.passed?<Check size={14}/>:<X size={14}/>}</div><div><strong>{c.label}</strong><p>{c.detail}</p></div></div>)}</div></div>}
    <p className="report-note"><LockKeyhole size={14}/> Reports are stored in <code>backend/data/history.sqlite3</code>. No login or cloud database is required.</p>
  </div>
}

export default function App(){
  const [tab,setTab]=useState<TabId>('home')
  const [catalog,setCatalog]=useState<Catalog|null>(null)
  const [analysis,setAnalysis]=useState<JobAnalysis|null>(null)
  const [trial,setTrial]=useState<Trial|null>(null)
  const [description,setDescription]=useState(DEFAULT_JOB)
  const [selected,setSelected]=useState<string|null>(null)
  const [forcedTrack,setForcedTrack]=useState('auto')
  const [preferredLanguage,setPreferredLanguage]=useState('auto')
  const [difficulty,setDifficulty]=useState('easy')
  const [intensity,setIntensity]=useState(20)
  const [variationIndex,setVariationIndex]=useState(0)
  const [offlineDemo,setOfflineDemo]=useState(false)
  const [aiOnline,setAiOnline]=useState(false)
  const [loading,setLoading]=useState(false)
  const [uploading,setUploading]=useState(false)
  const [history,setHistory]=useState<HistoryItem[]>([])
  const [historyLoading,setHistoryLoading]=useState(false)
  const [error,setError]=useState('')
  const [menuOpen,setMenuOpen]=useState(false)
  const [backendError,setBackendError]=useState(false)
  useEffect(()=>{
    request<Catalog>('/catalog').then(setCatalog).catch(()=>setBackendError(true))
    request<{ok:boolean;ai_configured:boolean}>('/health').then(s=>setAiOnline(s.ai_configured)).catch(()=>setBackendError(true))
  },[])
  const loadHistory=()=>{setHistoryLoading(true);request<{items:HistoryItem[]}>('/history').then(s=>setHistory(s.items)).finally(()=>setHistoryLoading(false)).catch(()=>{})}
  useEffect(()=>{if(tab==='reports')loadHistory()},[tab])
  const analyze=async()=>{
    setLoading(true);setError('')
    try{
      const a=await post<JobAnalysis>('/analyze',{description,requested_track:forcedTrack==='auto'?null:forcedTrack,preferred_language:preferredLanguage==='auto'?null:preferredLanguage,difficulty_level:difficulty,difficulty_percent:intensity,variation_index:variationIndex,use_ai:!offlineDemo})
      const t=a.dynamic_trial||await request<Trial>(`/trials/${a.track}`)
      setAnalysis(a);setTrial(t);setTab('workspace');setMenuOpen(false)
    }catch(e){setError(e instanceof Error?e.message:'Something went wrong. Please try again.')}finally{setLoading(false)}
  }
  const fileUpload=async(file:File)=>{setUploading(true);setError('');try{
    const body=new FormData();body.append('file',file)
    const data=await request<{text:string;filename:string}>('/extract',{method:'POST',body})
    setDescription(data.text);setSelected(`Uploaded ${data.filename}`)
  }catch(e){setError(e instanceof Error?e.message:'Failed to read the file')}finally{setUploading(false)}}
  return <div className="shell">
    {menuOpen&&<div className="mobile-overlay" onClick={()=>setMenuOpen(false)}/>}
    <div className={`sidebar-wrap ${menuOpen?'sidebar-wrap--open':''}`}><Sidebar tab={tab} setTab={setTab} hasTrial={!!trial} aiOnline={aiOnline} onClose={()=>setMenuOpen(false)}/></div>
    <div className="main-wrap"><Topbar tab={tab} role={analysis?.role_title} onMenu={()=>setMenuOpen(true)}/>
      {backendError&&<div className="api-alert"><CircleAlert size={17}/> Backend is not responding. Open a VS Code terminal and start FastAPI on port 8000, then refresh the page.</div>}
      <main className="main-content">{tab==='home'?<Landing catalog={catalog} description={description} setDescription={setDescription} selected={selected} setSelected={setSelected} onLaunch={analyze} loading={loading} onFile={fileUpload} uploading={uploading} forcedTrack={forcedTrack} setForcedTrack={setForcedTrack} preferredLanguage={preferredLanguage} setPreferredLanguage={setPreferredLanguage} error={error} aiOnline={aiOnline} difficulty={difficulty} setDifficulty={setDifficulty} intensity={intensity} setIntensity={setIntensity} variationIndex={variationIndex} setVariationIndex={setVariationIndex} offlineDemo={offlineDemo} setOfflineDemo={setOfflineDemo}/>:tab==='workspace'&&analysis&&trial?<Workspace trial={trial} analysis={analysis} onBack={()=>setTab('home')} onSaveReport={loadHistory}/>:<Reports items={history} loading={historyLoading} onReload={loadHistory}/>}</main>
    </div>
  </div>
}

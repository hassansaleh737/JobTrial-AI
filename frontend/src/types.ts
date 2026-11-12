export type TrackId = 'backend'|'sql'|'frontend'|'security'|'professional'
export type TabId = 'home'|'workspace'|'reports'
export type TrackSummary = {
  id:TrackId; title:string; subtitle:string; category:string; duration:string; difficulty:string;
  color:string; skills:string[]; intro:string; company:string; role:string; task_count:number
}
export type DemoJob = {id:TrackId; title:string; company:string; description:string}
export type Catalog = {tracks:TrackSummary[]; examples:DemoJob[]}
export type JobAnalysis = {track:TrackId;role_title:string;skills:string[];company:string;manager_brief:string;ai_used:boolean;mode:string;limitations:string;dynamic_trial?:Trial;chosen_language?:string;matching_reason?:string;covered_skills?:string[];not_assessed_skills?:string[];assessment_type?:'automated'|'human-review-required';compiler_version?:string; difficulty_level?:string;difficulty_percent?:number;difficulty_band?:number[];generation_mode?:string;difficulty_reason?:string;custom_task_validated?:boolean;ai_scenario?:string;ai_artifact?:string;ai_deliverable?:string}
export type ProjectFile = {path:string;content:string;editable:boolean}
export type Task = {files?:ProjectFile[];evaluation?:string;project_kind?:string;id:string; title:string;tag:string;time:string;goal:string;spec:string[];starter?:string;starter_html?:string;starter_css?:string;hint:string;lang:string;ai_artifact?:string;ai_context?:string;challenge_intensity?:number}
export type Trial = Omit<TrackSummary,'task_count'> & {tasks:Task[]; sample_data?:Record<string,{columns:string[];rows:(string|number)[][]}>; logs?:LogEvent[]}
export type LogEvent = {id:number;time:string;ip:string;user:string;event:string;status:number;path:string}
export type Check = {label:string;passed:boolean;detail:string}
export type Grade = {score:number;passed:number;total:number;checks:Check[];feedback:string; preview?:{columns:string[];rows:(string|number|null)[][]}|null; mode:string;report_id?:string;saved_at?:string}
export type HistoryItem = {id:string;created_at:string;track:TrackId;task_id:string;job_title:string;score:number}
export type StoredReport = HistoryItem & {checks:Check[];feedback:string}

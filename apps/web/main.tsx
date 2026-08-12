import { FormEvent, useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Archive, ArrowLeft, ArrowRight, Bot, CalendarDays, CheckCircle2, ChevronDown, Clock, FileText, FolderOpen,
  LayoutDashboard, LockKeyhole, MessageSquare, Play, Plus, Send, Sparkles,
  UserRound, X,
} from 'lucide-react';
import './styles.css';
import './appointment.css';

type Page = 'resume' | 'projects' | 'interview';
type ProjectId = 'jianli' | 'sleep';
type BookingStep = 'login' | 'slots' | 'details' | 'confirm' | 'done';
type SlotStatus = 'available' | 'booked' | 'owner_locked' | 'unavailable';
type Slot = { id: string; start_at: string; end_at: string; status: SlotStatus; resource_version: number; ownership: 'none' | 'self' | 'other' };
type User = { id: string; email: string; role: 'interviewer' | 'owner_admin'; verified: boolean };
type Draft = { slot_ids: string[]; company_name: string; meeting_platform: string; meeting_number: string; contact_last_name: string; contact_salutation: string; contact_phone: string; notes: string | null };
type Preview = { confirmation_token: string; expires_at: string; company_name: string; recipient_email: string; salutation: string };

const emptyDraft: Draft = { slot_ids: [], company_name: '', meeting_platform: '腾讯会议', meeting_number: '', contact_last_name: '', contact_salutation: '老师', contact_phone: '', notes: null };

const shanghaiDay = (iso: string) => new Intl.DateTimeFormat('en-CA', {
  year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'Asia/Shanghai',
}).format(new Date(iso));

function csrfCookie(): string {
  return document.cookie.split('; ').find((part) => part.startsWith('__Host-csrf='))?.split('=')[1] || '';
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { credentials: 'include', ...init, headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) } });
  if (!response.ok) {
    const problem = await response.json().catch(() => ({}));
    throw new Error(problem.detail || problem.title || `请求失败 (${response.status})`);
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}

const sessions = [
  { title: '为什么 Agent 不直接预约？', meta: '今天 14:32' },
  { title: 'RAG 找不到证据怎么办？', meta: '昨天 20:18' },
  { title: '通知失败如何重试？', meta: '昨天 19:04' },
];

const projects = {
  jianli: {
    label: '项目 01', name: 'AI 面试协作站', accent: 'green',
    headline: '把简历、追问与面试预约做成一条可验证的产品链。',
    steps: [
      { title: '产品入口', body: '简历问答 + 项目追问 + 面试预约，围绕招聘方的真实判断路径组织信息。', mark: '01' },
      { title: 'Agent 边界', body: '模型只负责基于证据问答，预约写入始终经过确定性 UI 和后端事务。', mark: '02' },
      { title: '可靠性设计', body: 'Slot 锁、Outbox、重试、退信和 SSE 恢复共同承载可审计的业务闭环。', mark: '03' },
    ],
  },
  sleep: {
    label: '项目 02', name: 'Sleep AIoT Agent', accent: 'blue',
    headline: '把睡眠健康场景做成受治理、可评估的 Agent 系统。',
    steps: [
      { title: '系统全景', body: 'React/Taro、NestJS、Python Agent、RAG、MQTT 与边缘设备形成纵向链路。', mark: '01' },
      { title: 'Agent 工作流', body: 'route → policy → finalize，工具按风险分级，高影响动作进入人工审批。', mark: '02' },
      { title: '可验证边界', body: '回归、RAG 评测和 Prompt Injection 防护都有独立证据，不把本地验证写成线上结果。', mark: '03' },
    ],
  },
} satisfies Record<ProjectId, { label: string; name: string; accent: string; headline: string; steps: { title: string; body: string; mark: string }[] }>;

function HistoryRail({ page, onPage }: { page: Page; onPage: (page: Page) => void }) {
  return <aside className="history-rail">
    <div className="rail-brand"><span className="brand-mark">晓</span><span>Jianli 工作台</span></div>
    <button className="new-session"><Plus size={16} /> 新建对话</button>
    <div className="rail-label">工作区</div>
    <button className={page === 'resume' ? 'rail-link active' : 'rail-link'} onClick={() => onPage('resume')}><FileText size={16} /> 简历问答</button>
    <button className={page === 'projects' ? 'rail-link active' : 'rail-link'} onClick={() => onPage('projects')}><FolderOpen size={16} /> 项目说明</button>
    <button className={page === 'interview' ? 'rail-link active' : 'rail-link'} onClick={() => onPage('interview')}><CalendarDays size={16} /> 预约面试</button>
    <div className="rail-label history-title">历史对话</div>
    <div className="session-list">{sessions.map((session) => <button className="session-item" key={session.title}><MessageSquare size={14} /><span><b>{session.title}</b><small>{session.meta}</small></span></button>)}</div>
    <div className="rail-bottom"><button className="rail-link"><Archive size={16} /> 已归档</button><div className="account"><span className="avatar">晓</span><span><b>用户</b><small>静态演示账号</small></span><ChevronDown size={15} /></div></div>
  </aside>;
}

function ChatPanel({ context }: { context: string }) {
  const [draft, setDraft] = useState('');
  return <section className="chat-panel">
    <div className="chat-head"><div><span className="live-dot" /> <b>项目问答</b><small>静态演示</small></div><button aria-label="关闭对话"><X size={17} /></button></div>
    <div className="chat-context"><Sparkles size={14} /><span>当前上下文：{context}</span></div>
    <div className="chat-body">
      <div className="message assistant"><span className="message-icon"><Bot size={16} /></span><div><b>你好，我是项目数字分身。</b><p>我会基于已公开的项目证据回答问题，当前不会发送真实请求。</p></div></div>
      <div className="message user"><span>你可以从左侧历史对话开始，也可以直接提出一个问题。</span></div>
      <div className="suggested"><span>推荐追问</span><button>我的核心技术取舍是什么？<ArrowRight size={14} /></button><button>有哪些可验证的工程证据？<ArrowRight size={14} /></button></div>
    </div>
    <div className="composer"><textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="输入你想追问的问题…" rows={1} /><button aria-label="发送问题"><Send size={17} /></button></div>
    <div className="chat-foot"><LockKeyhole size={12} /> 当前为静态交互，不连接真实模型</div>
  </section>;
}

function TopBar({ page, onPage }: { page: Page; onPage: (page: Page) => void }) {
  const title = page === 'resume' ? '简历问答' : page === 'projects' ? '项目说明' : '预约面试';
  return <header className="topbar"><div className="top-title"><LayoutDashboard size={17} /><b>{title}</b><span>/</span><small>AI 全栈开发工程师 · Agent 方向</small></div><nav><button className={page === 'resume' ? 'active' : ''} onClick={() => onPage('resume')}>页面一</button><button className={page === 'projects' ? 'active' : ''} onClick={() => onPage('projects')}>页面二</button><button className={page === 'interview' ? 'active' : ''} onClick={() => onPage('interview')}>预约</button></nav><div className="top-status"><span className="live-dot" /> 仅桌面端</div></header>;
}

function ResumeView({ onInterview }: { onInterview: () => void }) {
  return <main className="workspace resume-view"><div className="workspace-heading"><div><span className="eyebrow">RESUME / 01</span><h1>先看简历，再聊项目。</h1><p>左侧预留可复制文字的 PDF 简历；右侧对话用于追问经历、判断取舍和定位面试重点。</p></div><div className="heading-actions"><span className="placeholder-badge">PDF 待补充</span><button className="appointment-cta" onClick={onInterview}><CalendarDays size={15} /> 预约面试</button></div></div><div className="resume-stage"><div className="pdf-placeholder"><div className="pdf-toolbar"><span><FileText size={16} /> 简历.pdf</span><span className="muted">文件待上传</span></div><div className="paper"><div className="paper-kicker">RESUME PLACEHOLDER</div><h2>PDF 简历将在这里显示</h2><p>后续补充 PDF 后，这里将保留可复制文本、页码和缩放控制。</p><div className="paper-lines"><span /><span /><span /><span /><span /></div><div className="paper-footer"><span>待补充</span><span>页 1 / 1</span></div></div></div></div></main>;
}

function ProjectView({ onInterview }: { onInterview: () => void }) {
  const [selected, setSelected] = useState<ProjectId>('jianli');
  const [step, setStep] = useState(0);
  const project = projects[selected];
  const currentStep = project.steps[step];
  const context = useMemo(() => project.name, [project.name]);
  const selectProject = (id: ProjectId) => { setSelected(id); setStep(0); };
  return <main className="workspace project-view"><div className="workspace-heading project-heading"><div><span className="eyebrow">PROJECT STORY / 02</span><h1>用播放式演示讲清楚项目。</h1><p>每个项目都按招聘方的阅读路径拆成几个可验证的章节，不把技术名词堆成清单。</p></div><div className="project-actions"><div className="project-tabs"><button className={selected === 'jianli' ? 'active' : ''} onClick={() => selectProject('jianli')}>项目 01 · jianli</button><button className={selected === 'sleep' ? 'active' : ''} onClick={() => selectProject('sleep')}>项目 02 · sleep AIoT</button></div><button className="appointment-cta" onClick={onInterview}><CalendarDays size={15} /> 预约面试</button></div></div><div className={`project-stage ${project.accent}`}><div className="stage-screen"><div className="stage-top"><span>{project.label}</span><span>演示占位 · {currentStep.mark} / 03</span></div><div className="stage-copy"><span className="stage-number">{currentStep.mark}</span><h2>{currentStep.title}</h2><p>{currentStep.body}</p></div><div className="stage-progress">{project.steps.map((item, index) => <button key={item.mark} className={index === step ? 'active' : ''} onClick={() => setStep(index)}><span>{item.mark}</span>{item.title}</button>)}</div></div><div className="stage-controls"><button onClick={() => setStep((value) => Math.max(0, value - 1))} disabled={step === 0} aria-label="上一步"><ArrowLeft size={16} /></button><button className="play-button" onClick={() => setStep((value) => (value + 1) % project.steps.length)}><Play size={15} /> 播放下一页</button><button onClick={() => setStep((value) => Math.min(project.steps.length - 1, value + 1))} disabled={step === project.steps.length - 1} aria-label="下一步"><ArrowRight size={16} /></button></div></div><div className="project-context"><span><Sparkles size={14} /> 内容占位</span><p>后续可替换为项目架构图、页面录屏、成本估算和真实验证证据。</p></div></main>;
}

function InterviewView() {
  const [step, setStep] = useState<BookingStep>('login');
  const [user, setUser] = useState<User | null>(null);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [csrf, setCsrf] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const loadSlots = async () => {
    const snapshots = await Promise.all([0, 1].map((week) => api<{ items: Slot[] }>(`/slots/snapshot?week_offset=${week}`)));
    setSlots(snapshots.flatMap((item) => item.items));
  };

  useEffect(() => {
    api<User>('/auth/me').then(async (me) => { setCsrf(csrfCookie()); setUser(me); await loadSlots(); setStep('slots'); }).catch(() => undefined);
  }, []);

  const login = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setBusy(true); setError('');
    const data = new FormData(event.currentTarget);
    try {
      const response = await fetch('/auth/login', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', Origin: window.location.origin }, body: JSON.stringify({ email: data.get('email'), password: data.get('password'), remember_me: Boolean(data.get('remember')) }) });
      if (!response.ok) throw new Error((await response.json()).detail || '登录失败');
      setCsrf(response.headers.get('X-CSRF-Token') || csrfCookie());
      const me = await api<User>('/auth/me'); setUser(me); await loadSlots(); setStep('slots');
    } catch (reason) { setError(reason instanceof Error ? reason.message : '登录失败'); } finally { setBusy(false); }
  };

  const choose = (slot: Slot) => {
    const ordered = slots.filter((item) => shanghaiDay(item.start_at) === shanghaiDay(slot.start_at)).sort((a, b) => a.start_at.localeCompare(b.start_at));
    const index = ordered.findIndex((item) => item.id === slot.id);
    const group = ordered.slice(index, index + 3);
    const valid = group.length === 3 && group.every((item) => item.status === 'available') && group.slice(1).every((item, offset) => item.start_at === group[offset].end_at);
    setError(valid ? '' : '请选择同一天内连续的三个绿色时段');
    setSelected(valid ? group.map((item) => item.id) : []);
  };

  const selectedSlots = slots.filter((item) => selected.includes(item.id)).sort((a, b) => a.start_at.localeCompare(b.start_at));
  const dayGroups = useMemo(() => Object.entries(slots.reduce<Record<string, Slot[]>>((groups, slot) => { const day = shanghaiDay(slot.start_at); (groups[day] ||= []).push(slot); return groups; }, {})), [slots]);
  const submitDetails = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setBusy(true); setError('');
    const data = new FormData(event.currentTarget);
    const next: Draft = { slot_ids: selected, company_name: String(data.get('company_name')), meeting_platform: String(data.get('meeting_platform')), meeting_number: String(data.get('meeting_number')), contact_last_name: String(data.get('contact_last_name')), contact_salutation: String(data.get('contact_salutation')), contact_phone: String(data.get('contact_phone')), notes: String(data.get('notes') || '') || null };
    try { const result = await api<Preview>('/appointment-confirmations', { method: 'POST', headers: { 'X-CSRF-Token': csrf }, body: JSON.stringify(next) }); setDraft(next); setPreview(result); setStep('confirm'); } catch (reason) { setError(reason instanceof Error ? reason.message : '预览失败'); } finally { setBusy(false); }
  };
  const confirm = async () => {
    if (!preview) return; setBusy(true); setError('');
    try { await api('/appointments', { method: 'POST', headers: { 'X-CSRF-Token': csrf, 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ confirmation_token: preview.confirmation_token, appointment: draft }) }); await loadSlots(); setStep('done'); } catch (reason) { setError(reason instanceof Error ? reason.message : '预约失败'); } finally { setBusy(false); }
  };
  const stageIndex = step === 'login' ? 0 : step === 'slots' ? 1 : 2;
  const stages = [{ icon: UserRound, title: '账号验证', detail: user ? user.email : '登录后进入选时' }, { icon: CalendarDays, title: '选择时间', detail: '连续 3 格，共 90 分钟' }, { icon: CheckCircle2, title: '确认预约', detail: '预览确认后原子提交' }];
  return <main className="workspace interview-view"><div className="workspace-heading"><div><span className="eyebrow">INTERVIEW / 03</span><h1>预约一次有准备的交流。</h1><p>登录后选择真实可用时段，填写会议信息并在三分钟内确认。</p></div><span className="placeholder-badge">真实预约流程</span></div>
    <div className="booking-steps">{stages.map((item, index) => { const Icon = item.icon; return <div className={index === stageIndex ? 'booking-step active' : 'booking-step'} key={item.title}><span className="step-icon"><Icon size={18} /></span><div><small>STEP 0{index + 1}</small><b>{item.title}</b><p>{item.detail}</p></div></div>; })}</div>
    {error && <div className="booking-error">{error}</div>}
    {step === 'login' && <section className="login-panel"><div><span className="eyebrow">SECURE SIGN IN</span><h2>面试官登录</h2><p>使用已验证账号进入预约日历。</p></div><form onSubmit={login}><label>邮箱<input name="email" type="email" required autoComplete="email" /></label><label>密码<input name="password" type="password" required autoComplete="current-password" /></label><label className="check-row"><input name="remember" type="checkbox" /> 14 天内保持登录</label><button disabled={busy}>{busy ? '正在登录…' : '登录并查看时段'}</button></form></section>}
    {step === 'slots' && <section className="booking-board"><div className="booking-calendar"><div className="calendar-head"><span><CalendarDays size={17} /> 未来两周可预约时间</span><span className="muted">绿色可选 · 红色不可约 · 深红色为本人预约</span></div><div className="slot-grid">{dayGroups.map(([day, items]) => <div className="slot-day" key={day}><b>{new Intl.DateTimeFormat('zh-CN', { month: 'numeric', day: 'numeric', weekday: 'short', timeZone: 'Asia/Shanghai' }).format(new Date(items[0].start_at))}</b><div>{items.map((slot) => { const ownBooking = slot.status === 'booked' && slot.ownership === 'self'; const slotLabel = ownBooking ? '已预约（本人）' : slot.status === 'booked' ? '已预约' : ''; return <button key={slot.id} className={`${slot.status} ${ownBooking ? 'own-booking' : ''} ${selected.includes(slot.id) ? 'selected' : ''}`} disabled={slot.status !== 'available'} title={slotLabel || undefined} aria-label={slotLabel ? `${new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Shanghai' }).format(new Date(slot.start_at))} ${slotLabel}` : undefined} onClick={() => choose(slot)}>{new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Shanghai' }).format(new Date(slot.start_at))}</button>; })}</div></div>)}</div></div><aside className="booking-summary"><span className="eyebrow">BOOKING SUMMARY</span><h2>预约摘要</h2><dl><div><dt>账号</dt><dd>{user?.email}</dd></div><div><dt>时长</dt><dd>90 分钟</dd></div><div><dt>时间</dt><dd>{selectedSlots[0] ? `${new Date(selectedSlots[0].start_at).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })} 起` : '尚未选择'}</dd></div></dl><button className="primary-command" disabled={selected.length !== 3} onClick={() => setStep('details')}>填写预约信息</button></aside></section>}
    {step === 'details' && <section className="details-panel"><button className="text-command" onClick={() => setStep('slots')}><ArrowLeft size={15} /> 返回选时</button><form onSubmit={submitDetails}><h2>填写会议信息</h2><div className="form-grid"><label>公司名称<input name="company_name" required maxLength={200} /></label><label>会议平台<input name="meeting_platform" defaultValue="腾讯会议" required /></label><label>会议号<input name="meeting_number" required /></label><label>联系人姓氏<input name="contact_last_name" required /></label><label>称呼<select name="contact_salutation"><option>老师</option><option>先生</option><option>女士</option></select></label><label>联系电话<input name="contact_phone" required /></label><label className="wide">备注<textarea name="notes" maxLength={2000} /></label></div><button className="primary-command" disabled={busy}>{busy ? '正在生成预览…' : '下一步：确认信息'}</button></form></section>}
    {step === 'confirm' && preview && <section className="confirm-panel"><span className="eyebrow">FINAL CHECK</span><h2>请确认预约信息</h2><p>确认链接有效至 {new Date(preview.expires_at).toLocaleTimeString('zh-CN')}，期间不预占时段。</p><dl><div><dt>公司</dt><dd>{preview.company_name}</dd></div><div><dt>收件邮箱</dt><dd>{preview.recipient_email}</dd></div><div><dt>称呼</dt><dd>{preview.salutation}</dd></div><div><dt>会议</dt><dd>{draft.meeting_platform} · {draft.meeting_number}</dd></div></dl><div className="confirm-actions"><button className="text-command" onClick={() => setStep('details')}>返回修改</button><button className="primary-command" disabled={busy} onClick={confirm}>{busy ? '正在提交…' : '确认预约'}</button></div></section>}
    {step === 'done' && <section className="success-panel"><CheckCircle2 size={34} /><h2>预约已创建</h2><p>时段已原子锁定，通知事件已进入异步处理队列。</p><button className="primary-command" onClick={() => { setSelected([]); setStep('slots'); }}>返回日历</button></section>}
  </main>;
}

function App() {
  const [page, setPage] = useState<Page>('resume');
  const content = page === 'resume' ? <ResumeView onInterview={() => setPage('interview')} /> : page === 'projects' ? <ProjectView onInterview={() => setPage('interview')} /> : <InterviewView />;
  const context = page === 'resume' ? '简历与全部项目' : page === 'projects' ? '当前项目说明' : '面试预约流程';
  return <div className="app-shell"><div className="desktop-gate"><LockKeyhole size={24} /><h2>请使用桌面端访问</h2><p>为保证简历与项目演示的三栏布局完整，1024px 以下暂不开放。</p></div><div className="desktop-app"><HistoryRail page={page} onPage={setPage} /><div className="main-column"><TopBar page={page} onPage={setPage} />{content}</div><ChatPanel context={context} /></div></div>;
}

export default App;

createRoot(document.getElementById('root')!).render(<App />);

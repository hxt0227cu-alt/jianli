import { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Archive, ArrowLeft, ArrowRight, Bot, ChevronDown, FileText, FolderOpen,
  LayoutDashboard, LockKeyhole, MessageSquare, Play, Plus, Send, Sparkles,
  UserRound, X,
} from 'lucide-react';
import './styles.css';

type Page = 'resume' | 'projects';
type ProjectId = 'jianli' | 'sleep';

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
  return <header className="topbar"><div className="top-title"><LayoutDashboard size={17} /><b>{page === 'resume' ? '简历问答' : '项目说明'}</b><span>/</span><small>AI 全栈开发工程师 · Agent 方向</small></div><nav><button className={page === 'resume' ? 'active' : ''} onClick={() => onPage('resume')}>页面一</button><button className={page === 'projects' ? 'active' : ''} onClick={() => onPage('projects')}>页面二</button></nav><div className="top-status"><span className="live-dot" /> 仅桌面端</div></header>;
}

function ResumeView() {
  return <main className="workspace resume-view"><div className="workspace-heading"><div><span className="eyebrow">RESUME / 01</span><h1>先看简历，再聊项目。</h1><p>左侧预留可复制文字的 PDF 简历；右侧对话用于追问经历、判断取舍和定位面试重点。</p></div><span className="placeholder-badge">PDF 待补充</span></div><div className="resume-stage"><div className="pdf-placeholder"><div className="pdf-toolbar"><span><FileText size={16} /> 简历.pdf</span><span className="muted">文件待上传</span></div><div className="paper"><div className="paper-kicker">RESUME PLACEHOLDER</div><h2>PDF 简历将在这里显示</h2><p>后续补充 PDF 后，这里将保留可复制文本、页码和缩放控制。</p><div className="paper-lines"><span /><span /><span /><span /><span /></div><div className="paper-footer"><span>待补充</span><span>页 1 / 1</span></div></div></div></div></main>;
}

function ProjectView() {
  const [selected, setSelected] = useState<ProjectId>('jianli');
  const [step, setStep] = useState(0);
  const project = projects[selected];
  const currentStep = project.steps[step];
  const context = useMemo(() => project.name, [project.name]);
  const selectProject = (id: ProjectId) => { setSelected(id); setStep(0); };
  return <main className="workspace project-view"><div className="workspace-heading project-heading"><div><span className="eyebrow">PROJECT STORY / 02</span><h1>用播放式演示讲清楚项目。</h1><p>每个项目都按招聘方的阅读路径拆成几个可验证的章节，不把技术名词堆成清单。</p></div><div className="project-tabs"><button className={selected === 'jianli' ? 'active' : ''} onClick={() => selectProject('jianli')}>项目 01 · jianli</button><button className={selected === 'sleep' ? 'active' : ''} onClick={() => selectProject('sleep')}>项目 02 · sleep AIoT</button></div></div><div className={`project-stage ${project.accent}`}><div className="stage-screen"><div className="stage-top"><span>{project.label}</span><span>演示占位 · {currentStep.mark} / 03</span></div><div className="stage-copy"><span className="stage-number">{currentStep.mark}</span><h2>{currentStep.title}</h2><p>{currentStep.body}</p></div><div className="stage-progress">{project.steps.map((item, index) => <button key={item.mark} className={index === step ? 'active' : ''} onClick={() => setStep(index)}><span>{item.mark}</span>{item.title}</button>)}</div></div><div className="stage-controls"><button onClick={() => setStep((value) => Math.max(0, value - 1))} disabled={step === 0} aria-label="上一步"><ArrowLeft size={16} /></button><button className="play-button" onClick={() => setStep((value) => (value + 1) % project.steps.length)}><Play size={15} /> 播放下一页</button><button onClick={() => setStep((value) => Math.min(project.steps.length - 1, value + 1))} disabled={step === project.steps.length - 1} aria-label="下一步"><ArrowRight size={16} /></button></div></div><div className="project-context"><span><Sparkles size={14} /> 内容占位</span><p>后续可替换为项目架构图、页面录屏、成本估算和真实验证证据。</p></div></main>;
}

function App() {
  const [page, setPage] = useState<Page>('resume');
  return <div className="app-shell"><div className="desktop-gate"><LockKeyhole size={24} /><h2>请使用桌面端访问</h2><p>为保证简历与项目演示的三栏布局完整，1024px 以下暂不开放。</p></div><div className="desktop-app"><HistoryRail page={page} onPage={setPage} /><div className="main-column"><TopBar page={page} onPage={setPage} />{page === 'resume' ? <ResumeView /> : <ProjectView />}</div><ChatPanel context={page === 'resume' ? '简历与全部项目' : '当前项目说明'} /></div></div>;
}

export default App;

createRoot(document.getElementById('root')!).render(<App />);

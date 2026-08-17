import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Archive, ArrowLeft, ArrowRight, Bot, CalendarCheck, CalendarDays, CheckCircle2, ChevronDown, Clock, Database, FileText, FolderOpen,
  LayoutDashboard, LockKeyhole, MessageSquare, Play, Plus, Send, Sparkles, Trash2, UploadCloud,
  UserRound, X,
} from 'lucide-react';
import './styles.css';
import './appointment.css';
import { MyAppointmentsView } from './my-appointments';

type Page = 'dashboard' | 'resume' | 'projects' | 'interview' | 'mine' | 'admin';
type ProjectId = 'jianli' | 'sleep';
type PageKey = 'resume' | 'projects';
type KnowledgeDoc = { id: string; name: string; type: string; size: number; status: 'indexing' | 'indexed' | 'failed'; parse_mode: string | null; failure_reason: string | null; created_at: string };
type Conversation = { id: string; created_at: string; updated_at: string };
type ApptSummary = { id: string; status: 'active' | 'cancelled' | 'completed'; start_at: string; end_at: string; company_name: string; meeting_platform: string; meeting_number: string; contact_salutation: string };
type ChatMessage = {
  role: 'assistant' | 'user';
  text: string;
  pending?: boolean;
  citations?: { doc: string; fragment: number }[];
  grounded?: boolean;
  offtopic?: boolean;
  error?: boolean;
  toolCalls?: string;
};

// 豆包式追问池：每次回答完成后从池中随机抽 3 条显示为气泡（点击直接发）。
const FOLLOWUP_POOL = [
  '展开介绍 Litchi Copilot 的 Planner → Guard → Executor 设计',
  '你做的 pgvector 多租户 RAG 怎么做的隔离？',
  '泰益智项目里 LangGraph 和 Temporal 各负责什么？',
  '你对 Prompt Injection 防护的思路是什么？',
  '两个项目里模型选型和降级策略有什么不同？',
  '你最有成就感的一段工程经历是哪一段？',
  '你适合什么样的团队和岗位？',
  '实习经历对正式工作的帮助有多大？',
  '你的职业规划是怎么样的？',
];
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

// POST /answers:stream (SSE over fetch, sse.md §3). EventSource only does GET, so the
// stream is read with fetch + ReadableStream and frames are parsed from the buffer.
// Anonymous calls need no CSRF; with a session cookie the X-CSRF-Token header is sent.
async function streamAnswer(
  body: Record<string, unknown>,
  onEvent: (event: string, data: Record<string, unknown>) => void,
): Promise<void> {
  const response = await fetch('/answers:stream', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfCookie() },
    body: JSON.stringify(body),
  });
  if (!response.ok || !response.body) {
    const problem = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(problem.detail || `回答请求失败 (${response.status})`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary = buffer.indexOf('\n\n');
    while (boundary !== -1) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      let event = 'message';
      const dataLines: string[] = [];
      for (const line of block.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim();
        else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
      }
      if (dataLines.length) onEvent(event, JSON.parse(dataLines.join('\n')));
      boundary = buffer.indexOf('\n\n');
    }
  }
}

type ProjectStep = { title: string; mark: string; summary?: string; points?: string[]; body?: string };
type ProjectInfo = { label: string; name: string; accent: string; headline: string; story: string; steps: ProjectStep[] };

const projects: Record<ProjectId, ProjectInfo> = {
  jianli: {
    label: '项目 01', name: 'AI 面试协作站', accent: 'green',
    headline: '把简历问答、项目追问与面试预约做成一条可验证的产品链。',
    story: '先有约束，再有功能：面试场景下真实性优先——宁可不答，也绝不编造。',
    steps: [
      {
        title: '背景与问题', mark: '01',
        summary: '面试初筛大量时间在重复确认基础经历；AI 问答天然幻觉，面试场景下编造=诚信风险。',
        points: ['简历问答 + 项目追问 + 面试预约，覆盖技术岗初筛的信息确认全流程', '核心约束：真实性优先——越界/无依据问题一律拒答，绝不编造经历', '不是"为了做 RAG 而做 RAG"，而是意识到场景约束后的产品设计'],
      },
      {
        title: '架构与选型', mark: '02',
        summary: 'FastAPI + PostgreSQL(pgvector) + Redis + React，前后端契约先行；每个选型说清放弃了什么。',
        points: ['FastAPI + SQLAlchemy + Alembic：0001-0007 迁移 11 张表，up→down→up 可逆', '放弃独立向量库（Milvus/Qdrant）：数据量 < 万条，pgvector 足够，独立部署运维收益为负', 'embedding 演进：本地哈希 → BGE-M3（1024 维），纯向量层 avg-rank 1.8 → 1.3', '会话用 Cookie + CSRF + Redis 限频，敏感字段 AES-256-GCM 加密，审计日志落库'],
      },
      {
        title: 'Agent 与 RAG', mark: '03',
        summary: '混合检索 + 双层拒答 + 模型自主决策调用只读工具，决策链 SSE 可观测。',
        points: ['混合检索：向量 top10 + BM25 top10 → RRF 融合 top6；CJK 单字 BM25 对 embedding 退化鲁棒', '越界拒答双层门槛：向量阈值 0.47（数据校准）+ CJK 停用词过滤，拒答率 0% → 100%', 'Agent 工具化：search_knowledge 白名单只读工具，模型 function calling 自主生成检索词，决策链 SSE 帧可见；预约/写入端点绝不注册为工具', '双路召回：模型改写 query + 原问题对照，防次优改写丢证据'],
      },
      {
        title: '工程化与证据', mark: '04',
        summary: '评测先暴露缺陷再修复闭环；全部数字真实可复现，含一段诚实记录的踩坑史。',
        points: ['RAG 评测（tests/aiqa/test_rag_eval.py，10 篇语料全链路）：LITERAL 8/8、REJECT 10/10、语义改写 6/6', '拒答率 0% → 100%（阈值引入前后）；BGE-M3 纯向量 avg-rank 1.3', '真实 PG16 + Redis7 集成测试 53+ passed；ruff/mypy 门禁全绿；SSE 恢复契约文档化', '真实踩坑：Agent 自主决策上线后评测 8/8→6/8→8/8，最终根因是 greeting 判定 "hi" 子串误匹配 "litchi"——诚实记录，不粉饰'],
      },
    ],
  },
  sleep: {
    label: '项目 02', name: 'Sleep AIoT Agent', accent: 'blue',
    headline: '把睡眠健康场景做成受治理、可评估的 Agent 系统。',
    story: '素材整理中，后续补充。',
    steps: [
      { title: '系统全景', body: 'React/Taro、NestJS、Python Agent、RAG、MQTT 与边缘设备形成纵向链路。', mark: '01' },
      { title: 'Agent 工作流', body: 'route → policy → finalize，工具按风险分级，高影响动作进入人工审批。', mark: '02' },
      { title: '可验证边界', body: '回归、RAG 评测和 Prompt Injection 防护都有独立证据，不把本地验证写成线上结果。', mark: '03' },
    ],
  },
};

function HistoryRail({ page, onPage, user, conversations, onSelectConversation, onNewConversation }: { page: Page; onPage: (page: Page) => void; user: User | null; conversations: Conversation[]; onSelectConversation: (id: string) => void; onNewConversation: () => void }) {
  const shortDay = (iso: string) => new Intl.DateTimeFormat('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(iso));
  return <aside className="history-rail">
    <div className="rail-brand"><span className="brand-mark">晓</span><span>Jianli 工作台</span></div>
    <button className="new-session" onClick={onNewConversation}><Plus size={16} /> 新建对话</button>
    <div className="rail-label">工作区</div>
    <button className={page === 'dashboard' ? 'rail-link active' : 'rail-link'} onClick={() => onPage('dashboard')}><LayoutDashboard size={16} /> 工作台</button>
    <button className={page === 'resume' ? 'rail-link active' : 'rail-link'} onClick={() => onPage('resume')}><FileText size={16} /> 简历问答</button>
    <button className={page === 'projects' ? 'rail-link active' : 'rail-link'} onClick={() => onPage('projects')}><FolderOpen size={16} /> 项目说明</button>
    <button className={page === 'interview' ? 'rail-link active' : 'rail-link'} onClick={() => onPage('interview')}><CalendarDays size={16} /> 预约面试</button>
    <button className={page === 'mine' ? 'rail-link active' : 'rail-link'} onClick={() => onPage('mine')}><CalendarCheck size={16} /> 我的预约</button>
    {user?.role === 'owner_admin' && <button className={page === 'admin' ? 'rail-link active' : 'rail-link'} onClick={() => onPage('admin')}><Database size={16} /> 知识库管理</button>}
    <div className="rail-label history-title">历史对话</div>
    {user ? <div className="session-list">{conversations.length === 0 ? <div className="session-empty">还没有历史对话，去简历问答页提问吧。</div> : conversations.map((conversation) => <button className="session-item" key={conversation.id} onClick={() => onSelectConversation(conversation.id)}><MessageSquare size={14} /><span><b>对话</b><small>{shortDay(conversation.created_at)}</small></span></button>)}</div> : <div className="session-empty">登录后显示历史对话。</div>}
    <div className="rail-bottom"><button className="rail-link"><Archive size={16} /> 已归档</button><div className="account"><span className="avatar">晓</span><span><b>{user ? user.email : '访客'}</b><small>{user ? `${user.role} · 已登录` : '未登录'}</small></span><ChevronDown size={15} /></div></div>
  </aside>;
}

function ChatPanel({ live, pageKey, projectKey, conversationId, canPersist, onConversationCreated }: { live: boolean; pageKey: PageKey; projectKey?: ProjectId; conversationId?: string | null; canPersist: boolean; onConversationCreated?: (id: string) => void }) {
  const [draft, setDraft] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [followups, setFollowups] = useState<string[]>([]);
  const chatBodyRef = useRef<HTMLDivElement | null>(null);
  const context = projectKey ? `当前项目：${projectKey === 'jianli' ? 'AI 面试协作站' : 'Sleep AIoT Agent'}` : pageKey === 'resume' ? '简历与全部项目' : '当前项目说明';

  useEffect(() => {
    setMessages([]);
    setFollowups([]);
    setRecommendations([]);
    if (!live) return;
    api<{ items: string[] }>(`/pages/${pageKey}/recommendations`).then((data) => setRecommendations(data.items)).catch(() => undefined);
    if (conversationId) {
      // 恢复历史会话：拉取该会话的消息填充对话（TASK-FE-INTERVIEWER-001）
      api<{ items: { role: 'user' | 'assistant'; content: string }[] }>(`/conversations/${conversationId}/messages`).then((data) => {
        setMessages(data.items.map((item) => ({ role: item.role, text: item.content })));
      }).catch(() => undefined);
    }
  }, [live, pageKey, projectKey, conversationId]);

  // 跟随新消息滚到底（防打扰）。豆包式只滚 chat-body（历史对话区），
  // 不影响 followups/composer。
  useEffect(() => {
    if (!live || messages.length === 0) return;
    const el = chatBodyRef.current;
    if (!el) return;
    if (el.scrollHeight - (el.scrollTop + el.clientHeight) < 160) {
      el.scrollTo(0, el.scrollHeight);
    }
  }, [live, messages]);

  const refreshFollowups = () => {
    const shuffled = [...FOLLOWUP_POOL].sort(() => Math.random() - 0.5);
    setFollowups(shuffled.slice(0, 3));
  };

  const send = async (question?: string) => {
    const text = (question ?? draft).trim();
    if (!text || busy) return;
    setDraft('');
    setFollowups([]);
    setBusy(true);
    let activeConversationId = conversationId ?? null;
    if (canPersist && !activeConversationId) {
      try {
        const created = await api<{ id: string }>('/conversations', { method: 'POST', headers: { 'X-CSRF-Token': csrfCookie() } });
        activeConversationId = created.id;
        onConversationCreated?.(created.id);
      } catch { /* 会话创建失败则本次按匿名处理 */ }
    }
    const body: Record<string, unknown> = { question: text, page_key: pageKey };
    if (projectKey) body.project_key = projectKey;
    if (activeConversationId) body.conversation_id = activeConversationId;
    setMessages((prev) => [...prev, { role: 'user', text }, { role: 'assistant', text: '', pending: true }]);
    try {
      let assistantText = '';
      await streamAnswer(body, (event, data) => {
        if (event === 'answer.delta') {
          assistantText += String(data.text ?? '');
          setMessages((prev) => { const next = [...prev]; const last = next[next.length - 1]; if (last?.role === 'assistant') next[next.length - 1] = { ...last, text: assistantText }; return next; });
        } else if (event === 'answer.tool_calls') {
          // Agent 工具化（TASK-AGENT-TOOLS-001）：决策链可见 —— 已调用 search_knowledge
          const calls = (data.calls as { name: string; query: string; hits: { doc: string; fragment: number }[] }[] | undefined) ?? [];
          const summary = calls.map((call) => `已检索知识库（query: ${call.query}）→ 命中 ${call.hits.length} 个片段`).join('；');
          if (summary) {
            setMessages((prev) => { const next = [...prev]; const last = next[next.length - 1]; if (last?.role === 'assistant') next[next.length - 1] = { ...last, toolCalls: summary }; return next; });
          }
        } else if (event === 'answer.citations') {
          const citations = (data.citations as { doc: string; fragment: number }[] | undefined) ?? [];
          setMessages((prev) => { const next = [...prev]; const last = next[next.length - 1]; if (last?.role === 'assistant') next[next.length - 1] = { ...last, citations }; return next; });
        } else if (event === 'answer.completed') {
          setMessages((prev) => { const next = [...prev]; const last = next[next.length - 1]; if (last?.role === 'assistant') next[next.length - 1] = { ...last, pending: false, grounded: Boolean(data.grounded), offtopic: Boolean(data.offtopic) }; return next; });
          // 豆包式：回答完成后下方出 3 条追问建议气泡（点击直接发）
          refreshFollowups();
        } else if (event === 'answer.error') {
          setMessages((prev) => { const next = [...prev]; const last = next[next.length - 1]; if (last?.role === 'assistant') next[next.length - 1] = { ...last, pending: false, error: true, text: String(data.detail ?? '回答失败，请稍后重试') }; return next; });
        }
      });
    } catch (reason) {
      setMessages((prev) => { const next = [...prev]; const last = next[next.length - 1]; if (last?.role === 'assistant') next[next.length - 1] = { ...last, pending: false, error: true, text: reason instanceof Error ? reason.message : '回答失败，请稍后重试' }; return next; });
    } finally { setBusy(false); }
  };

  if (!live) {
    // 静态降级（interview / mine 页）：与既有占位一致，不发送真实请求。
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

  return <section className="chat-panel">
    <div className="chat-head"><div><span className="live-dot" /> <b>项目问答</b><small>实时回答</small></div></div>
    <div className="chat-context"><Sparkles size={14} /><span>当前上下文：{context}</span></div>
    <div className="chat-body" ref={chatBodyRef}>
      {messages.length === 0 && <>
        <div className="message assistant"><span className="message-icon"><Bot size={16} /></span><div><b>你好，我是项目数字分身。</b><p>我会基于已公开的知识库与页面证据流式回答你的问题；无关或越界的问题会被拒绝。</p></div></div>
        {recommendations.length > 0 && <div className="suggested"><span>推荐追问</span>{recommendations.map((item) => <button key={item} onClick={() => send(item)}>{item}<ArrowRight size={14} /></button>)}</div>}
      </>}
      {messages.map((message, index) => {
        if (message.role === 'user') return <div className="message user" key={index}><span>{message.text}</span></div>;
        return <div className="message assistant" key={index}><span className="message-icon"><Bot size={16} /></span><div>
          {message.toolCalls && <small className="tool-chain">🤖 {message.toolCalls}</small>}
          {message.pending && message.text === '' ? <p className="typing-hint">正在思考…</p> : <p>{message.text}</p>}
          {!message.pending && message.citations && message.citations.length > 0 && <div className="citations"><span>引用</span>{message.citations.map((cite, citeIndex) => <code key={citeIndex}>{cite.doc} · {cite.fragment + 1}</code>)}</div>}
          {!message.pending && message.grounded && <small className="answer-state grounded">已基于资料回答</small>}
          {!message.pending && message.offtopic && <small className="answer-state offtopic">越界问题已拒绝</small>}
          {message.error && <small className="answer-state error">回答失败</small>}
        </div></div>;
      })}
    </div>
    {/* 中层：推荐追问（独立模块，不在消息流里） */}
    {followups.length > 0 && !busy && messages.length > 0 && messages[messages.length - 1]?.role === 'assistant' && !messages[messages.length - 1]?.pending && <div className="followups"><span className="followups-label">追问</span>{followups.map((item) => <button key={item} className="followup-bubble" onClick={() => send(item)}>{item}</button>)}</div>}
    {/* 底层：输入框（sticky 贴底） */}
    <div className="composer"><textarea value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder="输入你想追问的问题…" rows={1} disabled={busy} /><button disabled={busy} onClick={() => send()} aria-label="发送问题">{busy ? '回答中…' : <Send size={17} />}</button></div>
    <div className="chat-foot"><LockKeyhole size={12} /> 回答基于知识库与公开页面，越界问题将被拒绝</div>
  </section>;
}

function TopBar({ page, onPage }: { page: Page; onPage: (page: Page) => void }) {
  const title = page === 'dashboard' ? '工作台' : page === 'resume' ? '简历问答' : page === 'projects' ? '项目说明' : page === 'admin' ? '知识库管理' : '预约面试';
  return <header className="topbar"><div className="top-title"><LayoutDashboard size={17} /><b>{title}</b><span>/</span><small>AI 全栈开发工程师 · Agent 方向</small></div><nav><button className={page === 'dashboard' ? 'active' : ''} onClick={() => onPage('dashboard')}>工作台</button><button className={page === 'resume' ? 'active' : ''} onClick={() => onPage('resume')}>页面一</button><button className={page === 'projects' ? 'active' : ''} onClick={() => onPage('projects')}>页面二</button><button className={page === 'interview' ? 'active' : ''} onClick={() => onPage('interview')}>预约</button><button className={page === 'mine' ? 'active' : ''} onClick={() => onPage('mine')}>我的预约</button><button className={page === 'admin' ? 'active' : ''} onClick={() => onPage('admin')}>知识库</button></nav><div className="top-status"><span className="live-dot" /> 仅桌面端</div></header>;
}

function ResumeView({ onInterview }: { onInterview: () => void }) {
  return <main className="workspace resume-view"><div className="workspace-heading"><div><span className="eyebrow">RESUME / 01</span><h1>先看简历，再聊项目。</h1><p>左侧展示真实简历 PDF（放置于 apps/web/public/resume.pdf）；右侧对话用于追问经历、判断取舍和定位面试重点。</p></div><div className="heading-actions"><span className="placeholder-badge">PDF 简历</span><button className="appointment-cta" onClick={onInterview}><CalendarDays size={15} /> 预约面试</button></div></div><div className="resume-stage"><div className="pdf-placeholder"><div className="pdf-toolbar"><span><FileText size={16} /> 简历.pdf</span><span className="muted">PDF 简历将在这里显示 · 素材放于 public/resume.pdf</span></div><embed className="resume-embed" src="/resume.pdf" type="application/pdf" aria-label="简历 PDF" /></div></div></main>;
}

function ProjectView({ selected, onSelect, onInterview }: { selected: ProjectId; onSelect: (id: ProjectId) => void; onInterview: () => void }) {
  const [step, setStep] = useState(0);
  const project = projects[selected];
  const currentStep = project.steps[step];
  useEffect(() => { setStep(0); }, [selected]);
  return <main className="workspace project-view"><div className="workspace-heading project-heading"><div><span className="eyebrow">PROJECT STORY / 02</span><h1>问题 → 踩坑 → 演进。</h1><p>{project.story}</p></div><div className="project-actions"><div className="project-tabs"><button className={selected === 'jianli' ? 'active' : ''} onClick={() => onSelect('jianli')}>项目 01 · jianli</button><button className={selected === 'sleep' ? 'active' : ''} onClick={() => onSelect('sleep')}>项目 02 · sleep AIoT</button></div><button className="appointment-cta" onClick={onInterview}><CalendarDays size={15} /> 预约面试</button></div></div><div className={`project-stage ${project.accent}`}><div className="stage-screen"><div className="stage-top"><span>{project.label} · {project.name}</span><span>{currentStep.mark} / {project.steps.length}</span></div><div className="stage-copy"><span className="stage-number">{currentStep.mark}</span><h2>{currentStep.title}</h2>{currentStep.summary ? <p>{currentStep.summary}</p> : <p>{currentStep.body}</p>}{currentStep.points ? <ul className="stage-points">{currentStep.points.map((point) => <li key={point}>{point}</li>)}</ul> : null}</div><div className="stage-progress">{project.steps.map((item, index) => <button key={item.mark} className={index === step ? 'active' : ''} onClick={() => setStep(index)}><span>{item.mark}</span>{item.title}</button>)}</div></div><div className="stage-controls"><button onClick={() => setStep((value) => Math.max(0, value - 1))} disabled={step === 0} aria-label="上一步"><ArrowLeft size={16} /></button><button className="play-button" onClick={() => setStep((value) => (value + 1) % project.steps.length)}><Play size={15} /> 播放下一步</button><button onClick={() => setStep((value) => Math.min(project.steps.length - 1, value + 1))} disabled={step === project.steps.length - 1} aria-label="下一步"><ArrowRight size={16} /></button></div></div><div className="project-context"><span><Sparkles size={14} /> 右侧问答已按当前项目过滤</span><p>每个章节都可以直接在右侧追问细节——所有量化数字来自真实评测与测试，可复现。</p></div></main>;
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
  const [notice, setNotice] = useState('');
  const [authMode, setAuthMode] = useState<'login' | 'register' | 'forgot'>('login');
  const [busy, setBusy] = useState(false);

  const loadSlots = async () => {
    const snapshots = await Promise.all([0, 1].map((week) => api<{ items: Slot[] }>(`/slots/snapshot?week_offset=${week}`)));
    setSlots(snapshots.flatMap((item) => item.items));
  };

  useEffect(() => {
    api<User>('/auth/me').then(async (me) => { setCsrf(csrfCookie()); setUser(me); await loadSlots(); setStep('slots'); }).catch(() => undefined);
  }, []);

  // SSE 实时刷新（sse.md v0.1 / architecture §5）：订阅 slot.changed，按 resource_version 收敛；
  // 断线或 resync 回退到快照拉取（§5.7 降级路径与稳态一致）。
  const loadSlotsRef = useRef(loadSlots);
  loadSlotsRef.current = loadSlots;
  useEffect(() => {
    const source = new EventSource('/slots/events');
    const onChanged = (event: MessageEvent) => {
      try {
        const incoming = (JSON.parse(event.data) as { slot?: Slot }).slot;
        if (!incoming) return;
        setSlots((prev) => prev.map((slot) => (slot.id === incoming.id && incoming.resource_version > slot.resource_version ? { ...slot, ...incoming } : slot)));
      } catch { /* 忽略畸形帧 */ }
    };
    const onResync = () => { loadSlotsRef.current().catch(() => undefined); };
    source.addEventListener('slot.changed', onChanged as EventListener);
    source.addEventListener('resync.required', onResync as EventListener);
    source.onerror = () => { loadSlotsRef.current().catch(() => undefined); };
    return () => source.close();
  }, [setSlots]);

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

  const register = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setBusy(true); setError(''); setNotice('');
    const data = new FormData(event.currentTarget);
    try {
      const response = await fetch('/auth/register', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', Origin: window.location.origin }, body: JSON.stringify({ email: data.get('email'), password: data.get('password') }) });
      if (!response.ok) throw new Error((await response.json()).detail || '注册失败');
      setNotice('注册申请已提交：验证邮件已发送，请查收邮箱并点击链接完成验证，再返回登录。');
      setAuthMode('login');
    } catch (reason) { setError(reason instanceof Error ? reason.message : '注册失败'); } finally { setBusy(false); }
  };

  const forgotPassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setBusy(true); setError(''); setNotice('');
    const data = new FormData(event.currentTarget);
    try {
      const response = await fetch('/auth/password-reset/request', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', Origin: window.location.origin }, body: JSON.stringify({ email: data.get('email') }) });
      if (!response.ok) throw new Error((await response.json()).detail || '发送失败');
      setNotice('重置链接已发送到你的邮箱（若账号存在）。请查收邮件操作。');
      setAuthMode('login');
    } catch (reason) { setError(reason instanceof Error ? reason.message : '发送失败'); } finally { setBusy(false); }
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
    try {
      await api('/appointments', { method: 'POST', headers: { 'X-CSRF-Token': csrf, 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ confirmation_token: preview.confirmation_token, appointment: draft }) });
      setStep('done');
      try { await loadSlots(); } catch { setError('预约已创建，但日历刷新失败；返回日历时将重试。'); }
    } catch (reason) { setError(reason instanceof Error ? reason.message : '预约失败'); } finally { setBusy(false); }
  };
  const returnToCalendar = async () => {
    setBusy(true); setError('');
    try { await loadSlots(); setSelected([]); setStep('slots'); }
    catch { setError('日历刷新失败，预约已成功保存，请重试。'); }
    finally { setBusy(false); }
  };
  const stageIndex = step === 'login' ? 0 : step === 'slots' ? 1 : 2;
  const stages = [{ icon: UserRound, title: '账号验证', detail: user ? user.email : '登录后进入选时' }, { icon: CalendarDays, title: '选择时间', detail: '连续 3 格，共 90 分钟' }, { icon: CheckCircle2, title: '确认预约', detail: '预览确认后原子提交' }];
  return <main className="workspace interview-view"><div className="workspace-heading"><div><span className="eyebrow">INTERVIEW / 03</span><h1>预约一次有准备的交流。</h1><p>登录后选择真实可用时段，填写会议信息并在三分钟内确认。</p></div><span className="placeholder-badge">真实预约流程</span></div>
    <div className="booking-steps">{stages.map((item, index) => { const Icon = item.icon; return <div className={index === stageIndex ? 'booking-step active' : 'booking-step'} key={item.title}><span className="step-icon"><Icon size={18} /></span><div><small>STEP 0{index + 1}</small><b>{item.title}</b><p>{item.detail}</p></div></div>; })}</div>
    {error && <div className="booking-error">{error}</div>}
    {step === 'login' && <section className="login-panel"><div><span className="eyebrow">{authMode === 'register' ? 'CREATE ACCOUNT' : authMode === 'forgot' ? 'RESET PASSWORD' : 'SECURE SIGN IN'}</span><h2>{authMode === 'register' ? '注册账号' : authMode === 'forgot' ? '找回密码' : '面试官登录'}</h2><p>{authMode === 'register' ? '注册后前往邮箱验证，即可预约面试。' : authMode === 'forgot' ? '输入注册邮箱，我们会发送重置链接。' : '使用已验证账号进入预约日历。'}</p></div>{notice && <div className="booking-success">{notice}</div>}{authMode === 'login' && <form onSubmit={login}><label>邮箱<input name="email" type="email" required autoComplete="email" /></label><label>密码<input name="password" type="password" required autoComplete="current-password" /></label><label className="check-row"><input name="remember" type="checkbox" /> 14 天内保持登录</label><button disabled={busy}>{busy ? '正在登录…' : '登录并查看时段'}</button><div className="auth-switch"><button type="button" className="text-command" onClick={() => { setError(''); setNotice(''); setAuthMode('register'); }}>没有账号？注册</button><button type="button" className="text-command" onClick={() => { setError(''); setNotice(''); setAuthMode('forgot'); }}>忘记密码？</button></div></form>}{authMode === 'register' && <form onSubmit={register}><label>邮箱<input name="email" type="email" required autoComplete="email" /></label><label>密码（10-72 字符）<input name="password" type="password" minLength={10} maxLength={72} required autoComplete="new-password" /></label><button disabled={busy}>{busy ? '正在注册…' : '注册并发送验证邮件'}</button><div className="auth-switch"><button type="button" className="text-command" onClick={() => { setError(''); setNotice(''); setAuthMode('login'); }}>已有账号？返回登录</button></div></form>}{authMode === 'forgot' && <form onSubmit={forgotPassword}><label>邮箱<input name="email" type="email" required autoComplete="email" /></label><button disabled={busy}>{busy ? '正在发送…' : '发送重置链接'}</button><div className="auth-switch"><button type="button" className="text-command" onClick={() => { setError(''); setNotice(''); setAuthMode('login'); }}>返回登录</button></div></form>}</section>}
    {step === 'slots' && <section className="booking-board"><div className="booking-calendar"><div className="calendar-head"><span><CalendarDays size={17} /> 未来两周可预约时间</span><span className="muted">绿色可选 · 红色不可约 · 深红色为本人预约</span></div><div className="slot-grid">{dayGroups.map(([day, items]) => <div className="slot-day" key={day}><b>{new Intl.DateTimeFormat('zh-CN', { month: 'numeric', day: 'numeric', weekday: 'short', timeZone: 'Asia/Shanghai' }).format(new Date(items[0].start_at))}</b><div>{items.map((slot) => { const ownBooking = slot.status === 'booked' && slot.ownership === 'self'; const slotLabel = ownBooking ? '已预约（本人）' : slot.status === 'booked' ? '已预约' : ''; return <button key={slot.id} className={`${slot.status} ${ownBooking ? 'own-booking' : ''} ${selected.includes(slot.id) ? 'selected' : ''}`} disabled={slot.status !== 'available'} title={slotLabel || undefined} aria-label={slotLabel ? `${new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Shanghai' }).format(new Date(slot.start_at))} ${slotLabel}` : undefined} onClick={() => choose(slot)}>{new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Shanghai' }).format(new Date(slot.start_at))}</button>; })}</div></div>)}</div></div><aside className="booking-summary"><span className="eyebrow">BOOKING SUMMARY</span><h2>预约摘要</h2><dl><div><dt>账号</dt><dd>{user?.email}</dd></div><div><dt>时长</dt><dd>90 分钟</dd></div><div><dt>时间</dt><dd>{selectedSlots[0] ? `${new Date(selectedSlots[0].start_at).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })} 起` : '尚未选择'}</dd></div></dl><button className="primary-command" disabled={selected.length !== 3} onClick={() => setStep('details')}>填写预约信息</button></aside></section>}
    {step === 'details' && <section className="details-panel"><button className="text-command" onClick={() => setStep('slots')}><ArrowLeft size={15} /> 返回选时</button><form onSubmit={submitDetails}><h2>填写会议信息</h2><div className="form-grid"><label>公司名称<input name="company_name" required maxLength={200} /></label><label>会议平台<input name="meeting_platform" defaultValue="腾讯会议" required /></label><label>会议号<input name="meeting_number" required /></label><label>联系人姓氏<input name="contact_last_name" required /></label><label>称呼<select name="contact_salutation"><option>老师</option><option>先生</option><option>女士</option></select></label><label>联系电话<input name="contact_phone" required /></label><label className="wide">备注<textarea name="notes" maxLength={2000} /></label></div><button className="primary-command" disabled={busy}>{busy ? '正在生成预览…' : '下一步：确认信息'}</button></form></section>}
    {step === 'confirm' && preview && <section className="confirm-panel"><span className="eyebrow">FINAL CHECK</span><h2>请确认预约信息</h2><p>确认链接有效至 {new Date(preview.expires_at).toLocaleTimeString('zh-CN')}，期间不预占时段。</p><dl><div><dt>公司</dt><dd>{preview.company_name}</dd></div><div><dt>收件邮箱</dt><dd>{preview.recipient_email}</dd></div><div><dt>称呼</dt><dd>{preview.salutation}</dd></div><div><dt>会议</dt><dd>{draft.meeting_platform} · {draft.meeting_number}</dd></div></dl><div className="confirm-actions"><button className="text-command" onClick={() => setStep('details')}>返回修改</button><button className="primary-command" disabled={busy} onClick={confirm}>{busy ? '正在提交…' : '确认预约'}</button></div></section>}
    {step === 'done' && <section className="success-panel"><CheckCircle2 size={34} /><h2>预约已创建</h2><p>时段已原子锁定，通知事件已进入异步处理队列。</p><button className="primary-command" disabled={busy} onClick={returnToCalendar}>{busy ? '正在刷新…' : '返回日历'}</button></section>}
  </main>;
}

function AdminView() {
  const [user, setUser] = useState<User | null>(null);
  const [csrf, setCsrf] = useState('');
  const [docs, setDocs] = useState<KnowledgeDoc[]>([]);
  const [files, setFiles] = useState<FileList | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'overview' | 'appointments' | 'qa' | 'kb'>('overview');
  const [stats, setStats] = useState<any>(null);
  const [allAppts, setAllAppts] = useState<any[]>([]);
  const [qaConvs, setQaConvs] = useState<any[]>([]);
  const [openConvId, setOpenConvId] = useState<string | null>(null);
  const [openConvMessages, setOpenConvMessages] = useState<any[]>([]);

  const loadDocs = async () => {
    const data = await api<{ items: KnowledgeDoc[] }>('/admin/knowledge-documents');
    setDocs(data.items);
  };
  const loadAdminData = async () => {
    try { const data = await api<any>('/admin/aiqa-stats'); setStats(data); } catch { /* ignore */ }
    try { const data = await api<{ items: any[] }>('/admin/appointments'); setAllAppts(data.items); } catch { /* ignore */ }
    try { const data = await api<{ items: any[] }>('/admin/conversations'); setQaConvs(data.items); } catch { /* ignore */ }
  };
  useEffect(() => {
    api<User>('/auth/me').then(async (me) => { setCsrf(csrfCookie()); setUser(me); await loadDocs(); await loadAdminData(); }).catch(() => undefined);
  }, []);

  const login = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setBusy(true); setError('');
    const data = new FormData(event.currentTarget);
    try {
      const response = await fetch('/auth/login', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', Origin: window.location.origin }, body: JSON.stringify({ email: data.get('email'), password: data.get('password'), remember_me: Boolean(data.get('remember')) }) });
      if (!response.ok) throw new Error((await response.json()).detail || '登录失败');
      setCsrf(response.headers.get('X-CSRF-Token') || csrfCookie());
      const me = await api<User>('/auth/me'); setUser(me); await loadDocs();
    } catch (reason) { setError(reason instanceof Error ? reason.message : '登录失败'); } finally { setBusy(false); }
  };

  const upload = async () => {
    if (!files || files.length === 0) return; setBusy(true); setError('');
    const form = new FormData();
    for (const file of Array.from(files)) form.append('files', file);
    try {
      const response = await fetch('/admin/knowledge-documents', { method: 'POST', credentials: 'include', headers: { 'X-CSRF-Token': csrf }, body: form });
      if (!response.ok) throw new Error((await response.json()).detail || '上传失败');
      setFiles(null);
      await loadDocs();
    } catch (reason) { setError(reason instanceof Error ? reason.message : '上传失败'); } finally { setBusy(false); }
  };

  const remove = async (id: string) => {
    setBusy(true); setError('');
    try { await api(`/admin/knowledge-documents/${id}`, { method: 'DELETE', headers: { 'X-CSRF-Token': csrf } }); await loadDocs(); } catch (reason) { setError(reason instanceof Error ? reason.message : '删除失败'); } finally { setBusy(false); }
  };

  const sizeLabel = (size: number) => size >= 1024 * 1024 ? `${(size / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(size / 1024))} KB`;
  const shortTime = (iso: string) => new Intl.DateTimeFormat('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Shanghai' }).format(new Date(iso));
  const openConv = async (id: string) => {
    setOpenConvId(id); setOpenConvMessages([]);
    try { const data = await api<{ items: any[] }>(`/admin/conversations/${id}/messages`); setOpenConvMessages(data.items); } catch { /* ignore */ }
  };
  return <main className="workspace admin-view"><div className="workspace-heading"><div><span className="eyebrow">OPERATIONS COCKPIT / ADMIN</span><h1>运营驾驶舱。</h1><p>预约全貌、AI 问答效果、所有 interviewer 的对话历史，以及知识库管理——只有 owner_admin 可访问。</p></div><span className="placeholder-badge">owner_admin</span></div>
    {error && <div className="booking-error">{error}</div>}
    {!user && <section className="login-panel"><div><span className="eyebrow">OWNER SIGN IN</span><h2>管理员登录</h2><p>使用 owner_admin 账号进入运营驾驶舱。</p></div><form onSubmit={login}><label>邮箱<input name="email" type="email" required autoComplete="email" /></label><label>密码<input name="password" type="password" required autoComplete="current-password" /></label><button disabled={busy}>{busy ? '正在登录…' : '登录并管理'}</button></form></section>}
    {user && <nav className="admin-tabs"><button className={activeTab === 'overview' ? 'active' : ''} onClick={() => setActiveTab('overview')}>效果大屏</button><button className={activeTab === 'appointments' ? 'active' : ''} onClick={() => setActiveTab('appointments')}>预约全貌 <small>({allAppts.length})</small></button><button className={activeTab === 'qa' ? 'active' : ''} onClick={() => setActiveTab('qa')}>问答历史 <small>({qaConvs.length})</small></button><button className={activeTab === 'kb' ? 'active' : ''} onClick={() => setActiveTab('kb')}>知识库 <small>({docs.length})</small></button></nav>}
    {user && activeTab === 'overview' && <section className="admin-overview">{!stats ? <p className="kb-empty">暂无统计数据。</p> : <>{<div className="dash-stats">{[
      { label: '总对话数', value: stats.totals.total_conversations, tone: 'green' },
      { label: '总消息数', value: stats.totals.total_messages, tone: 'blue' },
      { label: '活跃 interviewer', value: stats.totals.active_users, tone: 'gray' },
      { label: '拒答数', value: `${stats.totals.offtopic_messages}（${(stats.totals.offtopic_rate * 100).toFixed(1)}%）`, tone: 'gray' },
    ].map((stat) => <div className={`dash-stat ${stat.tone}`} key={stat.label}><b>{stat.value}</b><span>{stat.label}</span></div>)}</div>}{<section className="admin-panel"><span className="eyebrow">NEAR 7 DAYS</span><h3>近 7 天每日消息量</h3>{stats.recent_7d.length === 0 ? <p className="kb-empty">近 7 天无消息。</p> : <ul className="bars">{(() => { const max = Math.max(...stats.recent_7d.map((d: any) => d.message_count)); return stats.recent_7d.map((d: any) => <li key={d.day}><span className="bar-label">{d.day}</span><span className="bar-track"><span className="bar-fill" style={{ width: `${(d.message_count / max) * 100}%` }} /></span><b>{d.message_count}</b></li>); })()}</ul>}</section>}{<section className="admin-panel"><span className="eyebrow">TOP INTERVIEWERS</span><h3>对话数 Top 10</h3>{stats.by_user.length === 0 ? <p className="kb-empty">暂无数据。</p> : <ol className="admin-rank">{stats.by_user.map((row: any, i: number) => <li key={row.email}><b>#{i + 1}</b><span>{row.email}</span><small>{row.conversation_count} 个对话</small></li>)}</ol>}</section>}</>}</section>}
    {user && activeTab === 'appointments' && (
      <section className="admin-panel">
        {allAppts.length === 0 ? (
          <p className="kb-empty">暂无预约。</p>
        ) : (
          <div className="admin-table">
            <div className="admin-row head">
              <span>时间</span><span>面试官</span><span>公司</span><span>会议</span><span>状态</span>
            </div>
            {allAppts.map((item: any) => (
              <div className={`admin-row ${item.status}`} key={item.id}>
                <span>{shortTime(item.start_at)}</span>
                <span>{item.user_email}</span>
                <b>{item.company_name}</b>
                <small>{item.meeting_platform} · {item.meeting_number}</small>
                <span className={`kb-status ${item.status}`}>{item.status}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    )}
    {user && activeTab === 'qa' && (
      <section className="admin-panel">
        {qaConvs.length === 0 ? (
          <p className="kb-empty">暂无对话。</p>
        ) : (
          <div className="admin-table">
            <div className="admin-row head">
              <span>最近活动</span><span>面试官</span><span>消息数</span><span></span>
            </div>
            {qaConvs.map((c: any) => (
              <div className="admin-conv" key={c.id}>
                <div className="admin-row" onClick={() => openConv(c.id)} style={{ cursor: 'pointer' }}>
                  <span>{shortTime(c.updated_at)}</span>
                  <span>{c.user_email}</span>
                  <small>{c.message_count} 条</small>
                  <small>{openConvId === c.id ? '▼' : '▶'}</small>
                </div>
                {openConvId === c.id && (
                  <div className="admin-conv-msgs">
                    {openConvMessages.length === 0 ? (
                      <p className="kb-empty">加载中…</p>
                    ) : (
                      openConvMessages.map((m: any) => (
                        <div className={`admin-msg ${m.role} ${m.is_offtopic ? 'offtopic' : ''}`} key={m.id}>
                          <div className="admin-msg-meta">
                            <b>{m.role === 'user' ? '👤 用户' : '🤖 助手'}</b>
                            {m.is_offtopic && <span className="kb-status indexed">越界拒答</span>}
                            <small>{shortTime(m.created_at)}</small>
                          </div>
                          <pre>{m.content}</pre>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    )}
    {user && activeTab === 'kb' && <>{<section className="kb-upload"><label className="kb-file-picker"><UploadCloud size={18} /><span>{files && files.length > 0 ? `${files.length} 个文件已选择` : '选择 PDF / md / txt 文件'}</span><input type="file" accept=".pdf,.md,.txt" multiple onChange={(event) => setFiles(event.currentTarget.files)} /></label><button className="primary-command" disabled={busy || !files || files.length === 0} onClick={upload}>{busy ? '处理中…' : '上传并索引'}</button><small>支持 md/txt（文本）与 PDF（简历）· 单文件 ≤ 10MB · 同名内容自动去重</small></section>}<section className="kb-list"><div className="kb-list-head"><span className="eyebrow">DOCUMENTS</span><small>{docs.length} 份</small></div>{docs.length === 0 ? <p className="kb-empty">暂无文档，上传第一份简历或项目资料。</p> : <div className="kb-table">{docs.map((doc) => <div className="kb-row" key={doc.id}><span className={`kb-status ${doc.status}`}>{doc.status}</span><b>{doc.name}</b><small>{doc.type.toUpperCase()} · {sizeLabel(doc.size)} · {doc.parse_mode || '-'}{doc.failure_reason ? ` · ${doc.failure_reason}` : ''}</small><button aria-label={`删除 ${doc.name}`} onClick={() => remove(doc.id)} disabled={busy}><Trash2 size={15} /></button></div>)}</div>}</section></>}
  </main>;
}

function DashboardView({ user, appts, onNavigate }: { user: User | null; appts: ApptSummary[]; onNavigate: (page: Page) => void }) {
  const now = Date.now();
  const active = appts.filter((item) => item.status === 'active');
  const upcoming = active
    .filter((item) => new Date(item.start_at).getTime() > now - 3600e3 && new Date(item.start_at).getTime() < now + 7 * 86400e3)
    .sort((a, b) => a.start_at.localeCompare(b.start_at))
    .slice(0, 5);
  const dayLabel = (iso: string) => new Intl.DateTimeFormat('zh-CN', { month: 'numeric', day: 'numeric', weekday: 'short', hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Shanghai' }).format(new Date(iso));
  return <main className="workspace dashboard-view"><div className="workspace-heading"><div><span className="eyebrow">WORKSPACE / DASHBOARD</span><h1>{user ? `你好，${user.email.split('@')[0]}。` : '先认识一下我，再聊正事。'}</h1><p>{user ? '这里是你的面试安排与快捷入口概览。' : '登录后查看面试安排；也可以先看看简历与项目，或直接提问。'}</p></div>{user && <span className="placeholder-badge">{user.role === 'owner_admin' ? 'owner_admin' : 'interviewer'} · 已登录</span>}</div>
    {!user && <section className="dash-guest"><div className="dash-guest-card"><span className="eyebrow">GET STARTED</span><h2>登录你的账号</h2><p>预约面试、查看我的预约、恢复历史对话。</p><div className="dash-guest-actions"><button className="primary-command" onClick={() => onNavigate('interview')}>去预约面试</button><button className="text-command" onClick={() => onNavigate('resume')}>先看简历 →</button></div></div></section>}
    {user && <>
      <section className="dash-stats">{[
        { label: '进行中', value: active.length, tone: 'green' },
        { label: '已完成', value: appts.filter((item) => item.status === 'completed').length, tone: 'blue' },
        { label: '已取消', value: appts.filter((item) => item.status === 'cancelled').length, tone: 'gray' },
      ].map((stat) => <div className={`dash-stat ${stat.tone}`} key={stat.label}><b>{stat.value}</b><span>{stat.label}</span></div>)}</section>
      <section className="dash-upcoming"><div className="dash-sec-head"><span className="eyebrow">UPCOMING</span><button className="text-command" onClick={() => onNavigate('mine')}>全部预约 →</button></div>
        {upcoming.length === 0 ? <p className="kb-empty">未来 7 天没有已预约的面试。<button className="text-command" onClick={() => onNavigate('interview')}>去预约 →</button></p> : <div className="dash-appt-list">{upcoming.map((item) => <div className="dash-appt" key={item.id}><span className="dash-appt-time">{dayLabel(item.start_at)}</span><b>{item.company_name}</b><small>{item.meeting_platform} · {item.meeting_number} · 联系人{item.contact_salutation}</small><span className="kb-status indexed">进行中</span></div>)}</div>}
      </section>
      <section className="dash-quick"><span className="eyebrow">QUICK ACTIONS</span><div className="dash-quick-row"><button onClick={() => onNavigate('interview')}><CalendarDays size={17} /><b>预约面试</b><small>选择真实可用时段</small></button><button onClick={() => onNavigate('mine')}><CalendarCheck size={17} /><b>我的预约</b><small>改期 / 取消 / 修改信息</small></button><button onClick={() => onNavigate('resume')}><FileText size={17} /><b>简历问答</b><small>基于简历与知识库提问</small></button></div></section>
    </>}
  </main>;
}

function App() {
  const [page, setPage] = useState<Page>('dashboard');
  const [project, setProject] = useState<ProjectId>('jianli');
  const [user, setUser] = useState<User | null>(null);
  const [appts, setAppts] = useState<ApptSummary[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [urlAction, setUrlAction] = useState<{ kind: 'verify' | 'reset'; token: string } | null>(null);
  const [actionNotice, setActionNotice] = useState('');
  const [actionBusy, setActionBusy] = useState(false);

  // 邮箱验证 / 密码重置链接（M4）：/verify-email?token=…、/reset-password?token=…
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (!token) return;
    const path = window.location.pathname;
    if (path.endsWith('/verify-email')) setUrlAction({ kind: 'verify', token });
    else if (path.endsWith('/reset-password')) setUrlAction({ kind: 'reset', token });
    window.history.replaceState({}, '', window.location.pathname);
  }, []);

  const runUrlAction = async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    if (!urlAction) return;
    setActionBusy(true); setActionNotice('');
    try {
      const endpoint = urlAction.kind === 'verify' ? '/auth/verify-email' : '/auth/password-reset/confirm';
      const body: Record<string, unknown> = { token: urlAction.token };
      if (urlAction.kind === 'reset') {
        const data = new FormData(event?.currentTarget);
        body.new_password = String(data.get('new_password') || '');
      }
      const response = await fetch(endpoint, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', Origin: window.location.origin }, body: JSON.stringify(body) });
      if (!response.ok) throw new Error((await response.json()).detail || '操作失败');
      setActionNotice(urlAction.kind === 'verify' ? '邮箱已验证，请返回登录。' : '密码已重置，请用新密码登录。');
      setUrlAction(null);
    } catch (reason) { setActionNotice(reason instanceof Error ? reason.message : '操作失败'); } finally { setActionBusy(false); }
  };

  useEffect(() => {
    api<User>('/auth/me').then(async (me) => { setUser(me); const data = await api<{ items: Conversation[] }>('/conversations'); setConversations(data.items); }).catch(() => undefined);
    api<{ items: ApptSummary[] }>('/appointments').then((data) => setAppts(data.items)).catch(() => undefined);
  }, []);

  const selectConversation = (id: string) => { setConversationId(id); setPage('resume'); };
  const newConversation = () => { setConversationId(null); setPage('resume'); };
  const onConversationCreated = (id: string) => {
    setConversationId(id);
    setConversations((prev) => (prev.some((item) => item.id === id) ? prev : [{ id, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }, ...prev]));
  };
  const content = page === 'dashboard' ? <DashboardView user={user} appts={appts} onNavigate={setPage} /> : page === 'resume' ? <ResumeView onInterview={() => setPage('interview')} /> : page === 'projects' ? <ProjectView selected={project} onSelect={setProject} onInterview={() => setPage('interview')} /> : page === 'mine' ? <MyAppointmentsView onInterview={() => setPage('interview')} /> : page === 'admin' ? <AdminView /> : <InterviewView />;
  const live = page === 'resume' || page === 'projects';
  return <div className="app-shell">{urlAction && <div className="auth-overlay"><section className="login-panel"><div><span className="eyebrow">{urlAction.kind === 'verify' ? 'VERIFY EMAIL' : 'RESET PASSWORD'}</span><h2>{urlAction.kind === 'verify' ? '验证邮箱' : '设置新密码'}</h2><p>{urlAction.kind === 'verify' ? '点击确认即完成邮箱验证，然后返回登录。' : '输入新密码（10-72 字符）完成重置。'}</p></div>{actionNotice && <div className="booking-success">{actionNotice}</div>}{urlAction.kind === 'verify' ? <button className="primary-command" disabled={actionBusy} onClick={() => void runUrlAction()}>{actionBusy ? '验证中…' : '确认验证'}</button> : <form onSubmit={(event) => void runUrlAction(event)}><label>新密码<input name="new_password" type="password" minLength={10} maxLength={72} required autoComplete="new-password" /></label><button disabled={actionBusy}>{actionBusy ? '提交中…' : '重置密码'}</button></form>}</section></div>}<div className="desktop-gate"><LockKeyhole size={24} /><h2>请使用桌面端访问</h2><p>为保证简历与项目演示的三栏布局完整，1024px 以下暂不开放。</p></div><div className="desktop-app"><HistoryRail page={page} onPage={setPage} user={user} conversations={conversations} onSelectConversation={selectConversation} onNewConversation={newConversation} /><div className="main-column"><TopBar page={page} onPage={setPage} />{content}</div><ChatPanel live={live} pageKey={page === 'projects' ? 'projects' : 'resume'} projectKey={page === 'projects' ? project : undefined} conversationId={conversationId} canPersist={user !== null} onConversationCreated={onConversationCreated} /></div></div>;
}

export default App;

createRoot(document.getElementById('root')!).render(<App />);

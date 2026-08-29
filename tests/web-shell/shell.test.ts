import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(resolve(process.cwd(), 'apps/web/main.tsx'), 'utf8');
const styles = readFileSync(resolve(process.cwd(), 'apps/web/styles.css'), 'utf8');
const myAppointments = readFileSync(resolve(process.cwd(), 'apps/web/my-appointments.tsx'), 'utf8');
const appointmentCss = readFileSync(resolve(process.cwd(), 'apps/web/appointment.css'), 'utf8');
const evalReport = JSON.parse(readFileSync(resolve(process.cwd(), 'apps/web/evals/latest.json'), 'utf8'));
const qualityWorkflow = readFileSync(resolve(process.cwd(), '.github/workflows/agent-quality-gate.yml'), 'utf8');
describe('web shell acceptance surface', () => {
  it('keeps the three static destinations and evidence boundaries', () => {
    expect(source).toContain("'resume' | 'projects'");
    expect(source).toContain('<iframe className="resume-embed" src="/resume.pdf" title="简历 PDF"');
    expect(source).toContain('正在加载简历…');
    expect(source).toContain("fetch('/resume.pdf', { method: 'HEAD'");
    expect(source).toContain('简历暂时无法加载');
    expect(source).toContain('重新加载');
    expect(source).not.toContain('PDF 简历将在这里显示');
    expect(source).toContain('登录并查看时段');
    expect(source).toContain('邮箱或密码错误，请检查后重试。');
    expect(source).toContain('无法连接到登录服务，请确认本地 API 已启动后重试。');
    expect(source).toContain("page === 'mine' ? '我的预约'");
    expect(source).toContain('/slots/snapshot?week_offset=');
    expect(source).toContain('/appointment-confirmations');
    expect(source).toContain("'/appointments'");
    expect(source.indexOf("setStep('done')")).toBeLessThan(source.indexOf("try { await loadSlots(); } catch"));
    expect(source).toContain('预约已创建，但日历刷新失败');
    expect(source).toContain('AI 面试协作站');
    expect(source).toContain('Sleep AIoT Agent');
    // TASK-PAGE2-EVIDENCE-VISUAL-001: equalized evidence density and warm themes.
    expect(source).toContain("accent: 'khaki'");
    expect(source).toContain("accent: 'sun'");
    expect(source).not.toContain("accent: 'blue'");
    expect(source).not.toContain("accent: 'purple'");
    expect(source).toContain('18,720 · LAG 0');
    expect(source).toContain('MIGRATION OK · APP FAIL');
    expect(source).toContain('MILVUS · NEO4J · OLLAMA');
    expect(source).toContain('50C · P95 11.2S');
    expect(styles).toContain('.project-card.khaki');
    expect(styles).toContain('.project-card.sun');
    expect(styles).toContain('.agent-scenarios button>small{color:#53675a;font-size:14px;line-height:1.7}');
    // TASK-PAGE2-PROJECT-DEPTH-001: every project has three substantive blocks.
    expect(source).toContain('function SleepReliabilityReplay()');
    expect(source).toContain('function SleepDeliveryEvidence()');
    expect(source).toContain('function LitchiEngineeringMap()');
    expect(source).toContain('function LitchiAcceptanceEvidence()');
    expect(source).toContain('把 51 条幽灵重复追到类型边界');
    expect(source).toContain('安全、性能和上云，按证据等级拆开说');
    expect(source).toContain('一个人交付，不等于把所有责任都交给模型');
    expect(source).toContain('答辩分数之外，更值钱的是我知道数据能证明什么');
    expect(source).toContain('迁移成功 · 应用失败');
    expect(source).toContain('50C OK · 100C FAIL');
    expect(source).toContain('不能外推为跨区域生产容灾');
    expect(source).toContain('不是模型能力提升八倍');
    expect(styles).toContain('.project-depth-panel.khaki-light');
    expect(styles).toContain('.project-depth-panel.sun-light');
    expect(styles).toContain('.project-proof-panel.khaki-dark');
    expect(styles).toContain('.project-proof-panel.sun-dark');
    // TASK-PAGE2-TYPE-SCALE-001: project-wide two-step type scale increase.
    expect(styles).toContain('TASK-PAGE2-TYPE-SCALE-001');
    expect(styles).toContain('.project-view .evidence-card p{font-size:15px}');
    expect(styles).toContain('.project-view .agent-scenarios button>small{font-size:17px}');
    expect(styles).toContain('.project-view .eval-suite-grid p{font-size:13px}');
    expect(styles).toContain('.project-view .replay-flow article>p{font-size:16px}');
    expect(styles).toContain('.project-view .lane-flow article>p{font-size:15px}');
    expect(styles).toContain('.project-view .proof-grid article>p{font-size:15px}');
    expect(styles).toContain('.project-view .project-context{font-size:14px}');
    expect(source).toContain('不会发送真实请求');
    // TASK-FE-AIQA-001: ChatPanel live SSE answers (resume page), static fallback kept
    // for interview/mine (hence the old static copy assertion above still holds).
    expect(source).toContain("fetch('/answers:stream'");
    expect(source).toContain("event === 'answer.delta'");
    expect(source).toContain("event === 'answer.citations'");
    expect(source).toContain("event === 'answer.completed'");
    expect(source).toContain('answer-state grounded');
    expect(source).toContain('answer-state offtopic');
    expect(source).toContain('推荐追问');
    // TASK-WEB-FOLLOWUP-SCOPE-001: cross-project/general followups carry their own evidence scope.
    expect(source).toContain("{ question: '你适合什么样的团队和岗位？', pageKey: 'resume' }");
    expect(source).toContain("{ question: '你最有成就感的一段工程经历是哪一段？', pageKey: 'resume' }");
    expect(source).toContain("projectKey: 'litchi'");
    expect(source).toContain("projectKey: 'sleep'");
    expect(source).toContain('const requestedScope = scope ?? FOLLOWUP_POOL.find((item) => item.question === text);');
    expect(source).toContain('if (requestProjectKey) body.project_key = requestProjectKey;');
    expect(source).not.toContain('if (projectKey) body.project_key = projectKey;');
    // TASK-AGENT-TOOLS-001: visible tool-call decision chain.
    expect(source).toContain("event === 'answer.tool_calls'");
    expect(source).toContain('已检索知识库');
    expect(source).toContain('tool-chain');
    // TC-AI-010: live Agent Lab scenarios + privacy-safe structured trace timeline.
    expect(source).toContain("event === 'answer.trace'");
    expect(source).toContain('AGENT LAB / LIVE');
    expect(source).toContain('依据问答');
    expect(source).toContain('多步预约');
    expect(source).toContain('安全攻击');
    expect(source).toContain('无依据拒答');
    expect(source).toContain('仅展示服务端结构化事件，不包含模型思维链、Prompt 或敏感参数');
    // TC-AI-011: versioned evaluation evidence, honest CI state and failure boundaries.
    expect(source).toContain('EVALUATION / VERSIONED');
    expect(source).toContain('结果、门禁和失败，都留证据');
    expect(source).toContain('工作流已配置 · 待首次远端运行');
    expect(evalReport.overall).toEqual({ passed: 79, total: 79 });
    expect(evalReport.comparisons[0].label).toBe('RRF → Cross-Encoder');
    expect(source).toContain('REAL PROVIDER');
    expect(evalReport.comparisons[0]).toMatchObject({
      evidence_level: 'real_provider_component_benchmark',
      baseline: 'MRR 0.3333 · Hit@1 0/5',
      reranked: 'MRR 1.0000 · Hit@1 5/5',
    });
    expect(evalReport.cases.map((item: { category: string }) => item.category)).toContain('known_limitation');
    expect(JSON.stringify(evalReport)).not.toMatch(/answer_text|system_prompt|appointment_id|api_key/i);
    expect(qualityWorkflow).toContain('backend-agent:');
    expect(qualityWorkflow).toContain('rag-integration:');
    expect(qualityWorkflow).toContain('web-delivery:');
    expect(qualityWorkflow).toContain('tests/aiqa/test_rag_eval.py::test_rag_literal_hit_cases');
    expect(qualityWorkflow).toContain('tests/aiqa/test_rag_eval.py::test_rag_reject_cases');
    // TASK-KB-PDF-001: knowledge-base admin view + resume PDF embed.
    expect(source).toContain("'/admin/knowledge-documents'");
    expect(source).toContain('resume.pdf');
    expect(source).toContain('kb-status');
    expect(source).toContain('知识库管理');
    // TASK-FE-INTERVIEWER-001: dashboard + real conversation history.
    expect(source).toContain("'/conversations'");
    expect(source).toContain('conversation_id');
    expect(source).toContain('DashboardView');
    expect(source).toContain('工作台');
    expect(source).toContain('登录后显示历史对话');
    expect(source).toContain("'/auth/resend-verification'");
    expect(source).toContain("'/auth/logout'");
    expect(source).toContain("'app-shell no-chat'");
    expect(source).toContain('[0, 1, 2]');
    expect(source).toContain('cropBookingWindow');
    expect(source).toContain('从明天起 15 天可预约时间');
    expect(source).toContain('admin-slot-board');
    expect(source).toContain('点击任意 30 分钟格子');
    expect(myAppointments).toContain('[0, 1, 2]');
    expect(myAppointments).toContain('从明天起 15 天内');
    expect(myAppointments).toContain('预约暂时无法加载');
    expect(myAppointments).toContain('暂时无法连接预约服务');
    expect(myAppointments).toContain('!loading && !error && items.length === 0');
    expect(appointmentCss).toContain('grid-template-columns: minmax(0, 1fr) 300px');
    expect(appointmentCss).toContain('.mine-view { width: 100%; max-width: none; }');
    expect(appointmentCss).toContain('grid-template-columns: repeat(auto-fit, minmax(390px, 1fr))');
    expect(appointmentCss).toContain('.appointment-state');
    expect(appointmentCss).toContain('.admin-slot-board');
  });
});

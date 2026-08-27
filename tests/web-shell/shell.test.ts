import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(resolve(process.cwd(), 'apps/web/main.tsx'), 'utf8');
const myAppointments = readFileSync(resolve(process.cwd(), 'apps/web/my-appointments.tsx'), 'utf8');
const appointmentCss = readFileSync(resolve(process.cwd(), 'apps/web/appointment.css'), 'utf8');
const evalReport = JSON.parse(readFileSync(resolve(process.cwd(), 'apps/web/evals/latest.json'), 'utf8'));
const qualityWorkflow = readFileSync(resolve(process.cwd(), '.github/workflows/agent-quality-gate.yml'), 'utf8');
describe('web shell acceptance surface', () => {
  it('keeps the three static destinations and evidence boundaries', () => {
    expect(source).toContain("'resume' | 'projects'");
    expect(source).toContain('<iframe className="resume-embed" src="/resume.pdf" title="简历 PDF"');
    expect(source).toContain('正在加载简历…');
    expect(source).not.toContain('PDF 简历将在这里显示');
    expect(source).toContain('登录并查看时段');
    expect(source).toContain('/slots/snapshot?week_offset=');
    expect(source).toContain('/appointment-confirmations');
    expect(source).toContain("'/appointments'");
    expect(source.indexOf("setStep('done')")).toBeLessThan(source.indexOf("try { await loadSlots(); } catch"));
    expect(source).toContain('预约已创建，但日历刷新失败');
    expect(source).toContain('AI 面试协作站');
    expect(source).toContain('Sleep AIoT Agent');
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
    expect(evalReport.overall).toEqual({ passed: 73, total: 73 });
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
    expect(appointmentCss).toContain('grid-template-columns: minmax(0, 1fr) 300px');
    expect(appointmentCss).toContain('.admin-slot-board');
  });
});

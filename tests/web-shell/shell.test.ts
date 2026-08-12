import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(resolve(process.cwd(), 'apps/web/main.tsx'), 'utf8');
describe('web shell acceptance surface', () => {
  it('keeps the three static destinations and evidence boundaries', () => {
    expect(source).toContain("'resume' | 'projects'");
    expect(source).toContain('PDF 简历将在这里显示');
    expect(source).toContain('登录并查看时段');
    expect(source).toContain('/slots/snapshot?week_offset=');
    expect(source).toContain('/appointment-confirmations');
    expect(source).toContain("'/appointments'");
    expect(source.indexOf("setStep('done')")).toBeLessThan(source.indexOf("try { await loadSlots(); } catch"));
    expect(source).toContain('预约已创建，但日历刷新失败');
    expect(source).toContain('AI 面试协作站');
    expect(source).toContain('Sleep AIoT Agent');
    expect(source).toContain('不会发送真实请求');
  });
});

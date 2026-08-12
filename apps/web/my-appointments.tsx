import { FormEvent, useEffect, useMemo, useState } from 'react';
import { CalendarDays, CheckCircle2, Clock, Pencil, RotateCcw, Trash2, X } from 'lucide-react';

type ApptStatus = 'active' | 'cancelled' | 'completed';
type SlotStatus = 'available' | 'booked' | 'owner_locked' | 'unavailable';
type Slot = {
  id: string;
  start_at: string;
  end_at: string;
  status: SlotStatus;
  resource_version: number;
  ownership: 'none' | 'self' | 'other';
};
type Appointment = {
  id: string;
  slot_ids: string[];
  company_name: string;
  meeting_platform: string;
  meeting_number: string;
  contact_last_name: string;
  contact_salutation: string;
  contact_phone: string;
  notes: string | null;
  status: ApptStatus;
  version: number;
  start_at: string;
  end_at: string;
};

const shanghaiDay = (iso: string) =>
  new Intl.DateTimeFormat('en-CA', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: 'Asia/Shanghai',
  }).format(new Date(iso));

function csrfCookie(): string {
  return (
    document.cookie.split('; ').find((part) => part.startsWith('__Host-csrf='))?.split('=')[1] || ''
  );
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: 'include',
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => ({}));
    throw new Error(problem.detail || problem.title || `请求失败 (${response.status})`);
  }
  return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>);
}

const statusLabel: Record<ApptStatus, string> = {
  active: '进行中',
  cancelled: '已取消',
  completed: '已完成',
};

export function MyAppointmentsView({ onInterview }: { onInterview: () => void }) {
  const [items, setItems] = useState<Appointment[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [rescheduleId, setRescheduleId] = useState<string | null>(null);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [selected, setSelected] = useState<string[]>([]);

  const load = async () => {
    try {
      const data = await api<{ items: Appointment[] }>('/appointments');
      setItems(data.items);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '加载失败');
    }
  };

  useEffect(() => {
    load();
  }, []);

  const cancel = async (id: string) => {
    if (!window.confirm('确定取消该预约？时段将释放，并触发取消告知函。')) return;
    setBusy(true);
    setError('');
    try {
      await api(`/appointments/${id}`, {
        method: 'DELETE',
        headers: { 'X-CSRF-Token': csrfCookie(), 'Idempotency-Key': crypto.randomUUID() },
      });
      setItems((prev) => prev.map((item) => (item.id === id ? { ...item, status: 'cancelled' } : item)));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '取消失败');
    } finally {
      setBusy(false);
    }
  };

  const saveDetails = async (id: string, version: number, patch: Record<string, string | null>) => {
    setBusy(true);
    setError('');
    try {
      const updated = await api<Appointment>(`/appointments/${id}`, {
        method: 'PATCH',
        headers: { 'X-CSRF-Token': csrfCookie(), 'Idempotency-Key': crypto.randomUUID() },
        body: JSON.stringify({ version, ...patch }),
      });
      setItems((prev) => prev.map((item) => (item.id === id ? updated : item)));
      setEditId(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '保存失败');
    } finally {
      setBusy(false);
    }
  };

  const openReschedule = async (id: string) => {
    setRescheduleId(id);
    setSelected([]);
    setError('');
    try {
      const snapshots = await Promise.all(
        [0, 1].map((week) => api<{ items: Slot[] }>(`/slots/snapshot?week_offset=${week}`)),
      );
      setSlots(snapshots.flatMap((snap) => snap.items));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '加载时段失败');
    }
  };

  const choose = (slot: Slot) => {
    const ordered = slots
      .filter((item) => shanghaiDay(item.start_at) === shanghaiDay(slot.start_at))
      .sort((a, b) => a.start_at.localeCompare(b.start_at));
    const index = ordered.findIndex((item) => item.id === slot.id);
    const group = ordered.slice(index, index + 3);
    const valid =
      group.length === 3 &&
      group.every((item) => item.status === 'available') &&
      group.slice(1).every((item, offset) => item.start_at === group[offset].end_at);
    setError(valid ? '' : '请选择同一天内连续的三个绿色时段');
    setSelected(valid ? group.map((item) => item.id) : []);
  };

  const submitReschedule = async () => {
    if (!rescheduleId || selected.length !== 3) return;
    const appointment = items.find((item) => item.id === rescheduleId);
    if (!appointment) return;
    setBusy(true);
    setError('');
    try {
      const updated = await api<Appointment>(`/appointments/${rescheduleId}`, {
        method: 'PATCH',
        headers: { 'X-CSRF-Token': csrfCookie(), 'Idempotency-Key': crypto.randomUUID() },
        body: JSON.stringify({ version: appointment.version, new_slot_ids: selected }),
      });
      setItems((prev) => prev.map((item) => (item.id === rescheduleId ? updated : item)));
      setRescheduleId(null);
      setSelected([]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '改期失败');
    } finally {
      setBusy(false);
    }
  };

  const dayGroups = useMemo(
    () =>
      Object.entries(
        slots.reduce<Record<string, Slot[]>>((groups, slot) => {
          const day = shanghaiDay(slot.start_at);
          (groups[day] ||= []).push(slot);
          return groups;
        }, {}),
      ),
    [slots],
  );

  const formatTime = (iso: string) =>
    new Date(iso).toLocaleString('zh-CN', {
      month: 'numeric',
      day: 'numeric',
      weekday: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: 'Asia/Shanghai',
    });

  return (
    <main className="workspace mine-view">
      <div className="workspace-heading">
        <div>
          <span className="eyebrow">MY APPOINTMENTS / 03</span>
          <h1>我的预约</h1>
          <p>查看本人预约，可改会议信息、改期或取消。时段释放遵循不可用时段规则重新物化。</p>
        </div>
        <button className="appointment-cta" onClick={onInterview}>
          <CalendarDays size={15} /> 新建预约
        </button>
      </div>
      {error && <div className="booking-error">{error}</div>}
      {items.length === 0 && (
        <div className="empty-state">
          <CheckCircle2 size={28} />
          <p>还没有预约。去预约面试页选择时段吧。</p>
          <button className="primary-command" onClick={onInterview}>
            去预约
          </button>
        </div>
      )}
      <div className="appointment-list">
        {items.map((appointment) => (
          <section className="appointment-card" key={appointment.id}>
            <div className="card-head">
              <b>{appointment.company_name}</b>
              <span className={`status-badge ${appointment.status}`}>{statusLabel[appointment.status]}</span>
            </div>
            <dl className="card-detail">
              <div>
                <dt>时间</dt>
                <dd>
                  <Clock size={13} /> {formatTime(appointment.start_at)} 起
                </dd>
              </div>
              <div>
                <dt>会议</dt>
                <dd>
                  {appointment.meeting_platform} · {appointment.meeting_number}
                </dd>
              </div>
              <div>
                <dt>联系人</dt>
                <dd>
                  {appointment.contact_last_name} {appointment.contact_salutation} · {appointment.contact_phone}
                </dd>
              </div>
              {appointment.notes && (
                <div>
                  <dt>备注</dt>
                  <dd>{appointment.notes}</dd>
                </div>
              )}
            </dl>

            {editId === appointment.id && appointment.status === 'active' ? (
              <EditForm
                appointment={appointment}
                busy={busy}
                onCancel={() => setEditId(null)}
                onSave={(patch) => saveDetails(appointment.id, appointment.version, patch)}
              />
            ) : rescheduleId === appointment.id ? (
              <div className="reschedule-board">
                <div className="booking-calendar">
                  <div className="calendar-head">
                    <span>
                      <CalendarDays size={17} /> 选择新的连续三格（共 90 分钟）
                    </span>
                    <span className="muted">绿色可选 · 红色不可约</span>
                  </div>
                  <div className="slot-grid">
                    {dayGroups.map(([day, daySlots]) => (
                      <div className="slot-day" key={day}>
                        <b>
                          {new Intl.DateTimeFormat('zh-CN', {
                            month: 'numeric',
                            day: 'numeric',
                            weekday: 'short',
                            timeZone: 'Asia/Shanghai',
                          }).format(new Date(daySlots[0].start_at))}
                        </b>
                        <div>
                          {daySlots.map((slot) => (
                            <button
                              key={slot.id}
                              className={`${slot.status} ${selected.includes(slot.id) ? 'selected' : ''}`}
                              disabled={slot.status !== 'available'}
                              onClick={() => choose(slot)}
                            >
                              {new Intl.DateTimeFormat('zh-CN', {
                                hour: '2-digit',
                                minute: '2-digit',
                                hour12: false,
                                timeZone: 'Asia/Shanghai',
                              }).format(new Date(slot.start_at))}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="confirm-actions">
                  <button className="text-command" onClick={() => setRescheduleId(null)} disabled={busy}>
                    <X size={15} /> 取消改期
                  </button>
                  <button
                    className="primary-command"
                    disabled={busy || selected.length !== 3}
                    onClick={submitReschedule}
                  >
                    {busy ? '正在提交…' : '确认改期'}
                  </button>
                </div>
              </div>
            ) : (
              appointment.status === 'active' && (
                <div className="card-actions">
                  <button className="text-command" onClick={() => setEditId(appointment.id)} disabled={busy}>
                    <Pencil size={15} /> 改会议信息
                  </button>
                  <button className="text-command" onClick={() => openReschedule(appointment.id)} disabled={busy}>
                    <RotateCcw size={15} /> 改期
                  </button>
                  <button className="text-command danger" onClick={() => cancel(appointment.id)} disabled={busy}>
                    <Trash2 size={15} /> 取消预约
                  </button>
                </div>
              )
            )}
          </section>
        ))}
      </div>
    </main>
  );
}

function EditForm({
  appointment,
  busy,
  onCancel,
  onSave,
}: {
  appointment: Appointment;
  busy: boolean;
  onCancel: () => void;
  onSave: (patch: Record<string, string | null>) => void;
}) {
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    onSave({
      meeting_platform: String(data.get('meeting_platform')),
      meeting_number: String(data.get('meeting_number')),
      contact_last_name: String(data.get('contact_last_name')),
      contact_salutation: String(data.get('contact_salutation')),
      contact_phone: String(data.get('contact_phone')),
      notes: String(data.get('notes') || '') || null,
    });
  };
  return (
    <form className="details-panel" onSubmit={submit}>
      <button type="button" className="text-command" onClick={onCancel}>
        <X size={15} /> 返回
      </button>
      <h2>修改会议信息</h2>
      <div className="form-grid">
        <label>
          会议平台
          <input name="meeting_platform" defaultValue={appointment.meeting_platform} required />
        </label>
        <label>
          会议号
          <input name="meeting_number" defaultValue={appointment.meeting_number} required />
        </label>
        <label>
          联系人姓氏
          <input name="contact_last_name" defaultValue={appointment.contact_last_name} required />
        </label>
        <label>
          称呼
          <select name="contact_salutation" defaultValue={appointment.contact_salutation}>
            <option>老师</option>
            <option>先生</option>
            <option>女士</option>
          </select>
        </label>
        <label>
          联系电话
          <input name="contact_phone" defaultValue={appointment.contact_phone} required />
        </label>
        <label className="wide">
          备注
          <textarea name="notes" defaultValue={appointment.notes || ''} maxLength={2000} />
        </label>
      </div>
      <button className="primary-command" disabled={busy}>
        {busy ? '正在保存…' : '保存修改'}
      </button>
    </form>
  );
}

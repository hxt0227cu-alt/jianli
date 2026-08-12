"""Notification delivery (M3): consume the notification_events Outbox and send email.

Feishu channel is deferred: no Feishu credentials are configured in this environment,
so Feishu delivery is skipped with a clear log line. The email channel uses the
runtime SMTP secret only (never written to files). See TASK-M3-APPOINTMENTS.
"""

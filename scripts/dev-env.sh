#!/usr/bin/env bash
# jianli 本地开发环境（WSL bash）
#
# 用法（每个终端都要跑一次，uvicorn 与 worker 共用同一份，保证 key 一致）：
#   cd /mnt/c/Users/hxt02/Desktop/jianli
#   source scripts/dev-env.sh
#   export JIANLI_SMTP_PASSWORD='163授权码'          # 真实凭据只走运行时 export
#   export JIANLI_LLM_API_KEY='sk-...'               # DeepSeek
#   export JIANLI_LLM_EMBEDDING_API_KEY='sk-...'     # SiliconFlow
#
# 首次运行生成 apps/api/.env.local（gitignored，不进 Git）：CSRF/RATE_LIMIT/
# 字段加密 4 key/DB/Redis/允许源/SMTP host 等本地开发固定值。之后复用同一份，
# 保证 uvicorn、worker、评测多终端拿到的 FIELD_ENCRYPTION_KEYS 完全一致
# （worker 需解密 uvicorn 写入的预约密文，key 不一致会解密失败）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/apps/api/.env.local"

if [ ! -f "$ENV_FILE" ]; then
  echo "generating $ENV_FILE (first run)"
  cat > "$ENV_FILE" <<EOF
export JIANLI_CSRF_HMAC_KEY='$(python3 -c 'import secrets;print(secrets.token_urlsafe(24))')'
export JIANLI_RATE_LIMIT_HMAC_KEY='$(python3 -c 'import secrets;print(secrets.token_urlsafe(24))')'
export JIANLI_FIELD_ENCRYPTION_CURRENT_KEY_ID='k1'
export JIANLI_FIELD_ENCRYPTION_KEYS='{"k1":"$(python3 -c 'import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())')"}'
export JIANLI_COMPANY_FINGERPRINT_HMAC_KEY='$(python3 -c 'import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())')'
export JIANLI_APPOINTMENT_CONFIRMATION_HMAC_KEY='$(python3 -c 'import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())')'
export JIANLI_ALLOWED_ORIGINS='http://localhost:5173,http://127.0.0.1:5173'
export JIANLI_DATABASE_URL='postgresql+psycopg://jianli:jianli_local_only@127.0.0.1:55432/jianli_dev'
export JIANLI_REDIS_URL='redis://127.0.0.1:63790/0'
export JIANLI_KB_MIN_SCORE='0.47'
export JIANLI_SMTP_HOST='smtp.163.com'
export JIANLI_SMTP_PORT='465'
export JIANLI_SMTP_USER='[邮箱已脱敏]'
export JIANLI_SMTP_FROM='[邮箱已脱敏]'
EOF
fi

# 加载 .env.local（只设置未导出的变量，不覆盖已 export 的真实凭据）
set -a
# shellcheck disable=SC1090
# Windows editors may persist this gitignored file with CRLF. Strip the trailing
# carriage return in-memory so WSL never appends `\r` to URLs, host names or secrets.
source <(sed 's/\r$//' "$ENV_FILE")
set +a

echo "env ready: DB=${JIANLI_DATABASE_URL:-<missing>} SMTP_HOST=${JIANLI_SMTP_HOST:-<missing>} ENC=${JIANLI_FIELD_ENCRYPTION_KEYS:+set}"

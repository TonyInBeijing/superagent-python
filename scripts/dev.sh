#!/bin/bash
# 一键启动/停止前后端（本地开发用，macOS bash 3.2 兼容）。
# 用法: scripts/dev.sh start [--no-migrate] | stop | restart [--no-migrate] | status
# 端口可用环境变量覆盖: BACKEND_PORT(默认 8000)、FRONTEND_PORT(默认 5173)。
# 日志: run/logs/{backend,frontend}.log；pid: run/{backend,frontend}.pid。
set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
RUN_DIR="$ROOT/run"
LOG_DIR="$RUN_DIR/logs"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
WAIT_TIMEOUT=30   # 等待服务就绪的秒数
STOP_TIMEOUT=10   # TERM 后等待退出的秒数

log()  { printf '%s\n' "$*"; }
die()  { printf '错误: %s\n' "$*" >&2; exit 1; }

pid_file()  { printf '%s/%s.pid' "$RUN_DIR" "$1"; }
log_file()  { printf '%s/%s.log' "$LOG_DIR" "$1"; }

# 返回 0 表示记录的进程存活
alive() {
  local f pid
  f=$(pid_file "$1")
  [ -f "$f" ] || return 1
  pid=$(cat "$f" 2>/dev/null)
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

port_listening() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

http_code() {
  curl -s -o /dev/null -m 3 -w '%{http_code}' "$1" 2>/dev/null
}

check_prereqs() {
  local missing=0
  if [ ! -f "$ROOT/.env" ]; then
    log "缺少 $ROOT/.env，请先执行: cp .env.example .env  # 然后改成自己的库名/账号/密码"
    missing=1
  fi
  if [ ! -d "$ROOT/backend/.venv" ]; then
    log "缺少 backend/.venv，请先执行:"
    log "  cd backend && /opt/homebrew/bin/python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.lock"
    missing=1
  fi
  if [ ! -d "$ROOT/frontend/node_modules" ]; then
    log "缺少 frontend/node_modules，请先执行: cd frontend && npm ci"
    missing=1
  fi
  [ "$missing" -eq 0 ] || die "前置条件缺失，请先按上面的命令安装（脚本不自动安装）"
}

run_migrate() {
  log "执行数据库迁移 (alembic upgrade head) ..."
  if ! (cd "$ROOT/backend" && .venv/bin/alembic upgrade head) >&2; then
    die "迁移失败：请检查 MySQL 是否在运行、.env 的 DB_HOST/DB_PORT/账号/密码；确认可跳过时用 --no-migrate"
  fi
}

wait_backend() {
  local i=0 code
  while [ "$i" -lt "$WAIT_TIMEOUT" ]; do
    if ! alive backend; then
      log "后端进程已退出，日志末尾:"
      tail -n 30 "$(log_file backend)" >&2
      return 1
    fi
    code=$(http_code "http://127.0.0.1:$BACKEND_PORT/api/v1/health/live")
    [ "$code" = "200" ] && return 0
    i=$((i + 1)); sleep 1
  done
  log "等待后端 live 超时（${WAIT_TIMEOUT}s），日志末尾:"
  tail -n 30 "$(log_file backend)" >&2
  return 1
}

wait_frontend() {
  local i=0
  while [ "$i" -lt "$WAIT_TIMEOUT" ]; do
    if ! alive frontend; then
      log "前端进程已退出，日志末尾:"
      tail -n 30 "$(log_file frontend)" >&2
      return 1
    fi
    if [ "$(http_code "http://127.0.0.1:$FRONTEND_PORT/")" = "200" ]; then return 0; fi
    i=$((i + 1)); sleep 1
  done
  log "等待前端端口 $FRONTEND_PORT 超时（${WAIT_TIMEOUT}s），日志末尾:"
  tail -n 30 "$(log_file frontend)" >&2
  return 1
}

do_start() {
  local no_migrate="$1"
  check_prereqs
  mkdir -p "$LOG_DIR"

  local start_backend=1 start_frontend=1
  if alive backend; then
    log "后端已在运行 (pid $(cat "$(pid_file backend)"))，跳过"
    start_backend=0
  else
    rm -f "$(pid_file backend)"   # 清理残留 pid 文件
    if port_listening "$BACKEND_PORT"; then
      die "端口 $BACKEND_PORT 已被其他进程占用；请自行处理占用者，或用 BACKEND_PORT=<port> 换端口"
    fi
  fi
  if alive frontend; then
    log "前端已在运行 (pid $(cat "$(pid_file frontend)"))，跳过"
    start_frontend=0
  else
    rm -f "$(pid_file frontend)"
    if port_listening "$FRONTEND_PORT"; then
      die "端口 $FRONTEND_PORT 已被其他进程占用；请自行处理占用者，或用 FRONTEND_PORT=<port> 换端口"
    fi
  fi

  if [ "$start_backend" -eq 1 ] && [ "$no_migrate" -eq 0 ]; then
    run_migrate
  elif [ "$start_backend" -eq 1 ]; then
    log "已按 --no-migrate 跳过迁移"
  fi

  local failed=0
  if [ "$start_backend" -eq 1 ]; then
    ( cd "$ROOT/backend" && exec .venv/bin/uvicorn app.main:app \
        --host 127.0.0.1 --port "$BACKEND_PORT" ) >>"$(log_file backend)" 2>&1 &
    local bpid=$!
    disown "$bpid"
    printf '%s\n' "$bpid" >"$(pid_file backend)"
    log "后端已启动 (pid $bpid, 端口 $BACKEND_PORT)，日志: run/logs/backend.log"
  fi
  if [ "$start_frontend" -eq 1 ]; then
    # --host 127.0.0.1：新版 Node 下 localhost 会解析为 ::1，显式绑定 IPv4
    ( cd "$ROOT/frontend" && exec env \
        VITE_PORT="$FRONTEND_PORT" \
        VITE_API_PROXY_TARGET="http://127.0.0.1:$BACKEND_PORT" \
        node_modules/.bin/vite --host 127.0.0.1 ) >>"$(log_file frontend)" 2>&1 &
    local fpid=$!
    disown "$fpid"
    printf '%s\n' "$fpid" >"$(pid_file frontend)"
    log "前端已启动 (pid $fpid, 端口 $FRONTEND_PORT)，日志: run/logs/frontend.log"
  fi

  if [ "$start_backend" -eq 1 ]; then
    wait_backend || failed=1
  fi
  if [ "$start_frontend" -eq 1 ]; then
    wait_frontend || failed=1
  fi
  [ "$failed" -eq 0 ] || die "启动失败，见上面的日志末尾"

  log ""
  log "前端地址: http://127.0.0.1:$FRONTEND_PORT"
  log "后端地址: http://127.0.0.1:$BACKEND_PORT"
  local ready_code
  ready_code=$(http_code "http://127.0.0.1:$BACKEND_PORT/api/v1/health/ready")
  if [ "$ready_code" = "200" ]; then
    log "ready: 200 (数据库可用)"
  elif [ "$ready_code" = "503" ]; then
    log "ready: 503 —— 数据库不可用（不算启动失败）；检查 MySQL 与 .env 的 DB_* 配置"
  else
    log "ready: HTTP $ready_code（非预期，可 curl /api/v1/health/ready 查看）"
  fi
}

stop_one() {
  local name="$1" f pid i
  f=$(pid_file "$name")
  if [ ! -f "$f" ]; then
    log "$name 未在运行（无 pid 文件）"
    return 0
  fi
  pid=$(cat "$f" 2>/dev/null)
  if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
    log "$name 未在运行（pid 文件残留），已清理"
    rm -f "$f"
    return 0
  fi
  kill -TERM "$pid" 2>/dev/null
  i=0
  while [ "$i" -lt "$STOP_TIMEOUT" ]; do
    kill -0 "$pid" 2>/dev/null || break
    i=$((i + 1)); sleep 1
  done
  if kill -0 "$pid" 2>/dev/null; then
    log "$name (pid $pid) TERM 后 ${STOP_TIMEOUT}s 未退出，发送 KILL"
    kill -KILL "$pid" 2>/dev/null
    sleep 1
  fi
  if kill -0 "$pid" 2>/dev/null; then
    rm -f "$f"
    die "$name (pid $pid) KILL 后仍存活，请手动检查"
  fi
  rm -f "$f"
  log "$name (pid $pid) 已停止"
}

do_stop() {
  # 先停前端再停后端；只处理本脚本记录的 pid，不动 MySQL 等其他服务
  stop_one frontend
  stop_one backend
  local p
  for p in "$BACKEND_PORT" "$FRONTEND_PORT"; do
    if port_listening "$p"; then
      log "提示: 端口 $p 仍有监听（可能是其他进程，或子进程尚未退出，可稍后复查 lsof -nP -iTCP:$p -sTCP:LISTEN）"
    fi
  done
}

do_status() {
  local name code pid
  for name in backend frontend; do
    if alive "$name"; then
      pid=$(cat "$(pid_file "$name")")
      if [ "$name" = "backend" ]; then
        log "后端: 运行中 (pid $pid, 端口 $BACKEND_PORT)"
        code=$(http_code "http://127.0.0.1:$BACKEND_PORT/api/v1/health/live")
        log "  live : HTTP ${code:-无响应}"
        code=$(http_code "http://127.0.0.1:$BACKEND_PORT/api/v1/health/ready")
        log "  ready: HTTP ${code:-无响应}"
      else
        log "前端: 运行中 (pid $pid, 端口 $FRONTEND_PORT)"
        if port_listening "$FRONTEND_PORT"; then
          log "  端口 $FRONTEND_PORT 监听中"
        else
          log "  端口 $FRONTEND_PORT 未监听（可能仍在启动）"
        fi
      fi
    else
      rm -f "$(pid_file "$name")"
      if [ "$name" = "backend" ]; then
        log "后端: 未运行"
      else
        log "前端: 未运行"
      fi
    fi
  done
}

usage() {
  cat <<'EOF'
用法: scripts/dev.sh <command> [--no-migrate]

  start    [--no-migrate]   启动前后端（默认先执行 alembic upgrade head）
  stop                      停止本脚本启动的前后端进程
  restart  [--no-migrate]   stop 后 start
  status                    查看运行状态与 live/ready 结果

端口覆盖: BACKEND_PORT(默认 8000)、FRONTEND_PORT(默认 5173)。
日志: run/logs/{backend,frontend}.log；pid: run/{backend,frontend}.pid。
EOF
}

CMD="${1:-}"
FLAG="${2:-}"
case "$CMD" in
  start)
    case "$FLAG" in
      "")            do_start 0 ;;
      --no-migrate)  do_start 1 ;;
      *)             usage; die "未知参数: $FLAG" ;;
    esac
    ;;
  stop)
    do_stop
    ;;
  restart)
    do_stop
    case "$FLAG" in
      "")            do_start 0 ;;
      --no-migrate)  do_start 1 ;;
      *)             usage; die "未知参数: $FLAG" ;;
    esac
    ;;
  status)
    do_status
    ;;
  *)
    usage
    exit 1
    ;;
esac

# superagent-python

SuperAgent Python 版（05 节：控制面初始化）。链路：浏览器 → 前端（Vite / Nginx，相对路径 `/api`）→ FastAPI → MySQL。
当前只有健康检查和页面外壳；不含账号、Chat、Task、Agent。

## 技术与版本（与执行文档的差异）

| 项 | 文档要求 | 本次实际 |
| --- | --- | --- |
| Python 依赖管理 | uv | venv + pip + pip-tools（`pip-compile` 生成 `backend/requirements.lock`） |
| MySQL | 8.0 | 本机验证用 Homebrew MySQL 9.6.0；Compose 文件写的是 `mysql:8.0`（未验证） |
| Node | 22 | 本机验证用 v26.13.0 / npm 11；Dockerfile 写 node:22（未验证） |

## 本地开发

前置：Python 3.12（`brew install python@3.12`）、Node、MySQL。

```bash
cp .env.example .env        # 然后改成自己的库名/账号/密码；.env 已被 .gitignore 忽略
```

端口：`.env.example` 按 Compose 场景写 `DB_PORT=3307`。使用本机已有 MySQL 时改为 `DB_PORT=3306`，并自行创建专用库和账号（不要使用 root，不要影响其他库）。后端和 Alembic 都从仓库根目录读 `.env`，与启动目录无关；环境变量优先于 `.env`。

### 一键启动/停止

前置同上（`.env`、`backend/.venv`、`frontend/node_modules` 需已存在，脚本只检查并提示安装命令，不自动安装）：

```bash
scripts/dev.sh start                # 默认先执行 alembic upgrade head，再后台拉起后端(8000)和前端(5173)
scripts/dev.sh start --no-migrate   # 跳过迁移
scripts/dev.sh status               # 查看运行状态与 live/ready 结果
scripts/dev.sh restart              # stop 后 start（支持 --no-migrate）
scripts/dev.sh stop                 # 只停本脚本启动的进程，不动 MySQL
```

- 可从任意工作目录执行；已在运行的服务会被跳过，不重复启动；端口被其他进程占用时报错退出，不会杀占用者。
- 端口覆盖：`BACKEND_PORT`（默认 8000）、`FRONTEND_PORT`（默认 5173，经 `VITE_PORT` 传给 Vite，并自动把 `VITE_API_PROXY_TARGET` 指向后端端口）。例：`BACKEND_PORT=8001 FRONTEND_PORT=5174 scripts/dev.sh start`。
- 日志：`run/logs/backend.log`、`run/logs/frontend.log`；pid：`run/backend.pid`、`run/frontend.pid`（`run/` 已被 `.gitignore` 忽略）。启动失败或等待超时会打印日志末尾。
- 迁移失败会报错退出：检查 MySQL 与 `.env`，或确认无需迁移时用 `--no-migrate`。`ready` 返回 503 只提示数据库不可用，不算启动失败。

下面的手动步骤保留，供单独调试某一端时使用。

### 后端

```bash
cd backend
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.lock
.venv/bin/alembic upgrade head                 # 迁移（与应用启动分开，需手动执行）
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

更新依赖锁文件（修改 `pyproject.toml` 后）：

```bash
cd backend
.venv/bin/pip-compile --strip-extras -o requirements.lock pyproject.toml
.venv/bin/pip-compile --strip-extras --extra dev -o requirements-dev.lock pyproject.toml
```

### 测试

测试固定使用测试库 `superagent_test`（需已存在且 `.env` 中的账号对其有权限），不依赖模型。

```bash
cd backend && .venv/bin/python -m pytest -q
```

### 前端

```bash
cd frontend
npm ci
npm run dev          # 默认 http://127.0.0.1:5173，/api 代理到 VITE_API_PROXY_TARGET（默认 http://127.0.0.1:8000）
npm run build
```

### 检查

```bash
curl -i http://127.0.0.1:5173/api/v1/health/live
curl -i http://127.0.0.1:5173/api/v1/health/ready
```

数据库不可用时后端仍能启动：live 返回 200，ready 返回 503（`DEPENDENCY_UNAVAILABLE`）。ready 只检查连接和轻量查询，不检查迁移是否完成。

## Docker Compose（未验证）

以下文件只按文档编写，**没有构建、运行或测试过**（编写时 Docker 守护进程未运行）：`docker-compose.yml`、`backend/Dockerfile`、`frontend/Dockerfile`、`frontend/nginx.conf`。使用前请自行验证。

```bash
cp .env.example .env
docker compose up -d mysql                                # 等 healthcheck 变为 healthy：docker compose ps
docker compose run --rm backend alembic upgrade head      # 单独执行一次迁移
docker compose up -d --build backend frontend
docker compose logs -f backend
# 访问 http://localhost:8080
```

容器内后端使用 `DB_HOST=mysql`、`DB_PORT=3306`；MySQL 仅映射到 `127.0.0.1:3307`。

## 停止服务与删除数据

- 停止（保留数据）：`docker compose stop` 或 `docker compose down`。
- **删除数据**（不可恢复，不是普通重启步骤）：`docker compose down -v` 会删除命名卷 `mysql_data`。
- 本地进程用 Ctrl-C 停止，不影响数据库数据。

## 排错

- `ready` 返回 503：检查 MySQL 是否在监听、`.env` 的 `DB_PORT`/账号/密码、账号对库的权限。日志不会输出密码或连接串。
- 迁移报连接错误：同上；确认库已创建。
- 端口 3307 被占用：修改 `docker-compose.yml` 映射和 `.env`，不要停止占用端口的其他服务。
- 前端请求 `/api` 失败：确认后端已启动，必要时设置 `VITE_API_PROXY_TARGET`。

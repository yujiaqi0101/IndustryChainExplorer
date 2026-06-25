# 启动脚本

前后端启动脚本，支持 bash（Git Bash / WSL / macOS / Linux）和 Windows CMD。

## 脚本一览

| 脚本 | 作用 | 默认端口 |
|------|------|---------|
| `start_backend.sh` / `.bat` | 启动后端（FastAPI + Uvicorn） | 8000 |
| `start_frontend.sh` / `.bat` | 启动前端（Streamlit） | 8501 |
| `dev.sh` / `.bat` | 一键启动前后端（开发模式） | 8000 + 8501 |

## Python 探测顺序

脚本自动按以下顺序找 Python 解释器：

1. 项目本地 `.venv/Scripts/python.exe`
2. 隔离 venv `C:\Users\AAA\.workbuddy\binaries\python\envs\default\Scripts\python.exe`
3. 系统 `python`（PATH）

## 用法

### bash（Git Bash / WSL）

```bash
# 只起后端
bash scripts/start_backend.sh

# 只起前端
bash scripts/start_frontend.sh

# 一键起前后端（后端后台，前端前台，Ctrl+C 同停）
bash scripts/dev.sh

# 自定义端口
bash scripts/start_backend.sh 9000
bash scripts/start_frontend.sh 8600

# 环境变量自定义端口
BACKEND_PORT=9000 FRONTEND_PORT=8600 bash scripts/dev.sh
```

### Windows CMD

```cmd
:: 只起后端
scripts\start_backend.bat

:: 只起前端
scripts\start_frontend.bat

:: 一键起前后端（关闭窗口同停）
scripts\dev.bat

:: 自定义端口
scripts\start_backend.bat 9000
scripts\start_frontend.bat 8600
```

## 访问地址

- 后端 API：http://127.0.0.1:8000
- 后端文档（Swagger）：http://127.0.0.1:8000/docs
- 前端 UI：http://localhost:8501

## 依赖

首次运行需安装依赖（已声明在 `requirements.txt`）：

```bash
pip install -r requirements.txt
```

核心依赖：`fastapi`、`uvicorn[standard]`、`streamlit`、`pydantic`、`networkx`、`pyyaml`。

## 停止

- 单独启动：`Ctrl+C`
- `dev.sh`：`Ctrl+C`（trap 自动杀后台后端）
- `dev.bat`：关闭 CMD 窗口（自动杀后端子窗口）

## 架构说明

当前前后端基于 **v5 Layered Value Chain 架构**（`api/app.py` + `ui/streamlit/app.py` + `chains/`）。

新 M1 架构（`src/` + `packages/`）的 API/UI 尚未迁移（M2 范围）。CLI 已可用：

```bash
python -m src.cli.app validate
python -m src.cli.app search dsp
python -m src.cli.app show dsp
```

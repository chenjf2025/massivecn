# 国内股票行情多源聚合网关

个人量化数据指挥中心，支持实时行情获取、历史数据回测与可视化分析。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                         │
├─────────────┬─────────────────────┬───────────────────────┤
│   Frontend  │       Backend       │      TDengine         │
│  (Vue 3 +   │    (FastAPI +       │   (时序数据库)        │
│   ECharts)  │     异步网关)        │                       │
│   :3000     │      :8000          │      :6030            │
└─────────────┴─────────────────────┴───────────────────────┘
```

## 快速开始

### 1. 环境要求

- Docker & Docker Compose
- Python 3.10+ (本地开发)
- Node.js 18+ (本地开发前端)

### 2. 一键启动

```bash
# 克隆后进入目录
cd MassiveCN

# 启动所有服务 (首次启动自动构建镜像)
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端管理后台 | http://localhost:3000 | Vue 3 + Element Plus |
| 后端 API | http://localhost:8000 | FastAPI |
| API 文档 | http://localhost:8000/docs | Swagger |
| TDengine REST | http://localhost:6030 | 数据查询 |

## 核心功能

### 实时行情 API

```bash
# 获取单只股票行情
curl -X POST http://localhost:8000/api/v1/quote \
  -H "Content-Type: application/json" \
  -d '{"symbol": "sh600000"}'

# 批量获取
curl -X POST "http://localhost:8000/api/v1/quote/batch?symbols=sh600000&symbols=sh601318"
```

### 历史数据查询

```bash
# 获取 K 线数据
curl "http://localhost:8000/api/v1/history/sh600000?interval=5min&aggregation=5"
```

### 配置管理

```bash
# 获取当前配置
curl http://localhost:8000/api/v1/config

# 更新配置 (热生效)
curl -X PUT http://localhost:8000/api/v1/config \
  -H "Content-Type: application/json" \
  -d '{"sources": {"primary": [{"name": "eastmoney", "enabled": true}]}}'
```

## 前端功能

1. **仪表盘** - 系统状态、数据源监控、快速查询
2. **配置管理** - 动态调整数据源优先级、超时参数
3. **数据看板** - K 线图 + VWAP 均价 + 成交量 + 主力资金流向

## 本地开发

### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
# 或
uvicorn main:app --reload
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产
npm run build
```

## 数据源

| 名称 | 类型 | 说明 |
|------|------|------|
| eastmoney | 主源 | 东方财富 (推荐) |
| tencent | 备源 | 腾讯财经 |
| sina | 备源 | 新浪财经 |

## 技术栈

- **后端**: Python 3.10, FastAPI, aiohttp, TDengine 3.x
- **前端**: Vue 3, Vite, Element Plus, ECharts
- **数据库**: TDengine (时序数据库)
- **部署**: Docker Compose (ARM64/x86_64)

## 项目结构

```
.
├── docker-compose.yml      # 容器编排
├── config.yaml              # 网关配置
├── backend/
│   ├── main.py             # FastAPI 主程序
│   ├── config_manager.py   # 配置管理器
│   ├── models.py           # Pydantic 模型
│   ├── database.py         # TDengine 连接池
│   ├── parsers/            # 数据源解析器
│   │   ├── base.py
│   │   ├── eastmoney.py
│   │   └── tencent.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── views/          # 页面组件
    │   │   ├── Dashboard.vue
    │   │   ├── ConfigManager.vue
    │   │   └── DataViewer.vue  # K线图组件
    │   ├── api/           # API 服务
    │   └── router/        # 路由配置
    ├── package.json
    └── nginx.conf
```

## 注意事项

1. 首次启动需要等待 TDengine 初始化完成
2. 前端默认代理 API 到 `localhost:8000`
3. 生产环境修改 `config.yaml` 中的数据源配置
4. Apple Silicon (M1/M2) 和 Ubuntu x86_64 均可运行

# 舆情监控与汇总系统

一个基于 AI 的财经新闻舆情监控与分析系统，支持自动化爬取、智能评分和可视化展示。

## 功能特性

- **自动化爬取**: 使用 Selenium + ChromeDriver 自动抓取同花顺财经电报新闻
- **AI 智能分析**: 接入 DeepSeek 大模型进行新闻重要性评分、增量信息识别、预期差分析
- **综合评分**: 多维度评分算法，综合考虑重要性、增量属性、预期差等因素
- **智能分类**: 自动将新闻分为紧急、重点关注、一般参考、已处理噪音四个等级
- **可视化展示**: 现代化的 Web 界面，实时展示新闻列表、统计数据、分布图表

## 技术栈

### 后端
- FastAPI - 高性能 API 框架
- SQLAlchemy - ORM
- PostgreSQL - 数据库
- Redis - 缓存和消息队列
- Selenium - 网页爬取
- DeepSeek API - AI 分析

### 前端
- Vue 3 - 渐进式 JavaScript 框架
- TypeScript - 类型安全
- Element Plus - UI 组件库
- ECharts - 数据可视化
- Pinia - 状态管理

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Chrome/Chromium

### 1. 克隆项目

```bash
cd sentiment_monitor
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 DeepSeek API Key
```

### 3. 启动基础设施

```bash
docker-compose up -d db redis
```

### 4. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 6. 访问系统

打开浏览器访问 http://localhost:3000

## 使用 Docker Compose 完整部署

```bash
# 设置 DeepSeek API Key
export DEEPSEEK_API_KEY=your_api_key

# 启动所有服务
docker-compose up -d
```

## API 文档

启动后端后，访问 http://localhost:8000/docs 查看完整的 API 文档。

### 主要接口

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/news | 获取新闻列表 |
| GET | /api/news/{id} | 获取新闻详情 |
| POST | /api/news/scrape | 触发爬虫 |
| POST | /api/news/analyze/{id} | 分析单条新闻 |
| POST | /api/news/analyze-all | 批量分析 |
| GET | /api/news/stats/summary | 获取统计 |

## 项目结构

```
sentiment_monitor/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # 配置
│   │   ├── database.py      # 数据库连接
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic 模型
│   │   ├── routers/         # API 路由
│   │   ├── services/        # 业务服务
│   │   └── tasks/           # Celery 任务
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── api/             # API 调用
│   │   ├── components/      # Vue 组件
│   │   └── stores/          # Pinia 状态
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 配置说明

### DeepSeek API

系统需要 DeepSeek API Key 来进行 AI 分析。请在 https://platform.deepseek.com/ 注册并获取 API Key。

### 评分权重

综合评分公式:

```
综合分数 = 重要性分数 × 0.4
         + 增量系数 × 30
         + 预期差系数 × 20
         + 市场敏感度 × 10
```

可在 `backend/app/config.py` 中修改权重配置。

## License

MIT

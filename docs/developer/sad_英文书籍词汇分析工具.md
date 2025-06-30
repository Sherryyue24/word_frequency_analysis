# 软件架构设计文档 (SAD)

## 1. 分层架构概览

```text
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  接口层 (Interface) │ ──> │  服务层 (Service) │ ──> │  核心层 (Core)     │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

- **接口层**：CLI、API、Web（三阶段演进）。
- **服务层**：分析服务、词汇服务、导出服务、配置服务。
- **核心层**：文本处理引擎、词汇管理引擎、数据存储与缓存。


## 2. 模块划分

### 2.1 核心业务层 (Core Layer)
```
core/
├── engines/            # 文本处理引擎
│   ├── reader.py       # 文件读取器 (.txt/.pdf/.epub)
│   ├── preprocessor.py # 文本清洗、标准化
│   ├── tokenizer.py    # 分词与词频分析器
│   └── cache.py        # 缓存管理器
│
├── vocab/              # 词汇管理引擎
│   ├── database.py     # 词形变化、标签系统
│   ├── importer.py     # 词表导入器
│   ├── nlp.py          # 词性标注、词形还原
│   └── relations.py    # 同义词/派生词分析
│
└── storage/            # 数据存储层
    ├── models.py       # ORM 模型
    ├── sqlite.py       # 本地 SQLite 存储
    ├── postgres.py     # PostgreSQL 存储
    └── redis.py        # 缓存与队列
```

### 2.2 服务层 (Service Layer)
```
services/
├── analysis_service.py  # 单文件/批量/历史分析
├── vocab_service.py     # 词汇查询、标签及统计
├── export_service.py    # 报告生成、可视化、格式转换
└── config_service.py    # 用户偏好、分析参数管理
```

### 2.3 接口层 (Interface Layer)
```
interfaces/
├── cli/                 # Click + Rich CLI 工具
├── api/                 # FastAPI + Celery 异步
└── web/                 # Vue.js 前端 (后续)
```


## 3. 数据流与存储设计

1. **原始输入**：用户上传文件 → reader → preprocessor → tokenizer → 中间数据
2. **处理过程**：核心模块生成词频、匹配结果 → 缓存（Redis）
3. **持久化**：SQLite/PostgreSQL 存储日志、用户词库等结构化数据
4. **导出层**：export_service 输出 CSV/JSON 或通过 API 返回


## 4. 安全与扩展

- **安全**：文件扫描、防路径遍历；API 层 JWT 认证、限流
- **扩展**：异步任务 (Celery + Redis)；微服务拆分；插件化架构
- **部署**：Docker + Kubernetes；CI/CD (GitHub Actions)
- **监控**：Prometheus + Grafana


## 5. 技术栈概览

```
后端: Python 3.9+, Click, Rich, FastAPI, Celery, Redis
NLP: spaCy, NLTK, flashtext
存储: SQLite/PostgreSQL, Redis
数据: Pandas, NumPy
配置: PyYAML, Pydantic
可视化: Matplotlib, Seaborn

前端 (后续): Vue3, TypeScript, Element Plus, ECharts

运维: Docker, Kubernetes, GitHub Actions, Prometheus, Grafana
```  


## 6. 目录结构

```text
word-frequency-analysis/
├── config/              # 配置文件
├── core/                # 核心业务逻辑
├── services/            # 服务层
├── interfaces/          # 接口层
├── data/                # 原始数据、缓存、导出
├── tests/               # 各类测试
├── docs/                # SRS, SAD, API, 用户手册
├── scripts/             # 辅助脚本
├── deployment/          # 部署配置
└── requirements.txt     # 依赖列表
```

---




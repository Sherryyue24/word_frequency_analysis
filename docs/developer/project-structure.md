# 项目结构说明文档
# 路径: docs/developer/project-structure.md
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

## 📋 项目概述

本文档详细说明了词频分析系统的项目结构，特别是核心engines模块的三层架构设计。

### 最后更新
- **时间**: 2025-06-30
- **版本**: v1.0.0
- **重构**: engines模块三层架构完成

## 🏗️ 整体项目结构

```
word-frequency-analysis/
├── README.md                      # 项目说明
├── run.py                         # 统一启动脚本
├── setup.py                       # 项目安装配置
├── config/                        # 配置管理
│   ├── default.yaml              # 默认配置
│   ├── development.yaml          # 开发环境配置
│   └── production.yaml           # 生产环境配置
├── core/                          # 核心模块
│   ├── __init__.py
│   ├── engines/                   # 🔥 核心引擎模块（三层架构）
│   ├── models/                    # 数据模型
│   ├── services/                  # 业务服务
│   └── utils/                     # 工具函数
├── interfaces/                    # 用户接口层
│   ├── api/                       # REST API接口
│   ├── cli/                       # 命令行接口
│   └── web/                       # Web接口（未来）
├── data/                          # 数据存储
│   ├── files/                     # 文件管理
│   ├── databases/                 # 数据库文件
│   ├── cache/                     # 缓存文件
│   └── exports/                   # 导出结果
├── scripts/                       # 维护脚本
├── docs/                          # 项目文档
├── tests/                         # 测试代码
└── deployment/                    # 部署配置
```

## 🚀 核心Engines模块架构

### 架构理念

engines模块采用**三层功能架构**，按照数据流向和职责分离：

```
core/engines/
├── input/       🔽 输入处理层：文件处理、词汇表导入
├── vocabulary/  🔄 词汇处理层：词汇分析、语言学处理  
└── database/    💾 数据持久层：数据存储、检索管理
```

### 详细模块结构

#### 🔽 Input 输入处理模块

**职责**: 处理所有输入数据，包括文本文件和词汇表文件

```
core/engines/input/
├── __init__.py                    # 模块统一导出
├── file_processor.py              # 文件处理器
│   ├── TextProcessor             # 文本文件批量处理
│   ├── FileProcessor             # 单文件处理（别名）
│   └── 功能：缓存检查、文件移动、进度显示
├── file_reader.py                 # 文件阅读器
│   ├── TextReader                # 多格式文件读取
│   ├── 支持格式：PDF、TXT、DOCX、HTML等
│   └── 功能：文本预处理、编码检测、元数据提取
└── modern_wordlist_import.py      # 现代化词汇表导入
    ├── import_wordlist_from_file()   # 单个词汇表导入
    ├── import_multiple_wordlists()  # 批量导入
    ├── get_available_wordlists()    # 列出已导入词汇表
    ├── get_wordlist_stats()         # 词汇表统计
    └── import_wordlist_to_database() # 向后兼容接口
```

**核心功能**:
- 支持多种文本格式解析
- 智能词汇表导入与验证
- 重复内容检测（SHA256）
- 详细的导入报告生成
- 文件状态管理（new → processed）

#### 🔄 Vocabulary 词汇处理模块

**职责**: 词汇分析、语言学处理、词频统计

```
core/engines/vocabulary/
├── __init__.py                    # 模块统一导出
└── word_analyzer.py               # 词汇分析器
    ├── analyze_text()            # 主分析函数
    ├── 功能：词频统计、词汇提取
    ├── 语言学处理：词干提取、词性分析
    └── 统计信息：总词数、唯一词数、元数据
```

**核心功能**:
- 智能词汇提取与清理
- 词频统计与分析
- 语言学特征提取
- 性能优化的批量处理

#### 💾 Database 数据持久层模块

**职责**: 数据存储、检索、数据库管理

```
core/engines/database/
├── __init__.py                    # 模块统一导出
├── unified_database.py            # 统一数据库核心
│   ├── UnifiedDatabase           # 现代化数据库类
│   ├── UUID-based设计           # 现代化架构
│   ├── 关联查询支持             # 复杂分析功能
│   └── 高级功能：TF-IDF、相似度分析
└── database_adapter.py            # 兼容性适配器
    ├── UnifiedDatabaseAdapter    # 统一适配器类
    ├── unified_adapter          # 全局适配器实例
    ├── 向后兼容接口             # 兼容旧API
    └── 无缝迁移支持             # 平滑过渡
```

**核心功能**:
- 现代化数据库设计（UUID、JSON字段）
- 强大的关联查询能力
- 高级分析功能（相似度、TF-IDF）
- 完全向后兼容
- 事务处理与数据完整性

### 模块间协作

#### 数据流向
```
输入文件 → Input模块 → Vocabulary模块 → Database模块 → 用户接口
    ↓         ↓            ↓            ↓
  文件读取   文本分析    词频统计     数据存储
  格式转换   词汇提取    语言学处理   关联查询
  内容校验   质量评估    统计计算     高级分析
```

#### 依赖关系
```python
# Input模块依赖
from ..vocabulary.word_analyzer import analyze_text      # 词汇分析
from ..database.database_adapter import unified_adapter  # 数据存储

# Vocabulary模块依赖
from ..input.file_reader import TextReader              # 文件读取工具

# Database模块依赖
from .unified_database import UnifiedDatabase           # 核心数据库
```

## 📦 导入使用方式

### 新的模块化导入

```python
# 按功能模块导入
from core.engines import input, vocabulary, database

# 使用输入处理功能
from core.engines.input import FileProcessor, import_wordlist_from_file

# 使用词汇分析功能  
from core.engines.vocabulary import analyze_text

# 使用数据库功能
from core.engines.database import unified_adapter, UnifiedDatabase
```

### 向后兼容导入

```python
# 仍然支持旧的导入方式
from core.engines import (
    FileProcessor,           # 文件处理器
    unified_adapter,         # 数据库适配器
    analyze_text,           # 词汇分析
    import_wordlist_from_file # 词汇表导入
)
```

### CLI模块导入

```python
# CLI中的典型使用
from core.engines.input.modern_wordlist_import import import_wordlist_from_file
from core.engines.database.database_adapter import unified_adapter
```

## 🔧 配置管理

### 配置文件层次

```yaml
# config/default.yaml - 基础配置
database:
  path: "data/databases/unified.db"
  
processing:
  supported_formats: ["pdf", "txt", "docx"]
  
# config/development.yaml - 开发配置
database:
  path: "data/databases/dev_unified.db"
  debug: true

# config/production.yaml - 生产配置  
database:
  path: "data/databases/prod_unified.db"
  optimization: true
```

### 配置使用

```python
from core.utils.config_manager import ConfigManager

config = ConfigManager()
db_path = config.get('database.path')
formats = config.get('processing.supported_formats')
```

## 🎯 架构优势

### 1. 模块化设计
- **职责分离**: 每个模块专注特定功能
- **低耦合**: 模块间依赖清晰可控
- **高内聚**: 相关功能集中管理

### 2. 扩展性强
- **功能扩展**: 在对应模块添加新功能
- **格式支持**: 在input模块添加新格式
- **分析算法**: 在vocabulary模块添加新算法
- **存储后端**: 在database模块支持新数据库

### 3. 维护友好
- **代码组织**: 按功能清晰分组
- **测试策略**: 模块化单元测试
- **调试便利**: 问题定位准确

### 4. 向后兼容
- **API保持**: 所有原有接口不变
- **渐进迁移**: 支持逐步采用新架构
- **无缝升级**: 用户无感知切换

## 📚 相关文档

- `unified-architecture-migration.md` - 数据库架构迁移详情
- `cli-refactor.md` - CLI模块重构说明
- `data-structure.md` - 数据存储结构说明
- `api/` - API接口文档（未来）

## 🚀 未来规划

### 短期目标
1. **Web接口**: 在 `interfaces/web/` 开发Web管理界面
2. **API服务**: 在 `interfaces/api/` 提供RESTful API
3. **性能优化**: 进一步优化各模块性能

### 长期目标
1. **机器学习集成**: 在vocabulary模块集成ML算法
2. **分布式支持**: 在database模块支持分布式存储
3. **实时处理**: 支持流式数据处理
4. **可视化分析**: 丰富的数据可视化功能

这种三层架构设计为系统提供了清晰的结构、强大的扩展性和优秀的维护性，是现代软件架构的最佳实践。 
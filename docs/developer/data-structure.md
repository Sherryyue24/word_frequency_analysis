# Data目录结构说明

## 🎯 设计理念

data目录采用**统一输入管理**的设计理念，所有用户输入的文件（文本文件、词汇表文件等）都按照处理状态进行分类管理，通过程序逻辑而非目录结构来区分文件类型和处理方式。

## 🗂️ 目录结构

```
data/
├── 📁 files/               # 📂 统一文件管理
│   ├── 📁 new/             # 🆕 待处理文件 (文本+词汇表)
│   ├── 📁 processed/       # ✅ 已处理文件归档
│   └── 📁 samples/         # 🧪 示例测试文件
├── 📁 databases/           # 🗃️ 数据库集中存储
│   └── 📄 unified.db       # 🌟 统一数据库 (现代化架构)
├── 📁 cache/              # 💾 临时缓存 (空)
└── 📁 exports/            # 📤 导出结果 (空)
```

## 🔄 统一数据流

```
用户输入 → files/new/ → [智能处理引擎] → databases/ → files/processed/
                              ↓
                        根据文件类型选择处理方式:
                        • 文本文件 → 词频分析 → unified.db (documents + words + occurrences)
                        • 词汇表 → 词汇导入 → unified.db (wordlists + memberships)
```

## 📋 目录功能详解

### 📂 files/ - 统一文件生命周期管理

| 目录 | 功能 | 包含文件类型 | 处理状态 |
|------|------|-------------|----------|
| `new/` | 待处理队列 | 📚 文本文件 + 📝 词汇表文件 | 🔄 未处理 |
| `processed/` | 已处理归档 | 📚 已分析文本 + 📝 已导入词汇表 | ✅ 已完成 |
| `samples/` | 测试样本 | 🧪 示例文件 | 🔬 测试用 |

**当前files/new/内容示例：**
```
📚 文本文件:
- A to Z Mysteries系列PDF (英文儿童读物)
- story.txt, story2.txt (测试文本)

📝 词汇表文件:
- IELTS_Word_List.txt (雅思词汇 3,707词)
- GRE_8000_Words.txt (GRE词汇 7,744词) 
- CET_4+6_edited.txt (四六级词汇 8,028词)
- allWords.xlsx (综合词汇表)
- 柯林斯词频-5星至0星.xlsx (词频数据)
- 英语专业四八级词汇表.docx (专业词汇)
```

### 🗃️ databases/ - 统一数据库架构

```
databases/
└── unified.db      # 🌟 现代化统一数据库 (UUID-based)
    ├── 📄 documents (文档管理)
    │   ├── 文档元数据 (filename, content_hash, file_size)
    │   ├── 处理状态 (status, processed_at)
    │   └── JSON字段 (metadata, 灵活扩展)
    ├── 🔤 words (统一词汇表)
    │   ├── 表面形式 (surface_form: "running")
    │   ├── 词根形式 (lemma: "run")
    │   └── 语言学特征 (linguistic_features)
    ├── 📊 occurrences (词频关联)
    │   ├── 文档-词汇关联 (document_id + word_id)
    │   ├── 频率统计 (frequency, tf_score)
    │   └── 位置信息 (positions JSON)
    ├── 📚 wordlists (词汇表管理)
    │   ├── 词汇表信息 (IELTS/GRE/CET等)
    │   ├── 版本管理 (version, source_file)
    │   └── 统计信息 (word_count)
    └── 🔗 word_wordlist_memberships (关联表)
        ├── 词汇-词汇表关联
        ├── 置信度评分 (confidence)
        └── 来源元数据 (source_metadata)
```

### 🔧 工具目录

| 目录 | 用途 | 当前状态 |
|------|------|----------|
| `cache/` | 处理过程临时文件 | 空 |
| `exports/` | 导出结果存储 | 空 |

## 🎯 设计优势

### 1. **统一输入管理**
- 所有输入文件都进入 `files/new/`
- 程序智能识别文件类型并选择处理方式
- 处理完成后统一归档到 `files/processed/`

### 2. **清晰的状态管理**
```
输入阶段 → 处理阶段 → 存储阶段 → 归档阶段
new/      程序处理    databases/   processed/
```

### 3. **简化的目录结构**
- 减少目录层级，避免功能重复
- 通过代码逻辑而非目录区分文件类型
- 更容易理解和维护

### 4. **灵活的处理方式**
```python
# 智能文件处理伪代码
for file in files/new/:
    if is_vocabulary_file(file):
        import_to_vocabulary_db(file)
    elif is_text_file(file):
        analyze_and_store(file)
    
    # 处理完成后移动到processed/
    move_to_processed(file)
```

## 💡 使用场景

### 📝 处理词汇表
```bash
# 1. 放入词汇表文件
cp my_wordlist.txt data/files/new/

# 2. 运行词汇导入
python run.py vocab import-words data/files/new/my_wordlist.txt

# 3. 文件自动归档到processed/
```

### 📚 分析文本
```bash  
# 1. 放入文本文件
cp my_document.pdf data/files/new/

# 2. 运行文本分析
python run.py text process -i data/files/new/

# 3. 文件自动归档到processed/
```

## 🔮 扩展性

这种设计支持未来功能扩展：
- **新文件类型** - 只需添加识别和处理逻辑
- **批量处理** - 可以批量处理new/目录下所有文件
- **处理历史** - processed/目录保留完整处理历史
- **工作流自动化** - 可以实现监控new/目录的自动处理

## 🎉 总结

这种**统一输入、智能处理、分类存储**的设计更加简洁和高效：
- 用户只需关心一个入口：`files/new/`
- 系统智能处理不同类型文件
- 结果存储在相应数据库中
- 原文件归档便于追溯

这是一个更符合用户直觉的设计！

---

## 🔗 与Engines模块的协作

### 三层架构配合

data目录结构与核心engines模块的**三层架构**紧密配合：

```
🔽 Input层 (core/engines/input/)
    ↓ 处理 files/new/ 中的所有文件
    ├── file_processor.py      → 文本文件批量处理
    ├── file_reader.py         → 多格式文件读取  
    └── modern_wordlist_import.py → 词汇表文件导入

🔄 Vocabulary层 (core/engines/vocabulary/)
    ↓ 对文本进行词汇分析
    └── word_analyzer.py       → 词频统计、语言学处理

💾 Database层 (core/engines/database/)
    ↓ 存储到 databases/unified.db
    ├── unified_database.py    → 现代化数据库操作
    └── database_adapter.py    → 向后兼容接口
```

### 数据处理流程

#### 文本文件处理流程
```
1. 用户文件 → data/files/new/document.pdf
2. Input层读取 → file_reader.py 解析PDF
3. Vocabulary层分析 → word_analyzer.py 提取词频
4. Database层存储 → unified_database.py 保存到unified.db
5. 文件归档 → data/files/processed/document.pdf
```

#### 词汇表导入流程
```
1. 词汇表文件 → data/files/new/IELTS_words.txt
2. Input层导入 → modern_wordlist_import.py 解析词汇
3. Database层存储 → 创建wordlist记录和word关联
4. 文件归档 → data/files/processed/IELTS_words.txt
```

### 模块职责分工

| 层级 | 负责的data操作 | 具体功能 |
|------|---------------|----------|
| **Input层** | `files/new/` → `files/processed/` | 文件读取、格式转换、状态管理 |
| **Vocabulary层** | 内存中词汇处理 | 词汇提取、频率计算、语言学分析 |
| **Database层** | `databases/unified.db` | 数据持久化、关联查询、统计分析 |

### 配置集成

engines模块通过配置系统与data目录协作：

```yaml
# config/default.yaml
database:
  path: "data/databases/unified.db"

processing:
  input_directory: "data/files/new"
  processed_directory: "data/files/processed"
  supported_formats: ["pdf", "txt", "docx", "xlsx"]

export:
  output_directory: "data/exports"
```

### 错误恢复机制

- **处理失败的文件**: 保留在 `files/new/` 等待重试
- **数据库事务**: 使用SQLite事务保证数据一致性
- **备份机制**: `databases/backup/` 保存历史版本
- **日志记录**: 详细记录处理过程和错误信息

### 性能优化

#### 缓存策略
```
data/cache/
├── content_hashes/    # 文件内容哈希缓存
├── word_frequencies/  # 词频计算缓存  
└── analysis_results/  # 分析结果缓存
```

#### 批量处理
```python
# engines模块支持批量处理data目录
from core.engines.input import FileProcessor

processor = FileProcessor()
processor.process_new_texts("data/files/new")  # 批量处理所有文件
```

### 扩展性支持

这种架构支持未来功能扩展：

1. **新输入格式**: 在Input层添加新的reader支持
2. **高级分析**: 在Vocabulary层添加ML算法
3. **多数据库**: Database层支持分布式存储
4. **实时监控**: 监控 `files/new/` 目录自动处理新文件

### 最佳实践

#### 开发新功能时
```python
# 1. Input层处理 - 添加新格式支持
def read_new_format(file_path):
    # 读取新格式文件
    return content

# 2. Vocabulary层分析 - 添加新分析功能  
def advanced_analysis(text):
    # 高级词汇分析
    return analysis_result

# 3. Database层存储 - 扩展数据模型
def store_advanced_result(analysis):
    # 存储高级分析结果
    pass
```

这种**三层架构 + 统一数据管理**的设计实现了：
- 📁 清晰的数据流向
- 🔧 模块化的功能分离  
- 🚀 强大的扩展能力
- 🛡️ 可靠的错误处理

为系统的长期发展奠定了坚实基础！ 
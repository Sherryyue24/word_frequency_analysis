# 📚 词频分析工具 Word Frequency Analysis

> 一个专业的英文文本词频分析和词汇管理工具，集成语言学分析功能  
> **当前版本**: v1.0 MVP ✅ (已完成80%核心功能)  
> **下一版本**: v2.0 个性化学习支持 🔄 (规划中)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-MVP%20Complete-success.svg)](README.md)

---

## 🎯 项目概述

专为**研究者**、**英语学习者**和**内容分析师**设计的综合性文本分析工具。提供从基础词频统计到高级语言学分析的完整解决方案。

### ✨ 核心特性

🔤 **文本处理引擎**
- 多格式支持: TXT、PDF、DOCX
- 批量文档处理
- 智能分词与预处理


📊 **语言学分析** 
- **词性标注**: 35种英语词性 (NN, VBG, JJ, RB等)
- **形态学分析**: 前缀后缀识别 (un-, re-, -ing, -ly等)  
- **词汇复杂度**: simple/prefixed/suffixed/complex分类
- **上下文分析**: 提高标注准确性

📚 **词汇管理系统**
- **自定义词表**: 支持导入词表
- **词汇存储**: 统一数据库管理
- **精细化查询**: 多维度词汇检索
- **变形分析**: 词根-变形关系追踪

---

## 🚀 快速开始

### 环境要求
```bash
Python 3.9+
```

### 安装依赖
```bash
# 克隆项目
git clone https://github.com/Sherryyue24/word_frequency_analysis.git
cd word_frequency_analysis

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# 安装依赖
pip install click rich PyYAML python-docx PyPDF2 nltk
```

### 初始化系统
```bash
# 下载NLTK数据 (首次运行)
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"

# 查看系统状态
python run.py config show
```

---

## 💡 使用指南

### 📁 1. 文本处理
```bash
# 处理新文本文件
python run.py text process

# 查看处理历史  
python run.py text history --limit 5

# 导出分析结果
python run.py text export --format excel --output analysis_report.xlsx
python run.py text export --format csv --output word_frequencies.csv
```

### 🔍 2. 词汇查询与分析
```bash
# 基础词汇查询
python run.py vocab info apple

# 语言学特征查询 (新功能)
python run.py vocab pos disappeared
# 输出: 📝 词汇: disappeared
#       🏷️ 词性: VBD (动词过去式)  
#       🔧 形态: complex (前缀dis- + 后缀-ed)

# 词性统计分析
python run.py vocab by-pos --type VB    # 查询所有动词
python run.py vocab by-pos              # 显示词性分布

# 形态学分析
python run.py vocab morphology          # 形态学统计报告
```

### 📚 3. 词表管理
```bash
# 查看已导入词表
python run.py wordlist status

# 导入新词表
python run.py wordlist import data/wordlists/new/custom_list.txt

# 词表统计分析
python run.py wordlist stats --wordlist CET4
python run.py wordlist coverage         # 整体覆盖度分析
```

### ⚙️ 4. 系统管理
```bash
# 查看配置
python run.py config show

# 系统重置 (level 1-3)
python run.py config reset --level 1    # 清空缓存
python run.py config reset --level 2    # 重置处理状态
python run.py config reset --level 3    # 完全重置

# 数据库统计
python run.py config stats
```

---


## 🏗️ 项目架构

### 📁 目录结构
```
word-frequency-analysis/
├── 📁 config/                  # 配置管理
├── 📁 core/                    # 核心业务逻辑  
│   ├── engines/               # 处理引擎
│   │   ├── database/          # 统一数据库引擎
│   │   ├── input/             # 文件处理引擎
│   │   └── vocabulary/        # 词汇分析引擎
│   ├── models/                # 数据模型
│   ├── services/              # 业务服务
│   └── utils/                 # 工具库
├── 📁 interfaces/              # 接口层
│   ├── cli/                   # 命令行接口 ✅
│   ├── api/                   # REST API (v3.0)
│   └── web/                   # Web界面 (v3.0)
├── 📁 data/                    # 数据存储
│   ├── databases/             # SQLite数据库
│   ├── files/                 # 文本文件存储
│   ├── wordlists/             # 词汇表管理
│   ├── cache/                 # 缓存文件
│   └── exports/               # 导出报告
├── 📁 docs/                    # 项目文档
├── 📁 scripts/                 # 维护脚本
└── 📁 tests/                   # 测试套件
```

### 🔧 技术栈
```
核心语言: Python 3.9+
数据库: SQLite + JSON (语言学特征)
CLI框架: Click + Rich
文本处理: NLTK + PyPDF2 + python-docx
语言学分析: NLTK POS Tagging
```

---

## 📖 命令参考

### 🔤 text - 文本处理
```bash
python run.py text process              # 处理新文件
python run.py text history [--limit N]  # 查看处理历史
python run.py text export [--format]    # 导出分析结果
```

### 🔍 vocab - 词汇查询
```bash
python run.py vocab info <word>         # 基础词汇信息
python run.py vocab pos <word>          # 语言学特征
python run.py vocab by-pos [--type]     # 词性查询
python run.py vocab morphology          # 形态学分析 
```

### 📚 wordlist - 词表管理  
```bash
python run.py wordlist status           # 词表状态
python run.py wordlist import <file>    # 导入词表
python run.py wordlist stats [--wordlist] # 词表统计
python run.py wordlist coverage         # 覆盖度分析
```

### ⚙️ config - 系统配置
```bash
python run.py config show               # 显示配置
python run.py config reset [--level]    # 系统重置
python run.py config stats              # 系统统计
```

---

## 🔮 版本规划

### ✅ v1.0 MVP (已完成) 
**核心功能**: 文本处理 + 词汇管理 + 语言学分析
- [x] 统一SQLite数据库架构
- [x] 完整CLI命令行工具  
- [x] 多格式文件处理 (TXT/PDF/DOCX)
- [x] 语言学分析 (词性标注、形态学)
- [x] 精细化词汇查询系统
- [x] 多格式报告导出

### 🔄 v2.0 个性化学习
**核心功能**: 个人词表管理 + 智能难度评估  
- [ ] **FR8 个人词表管理**: 掌握状态追踪 (Mastered/Learning/Unknown/Review)
- [ ] **FR4 难度评估算法**: 基于个人掌握度的智能评估
- [ ] **学习建议系统**: 个性化阅读材料推荐
- [ ] **FR10 EPUB支持**: 电子书格式处理
- [ ] **进度可视化**: 学习历史和统计图表

### 🚀 v3.0 服务化架构 
**核心功能**: API服务 + Web界面
- [ ] RESTful API服务 (FastAPI)
- [ ] 现代化Web界面 (Vue.js 3)
- [ ] 多用户支持和权限管理  
- [ ] 实时数据可视化
- [ ] 移动端适配

---



## 🤝 社区与支持

### 问题反馈
- 🐛 [Bug Reports](https://github.com/Sherryyue24/word_frequency_analysis/issues)
- 💡 [Feature Requests](https://github.com/Sherryyue24/word_frequency_analysis/discussions)  

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 👨‍💻 作者信息

**项目维护者**: Sherryyue  
**项目地址**: [GitHub Repository](https://github.com/Sherryyue24/word_frequency_analysis)  
**创建时间**: 2025年  

---

<div align="center">

**🌟 如果这个项目对您有帮助，请考虑给它一个Star！🌟**

*使用 `python run.py --help` 开始您的词汇分析之旅！*

</div>


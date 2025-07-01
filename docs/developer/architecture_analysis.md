# Word表词性分离架构分析

## 🎯 **核心问题**
当前架构不一致：
- **字典表**：支持多词性 `(word, pos_primary)` 
- **words表**：无词性字段，只有 `(surface_form, lemma)`

## 📋 **解决方案对比**

### **方案A：为words表添加词性字段**
```sql
ALTER TABLE words ADD COLUMN pos_primary TEXT;
CREATE UNIQUE INDEX idx_words_unique ON words(surface_form, lemma, pos_primary);
```

**优势：**
- 架构一致，与字典表对应
- 精确匹配：`run`动词 vs `run`名词
- 更准确的难度评估和学习状态管理

**挑战：**
- 需要实现词性标注（POS tagging）
- 需要迁移现有14,469条词汇记录
- 文本处理性能会略有下降

### **方案B：保持现状，关联时处理**
```sql
-- 保持words表不变
-- 在查询时通过frequency_rank选择最佳词性匹配
```

**优势：**
- 无需修改现有架构
- 性能开销最小

**劣势：**
- 匹配不够精确
- 难以区分同词不同词性的学习状态

### **方案C：创建word_instances表**
```sql
-- words表作为抽象词汇
-- word_instances表记录具体词性实例
CREATE TABLE word_instances (
    word_id TEXT,
    pos_primary TEXT,
    confidence REAL,
    FOREIGN KEY (word_id) REFERENCES words(id)
);
```

**优势：**
- 最灵活的设计
- 支持词性置信度

**劣势：**
- 架构复杂度增加
- 查询性能开销

## 🛠️ **推荐实施方案A**

### **实施步骤：**

1. **添加词性字段**
2. **实现词性标注**（使用spaCy或NLTK）
3. **迁移现有数据**（批量词性标注）
4. **更新查询逻辑**
5. **重建索引**

### **代码示例：**
```python
# 文本处理时的词性标注
import spacy
nlp = spacy.load("en_core_web_sm")

def analyze_text_with_pos(text):
    doc = nlp(text)
    for token in doc:
        surface_form = token.text.lower()
        lemma = token.lemma_.lower()
        pos = token.pos_  # NOUN/VERB/ADJ/etc
```

## 🎯 **用户决策点**
1. 是否实施词性分离？
2. 如果是，选择哪个方案？
3. 是否立即迁移，还是仅对新数据启用？ 
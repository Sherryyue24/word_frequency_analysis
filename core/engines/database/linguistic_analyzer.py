# 语言学分析模块
# 路径: core/engines/database/linguistic_analyzer.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

"""
语言学分析模块 - 负责词性标注和语言学特征提取

该模块提供：
- 词性标注 (POS tagging)
- 词汇形态学分析
- 语言学特征提取和存储
"""

import json
from typing import Dict, List, Optional, Tuple
import re

# NLTK相关导入
try:
    import nltk
    from nltk import pos_tag, word_tokenize
    from nltk.corpus import wordnet
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("⚠️  NLTK不可用，词性标注功能将被禁用")

class LinguisticAnalyzer:
    """语言学分析器 - 提供词性标注和语言学特征提取"""
    
    def __init__(self):
        self.pos_mappings = {
            # 名词类
            'NN': {'type': 'noun', 'subtype': 'singular', 'description': '名词(单数)'},
            'NNS': {'type': 'noun', 'subtype': 'plural', 'description': '名词(复数)'},
            'NNP': {'type': 'noun', 'subtype': 'proper_singular', 'description': '专有名词(单数)'},
            'NNPS': {'type': 'noun', 'subtype': 'proper_plural', 'description': '专有名词(复数)'},
            
            # 动词类
            'VB': {'type': 'verb', 'subtype': 'base', 'description': '动词原形'},
            'VBD': {'type': 'verb', 'subtype': 'past', 'description': '动词过去式'},
            'VBG': {'type': 'verb', 'subtype': 'gerund', 'description': '动名词/现在分词'},
            'VBN': {'type': 'verb', 'subtype': 'past_participle', 'description': '过去分词'},
            'VBP': {'type': 'verb', 'subtype': 'present', 'description': '动词现在时(非三单)'},
            'VBZ': {'type': 'verb', 'subtype': 'present_3rd', 'description': '动词现在时(三单)'},
            
            # 形容词类
            'JJ': {'type': 'adjective', 'subtype': 'base', 'description': '形容词'},
            'JJR': {'type': 'adjective', 'subtype': 'comparative', 'description': '形容词比较级'},
            'JJS': {'type': 'adjective', 'subtype': 'superlative', 'description': '形容词最高级'},
            
            # 副词类
            'RB': {'type': 'adverb', 'subtype': 'base', 'description': '副词'},
            'RBR': {'type': 'adverb', 'subtype': 'comparative', 'description': '副词比较级'},
            'RBS': {'type': 'adverb', 'subtype': 'superlative', 'description': '副词最高级'},
            
            # 代词类
            'PRP': {'type': 'pronoun', 'subtype': 'personal', 'description': '人称代词'},
            'PRP$': {'type': 'pronoun', 'subtype': 'possessive', 'description': '物主代词'},
            'WP': {'type': 'pronoun', 'subtype': 'wh', 'description': '疑问代词'},
            'WP$': {'type': 'pronoun', 'subtype': 'wh_possessive', 'description': '疑问物主代词'},
            
            # 限定词/冠词
            'DT': {'type': 'determiner', 'subtype': 'base', 'description': '限定词'},
            'PDT': {'type': 'determiner', 'subtype': 'predeterminer', 'description': '前置限定词'},
            'WDT': {'type': 'determiner', 'subtype': 'wh', 'description': '疑问限定词'},
            
            # 介词
            'IN': {'type': 'preposition', 'subtype': 'base', 'description': '介词/从属连词'},
            'TO': {'type': 'preposition', 'subtype': 'to', 'description': '介词to'},
            
            # 连词
            'CC': {'type': 'conjunction', 'subtype': 'coordinating', 'description': '并列连词'},
            
            # 数词
            'CD': {'type': 'numeral', 'subtype': 'cardinal', 'description': '基数词'},
            
            # 感叹词
            'UH': {'type': 'interjection', 'subtype': 'base', 'description': '感叹词'},
            
            # 其他
            'MD': {'type': 'modal', 'subtype': 'base', 'description': '情态动词'},
            'SYM': {'type': 'symbol', 'subtype': 'base', 'description': '符号'},
            'FW': {'type': 'foreign', 'subtype': 'base', 'description': '外语词'},
            'LS': {'type': 'list_marker', 'subtype': 'base', 'description': '列表标记'},
            'RP': {'type': 'particle', 'subtype': 'base', 'description': '小品词'},
        }
    
    def analyze_word(self, word: str, context: List[str] = None) -> Dict:
        """
        分析单个词汇的语言学特征
        
        Args:
            word: 要分析的词汇
            context: 上下文词汇列表，有助于提高标注准确性
            
        Returns:
            包含语言学特征的字典
        """
        if not NLTK_AVAILABLE:
            return self._fallback_analysis(word)
        
        try:
            # 词性标注
            if context:
                # 使用上下文进行更准确的标注
                text = ' '.join(context)
                tokens = word_tokenize(text.lower())
                pos_tags = pos_tag(tokens)
                
                # 找到目标词汇的标注
                word_lower = word.lower()
                pos_tag_result = None
                for token, tag in pos_tags:
                    if token == word_lower:
                        pos_tag_result = tag
                        break
            else:
                # 单词标注
                pos_tags = pos_tag([word.lower()])
                pos_tag_result = pos_tags[0][1]
            
            # 构建语言学特征
            features = self._build_features(word, pos_tag_result)
            
            # 添加形态学分析
            morphology = self._analyze_morphology(word, pos_tag_result)
            features.update(morphology)
            
            return features
            
        except Exception as e:
            print(f"⚠️  词性分析失败 {word}: {e}")
            return self._fallback_analysis(word)
    
    def _build_features(self, word: str, pos_tag: str) -> Dict:
        """根据词性标注构建特征字典"""
        pos_info = self.pos_mappings.get(pos_tag, {
            'type': 'unknown',
            'subtype': 'unknown',
            'description': f'未知类型({pos_tag})'
        })
        
        features = {
            'pos_tag': pos_tag,
            'pos_type': pos_info['type'],
            'pos_subtype': pos_info['subtype'],
            'pos_description': pos_info['description'],
            'word_length': len(word),
            'has_prefix': self._detect_prefix(word),
            'has_suffix': self._detect_suffix(word),
            'capitalized': word[0].isupper() if word else False,
            'all_caps': word.isupper() if word else False,
        }
        
        return features
    
    def _analyze_morphology(self, word: str, pos_tag: str) -> Dict:
        """形态学分析 - 检测词缀、词根等"""
        morphology = {
            'morphology': {
                'prefix': None,
                'suffix': None,
                'root_length': len(word),
                'complexity': 'simple'
            }
        }
        
        # 前缀检测
        common_prefixes = ['un', 're', 'pre', 'dis', 'mis', 'over', 'under', 'out']
        for prefix in common_prefixes:
            if word.lower().startswith(prefix) and len(word) > len(prefix) + 2:
                morphology['morphology']['prefix'] = prefix
                morphology['morphology']['root_length'] = len(word) - len(prefix)
                morphology['morphology']['complexity'] = 'prefixed'
                break
        
        # 后缀检测
        common_suffixes = {
            'ing': 'progressive/gerund',
            'ed': 'past/past_participle', 
            'er': 'comparative/agent',
            'est': 'superlative',
            'ly': 'adverbial',
            'tion': 'nominalization',
            'sion': 'nominalization',
            'ness': 'nominalization',
            'ment': 'nominalization',
            'ful': 'adjectival',
            'less': 'adjectival',
            's': 'plural/3rd_person',
            'es': 'plural/3rd_person'
        }
        
        for suffix, meaning in common_suffixes.items():
            if word.lower().endswith(suffix) and len(word) > len(suffix) + 2:
                morphology['morphology']['suffix'] = suffix
                morphology['morphology']['suffix_meaning'] = meaning
                if morphology['morphology']['prefix']:
                    morphology['morphology']['complexity'] = 'complex'
                else:
                    morphology['morphology']['complexity'] = 'suffixed'
                break
        
        return morphology
    
    def _detect_prefix(self, word: str) -> bool:
        """检测是否有常见前缀"""
        prefixes = ['un', 're', 'pre', 'dis', 'mis', 'over', 'under', 'out', 'in', 'im']
        return any(word.lower().startswith(p) and len(word) > len(p) + 2 for p in prefixes)
    
    def _detect_suffix(self, word: str) -> bool:
        """检测是否有常见后缀"""
        suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'ness', 'ment', 'ful', 'less']
        return any(word.lower().endswith(s) and len(word) > len(s) + 2 for s in suffixes)
    
    def _fallback_analysis(self, word: str) -> Dict:
        """备用分析方法，当NLTK不可用时使用"""
        return {
            'pos_tag': 'UNKNOWN',
            'pos_type': 'unknown',
            'pos_subtype': 'unknown',
            'pos_description': '无法分析(NLTK不可用)',
            'word_length': len(word),
            'has_prefix': self._detect_prefix(word),
            'has_suffix': self._detect_suffix(word),
            'capitalized': word[0].isupper() if word else False,
            'all_caps': word.isupper() if word else False,
            'morphology': {
                'complexity': 'simple'
            }
        }
    
    def batch_analyze(self, words: List[str], context_text: str = None) -> Dict[str, Dict]:
        """批量分析词汇的语言学特征"""
        results = {}
        
        if context_text and NLTK_AVAILABLE:
            # 使用上下文进行整体分析
            try:
                tokens = word_tokenize(context_text.lower())
                pos_tags = pos_tag(tokens)
                tag_dict = dict(pos_tags)
                
                for word in words:
                    word_lower = word.lower()
                    pos_tag_result = tag_dict.get(word_lower, 'NN')  # 默认为名词
                    results[word] = self._build_features(word, pos_tag_result)
                    
                    # 添加形态学分析
                    morphology = self._analyze_morphology(word, pos_tag_result)
                    results[word].update(morphology)
                    
            except Exception as e:
                print(f"⚠️  批量分析失败，使用单词分析: {e}")
                for word in words:
                    results[word] = self.analyze_word(word)
        else:
            # 逐个分析
            for word in words:
                results[word] = self.analyze_word(word)
        
        return results
    
    def get_pos_statistics(self, features_list: List[Dict]) -> Dict:
        """统计词性分布"""
        pos_counts = {}
        type_counts = {}
        
        for features in features_list:
            pos_tag = features.get('pos_tag', 'UNKNOWN')
            pos_type = features.get('pos_type', 'unknown')
            
            pos_counts[pos_tag] = pos_counts.get(pos_tag, 0) + 1
            type_counts[pos_type] = type_counts.get(pos_type, 0) + 1
        
        return {
            'total_words': len(features_list),
            'pos_tag_distribution': pos_counts,
            'pos_type_distribution': type_counts,
            'most_common_pos': max(pos_counts.items(), key=lambda x: x[1]) if pos_counts else None,
            'most_common_type': max(type_counts.items(), key=lambda x: x[1]) if type_counts else None
        }

# 创建全局实例
linguistic_analyzer = LinguisticAnalyzer() 
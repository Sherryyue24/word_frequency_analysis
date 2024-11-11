# src/core/reader.py
import os
from pathlib import Path
from typing import List, Dict, Union, Optional
import chardet
import pandas as pd
import docx
import PyPDF2
import re

class TextReader:
    """文本读取器类，支持多种格式的文本读取和预处理"""
    
    def __init__(self):
        self.supported_formats = {
            '.txt': self._read_txt,
            '.pdf': self._read_pdf,
            '.docx': self._read_docx,
            '.csv': self._read_csv,
        }
        # 存储最近读取的文本
        self.current_text = ""
        # 存储文本的元数据
        self.metadata = {}

    def read_file(self, file_path: Union[str, Path], **kwargs) -> str:
        """
        读取文件主方法
        
        Args:
            file_path: 文件路径
            **kwargs: 额外的读取参数
        
        Returns:
            str: 处理后的文本内容
        
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}")
            
        self.current_text = self.supported_formats[file_extension](file_path, **kwargs)
        self.metadata['file_name'] = file_path.name
        self.metadata['file_size'] = os.path.getsize(file_path)
        
        return self.current_text

    def _read_txt(self, file_path: Path, encoding: Optional[str] = None) -> str:
        """
        读取txt文件，自动检测编码
        """
        if encoding is None:
            # 自动检测文件编码
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']

        with open(file_path, 'r', encoding=encoding) as file:
            return file.read()

    def _read_pdf(self, file_path: Path) -> str:
        """
        读取PDF文件
        """
        text = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text.append(page.extract_text())
        return '\n'.join(text)

    def _read_docx(self, file_path: Path) -> str:
        """
        读取Word文档
        """
        doc = docx.Document(file_path)
        return '\n'.join([paragraph.text for paragraph in doc.paragraphs])

    def _read_csv(self, file_path: Path, text_column: str = 'text') -> str:
        """
        读取CSV文件中的文本列
        """
        df = pd.read_csv(file_path)
        if text_column not in df.columns:
            raise ValueError(f"Column '{text_column}' not found in CSV file")
        return '\n'.join(df[text_column].astype(str).tolist())

    def preprocess_text(self, text: Optional[str] = None) -> str:
        """
        文本预处理方法
        
        Args:
            text: 要处理的文本，如果为None则处理当前文本
            
        Returns:
            str: 处理后的文本
        """
        if text is None:
            text = self.current_text

        # 基础文本清理
        text = text.lower()  # 转换为小写
        text = re.sub(r'\s+', ' ', text)  # 统一空白字符
        text = text.strip()  # 去除首尾空白

        return text

    def get_word_list(self, text: Optional[str] = None, 
                      min_length: int = 1) -> List[str]:
        """
        将文本转换为词列表
        
        Args:
            text: 要处理的文本，如果为None则使用当前文本
            min_length: 最小词长度
            
        Returns:
            List[str]: 词列表
        """
        if text is None:
            text = self.current_text
            
        # 使用正则表达式分词
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 过滤短词
        words = [word for word in words if len(word) >= min_length]
        
        return words

    def get_metadata(self) -> Dict:
        """
        获取文本元数据
        """
        self.metadata['word_count'] = len(self.get_word_list())
        self.metadata['char_count'] = len(self.current_text)
        return self.metadata
import os
import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.reader import TextReader

def test_txt_reader():
    reader = TextReader()
    test_file = Path("tests/test_data/test.txt")
    
    # 创建测试文件
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Hello World!")
    
    # 测试读取
    text = reader.read_file(test_file)
    assert text == "Hello World!"
    
    # 测试预处理
    processed_text = reader.preprocess_text(text)
    assert processed_text == "hello world!"
    
    # 测试词列表
    words = reader.get_word_list(text)
    assert words == ["hello", "world"]
    
    # 清理测试文件
    test_file.unlink()

def test_unsupported_format():
    reader = TextReader()
    
    # 创建一个临时的不支持格式的文件
    test_file = Path("tests/test_data/test.unsupported")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Some content")
    
    try:
        # 测试不支持的文件格式
        with pytest.raises(ValueError):
            reader.read_file(test_file)
    finally:
        # 清理测试文件
        test_file.unlink()
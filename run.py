#!/usr/bin/env python3
# 项目启动脚本
# 路径: run.py
# 项目名: Word Frequency Analysis
# 作者: Sherryyue

"""
词频分析工具主启动脚本 v1.0.0

使用说明:
    python run.py [CLI参数]
    
示例:
    python run.py --help                               # 显示帮助
    python run.py text process -i ./data/files         # 处理文本文件
    python run.py vocab query hello                    # 查询单词
    python run.py config-cmd show                      # 显示配置
"""

import sys
from pathlib import Path

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入CLI主程序
from interfaces.cli.main import main

if __name__ == "__main__":
    # 启动CLI
    main() 
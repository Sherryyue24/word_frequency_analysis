# 项目安装脚本
# 路径: setup.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

from setuptools import setup, find_packages
import os

# 读取README文件
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取requirements文件，过滤注释和空行
def parse_requirements():
    requirements = []
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-r"):
                    requirements.append(line)
    except FileNotFoundError:
        print("Warning: requirements.txt not found")
    return requirements

setup(
    name="word-frequency-analysis",
    version="1.0.0",
    author="Sherryyue",
    author_email="sherryyue24@example.com",
    description="专业的英文文本词频分析和词汇管理工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Sherryyue24/word_frequency_analysis",
    
    packages=find_packages(),
    include_package_data=True,
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Natural Language :: Chinese (Simplified)",
        "Natural Language :: English",
    ],
    
    python_requires=">=3.9",
    install_requires=parse_requirements(),
    
    entry_points={
        "console_scripts": [
            "wordfreq=interfaces.cli.main:main",
            "word-frequency-analysis=interfaces.cli.main:main",
        ],
    },
    
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt", "*.md"],
        "config": ["*.yaml", "*.yml"],
        "data": ["**/*"],
        "docs": ["**/*"],
    },
    
    # 额外的元数据
    keywords="nlp, text-analysis, word-frequency, vocabulary, linguistics, chinese-english",
    project_urls={
        "Bug Reports": "https://github.com/Sherryyue24/word_frequency_analysis/issues",
        "Source": "https://github.com/Sherryyue24/word_frequency_analysis",
        "Documentation": "https://github.com/Sherryyue24/word_frequency_analysis/tree/main/docs",
    },
) 
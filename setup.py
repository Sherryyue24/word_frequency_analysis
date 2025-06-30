# 项目安装脚本
# 路径: setup.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

from setuptools import setup, find_packages
import os

# 读取README文件
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取requirements文件
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="word-frequency-analysis",
    version="1.0.0",
    author="Sherryyue",
    author_email="dev@wordfreq.com",
    description="词频分析和词汇管理系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourorg/word-frequency-analysis",
    
    packages=find_packages(),
    include_package_data=True,
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    
    python_requires=">=3.8",
    install_requires=requirements,
    
    entry_points={
        "console_scripts": [
            "wordfreq=interfaces.cli.main:main",
        ],
    },
    
    package_data={
        "data": ["files/*", "databases/*"],
        "config": ["*.yaml"],
    },
) 
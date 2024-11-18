
import os

# 遍历顶层
def get_supported_files(directory_path, scan_subdirs=True, supported_formats=None):
    """获取支持的文件类型的所有文件路径"""
    supported_extensions = set(supported_formats) if supported_formats else {'.txt', '.pdf'}
    file_paths = []
    
    if scan_subdirs:
        walker = os.walk(directory_path)
    else:
        walker = [(directory_path, [], os.listdir(directory_path))]
    
    for root, dirs, files in walker:
        for file in files:
            _, extension = os.path.splitext(file)
            if extension.lower() in supported_extensions:
                full_path = os.path.join(root, file)
                file_paths.append(full_path)
    
    return sorted(file_paths)

'''
# 遍历子文件
def get_supported_files(directory_path, scan_subdirs=True):
    """
    获取目录中支持的文件类型的所有文件路径
    
    Args:
        directory_path (str): 要扫描的目录路径
        scan_subdirs (bool): 是否扫描子目录
        
    Returns:
        list: 支持的文件路径列表
    """
    supported_extensions = {'.txt', '.pdf'}
    file_paths = []
    
    if scan_subdirs:
        walker = os.walk(directory_path)
    else:
        walker = [(directory_path, [], os.listdir(directory_path))]
    
    for root, dirs, files in walker:
        for file in files:
            _, extension = os.path.splitext(file)
            if extension.lower() in supported_extensions:
                full_path = os.path.join(root, file)
                file_paths.append(full_path)
    
    return sorted(file_paths)
'''

def print_analysis_results(basic_info, word_frequencies):
    """打印分析结果"""
    print("\n基本信息:")
    for key, value in basic_info.items():
        print(f"{key}: {value}")
    
    print("\n词频统计 (前10个):")
    sorted_words = sorted(word_frequencies.items(), 
                        key=lambda x: x[1], 
                        reverse=True)[:10]
    for word, freq in sorted_words:
        print(f"{word}: {freq}")
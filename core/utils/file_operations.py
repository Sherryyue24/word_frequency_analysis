# 文件操作工具函数
# 路径: core/utils/file_operations.py  
# 项目名: Word Frequency Analysis
# 作者: Sherryyue

from core.utils.helpers import get_supported_files


def process_files(directory_path: str, processor, storage_manager, 
                 min_frequency: int = 100, scan_subdirs: bool = True) -> None:
    """
    处理指定目录下的所有支持的文件并生成词频统计。

    Args:
        directory_path: 要处理的目录路径
        processor: 文本处理器实例  
        storage_manager: 存储管理器实例
        min_frequency: 最小词频阈值，默认为100
        scan_subdirs: 是否扫描子目录，默认为True

    Returns:
        None

    Raises:
        Exception: 处理过程中发生的任何异常
    """
    try:
        # 获取所有支持的文件 - 现在支持scan_subdirs参数
        file_paths = get_supported_files(directory_path, scan_subdirs=scan_subdirs)
        
        if not file_paths:
            subdirs_text = "及其子目录" if scan_subdirs else ""
            print(f"在目录 {directory_path} {subdirs_text}中没有找到支持的文件类型")
            return
        
        # 处理所有文件
        subdirs_text = "(包含子目录)" if scan_subdirs else "(仅当前目录)"
        print(f"\n开始处理文件... {subdirs_text}")
        print(f"找到 {len(file_paths)} 个支持的文件")
        
        # 使用处理器处理文件
        processor.process_new_texts(directory_path)
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        raise  # 重新抛出异常，让调用者处理

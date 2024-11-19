
from src.utils.helpers import get_supported_files


def process_files(directory_path: str, processor, storage_manager, min_frequency: int = 100) -> None:
    """
    处理指定目录下的所有支持的文件并生成词频统计。

    Args:
        directory_path: 要处理的目录路径
        processor: 文本处理器实例
        storage_manager: 存储管理器实例
        min_frequency: 最小词频阈值，默认为100

    Returns:
        None

    Raises:
        Exception: 处理过程中发生的任何异常
    """
    try:
        # 获取所有支持的文件
        file_paths = get_supported_files(directory_path)
        
        if not file_paths:
            print(f"在目录 {directory_path} 及其子目录中没有找到支持的文件类型")
            return
        
        # 处理所有文件
        print("\n开始处理所有文件...")
        processor.process_new_texts(directory_path)
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        raise  # 可选：重新抛出异常，让调用者处理

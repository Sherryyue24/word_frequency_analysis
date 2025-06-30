


def query_database(storage_manager):
    """查询数据库"""
    while True:
        print("\n查询选项:")
        print("1. 查看所有文本列表")
        print("2. 查看特定文本的词频")
        print("3. 查看总体词频统计")
        print("4. 查看特定词的使用情况")
        print("0. 返回上级菜单")

        choice = input("请选择操作 (0-4): ")

        try:
            if choice == '0':
                break
            elif choice == '1':
                texts = storage_manager.get_all_analyses()
                print("\n文本列表:")
                for text_id, title, date in texts:
                    print(f"ID: {text_id}, 标题: {title},日期: {date}")

            elif choice == '2':
                text_id = input("请输入文本ID: ")
                word_freq = storage_manager.get_sepcific_analysis(int(text_id))
                print("\n词频统计:")
                for word, freq in word_freq:
                    print(f"词语: {word}, 频率: {freq}")

            elif choice == '3':
                min_freq = input("请输入最小词频阈值（默认100）: ") or 100
                stats = storage_manager.get_word_stats(min_frequency=int(min_freq))
                print("\n总体词频统计:")
                for word, total_freq, doc_count, _ in stats:
                    print(f"词语: {word}, 总频率: {total_freq}, 出现文档数: {doc_count}")

            elif choice == '4':
                word = input("请输入要查询的词: ")
                stats, usage_list = storage_manager.get_word_usage(word)
                total_freq, doc_count = stats
                
                print(f"\n'{word}'的使用情况:")
                print(f"总出现频率: {total_freq}")
                print(f"出现文档数: {doc_count}")
                
                if usage_list:
                    print("\n在各文本中的具体使用情况:")
                    for text_id, filename, analysis_date, freq in usage_list:
                        print(f"文本ID: {text_id}, 文件名: {filename}, 日期: {analysis_date}, 频率: {freq}")
                else:
                    print("未找到该词的使用记录")

            else:
                print("无效的选择，请重试")

        except Exception as e:
            print(f"查询失败: {str(e)}")


def delete_logs(storage_manager):
    """删除文本条目"""
    try:
        # 显示现有文本列表
        texts = storage_manager.get_all_analyses()
        if not texts:
            print("数据库中没有文本记录")
            return

        print("\n现有文本列表:")
        for text_id, title, date in texts:
            print(f"ID: {text_id}, 标题: {title},日期: {date}")

        # 获取要删除的文本ID
        text_id = input("\n请输入要删除的文本ID（多个ID用逗号分隔，直接回车取消）: ")
        if not text_id.strip():
            print("取消删除操作")
            return

        # 处理输入的ID
        text_ids = [int(id.strip()) for id in text_id.split(',')]
        
        # 逐个处理每个ID
        for id in text_ids:
            success = storage_manager.delete_analysis(id)
            if not success:
                print(f"删除ID {id} 失败")

        print("删除操作完成")

    except Exception as e:
        print(f"删除操作失败: {str(e)}")



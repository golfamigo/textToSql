import os
import glob
import re

def convert_sql_files_to_utf8():
    """轉換所有SQL文件為UTF-8編碼"""
    # 查找所有SQL文件
    sql_files = glob.glob('database_function/*.sql')
    
    print(f"找到 {len(sql_files)} 個SQL文件")
    
    for file_path in sql_files:
        try:
            # 嘗試以UTF-8打開，檢查是否已經是UTF-8
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"{file_path} 已經是UTF-8編碼")
        except UnicodeDecodeError:
            # 嘗試用不同編碼打開
            for encoding in ['cp950', 'big5', 'gb18030', 'latin-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    
                    # 以UTF-8保存
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"✓ 已將 {file_path} 從 {encoding} 轉換為 UTF-8")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print(f"× 無法轉換 {file_path} - 所有編碼均失敗")

def fix_schema_py():
    """修復schema.py中的編碼問題"""
    schema_path = "app/schema/schema.py"
    try:
        # 使用行號直接修改
        with open(schema_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 修改第94行
        if len(lines) >= 94 and "with open(sql_file, 'r') as f:" in lines[93]:
            lines[93] = "            with open(sql_file, 'r', encoding='utf-8') as f:\n"
            with open(schema_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"✓ 已修復 {schema_path} 中的編碼問題 (第94行)")
        else:
            print(f"× 在 {schema_path} 中沒有找到需要修復的代碼或行號不匹配")
    except Exception as e:
        print(f"× 修復 {schema_path} 時出錯: {e}")

if __name__ == "__main__":
    convert_sql_files_to_utf8()
    fix_schema_py()
    print("完成！請再次運行 python mini.py 測試")
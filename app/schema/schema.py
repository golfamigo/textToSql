from sqlalchemy import MetaData, Table, Column, String, Integer, Float, Boolean, DateTime, Date, Time, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
import os
import glob
import re

metadata = MetaData()

# 讀取 SQL 檔案創建 schema 定義
def load_schema_from_sql_files(schema_dir):
    """從 SQL 檔案讀取資料表定義並創建 schema 定義"""
    schema_definitions = {}
    
    sql_files = glob.glob(os.path.join(schema_dir, '*.sql'))
    
    for sql_file in sql_files:
        table_name = os.path.basename(sql_file).replace('.sql', '')
        with open(sql_file, 'r', encoding='utf-8') as f: # Added encoding='utf-8'
            sql_content = f.read()
            
            # 提取 CREATE TABLE 語句
            create_table_match = re.search(r'CREATE TABLE .*?\((.*?)\);', sql_content, re.DOTALL)
            if create_table_match:
                column_definitions = create_table_match.group(1).strip()
                
                # 解析欄位
                columns = []
                
                # 分割欄位定義
                column_defs = []
                current_def = ''
                parenthesis_count = 0
                
                for char in column_definitions:
                    if char == ',' and parenthesis_count == 0:
                        column_defs.append(current_def.strip())
                        current_def = ''
                    else:
                        current_def += char
                        if char == '(':
                            parenthesis_count += 1
                        elif char == ')':
                            parenthesis_count -= 1
                
                if current_def.strip():
                    column_defs.append(current_def.strip())
                
                for col_def in column_defs:
                    # 跳過主鍵和外鍵約束
                    if col_def.strip().upper().startswith('PRIMARY KEY') or col_def.strip().upper().startswith('FOREIGN KEY'):
                        continue
                    
                    # 提取列名和類型
                    col_match = re.match(r'([a-zA-Z0-9_]+)\s+(.*)', col_def.strip())
                    if col_match:
                        col_name = col_match.group(1)
                        col_type = col_match.group(2)
                        columns.append({
                            'name': col_name,
                            'type': col_type
                        })
                
                # 提取註解
                comment_match = re.search(r"COMMENT ON TABLE .* IS '(.*)';", sql_content)
                comment = comment_match.group(1) if comment_match else ''
                
                schema_definitions[table_name] = {
                    'columns': columns,
                    'comment': comment
                }
    
    return schema_definitions


# 從 SQL 文件加載 schema 定義
schema_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../n8n_booking_schemas'))
schema_definitions = load_schema_from_sql_files(schema_dir)


def load_database_functions():
    """從資料庫函數目錄加載函數定義"""
    functions = {}
    error_functions = {}  # 記錄解析出錯的函數
    db_function_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../database_function'))
    
    if not os.path.exists(db_function_dir):
        return functions
    
    sql_files = glob.glob(os.path.join(db_function_dir, '*.sql'))
    
    for sql_file in sql_files:
        file_name = os.path.basename(sql_file).replace('.sql', '')
        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
                
                # 提取函數的參數和返回值
                create_function_match = re.search(r'CREATE\s+OR\s+REPLACE\s+FUNCTION\s+(\w+)\s*\((.*?)\)\s*RETURNS\s+(.*?)\s+AS', 
                                                 sql_content, re.DOTALL | re.IGNORECASE)
                
                if create_function_match:
                    function_name = create_function_match.group(1)
                    parameters = create_function_match.group(2).strip()
                    return_type = create_function_match.group(3).strip()
                    
                    # 提取函數說明
                    comment_match = re.search(r'--\s*函數功能：(.*?)$', sql_content, re.MULTILINE)
                    comment = comment_match.group(1).strip() if comment_match else '無說明'
                    
                    # 提取參數說明
                    param_comments = []
                    param_comment_matches = re.finditer(r'--\s*(\w+):\s*(.*?)$', sql_content, re.MULTILINE)
                    for match in param_comment_matches:
                        param_comments.append(f"{match.group(1)}: {match.group(2).strip()}")
                    
                    # 儲存函數代碼，用於檢查和調試
                    function_code = sql_content
                    
                    # 儲存函數信息
                    functions[function_name] = {
                        'name': function_name,
                        'parameters': parameters,
                        'return_type': return_type,
                        'description': comment,
                        'param_comments': param_comments,
                        'file_path': sql_file,
                        'code': function_code,
                        'has_parse_error': False
                    }
                else:
                    # 如果無法解析函數定義，記錄錯誤
                    error_functions[file_name] = {
                        'name': file_name,
                        'file_path': sql_file,
                        'error': '無法解析函數定義',
                        'has_parse_error': True
                    }
        except Exception as e:
            # 處理文件讀取或解析過程中的錯誤
            error_functions[file_name] = {
                'name': file_name,
                'file_path': sql_file,
                'error': f'解析錯誤: {str(e)}',
                'has_parse_error': True
            }
    
    # 將解析錯誤的函數也加入返回結果，但標記為有錯誤
    functions.update(error_functions)
    
    # 記錄錯誤函數的數量
    error_count = len(error_functions)
    if error_count > 0:
        print(f"警告: {error_count} 個資料庫函數解析失敗")
        for func_name, func_info in error_functions.items():
            print(f"  - {func_name}: {func_info['error']}")
    
    return functions


def get_table_schema_description():
    """取得所有資料表的 schema 描述，用於 AI 生成 SQL 查詢"""
    description = "資料庫結構:\n\n"
    
    for table_name, table_def in schema_definitions.items():
        description += f"表名: {table_name}\n"
        description += f"描述: {table_def['comment']}\n"
        description += "欄位:\n"
        
        for column in table_def['columns']:
            description += f"  - {column['name']}: {column['type']}\n"
        
        description += "\n"
    
    # 添加一些關聯關係描述
    description += """
關聯關係:
- n8n_booking_businesses 是主表，包含商家基本資訊
- n8n_booking_users 通過 business_id 關聯到 n8n_booking_businesses
- n8n_booking_services 通過 business_id 關聯到 n8n_booking_businesses
- n8n_booking_time_periods 通過 business_id 關聯到 n8n_booking_businesses
- n8n_booking_staff_services 關聯員工 (n8n_booking_users) 和服務 (n8n_booking_services)
- n8n_booking_service_period_restrictions 關聯服務 (n8n_booking_services) 和時段 (n8n_booking_time_periods)
- n8n_booking_staff_availability 關聯員工 (n8n_booking_users) 和工作時間
- n8n_booking_bookings 是預約記錄，關聯到客戶、服務、時段和員工
- n8n_booking_history 記錄預約狀態的變更歷史
"""
    
    # 添加資料庫函數說明
    functions = load_database_functions()
    if functions:
        description += "\n資料庫函數:\n\n"
        for func_name, func_info in functions.items():
            # 檢查函數是否有解析錯誤
            if func_info.get('has_parse_error', False):
                description += f"函數名: {func_name} (此函數可能不可用)\n"
                description += f"錯誤: {func_info.get('error', '解析錯誤')}\n"
                description += "\n"
                continue
                
            description += f"函數名: {func_name}\n"
            description += f"描述: {func_info.get('description', '無描述')}\n"
            description += f"參數: {func_info.get('parameters', '無參數')}\n"
            description += f"返回類型: {func_info.get('return_type', '無返回類型')}\n"
            
            if func_info.get('param_comments'):
                description += "參數說明:\n"
                for param in func_info['param_comments']:
                    description += f"  - {param}\n"
            description += "\n"
    
    return description


# 載入資料庫函數定義
db_functions = load_database_functions()
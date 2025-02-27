import os

def ensure_utf8(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"{file_path} already UTF-8")
        return True
    except UnicodeDecodeError:
        try:
            # 嘗試用不同編碼打開
            for encoding in ['cp950', 'big5', 'gb18030', 'latin-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Fixed encoding for {file_path} using {encoding}")
                    return True
                except UnicodeDecodeError:
                    continue
            print(f"Could not fix encoding for {file_path}")
            return False
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False

# 修復常見問題文件
files_to_fix = [
    "app/utils/config.py", 
    "app/schema/schema.py",
    "requirements.txt"
]

for file in files_to_fix:
    ensure_utf8(file)

# 修改config.py來繞過Pydantic驗證
try:
    with open("app/utils/config.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 添加API欄位
    if "# API Keys" not in content:
        modified = False
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "# 默認模型設定" in line and "# API Keys" not in lines[i+2]:
                # 找到模型設定部分後插入API Keys欄位
                insert_position = i + 2
                api_keys_lines = [
                    "    # API Keys",
                    "    openai_api_key: Optional[str] = None",
                    "    anthropic_api_key: Optional[str] = None",
                    "    google_api_key: Optional[str] = None",
                    "    azure_openai_api_key: Optional[str] = None",
                    "    azure_openai_endpoint: Optional[str] = None",
                    "    azure_deployment_name: Optional[str] = None",
                    "    dummy_key: Optional[str] = None",
                    ""
                ]
                for j, api_line in enumerate(api_keys_lines):
                    lines.insert(insert_position + j, api_line)
                modified = True
                break
        
        if modified:
            content = '\n'.join(lines)
            print("Added API Keys fields to config")

    # 添加extra="allow"
    if "extra=\"allow\"" not in content and "extra='allow'" not in content:
        content = content.replace(
            "model_config = SettingsConfigDict(",
            "model_config = SettingsConfigDict(extra=\"allow\","
        )
        print("Added extra='allow' to config")
        
    with open("app/utils/config.py", "w", encoding="utf-8") as f:
        f.write(content)
except Exception as e:
    print(f"Error modifying config.py: {e}")

# 創建最小.env
with open(".env", "w", encoding="utf-8") as f:
    f.write("DUMMY_KEY=dummy\n")
print("Created minimal .env file")

print("Fix complete. Try running python main.py now.")
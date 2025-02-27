import zhconv
import sys
import os

def convert_to_traditional_chinese(path):
    # 只處理Python文件
    if os.path.isfile(path) and path.endswith('.py'):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            converted_content = zhconv.convert(content, 'zh-tw')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(converted_content)
            print(f"Converted {path} successfully.")
        except Exception as e:
            print(f"Error converting {path}: {e}")
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    convert_to_traditional_chinese(filepath)

if __name__ == "__main__":
    app_dir = "textToSql/app"
    if not os.path.exists(app_dir):
        print(f"Directory {app_dir} not found. Please make sure you're running this script from the project root directory.")
        sys.exit(1)
    
    print(f"Converting simplified Chinese to traditional Chinese in {app_dir}...")
    convert_to_traditional_chinese(app_dir)
    print("Conversion complete.")
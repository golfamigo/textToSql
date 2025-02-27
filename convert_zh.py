import zhconv
import sys
import os

def convert_to_traditional_chinese(path):
    if os.path.isfile(path):
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
                filepath = os.path.join(root, file)
                convert_to_traditional_chinese(filepath)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_zh.py <filepath or directory>")
        sys.exit(1)
    path = sys.argv[1]
    convert_to_traditional_chinese(path)
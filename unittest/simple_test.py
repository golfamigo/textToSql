"""
簡單測試文件，無需依賴外部模組
"""
import unittest
import json
import tempfile
import os


class TestBasicOperations(unittest.TestCase):
    """測試基本操作"""
    
    def setUp(self):
        """設置測試環境"""
        # 建立臨時目錄
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = os.path.join(self.temp_dir.name, "test.json")
    
    def tearDown(self):
        """清理測試環境"""
        self.temp_dir.cleanup()
    
    def test_json_operations(self):
        """測試JSON操作"""
        # 準備測試數據
        test_data = {
            "id": "test-id",
            "name": "測試數據",
            "values": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        # 寫入JSON文件
        with open(self.test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        # 讀取JSON文件
        with open(self.test_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        
        # 驗證數據
        self.assertEqual(loaded_data["id"], "test-id")
        self.assertEqual(loaded_data["name"], "測試數據")
        self.assertEqual(loaded_data["values"], [1, 2, 3])
        self.assertEqual(loaded_data["nested"]["key"], "value")
    
    def test_string_operations(self):
        """測試字符串操作"""
        # 測試字符串連接
        str1 = "Hello"
        str2 = "World"
        result = str1 + " " + str2
        self.assertEqual(result, "Hello World")
        
        # 測試字符串格式化
        name = "小明"
        age = 20
        formatted = f"{name}今年{age}歲"
        self.assertEqual(formatted, "小明今年20歲")
        
        # 測試字符串分割
        text = "apple,banana,orange"
        parts = text.split(",")
        self.assertEqual(parts, ["apple", "banana", "orange"])
    
    def test_list_operations(self):
        """測試列表操作"""
        # 測試列表添加
        numbers = [1, 2, 3]
        numbers.append(4)
        self.assertEqual(numbers, [1, 2, 3, 4])
        
        # 測試列表切片
        slice1 = numbers[1:3]
        self.assertEqual(slice1, [2, 3])
        
        # 測試列表排序
        unsorted = [3, 1, 4, 2]
        unsorted.sort()
        self.assertEqual(unsorted, [1, 2, 3, 4])
    
    def test_dict_operations(self):
        """測試字典操作"""
        # 測試字典添加
        person = {"name": "小明"}
        person["age"] = 20
        self.assertEqual(person, {"name": "小明", "age": 20})
        
        # 測試字典獲取
        self.assertEqual(person.get("name"), "小明")
        self.assertEqual(person.get("height", "未知"), "未知")
        
        # 測試字典遍歷
        keys = []
        values = []
        for k, v in person.items():
            keys.append(k)
            values.append(v)
        self.assertEqual(sorted(keys), ["age", "name"])
        # 檢查值是否存在 (不需要排序)
        self.assertIn(20, values)
        self.assertIn("小明", values)


if __name__ == '__main__':
    unittest.main()
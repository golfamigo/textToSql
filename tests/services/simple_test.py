#!/usr/bin/env python3
"""
極簡向量存儲測試
"""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

import numpy as np

# 添加項目根目錄到 Python 路徑
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# 設置需要的環境變量
os.environ["OPENAI_API_KEY"] = "dummy"
os.environ["ANTHROPIC_API_KEY"] = "dummy"
os.environ["GOOGLE_API_KEY"] = "dummy"


# 添加一個模擬的 SentenceTransformer 類
class MockSentenceTransformer:
    def __init__(self, model_name):
        self.model_name = model_name

    def encode(self, text):
        # 返回固定的向量
        return np.ones(384, dtype=np.float32)


# 模擬 faiss 模塊
class MockIndex:
    def __init__(self):
        self.ntotal = 0
        self.vectors = []

    def add(self, vectors):
        self.vectors.extend(vectors)
        self.ntotal = len(self.vectors)

    def search(self, query, k):
        # 返回假的距離和索引
        return np.array([[0.5] * min(k, self.ntotal)]), np.array(
            [[i for i in range(min(k, self.ntotal))]]
        )


# 使用模擬模塊替換真實模塊
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["sentence_transformers.SentenceTransformer"] = MockSentenceTransformer
sys.modules["faiss"] = MagicMock()
sys.modules["faiss.IndexFlatL2"] = MockIndex
sys.modules["faiss.read_index"] = lambda x: MockIndex()
sys.modules["faiss.write_index"] = lambda x, y: None

# 現在可以安全地導入向量存儲模塊
from app.services.vector_store import VectorStore


class SimpleVectorStoreTest(unittest.TestCase):
    def setUp(self):
        # 創建臨時目錄用於測試
        self.temp_dir = tempfile.mkdtemp()
        self.vector_store = VectorStore()

    def tearDown(self):
        # 刪除臨時目錄
        shutil.rmtree(self.temp_dir)

    def test_add_and_search(self):
        """測試添加和搜索功能"""
        # 添加測試數據
        self.vector_store.add_query("測試查詢", "SELECT * FROM test")

        # 搜索
        results = self.vector_store.search_similar("測試搜索", k=3)

        # 驗證結果
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["query"], "測試查詢")
        self.assertEqual(results[0]["sql"], "SELECT * FROM test")


if __name__ == "__main__":
    unittest.main()

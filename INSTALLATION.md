# 安裝指南

## 基本需求

首先安裝基本的Python套件需求：

```bash
pip install -r requirements.txt
```

## 特殊模組安裝指南

### FAISS 安裝

FAISS是一個高效能的相似性搜尋函式庫，用於搜尋大型資料集中的向量。

#### 在Windows上安裝FAISS:
```bash
pip install faiss-cpu
```

如果上面的命令在Windows上失敗，請嘗試使用以下替代方案:
```bash
pip install faiss-cpu-no-avx2
```

或使用Conda安裝：
```bash
conda install -c pytorch faiss-cpu
```

#### 在Mac OS上安裝FAISS:
```bash
pip install faiss-cpu
```

#### 在Linux上安裝FAISS:
```bash
pip install faiss-cpu
```

### 視覺化模組安裝

對於視覺化功能，需要安裝以下套件：

```bash
# 安裝視覺化相關套件
pip install matplotlib>=3.4.0
pip install seaborn>=0.11.0
```

### 其他可能需要的模組
根據您的環境，可能還需要安裝以下模組：

```bash
# 如果您需要使用SentenceTransformers
pip install sentence-transformers

# 如果您需要使用JobLib
pip install joblib
```

## 可選開發工具

```bash
# 安裝開發工具
pip install -e ".[dev]"

# 安裝測試工具
pip install -e ".[test]"

# 安裝 pre-commit 勾子
pre-commit install
```
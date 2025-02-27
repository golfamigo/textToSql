import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非互動模式，適合CLI環境
import seaborn as sns
from typing import List, Dict, Any, Optional, Tuple
import os
import tempfile
from pathlib import Path
import json
import re
import logging
from datetime import datetime

# 設定 logging
logger = logging.getLogger(__name__)

class VisualizationService:
    """查詢結果視覺化服務"""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化視覺化服務
        
        Args:
            output_dir: 輸出目錄，如果不指定則使用臨時目錄
        """
        self.output_dir = output_dir or os.path.join(tempfile.gettempdir(), "texttosql_viz")
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"視覺化輸出目錄: {self.output_dir}")
        
    def detect_chart_type(self, columns: List[str], rows: List[List[Any]]) -> str:
        """
        自動檢測最適合的圖表類型
        
        Args:
            columns: 列名
            rows: 資料行
            
        Returns:
            建議的圖表類型: 'bar', 'line', 'pie', 'scatter' 或 'table'
        """
        if not columns or not rows:
            return 'table'
            
        # 轉換為 DataFrame 以便分析
        df = pd.DataFrame(rows, columns=columns)
        
        # 計算列類型
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = [col for col in df.columns if col not in numeric_cols]
        
        # 嘗試將字符串列轉換為日期時間
        datetime_cols = []
        for col in categorical_cols[:]:
            try:
                # 轉換第一個非空值檢查是否為日期
                first_valid = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if first_valid and isinstance(first_valid, str):
                    pd.to_datetime(first_valid)
                    datetime_cols.append(col)
            except:
                pass
        
        num_numeric = len(numeric_cols)
        num_categorical = len(categorical_cols)
        num_datetime = len(datetime_cols)
        num_cols = len(columns)
        num_rows = len(rows)
        
        # 檢測圖表類型的邏輯
        
        # 數據太多，不適合可視化
        if num_cols > 15 or num_rows > 100:
            return 'table'
            
        # 時間序列資料 (日期時間 + 數值)
        if num_datetime > 0 and num_numeric > 0:
            return 'line'
            
        # 一個分類變量 + 一個數值變量 = 適合條形圖
        if num_categorical == 1 and num_numeric == 1:
            # 如果分類值較少 (< 10)，餅圖可能更合適
            unique_cat_values = len(pd.unique(df[categorical_cols[0]]))
            if unique_cat_values <= 7:
                return 'pie'
            else:
                return 'bar'
                
        # 兩個數值變量適合散點圖
        if num_numeric >= 2:
            return 'scatter'
            
        # 一個分類變量和多個數值變量可以是條形圖
        if num_categorical >= 1 and num_numeric >= 1:
            return 'bar'
            
        # 預設為表格顯示複雜數據
        return 'table'
        
    def create_visualization(self, 
                            columns: List[str], 
                            rows: List[List[Any]], 
                            chart_type: Optional[str] = None, 
                            title: str = "查詢結果視覺化") -> Tuple[str, Dict[str, Any]]:
        """
        根據查詢結果創建視覺化圖表
        
        Args:
            columns: 列名
            rows: 資料行
            chart_type: 圖表類型 ('bar', 'line', 'pie', 'scatter' 或 'table')。如果為 None，自動檢測。
            title: 圖表標題
            
        Returns:
            Tuple of (file_path, metadata)
        """
        if not columns or not rows:
            return None, {"error": "沒有數據可視覺化"}
            
        # 轉換為 DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
        # 自動檢測圖表類型
        if not chart_type:
            chart_type = self.detect_chart_type(columns, rows)
            
        # 創建文件路徑
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"viz_{chart_type}_{timestamp}"
        img_path = os.path.join(self.output_dir, f"{file_name}.png")
        
        # 創建視覺化
        metadata = {
            "type": chart_type,
            "title": title,
            "rows": len(rows),
            "columns": len(columns),
            "column_names": columns,
            "file_path": img_path
        }
        
        try:
            if chart_type == 'bar':
                self._create_bar_chart(df, img_path, title)
            elif chart_type == 'line':
                self._create_line_chart(df, img_path, title)
            elif chart_type == 'pie':
                self._create_pie_chart(df, img_path, title)
            elif chart_type == 'scatter':
                self._create_scatter_chart(df, img_path, title)
            else:
                # 預設使用表格視圖 - 不需要視覺化
                return None, {"type": "table"}
                
            logger.info(f"已創建 {chart_type} 圖: {img_path}")
            return img_path, metadata
            
        except Exception as e:
            logger.error(f"創建視覺化失敗: {e}")
            return None, {"error": str(e)}
    
    def _create_bar_chart(self, df, img_path, title):
        """創建條形圖"""
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        non_numeric_cols = [col for col in df.columns if col not in numeric_cols]
        
        if not numeric_cols or not non_numeric_cols:
            # 使用第一列為分類軸，第二列為數值軸
            cat_col = df.columns[0]
            num_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        else:
            cat_col = non_numeric_cols[0]
            num_col = numeric_cols[0]
        
        # 使用 Seaborn 生成條形圖
        plt.figure(figsize=(10, 6))
        sns.set_style("whitegrid")
        
        # 根據唯一值數量決定圖表方向
        if len(df[cat_col].unique()) > 10:
            # 水平條形圖更適合較多分類
            ax = sns.barplot(y=cat_col, x=num_col, data=df)
            # 確保所有標籤可見
            plt.tight_layout()
        else:
            ax = sns.barplot(x=cat_col, y=num_col, data=df)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
        plt.title(title)
        
        # 在每個條形上添加數值標籤
        for p in ax.patches:
            if ax.get_xticklabels()[0].get_rotation() == 45:  # 垂直條形圖
                ax.annotate(f'{p.get_height():.1f}', 
                          (p.get_x() + p.get_width()/2., p.get_height()), 
                          ha='center', va='bottom', rotation=0)
            else:  # 水平條形圖
                ax.annotate(f'{p.get_width():.1f}', 
                          (p.get_width(), p.get_y() + p.get_height()/2.), 
                          ha='left', va='center')
        
        plt.savefig(img_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    def _create_line_chart(self, df, img_path, title):
        """創建折線圖"""
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        non_numeric_cols = [col for col in df.columns if col not in numeric_cols]
        
        # 嘗試識別 x 軸 (優先選擇日期類型列)
        x_col = None
        
        # 嘗試將非數值列轉換為日期時間
        for col in non_numeric_cols:
            try:
                df[col] = pd.to_datetime(df[col])
                x_col = col
                break
            except:
                pass
                
        # 如果沒有找到日期列，使用第一個非數值列
        if not x_col and non_numeric_cols:
            x_col = non_numeric_cols[0]
        elif not x_col:
            # 如果沒有非數值列，使用第一列作為 x 軸
            x_col = df.columns[0]
            
        # 選擇要繪製的 y 軸列 (數值列)
        y_cols = [col for col in numeric_cols if col != x_col]
        if not y_cols and len(df.columns) > 1:
            y_cols = [df.columns[1]]  # 如果沒有數值列，使用第二列
        elif not y_cols:
            y_cols = [df.columns[0]]  # 只有一列時使用該列
        
        # 最多顯示 5 條線以保持清晰
        y_cols = y_cols[:5]
            
        # 使用 Seaborn 創建折線圖
        plt.figure(figsize=(12, 6))
        sns.set_style("whitegrid")
        
        # 針對每個 y 軸繪製一條線
        for y_col in y_cols:
            sns.lineplot(x=x_col, y=y_col, data=df, marker='o', label=y_col)
            
        plt.title(title)
        
        # 根據 x 軸類型調整標籤
        if pd.api.types.is_datetime64_any_dtype(df[x_col]):
            plt.xticks(rotation=45)
        elif len(df[x_col].unique()) > 10:
            plt.xticks(rotation=45)
            
        plt.legend()
        plt.tight_layout()
        plt.savefig(img_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    def _create_pie_chart(self, df, img_path, title):
        """創建餅圖"""
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        non_numeric_cols = [col for col in df.columns if col not in numeric_cols]
        
        if not numeric_cols or not non_numeric_cols:
            # 使用第一列為標籤，第二列為數值
            label_col = df.columns[0]
            value_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        else:
            label_col = non_numeric_cols[0]
            value_col = numeric_cols[0]
            
        # 準備資料 - 確保資料為正值
        pie_data = df.copy()
        pie_data[value_col] = pie_data[value_col].abs()
        
        # 限制切片數量以保持可讀性
        if len(pie_data) > 8:
            # 保留前 7 個最大值，其他歸為"其他"
            top_7 = pie_data.nlargest(7, value_col)
            others_sum = pie_data[~pie_data.index.isin(top_7.index)][value_col].sum()
            
            if others_sum > 0:
                others_row = pd.DataFrame({label_col: ['其他'], value_col: [others_sum]})
                pie_data = pd.concat([top_7, others_row])
            else:
                pie_data = top_7
            
        # 使用 Matplotlib 創建餅圖
        plt.figure(figsize=(10, 8))
        plt.pie(pie_data[value_col], labels=pie_data[label_col], autopct='%1.1f%%', 
               startangle=90, shadow=True)
        plt.axis('equal')  # 確保繪製的餅圖是圓形的
        plt.title(title)
        plt.tight_layout()
        plt.savefig(img_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    def _create_scatter_chart(self, df, img_path, title):
        """創建散點圖"""
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if len(numeric_cols) < 2:
            # 數值列不足，使用前兩列
            x_col = df.columns[0]
            y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        else:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            
        # 選擇顏色列（如果可用）
        other_cols = [col for col in df.columns if col not in [x_col, y_col]]
        color_col = other_cols[0] if other_cols else None
            
        # 使用 Seaborn 創建散點圖
        plt.figure(figsize=(10, 8))
        sns.set_style("whitegrid")
        
        if color_col and len(df[color_col].unique()) <= 10:
            # 使用分類顏色
            scatter_plot = sns.scatterplot(x=x_col, y=y_col, hue=color_col, data=df, s=100)
            plt.legend(title=color_col)
        else:
            scatter_plot = sns.scatterplot(x=x_col, y=y_col, data=df, s=100)
            
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.title(title)
        plt.tight_layout()
        plt.savefig(img_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    def detect_visualization_query(self, sql: str) -> bool:
        """
        檢測查詢是否適合視覺化
        
        Args:
            sql: SQL 查詢
            
        Returns:
            如果查詢適合視覺化，則為 True，否則為 False
        """
        # 包含聚合函數的查詢適合視覺化
        aggregation_patterns = [
            r'\bCOUNT\s*\(',
            r'\bSUM\s*\(',
            r'\bAVG\s*\(',
            r'\bMIN\s*\(',
            r'\bMAX\s*\(',
            r'\bGROUP\s+BY\b',
            r'\bORDER\s+BY\b'
        ]
        
        for pattern in aggregation_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return True
                
        return False

# 創建全局可視化服務實例
visualization_service = VisualizationService()
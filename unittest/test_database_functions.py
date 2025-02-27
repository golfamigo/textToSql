"""
測試資料庫函數的模擬實現
"""
import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys
from datetime import datetime, date
from typing import List, Dict, Any, Optional

# 添加應用路徑到系統路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class MockDatabaseConnection:
    """模擬資料庫連接"""
    
    def __init__(self):
        # 初始化模擬數據
        self.services = [
            {"id": 1, "name": "基礎美容護理", "business_id": 1, "duration": 60, "price": 1200},
            {"id": 2, "name": "進階美容SPA", "business_id": 1, "duration": 90, "price": 2000},
            {"id": 3, "name": "臉部按摩", "business_id": 1, "duration": 45, "price": 800}
        ]
        
        self.periods = [
            {"id": 1, "name": "上午", "start_time": "09:00", "end_time": "12:00", "business_id": 1},
            {"id": 2, "name": "下午", "start_time": "13:00", "end_time": "17:00", "business_id": 1},
            {"id": 3, "name": "晚上", "start_time": "18:00", "end_time": "21:00", "business_id": 1}
        ]
        
        self.staff = [
            {"id": 1, "name": "張美容師", "business_id": 1, "role": "staff"},
            {"id": 2, "name": "李按摩師", "business_id": 1, "role": "staff"}
        ]
        
        self.bookings = [
            {
                "id": 101, 
                "customer_name": "王小明", 
                "customer_email": "wang@example.com",
                "customer_phone": "0912345678",
                "service_id": 1, 
                "staff_id": 1, 
                "date": "2025-03-01", 
                "start_time": "10:00", 
                "end_time": "11:00",
                "status": "confirmed",
                "period_id": 1,
                "notes": "初次體驗",
                "business_id": 1
            }
        ]
        
        self.staff_availability = [
            {
                "id": 1, 
                "staff_id": 1, 
                "day_of_week": 1,  # 星期一
                "start_time": "09:00", 
                "end_time": "17:00", 
                "is_recurring": True,
                "business_id": 1
            },
            {
                "id": 2, 
                "staff_id": 1, 
                "specific_date": "2025-03-02",  # 特定日期
                "start_time": "09:00", 
                "end_time": "12:00", 
                "is_recurring": False,
                "business_id": 1
            }
        ]
    
    def execute_function(self, function_name: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        模擬執行資料庫函數
        
        Args:
            function_name: 要執行的函數名稱
            parameters: 函數參數
            
        Returns:
            函數執行結果
        """
        if function_name == "find_service":
            return self._find_service(
                p_business_id=parameters.get("p_business_id", 1),
                p_service_name=parameters.get("p_service_name", "")
            )
        elif function_name == "get_period_availability":
            return self._get_period_availability(
                service_name=parameters.get("service_name", ""),
                period_name=parameters.get("period_name", ""),
                start_date=parameters.get("start_date", ""),
                end_date=parameters.get("end_date", "")
            )
        elif function_name == "get_staff_availability_by_date":
            return self._get_staff_availability_by_date(
                p_staff_id=parameters.get("p_staff_id", 0),
                p_date=parameters.get("p_date", "")
            )
        elif function_name == "get_booking_details":
            return self._get_booking_details(
                p_booking_id=parameters.get("p_booking_id", 0)
            )
        else:
            # 未知函數
            return []
    
    def _find_service(self, p_business_id: int, p_service_name: str) -> List[Dict[str, Any]]:
        """模擬find_service函數"""
        results = []
        
        # 嘗試精確匹配
        exact_matches = [
            service for service in self.services 
            if service["business_id"] == p_business_id and service["name"].lower() == p_service_name.lower()
        ]
        
        if exact_matches:
            # 找到精確匹配
            for service in exact_matches:
                results.append({
                    "service_id": service["id"],
                    "name": service["name"],
                    "similarity": 1.0
                })
            return results
        
        # 沒有精確匹配，嘗試模糊匹配
        search_term = p_service_name.lower()
        for service in self.services:
            if service["business_id"] != p_business_id:
                continue
                
            service_name = service["name"].lower()
            # 簡單的相似度計算 (實際中可能使用更複雜的算法)
            if search_term in service_name:
                # 計算簡單相似度 (長度比例)
                similarity = min(len(search_term) / len(service_name), 0.9)  # 最高 0.9
                
                if similarity >= 0.3:  # 相似度閾值
                    results.append({
                        "service_id": service["id"],
                        "name": service["name"],
                        "similarity": similarity
                    })
        
        # 按相似度排序
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results
    
    def _get_period_availability(self, service_name: str, period_name: str, 
                                start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """模擬get_period_availability函數"""
        results = []
        
        # 查找服務ID
        service_id = None
        for service in self.services:
            if service["name"].lower() == service_name.lower():
                service_id = service["id"]
                break
        
        if not service_id:
            return []
            
        # 查找時段ID
        period_id = None
        for period in self.periods:
            if period["name"].lower() == period_name.lower():
                period_id = period["id"]
                break
                
        if not period_id:
            return []
        
        # 解析日期範圍
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return []
            
        # 為每個日期生成可用性數據
        current_date = start
        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # 計算該時段的預約數
            bookings_count = sum(1 for booking in self.bookings 
                             if booking["service_id"] == service_id 
                             and booking["period_id"] == period_id
                             and booking["date"] == date_str
                             and booking["status"] == "confirmed")
            
            # 假設每個時段總容量為5
            total_capacity = 5
            available = total_capacity - bookings_count
            
            results.append({
                "date": date_str,
                "period_name": period_name,
                "available": available,
                "total_capacity": total_capacity
            })
            
            # 移到下一天
            current_date = date(current_date.year, current_date.month, current_date.day + 1)
        
        return results
    
    def _get_staff_availability_by_date(self, p_staff_id: int, p_date: str) -> List[Dict[str, Any]]:
        """模擬get_staff_availability_by_date函數"""
        results = []
        
        try:
            target_date = datetime.strptime(p_date, "%Y-%m-%d").date()
            day_of_week = target_date.weekday() + 1  # 1-7 表示星期一到星期日
        except ValueError:
            return []
        
        # 檢查週期性排班
        for availability in self.staff_availability:
            if availability["staff_id"] != p_staff_id:
                continue
                
            if availability["is_recurring"] and availability["day_of_week"] == day_of_week:
                results.append({
                    "start_time": availability["start_time"],
                    "end_time": availability["end_time"],
                    "availability_type": "recurring",
                    "is_recurring": True,
                    "day_of_week": day_of_week,
                    "specific_date": None
                })
            elif not availability["is_recurring"] and availability["specific_date"] == p_date:
                results.append({
                    "start_time": availability["start_time"],
                    "end_time": availability["end_time"],
                    "availability_type": "specific",
                    "is_recurring": False,
                    "day_of_week": None,
                    "specific_date": p_date
                })
        
        return results
    
    def _get_booking_details(self, p_booking_id: int) -> List[Dict[str, Any]]:
        """模擬get_booking_details函數"""
        for booking in self.bookings:
            if booking["id"] == p_booking_id:
                # 查找相關的服務和員工信息
                service = next((s for s in self.services if s["id"] == booking["service_id"]), None)
                staff = next((s for s in self.staff if s["id"] == booking["staff_id"]), None)
                period = next((p for p in self.periods if p["id"] == booking["period_id"]), None)
                
                if not service or not staff or not period:
                    return []
                
                return [{
                    "booking_id": booking["id"],
                    "customer_name": booking["customer_name"],
                    "customer_email": booking["customer_email"],
                    "customer_phone": booking["customer_phone"],
                    "service_name": service["name"],
                    "service_duration": service["duration"],
                    "service_price": service["price"],
                    "staff_name": staff["name"],
                    "date": booking["date"],
                    "start_time": booking["start_time"],
                    "end_time": booking["end_time"],
                    "period_name": period["name"],
                    "status": booking["status"],
                    "notes": booking["notes"]
                }]
        
        return []


class MockDatabaseService:
    """模擬數據庫服務"""
    
    def __init__(self):
        self.connection = MockDatabaseConnection()
        self._connected = True
    
    def is_connected(self) -> bool:
        """檢查是否已連接到數據庫"""
        return self._connected
    
    def execute_function(self, function_name: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """執行數據庫函數"""
        if not self.is_connected():
            raise Exception("未連接到數據庫")
        
        return self.connection.execute_function(function_name, params)


class TestDatabaseFunctions(unittest.TestCase):
    """測試資料庫函數"""
    
    def setUp(self):
        """設置測試環境"""
        self.db_service = MockDatabaseService()
    
    def test_find_service_exact_match(self):
        """測試精確匹配服務"""
        # 執行函數
        results = self.db_service.execute_function(
            "find_service", 
            {"p_business_id": 1, "p_service_name": "基礎美容護理"}
        )
        
        # 驗證結果
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["service_id"], 1)
        self.assertEqual(results[0]["name"], "基礎美容護理")
        self.assertEqual(results[0]["similarity"], 1.0)
    
    def test_find_service_partial_match(self):
        """測試部分匹配服務"""
        # 執行函數
        results = self.db_service.execute_function(
            "find_service", 
            {"p_business_id": 1, "p_service_name": "美容"}
        )
        
        # 驗證結果
        self.assertGreater(len(results), 0)
        # 確保按相似度排序
        for i in range(len(results) - 1):
            self.assertGreaterEqual(results[i]["similarity"], results[i+1]["similarity"])
    
    def test_find_service_no_match(self):
        """測試無匹配服務"""
        # 執行函數
        results = self.db_service.execute_function(
            "find_service", 
            {"p_business_id": 1, "p_service_name": "不存在的服務"}
        )
        
        # 驗證結果
        self.assertEqual(len(results), 0)
    
    def test_get_period_availability(self):
        """測試獲取時段可用性"""
        # 執行函數
        results = self.db_service.execute_function(
            "get_period_availability", 
            {
                "service_name": "基礎美容護理",
                "period_name": "上午",
                "start_date": "2025-03-01",
                "end_date": "2025-03-03"
            }
        )
        
        # 驗證結果
        self.assertEqual(len(results), 3)  # 3天的數據
        
        # 驗證第一天數據 (有一個預約)
        self.assertEqual(results[0]["date"], "2025-03-01")
        self.assertEqual(results[0]["period_name"], "上午")
        self.assertEqual(results[0]["available"], 4)  # 總容量5減去1個預約
        self.assertEqual(results[0]["total_capacity"], 5)
        
        # 驗證其他天數據 (沒有預約)
        for i in range(1, 3):
            self.assertEqual(results[i]["available"], 5)  # 沒有預約，全部可用
    
    def test_get_staff_availability(self):
        """測試獲取員工可用性"""
        # 測試週期性排班 (星期一)
        monday_results = self.db_service.execute_function(
            "get_staff_availability_by_date", 
            {"p_staff_id": 1, "p_date": "2025-03-03"}  # 假設這是星期一
        )
        
        self.assertEqual(len(monday_results), 1)
        self.assertEqual(monday_results[0]["start_time"], "09:00")
        self.assertEqual(monday_results[0]["end_time"], "17:00")
        self.assertTrue(monday_results[0]["is_recurring"])
        
        # 測試特定日期排班
        specific_results = self.db_service.execute_function(
            "get_staff_availability_by_date", 
            {"p_staff_id": 1, "p_date": "2025-03-02"}
        )
        
        self.assertEqual(len(specific_results), 1)
        self.assertEqual(specific_results[0]["start_time"], "09:00")
        self.assertEqual(specific_results[0]["end_time"], "12:00")
        self.assertFalse(specific_results[0]["is_recurring"])
        self.assertEqual(specific_results[0]["specific_date"], "2025-03-02")
    
    def test_get_booking_details(self):
        """測試獲取預約詳情"""
        # 執行函數
        results = self.db_service.execute_function(
            "get_booking_details", 
            {"p_booking_id": 101}
        )
        
        # 驗證結果
        self.assertEqual(len(results), 1)
        booking = results[0]
        
        self.assertEqual(booking["booking_id"], 101)
        self.assertEqual(booking["customer_name"], "王小明")
        self.assertEqual(booking["service_name"], "基礎美容護理")
        self.assertEqual(booking["staff_name"], "張美容師")
        self.assertEqual(booking["date"], "2025-03-01")
        self.assertEqual(booking["period_name"], "上午")
        self.assertEqual(booking["status"], "confirmed")
    
    def test_get_booking_details_not_found(self):
        """測試獲取不存在的預約詳情"""
        # 執行函數
        results = self.db_service.execute_function(
            "get_booking_details", 
            {"p_booking_id": 9999}
        )
        
        # 驗證結果
        self.assertEqual(len(results), 0)


if __name__ == '__main__':
    unittest.main()
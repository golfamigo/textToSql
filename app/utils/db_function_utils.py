from ..schema import db_functions
from typing import Dict, List, Any, Optional, Tuple
import re

def get_function_suggestion(query: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    根據用戶查詢，推薦最適合的數據庫函數
    
    Args:
        query: 用戶的自然語言查詢
        
    Returns:
        推薦函數名稱和函數信息的元組，如果沒有合適的函數則返回 None
    """
    # 查詢關鍵詞與函數的映射
    keyword_mappings = {
        # 預約相關
        'booking': ['get_booking_details', 'get_bookings_by_customer_email', 'get_bookings_by_customer_phone'],
        '預約': ['get_booking_details', 'get_bookings_by_customer_email', 'get_bookings_by_customer_phone'],
        '客戶預約': ['get_bookings_by_customer_email', 'get_bookings_by_customer_phone'],
        
        # 服務相關
        'service': ['find_service', 'get_all_services', 'get_service_booking_settings', 'get_staff_by_service'],
        '服務': ['find_service', 'get_all_services', 'get_service_booking_settings', 'get_staff_by_service'],
        
        # 員工相關
        'staff': ['get_all_staff', 'get_staff_availability_by_date', 'get_staff_by_service', 'get_staff_schedule', 'get_staff_services'],
        '員工': ['get_all_staff', 'get_staff_availability_by_date', 'get_staff_by_service', 'get_staff_schedule', 'get_staff_services'],
        '人員': ['get_all_staff', 'get_staff_availability_by_date', 'get_staff_by_service'],
        
        # 時段相關
        'period': ['get_all_periods', 'get_period_availability', 'get_period_availability_by_date', 'get_period_availability_by_service'],
        '時段': ['get_all_periods', 'get_period_availability', 'get_period_availability_by_date', 'get_period_availability_by_service'],
        '可用時段': ['get_period_availability', 'get_period_availability_by_date', 'get_period_availability_by_service'],
        
        # 可用性相關
        'availability': ['get_detailed_availability', 'get_period_availability', 'get_staff_availability_by_date'],
        '可用性': ['get_detailed_availability', 'get_period_availability', 'get_staff_availability_by_date'],
        '空檔': ['get_period_availability', 'get_staff_availability_by_date']
    }
    
    # 查找查詢中包含的關鍵詞
    potential_functions = []
    for keyword, functions in keyword_mappings.items():
        if keyword.lower() in query.lower():
            potential_functions.extend(functions)
    
    # 如果沒有找到匹配的關鍵詞
    if not potential_functions:
        return None
    
    # 計算每個函數的出現次數
    function_counts = {}
    for func in potential_functions:
        if func in function_counts:
            function_counts[func] += 1
        else:
            function_counts[func] = 1
    
    # 按出現次數排序
    sorted_functions = sorted(function_counts.items(), key=lambda x: x[1], reverse=True)
    
    # 返回出現次數最多且沒有解析錯誤的函數
    for func_name, _ in sorted_functions:
        if func_name in db_functions:
            func_info = db_functions[func_name]
            # 確認此函數沒有解析錯誤
            if not func_info.get('has_parse_error', False):
                return func_name, func_info
    
    return None


def generate_function_example(func_name: str, func_info: Dict[str, Any]) -> str:
    """
    生成函數使用示例
    
    Args:
        func_name: 函數名稱
        func_info: 函數信息
        
    Returns:
        函數使用示例
    """
    # 檢查函數是否有解析錯誤
    if func_info.get('has_parse_error', False):
        return f"-- 此函數解析有誤，請使用原生 SQL 替代: {func_info.get('error', '未知錯誤')}"
    
    try:
        # 提取參數
        params = func_info.get('parameters', '')
        param_list = [p.strip() for p in re.split(r',(?![^(]*\))', params)]
        
        # 生成示例參數
        example_params = []
        for param in param_list:
            # 忽略空參數
            if not param.strip():
                continue
                
            param_parts = param.strip().split(' ')
            if len(param_parts) >= 2:
                param_name = param_parts[0].replace('p_', '')
                param_type = param_parts[-1]
                
                # 根據參數類型生成示例值
                if 'uuid' in param_type:
                    example_params.append("'12345678-1234-1234-1234-123456789012'")
                elif 'text' in param_type or 'varchar' in param_type:
                    example_params.append(f"'{param_name}_example'")
                elif 'date' in param_type:
                    example_params.append("CURRENT_DATE")
                elif 'int' in param_type or 'integer' in param_type:
                    example_params.append("1")
                elif 'bool' in param_type or 'boolean' in param_type:
                    example_params.append("true")
                else:
                    example_params.append("NULL")
        
        # 組合示例
        example = f"SELECT * FROM {func_name}({', '.join(example_params)});"
        
        return example
    except Exception as e:
        # 如果生成示例時出錯，提供備用方案
        return f"-- 無法生成示例: {str(e)}, 請使用適當的參數值調用此函數"


def get_function_examples() -> Dict[str, str]:
    """
    獲取所有函數的使用示例
    
    Returns:
        函數名稱到使用示例的映射
    """
    examples = {}
    
    for func_name, func_info in db_functions.items():
        # 只為沒有解析錯誤的函數生成示例
        if not func_info.get('has_parse_error', False):
            examples[func_name] = generate_function_example(func_name, func_info)
    
    return examples


def get_fallback_query(query: str, func_name: str) -> str:
    """
    當函數無法使用時，生成回退 SQL 查詢
    
    Args:
        query: 原始自然語言查詢
        func_name: 有問題的函數名稱
        
    Returns:
        回退的 SQL 查詢建議
    """
    fallback_queries = {
        # 預約相關
        'get_booking_details': """
-- 預約詳情查詢替代方案
SELECT 
    b.id, b.booking_start_time, b.booking_end_time, b.status,
    c.name as customer_name, c.email as customer_email, c.phone as customer_phone,
    s.name as service_name, s.price as service_price,
    staff.name as staff_name
FROM 
    n8n_booking_bookings b
JOIN 
    n8n_booking_users c ON b.customer_id = c.id
JOIN 
    n8n_booking_services s ON b.service_id = s.id
LEFT JOIN 
    n8n_booking_users staff ON b.staff_id = staff.id
WHERE 
    b.id = '12345678-1234-1234-1234-123456789012';  -- 請替換為實際預約ID
""",
        
        'get_bookings_by_customer_email': """
-- 查詢客戶預約的替代方案
SELECT 
    b.id, b.booking_start_time, b.booking_end_time, b.status,
    s.name as service_name,
    staff.name as staff_name
FROM 
    n8n_booking_bookings b
JOIN 
    n8n_booking_users c ON b.customer_id = c.id
JOIN 
    n8n_booking_services s ON b.service_id = s.id
LEFT JOIN 
    n8n_booking_users staff ON b.staff_id = staff.id
WHERE 
    c.email LIKE '%example@email.com%';  -- 請替換為實際客戶信箱
""",
        
        # 服務相關
        'find_service': """
-- 搜尋服務的替代方案
SELECT 
    id, name, description, price, duration
FROM 
    n8n_booking_services
WHERE 
    business_id = '12345678-1234-1234-1234-123456789012'  -- 請替換為實際商家ID
    AND (
        LOWER(name) LIKE LOWER('%服務名稱%')  -- 請替換為實際服務名稱
        OR similarity(LOWER(name), LOWER('服務名稱')) > 0.3
    )
ORDER BY 
    similarity(LOWER(name), LOWER('服務名稱')) DESC,
    name
LIMIT 1;
""",
        
        # 時段相關
        'get_period_availability': """
-- 查詢時段可用性的替代方案
WITH local_bookings AS (
    SELECT 
        b.id,
        (b.booking_start_time AT TIME ZONE 'Asia/Taipei')::date as local_date,
        b.period_id
    FROM 
        n8n_booking_bookings b
    WHERE 
        b.status = 'confirmed'
        AND b.business_id = '12345678-1234-1234-1234-123456789012'  -- 請替換為實際商家ID
)
SELECT 
    d.date::date as booking_date,
    tp.name as period_name,
    tp.max_capacity - COUNT(b.id)::integer as available_slots,
    tp.max_capacity
FROM 
    generate_series(CURRENT_DATE, CURRENT_DATE + interval '7 days', '1 day'::interval) d(date)
CROSS JOIN 
    n8n_booking_time_periods tp
JOIN 
    n8n_booking_services s ON s.business_id = tp.business_id
LEFT JOIN 
    local_bookings b ON b.local_date = d.date AND b.period_id = tp.id
WHERE 
    s.name = '基礎美容護理'  -- 請替換為實際服務名稱
    AND tp.name = '上午'  -- 請替換為實際時段名稱
GROUP BY 
    d.date, tp.name, tp.max_capacity
ORDER BY 
    d.date;
""",
        
        # 其他函數的回退查詢...
    }
    
    # 返回對應的回退查詢，如果沒有特定的回退查詢則返回通用查詢
    return fallback_queries.get(func_name, "-- 請使用直接查詢表代替函數調用")


def is_function_working(func_name: str) -> bool:
    """
    檢查函數是否可用
    
    Args:
        func_name: 函數名稱
        
    Returns:
        函數是否可用
    """
    if func_name not in db_functions:
        return False
    
    func_info = db_functions[func_name]
    return not func_info.get('has_parse_error', False)
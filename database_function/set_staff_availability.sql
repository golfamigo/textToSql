--- START OF FILE set_staff_availability.sql ---
-- 先刪除現有函數
DROP FUNCTION IF EXISTS set_staff_availability CASCADE;
-- 函數功能：設置員工可用時間。
-- 參數:
--   p_staff_id UUID: 員工 ID
--   p_business_id UUID: 商家 ID
--   p_start_time TIME: 可用時間開始時間
--   p_end_time TIME: 可用時間結束時間
--   p_is_recurring BOOLEAN: 是否為週期性可用時間
--   p_day_of_week INTEGER (optional, default: NULL): 星期幾 (僅在週期性可用時間時使用)
--   p_specific_date DATE (optional, default: NULL): 特定日期 (僅在非週期性可用時間時使用)
--   p_availability_type availability_type (optional, default: 'available'): 可用性類型 (available 或 unavailable)
-- 返回值:
--   JSON: 包含操作結果，包括 success (boolean) 和 message (text)
-- 設置員工可用時間
CREATE OR REPLACE FUNCTION set_staff_availability(
    p_staff_id UUID,
    p_business_id UUID,
    p_start_time TIME,
    p_end_time TIME,
    p_is_recurring BOOLEAN,
    p_day_of_week INTEGER DEFAULT NULL,
    p_specific_date DATE DEFAULT NULL,
    p_availability_type availability_type DEFAULT 'available'
) RETURNS JSON AS $$
DECLARE
    v_staff_id UUID;
BEGIN
    -- 驗證輸入
    IF p_is_recurring AND p_day_of_week IS NULL THEN
        RETURN json_build_object(
            'success', false,
            'message', '週期性可用時間必須指定星期幾'
        );
    END IF;
    
    IF NOT p_is_recurring AND p_specific_date IS NULL THEN
        RETURN json_build_object(
            'success', false,
            'message', '非週期性可用時間必須指定具體日期'
        );
    END IF;
    
    -- 插入可用時間記錄
    INSERT INTO n8n_booking_staff_availability (
        staff_id,
        business_id,
        start_time,
        end_time,
        is_recurring,
        day_of_week,
        specific_date,
        availability_type
    ) VALUES (
        p_staff_id,
        p_business_id,
        p_start_time,
        p_end_time,
        p_is_recurring,
        p_day_of_week,
        p_specific_date,
        p_availability_type
    );
    
    RETURN json_build_object(
        'success', true,
        'message', '員工可用時間已成功設置'
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'message', '設置員工可用時間時發生錯誤: ' || SQLERRM
        );
END;
$$ LANGUAGE plpgsql;
--- END OF FILE set_staff_availability.sql ---
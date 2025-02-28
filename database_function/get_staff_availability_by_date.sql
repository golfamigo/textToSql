--- START OF FILE get_staff_availability_by_date.sql ---
-- 先刪除現有函數
DROP FUNCTION IF EXISTS get_staff_availability_by_date CASCADE;

-- 函數功能：獲取員工在特定日期的可用時間。
-- 參數:
--   p_staff_id UUID: 員工 ID
--   p_date DATE: 查詢日期
-- 返回值:
--   TABLE: 包含員工在特定日期的可用時間資訊的表格，包含 start_time, end_time, availability_type, is_recurring, day_of_week, specific_date
CREATE OR REPLACE FUNCTION get_staff_availability_by_date(
    p_staff_id UUID,
    p_date DATE
) RETURNS TABLE (
    start_time TIME,
    end_time TIME,
    availability_type availability_type,
    is_recurring BOOLEAN,
    day_of_week INTEGER,
    specific_date DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        sa.start_time,
        sa.end_time,
        sa.availability_type,
        sa.is_recurring,
        sa.day_of_week,
        sa.specific_date
    FROM n8n_booking_staff_availability sa
    WHERE sa.staff_id = p_staff_id
    AND (
        (sa.is_recurring = true AND sa.day_of_week = EXTRACT(DOW FROM p_date))
        OR
        (sa.is_recurring = false AND sa.specific_date = p_date)
    )
    ORDER BY sa.start_time;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_staff_availability_by_date.sql ---

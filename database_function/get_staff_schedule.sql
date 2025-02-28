--- START OF FILE get_staff_schedule.sql ---
-- 先刪除現有函數
DROP FUNCTION IF EXISTS get_staff_schedule CASCADE;
-- 函數功能：獲取員工的預約排程。
-- 參數:
--   p_staff_id UUID: 員工 ID
--   p_start_date DATE: 排程開始日期
--   p_end_date DATE: 排程結束日期
-- 返回值:
--   TABLE: 包含員工預約排程的表格，
--     booking_id UUID,
--     booking_date DATE,
--     start_time TIMESTAMP WITH TIME ZONE,
--     end_time TIMESTAMP WITH TIME ZONE,
--     service_name TEXT,
--     customer_name TEXT,
--     customer_phone TEXT,
--     number_of_people INTEGER,
--     status TEXT
CREATE OR REPLACE FUNCTION get_staff_schedule(
    p_staff_id UUID,
    p_start_date DATE,
    p_end_date DATE
) RETURNS TABLE (
    booking_id UUID,
    booking_date DATE,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    service_name TEXT,
    customer_name TEXT,
    customer_phone TEXT,
    number_of_people INTEGER,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.id AS booking_id,
        b.booking_date,
        b.booking_start_time AS start_time,
        b.booking_start_time + b.booking_duration AS end_time,
        s.name AS service_name,
        b.customer_name,
        b.customer_phone,
        b.number_of_people,
        b.status
    FROM n8n_booking_bookings b
    JOIN n8n_booking_services s ON b.service_id = s.id
    WHERE b.staff_id = p_staff_id
    AND b.booking_date BETWEEN p_start_date AND p_end_date
    AND b.status = 'confirmed'
    ORDER BY b.booking_date, b.booking_start_time;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_staff_schedule.sql ---

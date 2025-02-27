DROP FUNCTION IF EXISTS get_bookings_by_customer_phone CASCADE;

--- START OF FILE get_bookings_by_customer_phone.sql ---
-- 函數功能：根據顧客電話號碼查詢預約
-- 參數:
--   p_customer_phone text: 顧客電話號碼
-- 返回值:
--   TABLE: 包含預約資訊的表格
CREATE OR REPLACE FUNCTION get_bookings_by_customer_phone(p_customer_phone text)
RETURNS TABLE (
    id uuid,
    customer_name text,
    customer_email text,
    customer_phone text,
    booking_date date,
    booking_start_time timestamp with time zone,
    booking_end_time timestamp with time zone,
    booking_duration interval,
    number_of_people integer,
    status text,
    service_name text,
    period_name text
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.id,
        b.customer_name,
        b.customer_email,
        b.customer_phone,
        b.booking_date,
        b.booking_start_time,
        (b.booking_start_time + b.booking_duration),
        b.booking_duration,
        b.number_of_people,
        b.status,
        s.name as service_name,
        tp.name as period_name
    FROM
        n8n_booking_bookings b
    JOIN
        n8n_booking_services s ON b.service_id = s.id
    JOIN
        n8n_booking_time_periods tp ON b.period_id = tp.id
    WHERE
        b.customer_phone = p_customer_phone
    ORDER BY
        b.booking_start_time DESC;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_bookings_by_customer_phone.sql ---

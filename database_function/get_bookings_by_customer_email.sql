DROP FUNCTION IF EXISTS get_bookings_by_customer_email CASCADE;

--- START OF FILE get_bookings_by_customer_email.sql ---
-- 函數功能：根據顧客 Email 查詢預約
-- 參數:
--   p_customer_email text: 顧客 Email
-- 返回值:
--   TABLE: 包含預約資訊的表格
CREATE OR REPLACE FUNCTION get_bookings_by_customer_email(p_customer_email text)
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
        b.customer_email = p_customer_email
    ORDER BY
        b.booking_start_time DESC;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_bookings_by_customer_email.sql ---
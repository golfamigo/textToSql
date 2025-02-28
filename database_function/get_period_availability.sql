DROP FUNCTION IF EXISTS get_period_availability CASCADE;

--- START OF FILE get_period_availability.sql ---
-- 函數功能：獲取特定服務和時段在指定日期範圍內的可用性
-- 參數:
--   p_service_name text: 服務名稱
--   p_period_name text: 時段名稱
--   p_start_date date: 開始日期
--   p_end_date date: 結束日期
-- 返回值:
--   TABLE: 包含每日時段可用性資訊的表格
CREATE OR REPLACE FUNCTION get_period_availability(
    p_service_name text,
    p_period_name text,
    p_start_date date,
    p_end_date date
)
RETURNS TABLE (
    booking_date date,
    period_name text,
    available_slots integer,
    total_capacity integer
)
AS $$
DECLARE
    v_business_timezone text;
    v_business_id uuid;
BEGIN
    -- 獲取服務對應的商家和時區
    SELECT s.business_id, b.timezone
    INTO v_business_id, v_business_timezone
    FROM n8n_booking_services s
    JOIN n8n_booking_businesses b ON b.id = s.business_id
    WHERE s.name = p_service_name
    LIMIT 1;

    RETURN QUERY
    WITH local_bookings AS (
        -- 轉換預約時間到商家時區
        SELECT
            b.id,
            (b.booking_start_time AT TIME ZONE v_business_timezone)::date as local_date,
            b.period_id
        FROM n8n_booking_bookings b
        WHERE b.status = 'confirmed'
        AND b.business_id = v_business_id
    )
    SELECT
        d.date::date as booking_date,
        tp.name as period_name,
        tp.max_capacity - COUNT(b.id)::integer as available_slots,
        tp.max_capacity
    FROM generate_series(p_start_date, p_end_date, '1 day'::interval) d(date)
    CROSS JOIN n8n_booking_time_periods tp
    JOIN n8n_booking_services s ON s.business_id = tp.business_id
    LEFT JOIN local_bookings b ON
        b.local_date = d.date
        AND b.period_id = tp.id
    WHERE
        s.name = p_service_name
        AND tp.name = p_period_name
    GROUP BY d.date, tp.name, tp.max_capacity
    ORDER BY d.date;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_period_availability.sql ---

DROP FUNCTION IF EXISTS get_service_booking_settings CASCADE;

--- START OF FILE get_service_booking_settings.sql ---
-- 函數功能：獲取服務預約設定
-- 參數:
--   p_business_id uuid: 商家 ID
-- 返回值:
--   TABLE: 包含服務預約設定的表格，包括 service_id, service_name, service_min_booking_lead_time, business_min_booking_lead_time
CREATE OR REPLACE FUNCTION get_service_booking_settings(
    p_business_id uuid
)
RETURNS TABLE (
    service_id uuid,
    service_name text,
    service_min_booking_lead_time interval,
    business_min_booking_lead_time interval
)
AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id as service_id,
        s.name as service_name,
        s.min_booking_lead_time as service_min_booking_lead_time,
        b.min_booking_lead_time as business_min_booking_lead_time
    FROM
        n8n_booking_services s
    JOIN
        n8n_booking_businesses b ON s.business_id = b.id
    WHERE
        s.business_id = p_business_id
        AND s.is_active = true
    ORDER BY
        s.name;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_service_booking_settings.sql ---

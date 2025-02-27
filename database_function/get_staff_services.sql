--- START OF FILE get_staff_services.sql ---
-- 先刪除現有函數
DROP FUNCTION IF EXISTS get_staff_services CASCADE;

-- 函數功能：獲取員工可提供的服務
-- 參數:
--   p_staff_id UUID: 員工 ID
-- 返回值:
--   TABLE: 包含員工可提供的服務資訊的表格，包含 service_id, service_name, description, duration, price, is_primary, proficiency_level
CREATE OR REPLACE FUNCTION get_staff_services(
    p_staff_id UUID
) RETURNS TABLE (
    service_id UUID,
    service_name TEXT,
    description TEXT,
    duration INTEGER,
    price NUMERIC,
    is_primary BOOLEAN,
    proficiency_level INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id AS service_id,
        s.name AS service_name,
        s.description,
        s.duration,
        s.price,
        ss.is_primary,
        ss.proficiency_level
    FROM n8n_booking_staff_services ss
    JOIN n8n_booking_services s ON ss.service_id = s.id
    WHERE ss.staff_id = p_staff_id
    AND s.is_active = true
    ORDER BY ss.is_primary DESC, s.name;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_staff_services.sql ---

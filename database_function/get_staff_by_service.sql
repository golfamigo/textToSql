--- START OF FILE get_staff_by_service.sql ---
-- 先刪除現有函數
DROP FUNCTION IF EXISTS get_staff_by_service CASCADE;
-- 函數功能：獲取可提供特定服務的員工列表
-- 參數:
--   p_business_id UUID: 商家 ID
--   p_service_name TEXT: 服務名稱
-- 返回值:
--   TABLE: 包含員工資訊的表格，欄位包括 staff_id, staff_name, is_primary, proficiency_level
-- 獲取可提供特定服務的員工
CREATE OR REPLACE FUNCTION get_staff_by_service(
    p_business_id UUID,
    p_service_name TEXT
) RETURNS TABLE (
    staff_id UUID,
    staff_name TEXT,
    is_primary BOOLEAN,
    proficiency_level INTEGER
) AS $$
DECLARE
    v_service_id UUID;
    v_matched_name TEXT;
BEGIN
    -- 查找服務 ID
    SELECT * FROM find_service(p_business_id => p_business_id, p_service_name => p_service_name)
    INTO v_service_id, v_matched_name;

    IF v_service_id IS NULL THEN
        RAISE EXCEPTION '找不到該服務，請確認服務名稱是否正確';
    END IF;

    RETURN QUERY
    SELECT
        u.id AS staff_id,
        u.name AS staff_name,
        ss.is_primary,
        ss.proficiency_level
    FROM n8n_booking_staff_services ss
    JOIN n8n_booking_users u ON ss.staff_id = u.id
    WHERE ss.service_id = v_service_id
    AND u.is_active = true
    AND u.role = 'staff'
    ORDER BY ss.is_primary DESC, ss.proficiency_level DESC, u.name;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_staff_by_service.sql ---

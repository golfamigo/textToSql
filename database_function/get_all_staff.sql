--- START OF FILE get_all_staff.sql ---
-- 先刪除現有函數
DROP FUNCTION IF EXISTS get_all_staff CASCADE;
-- 函數功能：獲取所有員工
-- 參數:
--   p_business_id UUID: 商家 ID
--   p_include_inactive BOOLEAN (optional, default: false): 是否包含非活躍員工
-- 返回值:
--   TABLE: 包含員工資訊的表格，欄位包括 id, name, email, phone, line_user_id, is_active, notes, created_at
-- 獲取所有員工。
CREATE OR REPLACE FUNCTION get_all_staff(
    p_business_id UUID,
    p_include_inactive BOOLEAN DEFAULT false
) RETURNS TABLE (
    id UUID,
    name TEXT,
    email TEXT,
    phone TEXT,
    line_user_id TEXT,
    is_active BOOLEAN,
    notes TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id, u.name, u.email, u.phone, u.line_user_id,
        u.is_active, u.notes, u.created_at
    FROM n8n_booking_users u
    WHERE u.business_id = p_business_id
    AND u.role = 'staff'
    AND (p_include_inactive OR u.is_active = true)
    ORDER BY u.name;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_all_staff.sql ---

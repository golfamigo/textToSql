DROP FUNCTION IF EXISTS update_staff CASCADE;

--- START OF FILE update_staff.sql ---
-- 更新員工信息
-- 函數功能：更新員工信息
-- 參數:
--   p_staff_id UUID: 員工 ID
--   p_name TEXT (optional, default: NULL): 員工姓名
--   p_email TEXT (optional, default: NULL): 員工 email
--   p_phone TEXT (optional, default: NULL): 員工電話
--   p_is_active BOOLEAN (optional, default: NULL): 員工是否啟用
--   p_notes TEXT (optional, default: NULL): 員工備註
-- 返回值:
--   JSON: 包含操作結果，包括 success (boolean) 和 message (text)
CREATE OR REPLACE FUNCTION update_staff(
    p_staff_id UUID,
    p_name TEXT DEFAULT NULL,
    p_email TEXT DEFAULT NULL,
    p_phone TEXT DEFAULT NULL,
    p_is_active BOOLEAN DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
) RETURNS JSON AS $$
BEGIN
    UPDATE n8n_booking_users
    SET
        name = COALESCE(p_name, name),
        email = COALESCE(p_email, email),
        phone = COALESCE(p_phone, phone),
        is_active = COALESCE(p_is_active, is_active),
        notes = COALESCE(p_notes, notes),
        updated_at = now()
    WHERE id = p_staff_id AND role = 'staff';

    IF FOUND THEN
        RETURN json_build_object(
            'success', true,
            'message', '員工資料已成功更新'
        );
    ELSE
        RETURN json_build_object(
            'success', false,
            'message', '找不到指定的員工'
        );
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'message', '更新員工資料時發生錯誤: ' || SQLERRM
        );
END;
$$ LANGUAGE plpgsql;
--- END OF FILE update_staff.sql ---

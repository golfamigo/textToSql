--- START OF FILE create_staff.sql ---
-- 先刪除現有函數
DROP FUNCTION IF EXISTS create_staff CASCADE;

-- 函數功能：創建新的員工
-- 參數:
--   p_business_id UUID: 商家 ID
--   p_name TEXT: 員工姓名
--   p_email TEXT: 員工 email
--   p_phone TEXT: 員工電話
--   p_line_user_id TEXT (optional, default: NULL): Line User ID
--   p_notes TEXT (optional, default: NULL): 備註
-- 返回值:
--   JSON: 包含操作結果，包括 success (boolean), staff_id (uuid), message (text)
-- 創建員工
CREATE OR REPLACE FUNCTION create_staff(
    p_business_id UUID,
    p_name TEXT,
    p_email TEXT,
    p_phone TEXT,
    p_line_user_id TEXT DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
) RETURNS JSON AS $$
DECLARE
    v_staff_id UUID;
BEGIN
    INSERT INTO n8n_booking_users (
        role, business_id, name, email, phone, line_user_id, notes, is_active
    ) VALUES (
        'staff', p_business_id, p_name, p_email, p_phone, p_line_user_id, p_notes, true
    ) RETURNING id INTO v_staff_id;
    
    RETURN json_build_object(
        'success', true,
        'staff_id', v_staff_id,
        'message', '員工已成功創建'
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'message', '創建員工時發生錯誤: ' || SQLERRM
        );
END;
$$ LANGUAGE plpgsql;
--- END OF FILE create_staff.sql ---
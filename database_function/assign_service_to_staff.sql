--- START OF FILE assign_service_to_staff.sql ---
DROP FUNCTION IF EXISTS assign_service_to_staff CASCADE;

-- 函數功能：設置員工可提供的專業服務
-- 參數:
--   p_staff_id UUID: 員工 ID
--   p_service_name TEXT: 服務名稱
--   p_business_id UUID: 商家 ID
--   p_is_primary BOOLEAN (optional, default: false): 是否為主要服務
--   p_proficiency_level INTEGER (optional, default: 3): 專業程度
-- 返回值:
--   JSON: 包含操作結果，包括 success (boolean) 和 message (text)
CREATE OR REPLACE FUNCTION assign_service_to_staff(
    p_staff_id UUID,
    p_service_name TEXT,
    p_business_id UUID,
    p_is_primary BOOLEAN DEFAULT false,
    p_proficiency_level INTEGER DEFAULT 3
) RETURNS JSON AS $$
DECLARE
    v_service_id UUID;
    v_matched_name TEXT;
    v_similarity_score REAL;
BEGIN
    -- 查找服務 ID
    SELECT * FROM find_service(p_business_id => p_business_id, p_service_name => p_service_name)
    INTO v_service_id, v_matched_name, v_similarity_score;


    IF v_service_id IS NULL THEN
        RETURN json_build_object(
            'success', false,
            'message', '找不到該服務，請確認服務名稱是否正確'
        );
    END IF;

    -- 檢查員工是否存在
    IF NOT EXISTS(SELECT 1 FROM n8n_booking_users WHERE id = p_staff_id AND role = 'staff') THEN
        RETURN json_build_object(
            'success', false,
            'message', '找不到指定的員工'
        );
    END IF;

    -- 插入或更新服務關聯
    INSERT INTO n8n_booking_staff_services (
        staff_id, service_id, is_primary, proficiency_level
    ) VALUES (
        p_staff_id, v_service_id, p_is_primary, p_proficiency_level
    ) ON CONFLICT (staff_id, service_id) DO UPDATE
    SET
        is_primary = p_is_primary,
        proficiency_level = p_proficiency_level;

    RETURN json_build_object(
        'success', true,
        'message', '已成功將服務 "' || v_matched_name || '" 分配給員工'
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'message', '分配服務時發生錯誤: ' || SQLERRM
        );
END;
$$ LANGUAGE plpgsql;
--- END OF FILE assign_service_to_staff.sql ---

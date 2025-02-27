--- START OF FILE delete_service_period_restriction.sql ---
-- 刪除服務時段限制 (使用服務名稱)
-- 函數功能：刪除特定服務和時段的限制
-- 參數:
--   p_business_id uuid: 商家 ID
--   p_service_name text: 服務名稱
--   p_period_id uuid: 時段 ID
-- 返回值:
--   JSON: 包含操作結果，包括 success (boolean), restriction_id (uuid), message (text) 和 matched_service_name (text)
-- 先刪除現有函數
DROP FUNCTION IF EXISTS delete_service_period_restriction CASCADE;

CREATE OR REPLACE FUNCTION delete_service_period_restriction(
    p_business_id uuid,
    p_service_name text,  -- 使用服務名稱
    p_period_id uuid
)
RETURNS json AS $$
DECLARE
    v_restriction_id uuid;
    v_service_id uuid;
BEGIN
    -- 查找服務 ID
    SELECT service_id 
    FROM find_service(p_business_id => p_business_id, p_service_name => p_service_name)
    INTO v_service_id;

    IF v_service_id IS NULL THEN
        RETURN json_build_object('success', false, 'message', '找不到該服務，請確認服務名稱是否正確');
    END IF;

    -- 先檢查是否存在相關的未來預約
    IF EXISTS (
        SELECT 1 
        FROM n8n_booking_bookings b
        WHERE b.service_id = v_service_id  -- 使用找到的 service_id
          AND b.period_id = p_period_id
          AND b.booking_date >= CURRENT_DATE
          AND b.status = 'confirmed'
    ) THEN
        RETURN json_build_object(
            'success', false,
            'message', '此時段已有未來預約，無法刪除限制'
        );
    END IF;

    -- 刪除限制
    DELETE FROM n8n_booking_service_period_restrictions
    WHERE service_id = v_service_id  -- 使用找到的 service_id
      AND period_id = p_period_id
    RETURNING id INTO v_restriction_id;

    IF FOUND THEN
        RETURN json_build_object(
            'success', true,
            'message', '服務時段限制已刪除',
            'restriction_id', v_restriction_id
        );
    ELSE
        RETURN json_build_object(
            'success', false,
            'message', '找不到指定的服務時段限制'
        );
    END IF;

EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'message', '刪除服務時段限制時發生錯誤',
            'error', SQLERRM
        );
END;
$$ LANGUAGE plpgsql;
--- END OF FILE delete_service_period_restriction.sql ---
--- START OF FILE create_service_period_restriction.sql ---
-- 新增服務時段限制 (使用服務名稱)
-- 函數功能：為特定服務和時段創建限制
-- 參數:
--   p_business_id uuid: 商家 ID
--   p_service_name text: 服務名稱
--   p_period_id uuid: 時段 ID
--   p_is_allowed boolean (optional, default: true): 是否允許預約
-- 返回值:
--   JSON: 包含操作結果，包括 success (boolean), restriction_id (uuid), message (text), service_name (text)
-- 先刪除現有函數
DROP FUNCTION IF EXISTS create_service_period_restriction CASCADE;

CREATE OR REPLACE FUNCTION create_service_period_restriction(
    p_business_id uuid,
    p_service_name text,  -- 使用服務名稱
    p_period_id uuid,
    p_is_allowed boolean DEFAULT true
)
RETURNS json AS $$
DECLARE
    v_restriction_id uuid;
    v_service_id uuid;
    v_matched_name text;
BEGIN
    -- 查找服務 ID
    SELECT service_id, matched_name 
    FROM find_service(p_business_id => p_business_id, p_service_name => p_service_name)
    INTO v_service_id, v_matched_name;

    IF v_service_id IS NULL THEN
        RETURN json_build_object('success', false, 'message', '找不到該服務，請確認服務名稱是否正確');
    END IF;

    -- 驗證時段存在
    IF NOT EXISTS (SELECT 1 FROM n8n_booking_time_periods WHERE id = p_period_id) THEN
        RETURN json_build_object('success', false, 'message', '找不到指定的時段');
    END IF;

    -- 插入或更新限制
    INSERT INTO n8n_booking_service_period_restrictions (
        service_id,
        period_id,
        is_allowed
    ) VALUES (
        v_service_id,  -- 使用找到的 service_id
        p_period_id,
        p_is_allowed
    )
    ON CONFLICT (service_id, period_id)
    DO UPDATE SET
        is_allowed = EXCLUDED.is_allowed,
        updated_at = now()
    RETURNING id INTO v_restriction_id;

    RETURN json_build_object(
        'success', true,
        'restriction_id', v_restriction_id,
        'message', '服務時段限制設定成功',
        'service_name', v_matched_name  -- 返回匹配到的服務名稱
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object('success', false, 'message', SQLERRM);
END;
$$ LANGUAGE plpgsql;
--- END OF FILE create_service_period_restriction.sql ---
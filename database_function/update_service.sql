--- START OF FILE update_service.sql ---
-- 更新服務 (同時支援服務 ID 和服務名稱)
-- 函數功能：更新服務項目信息
-- 參數:
--   p_business_id uuid: 商家 ID
--   p_service_id uuid (optional, default: NULL): 服務 ID
--   p_service_name text (optional, default: NULL): 服務名稱
--   p_name text (optional, default: NULL): 服務項目名稱
--   p_description text (optional, default: NULL): 服務項目描述
--   p_duration integer (optional, default: NULL): 服務項目時長(分鐘)
--   p_price numeric (optional, default: NULL): 服務項目價格
--   p_max_capacity integer (optional, default: NULL): 服務項目最大容量
--   p_min_booking_lead_time interval (optional, default: NULL): 服務項目最小預約提前時間
--   p_is_active boolean (optional, default: NULL): 服務項目是否啟用
-- 返回值:
--   JSON: 包含操作結果，包括 success (boolean), service_id (uuid), message (text)
-- 先刪除現有函數
DROP FUNCTION IF EXISTS update_service CASCADE;

CREATE OR REPLACE FUNCTION update_service(
    p_business_id uuid,
    p_service_id uuid DEFAULT NULL,          -- 保留 service_id 參數
    p_service_name text DEFAULT NULL,      -- 新增 service_name 參數
    p_name text DEFAULT NULL,
    p_description text DEFAULT NULL,
    p_duration integer DEFAULT NULL,
    p_price numeric DEFAULT NULL,
    p_max_capacity integer DEFAULT NULL,
    p_min_booking_lead_time interval DEFAULT NULL,
    p_is_active boolean DEFAULT NULL
)
RETURNS json
AS $$
DECLARE
    v_service_exists boolean;
    v_current_service record;
    v_service_id_to_use uuid;  -- 用於儲存實際使用的 service_id
BEGIN
    -- 優先使用 service_name 查找 service_id
    IF p_service_name IS NOT NULL THEN
        SELECT service_id
        FROM find_service(p_business_id => p_business_id, p_service_name => p_service_name)
        INTO v_service_id_to_use;

    IF v_service_id_to_use IS NULL THEN
        RETURN json_build_object('success', false, 'message', '找不到該服務，請確認服務名稱是否正確');
    END IF;
    ELSE
        -- 如果沒有提供 service_name，則使用 p_service_id
        v_service_id_to_use := p_service_id;
    END IF;

     -- 檢查服務是否存在
    SELECT EXISTS(SELECT 1 FROM n8n_booking_services WHERE id = v_service_id_to_use) INTO v_service_exists;
    IF NOT v_service_exists THEN
        RETURN json_build_object('success', false, 'message', '找不到服務項目.');
    END IF;


    -- 取得現有服務資料
    SELECT * INTO v_current_service
    FROM n8n_booking_services
    WHERE id = v_service_id_to_use;

    -- 驗證輸入
    IF COALESCE(p_name, v_current_service.name) IS NULL OR trim(COALESCE(p_name, v_current_service.name)) = '' THEN
        RETURN json_build_object('success', false, 'message', '服務項目名稱不能為空.');
    END IF;
    IF COALESCE(p_duration, v_current_service.duration) <= 0 THEN
        RETURN json_build_object('success', false, 'message', '服務項目時長必須是正整數.');
    END IF;
    IF COALESCE(p_max_capacity, v_current_service.max_capacity) <= 0 THEN
        RETURN json_build_object('success', false, 'message', '服務項目最大容量必須是正整數.');
    END IF;

    -- 更新服務
    UPDATE n8n_booking_services
    SET
        name         = COALESCE(p_name, v_current_service.name),
        description  = COALESCE(p_description, v_current_service.description),
        duration     = COALESCE(p_duration, v_current_service.duration),
        price        = COALESCE(p_price, v_current_service.price),
        max_capacity = COALESCE(p_max_capacity, v_current_service.max_capacity),
        min_booking_lead_time = COALESCE(p_min_booking_lead_time, v_current_service.min_booking_lead_time),
        is_active    = COALESCE(p_is_active, v_current_service.is_active),
        updated_at   = NOW()
    WHERE id = v_service_id_to_use;  -- 使用找到的或傳入的 service_id

    RETURN json_build_object(
        'success', true,
        'service_id', v_service_id_to_use,
        'message', '服務項目更新成功.'
    );

EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('success', false, 'message', SQLERRM);
END;
$$ LANGUAGE plpgsql;
--- END OF FILE update_service.sql ---
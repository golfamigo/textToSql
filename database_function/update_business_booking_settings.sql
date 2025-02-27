DROP FUNCTION IF EXISTS update_business_booking_settings CASCADE;

--- START OF FILE update_business_booking_settings.sql ---
-- 函數功能：更新商家預約設定
-- 參數:
--   p_business_id uuid: 商家 ID
--   p_min_booking_lead_time interval: 最小預約提前時間間隔
-- 返回值:
--   JSON: 包含操作結果，包括 success (boolean) 和 message (text)
CREATE OR REPLACE FUNCTION update_business_booking_settings(
    p_business_id uuid,
    p_min_booking_lead_time interval
)
RETURNS json
AS $$
BEGIN
    IF p_min_booking_lead_time IS NULL OR p_min_booking_lead_time < interval '0' THEN
        RETURN json_build_object('success', false, 'message', '提前預約時間必須是有效的時間間隔');
    END IF;

    UPDATE n8n_booking_businesses
    SET min_booking_lead_time = p_min_booking_lead_time,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_business_id;
    
    IF NOT FOUND THEN
        RETURN json_build_object('success', false, 'message', '找不到該商家');
    END IF;
    
    RETURN json_build_object(
        'success', true,
        'message', '預約設定已更新，現在客戶需要提前 ' || 
            EXTRACT(EPOCH FROM p_min_booking_lead_time)/3600 || ' 小時預約'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('success', false, 'message', SQLERRM);
END;
$$ LANGUAGE plpgsql;
--- END OF FILE update_business_booking_settings.sql ---
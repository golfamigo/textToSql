DROP FUNCTION IF EXISTS update_service_period_restriction CASCADE;

--- START OF FILE update-service-period-restriction.sql ---
-- 函數功能：更新服務時段限制
-- 參數:
--   p_restriction_id uuid: 限制 ID
--   p_is_allowed boolean (optional, default: NULL): 是否允許預約
-- 返回值:
--   JSON: 包含操作結果，包括 success (boolean), restriction_id (uuid), is_allowed (boolean)
CREATE OR REPLACE FUNCTION update_service_period_restriction(
    p_restriction_id uuid,
    p_is_allowed boolean = NULL  -- 將狀態設為 NULL 表示不更新該欄位
)
RETURNS json AS $$
DECLARE
    v_service_id uuid;
    v_period_id uuid;
    v_current_allowed boolean;
BEGIN
    -- 檢查限制是否存在
    SELECT 
        service_id,
        period_id,
        is_allowed 
    INTO 
        v_service_id,
        v_period_id,
        v_current_allowed
    FROM n8n_booking_service_period_restrictions
    WHERE id = p_restriction_id;

    IF NOT FOUND THEN
        RETURN json_build_object(
            'success', false,
            'message', '找不到指定的服務時段限制'
        );
    END IF;

    -- 如果提供了新的狀態，則更新
    IF p_is_allowed IS NOT NULL AND p_is_allowed != v_current_allowed THEN
        -- 檢查是否有相關的未來預約
        IF EXISTS (
            SELECT 1 
            FROM n8n_booking_bookings b
            WHERE b.service_id = v_service_id
              AND b.period_id = v_period_id
              AND b.booking_date >= CURRENT_DATE
              AND b.status = 'confirmed'
        ) AND NOT p_is_allowed THEN  -- 只在要禁用時段時檢查
            RETURN json_build_object(
                'success', false,
                'message', '此時段已有未來預約，無法禁用'
            );
        END IF;

        -- 更新限制
        UPDATE n8n_booking_service_period_restrictions
        SET 
            is_allowed = p_is_allowed,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = p_restriction_id;

        RETURN json_build_object(
            'success', true,
            'message', '服務時段限制已更新',
            'restriction_id', p_restriction_id,
            'is_allowed', p_is_allowed
        );
    END IF;

    -- 如果沒有提供新狀態或狀態相同
    RETURN json_build_object(
        'success', true,
        'message', '服務時段限制未變更',
        'restriction_id', p_restriction_id,
        'is_allowed', v_current_allowed
    );

EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'message', '更新服務時段限制時發生錯誤',
            'error', SQLERRM
        );
END;
$$ LANGUAGE plpgsql;
--- END OF FILE update-service-period-restriction.sql ---
DROP FUNCTION IF EXISTS delete_period CASCADE;

--- START OF FILE delete_period.sql ---
-- 函數功能：軟刪除時段
-- 參數:
--   p_period_id uuid: 時段 ID
-- 返回值:
--   JSON: 包含操作結果，包括 success (boolean), period_id (uuid), message (text)
CREATE OR REPLACE FUNCTION delete_period(
    p_period_id uuid
)
RETURNS json
AS $$
DECLARE
    v_period_exists boolean;
    v_bookings_exist boolean;
BEGIN
    SELECT EXISTS(SELECT 1 FROM n8n_booking_time_periods WHERE id = p_period_id) INTO v_period_exists;
    IF NOT v_period_exists THEN
        RETURN json_build_object('success', false, 'message', 'Time period not found.');
    END IF;

    SELECT EXISTS(SELECT 1 FROM n8n_booking_bookings WHERE period_id = p_period_id) INTO v_bookings_exist;
    IF v_bookings_exist THEN
        RETURN json_build_object('success', false, 'message', 'Cannot delete time period with existing bookings. Please cancel or reschedule bookings first.');
    END IF;

    -- Soft delete (只更新 is_active)
    UPDATE n8n_booking_time_periods
    SET
        is_active = false
    WHERE id = p_period_id;

    RETURN json_build_object(
        'success', true,
        'period_id', p_period_id,
        'message', 'Time period marked as inactive (soft deleted).'
    );

EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('success', false, 'message', SQLERRM);
END;
$$ LANGUAGE plpgsql;
--- END OF FILE delete_period.sql ---
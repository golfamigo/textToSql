DROP FUNCTION IF EXISTS cancel_booking CASCADE;

--- START OF FILE cancel_booking.sql ---
CREATE OR REPLACE FUNCTION cancel_booking(
    p_booking_id uuid
)
RETURNS json
AS $$
DECLARE
    v_result json;
BEGIN
    UPDATE n8n_booking_bookings
    SET status = 'cancelled'
    WHERE id = p_booking_id
    AND status = 'confirmed';

    IF FOUND THEN
        -- 記錄取消歷史 (保持不變)
        INSERT INTO n8n_booking_history (
            booking_id,
            previous_status,
            new_status,
            reason,
            created_at  -- 保持 created_at 欄位名稱
        ) VALUES (
            p_booking_id,
            'confirmed',
            'cancelled',
            '客戶取消',
            CURRENT_TIMESTAMP
        );

        RETURN json_build_object('success', true, 'message', '預約已成功取消');
    ELSE
        RETURN json_build_object('success', false, 'message', '找不到該預約或預約已被取消');
    END IF;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE cancel_booking.sql ---

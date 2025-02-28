-- 刪除服務 (使用服務名稱)
DROP FUNCTION IF EXISTS delete_service CASCADE;

CREATE OR REPLACE FUNCTION delete_service(
    p_business_id uuid,
    p_service_name text  -- 使用服務名稱
)
RETURNS json
AS $$
DECLARE
    v_service_id uuid;
    v_bookings_exist boolean;
BEGIN
    -- 查找服務 ID
    SELECT service_id
    FROM find_service(p_business_id, p_service_name)
    INTO v_service_id;

    IF v_service_id IS NULL THEN
        RETURN json_build_object('success', false, 'message', '找不到該服務，請確認服務名稱是否正確');
    END IF;

    -- Check if there are any existing bookings for this service (Prevent deletion if bookings exist)
    SELECT EXISTS(SELECT 1 FROM n8n_booking_bookings WHERE service_id = v_service_id) INTO v_bookings_exist;
    IF v_bookings_exist THEN
        RETURN json_build_object('success', false, 'message', 'Cannot delete service with existing bookings. Please cancel or reschedule bookings first.');
    END IF;

    -- Soft delete: Mark service as inactive (is_active = false)
    UPDATE n8n_booking_services
    SET
        is_active = false,
        updated_at = NOW()  -- Update the updated_at timestamp
    WHERE id = v_service_id;  -- 使用找到的 service_id

    RETURN json_build_object(
        'success', true,
        'service_id', v_service_id,
        'message', 'Service marked as inactive (soft deleted).'
    );

EXCEPTION WHEN OTHERS THEN  -- Catch any potential errors
    RETURN json_build_object('success', false, 'message', SQLERRM);
END;
$$ LANGUAGE plpgsql;

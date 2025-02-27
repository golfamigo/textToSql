DROP FUNCTION IF EXISTS create_service CASCADE;

--- START OF FILE create_service.sql ---
CREATE OR REPLACE FUNCTION create_service(
    p_business_id uuid,
    p_name text,
    p_description text,
    p_duration integer,
    p_price numeric,
    p_max_capacity integer,
    p_min_booking_lead_time interval DEFAULT NULL,
    p_is_active boolean DEFAULT true
)
RETURNS json
AS $$
DECLARE
    v_service_id uuid;
BEGIN
    -- Validate inputs (basic validation, can be expanded)
    IF p_business_id IS NULL THEN
        RETURN json_build_object('success', false, 'message', 'Business ID cannot be null.');
    END IF;
    IF p_name IS NULL OR trim(p_name) = '' THEN
        RETURN json_build_object('success', false, 'message', 'Service name cannot be empty.');
    END IF;
    IF p_duration <= 0 THEN
        RETURN json_build_object('success', false, 'message', 'Duration must be a positive integer.');
    END IF;
    IF p_max_capacity <= 0 THEN
        RETURN json_build_object('success', false, 'message', 'Max capacity must be a positive integer.');
    END IF;

    -- Insert new service record
    INSERT INTO n8n_booking_services (
        business_id,
        name,
        description,
        duration,
        price,
        max_capacity,
        min_booking_lead_time,
        is_active
    ) VALUES (
        p_business_id,
        p_name,
        p_description,
        p_duration,
        p_price,
        p_max_capacity,
        p_min_booking_lead_time,
        p_is_active
    ) RETURNING id INTO v_service_id;

    RETURN json_build_object(
        'success', true,
        'service_id', v_service_id,
        'message', 'Service created successfully.'
    );

EXCEPTION WHEN OTHERS THEN -- Catch any potential errors
    RETURN json_build_object('success', false, 'message', SQLERRM);
END;
$$ LANGUAGE plpgsql;
--- END OF FILE create_service.sql ---
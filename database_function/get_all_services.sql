DROP FUNCTION IF EXISTS get_all_services CASCADE;

--- START OF FILE get_all_services.sql ---
CREATE OR REPLACE FUNCTION get_all_services(
    p_business_id uuid,
    p_include_inactive boolean DEFAULT false -- Optional parameter to include inactive services
)
RETURNS TABLE (
    service_id uuid,
    business_id uuid,
    name text,
    description text,
    duration integer,
    price numeric,
    max_capacity integer,
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
)
AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id AS service_id,
        s.business_id,
        s.name,
        s.description,
        s.duration,
        s.price,
        s.max_capacity,
        s.is_active,
        s.created_at,
        s.updated_at
    FROM
        n8n_booking_services s
    WHERE
        s.business_id = p_business_id
        AND (p_include_inactive OR s.is_active = true) -- Conditionally include inactive services
    ORDER BY
        s.name; -- Order services by name for easy readability
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_all_services.sql ---

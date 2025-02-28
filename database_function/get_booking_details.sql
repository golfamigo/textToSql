DROP FUNCTION IF EXISTS get_booking_details CASCADE;

--- START OF FILE get_booking_details.sql ---
CREATE OR REPLACE FUNCTION get_booking_details(
    p_booking_id uuid
)
RETURNS TABLE (
    booking_id uuid,
    booking_date date,
    period_name text,
    service_name text,
    status text,
    booking_created_at timestamp with time zone,
    customer_name text,
    customer_email text,
    customer_phone text,
    customer_notes text,
    business_name text,
    business_description text,
    period_start_time time,
    period_end_time time,
    service_description text,
    service_duration integer,
    service_price numeric,
    service_max_capacity integer,
    number_of_people integer  -- 添加人數
)
AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.id AS booking_id,
        b.booking_date,
        tp.name AS period_name,
        s.name AS service_name,
        b.status,
        b.booking_created_at,
        b.customer_name,
        b.customer_email,
        b.customer_phone,
        b.customer_notes,
        bus.name AS business_name,
        bus.description AS business_description,
        tp.start_time AS period_start_time,
        tp.end_time AS period_end_time,
        s.description AS service_description,
        s.duration AS service_duration,
        s.price AS service_price,
        s.max_capacity AS service_max_capacity,
        b.number_of_people  -- 添加人數
    FROM
        n8n_booking_bookings b
    JOIN
        n8n_booking_time_periods tp ON b.period_id = tp.id
    JOIN
        n8n_booking_services s ON b.service_id = s.id
    JOIN
        n8n_booking_businesses bus ON b.business_id = bus.id
    WHERE
        b.id = p_booking_id;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_booking_details.sql ---

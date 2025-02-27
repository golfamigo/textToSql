DROP FUNCTION IF EXISTS get_all_periods CASCADE;

--- START OF FILE get_all_periods.sql ---
CREATE OR REPLACE FUNCTION get_all_periods(
    p_business_id uuid,
    p_include_inactive boolean DEFAULT false -- Parameter to include inactive periods
)
RETURNS TABLE (
    period_id uuid,
    business_id uuid,
    name text,
    start_time time without time zone,
    end_time time without time zone,
    max_capacity integer,
    is_active boolean
)
AS $$
BEGIN
    RETURN QUERY
    SELECT
        tp.id AS period_id,
        tp.business_id,
        tp.name,
        tp.start_time,
        tp.end_time,
        tp.max_capacity,
        tp.is_active
    FROM
        n8n_booking_time_periods tp
    WHERE
        tp.business_id = p_business_id
        AND (p_include_inactive OR tp.is_active = true) -- Include inactive periods conditionally
    ORDER BY
        tp.start_time; -- Order by start time for logical listing
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_all_periods.sql ---
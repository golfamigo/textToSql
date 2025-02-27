DROP FUNCTION IF EXISTS get_detailed_availability CASCADE;

--- START OF FILE get_detailed_availability.sql ---
-- 函數功能：查詢特定日期和時段的詳細預約情況，包括時段名稱、開始時間、結束時間、最大容量、已預訂名額、剩餘名額、預約列表和服務限制
-- 參數:
--   p_business_id uuid: 商家 ID
--   p_booking_date date: 預約日期
--   p_period_name text: 時段名稱
-- 返回值:
--   TABLE: 包含詳細時段可用性資訊的表格
CREATE OR REPLACE FUNCTION get_detailed_availability(
    p_business_id uuid,
    p_booking_date date,
    p_period_name text
)
RETURNS TABLE (
    period_name text,
    start_time time,
    end_time time,
    max_capacity integer,
    booked_slots bigint,
    available_slots integer,
    bookings jsonb,
    service_restrictions jsonb
)
AS $$
DECLARE
    v_period_id uuid;
    v_business_timezone text;
BEGIN
    -- 獲取商家時區
    SELECT timezone INTO v_business_timezone
    FROM n8n_booking_businesses
    WHERE id = p_business_id;

    -- 取得 period_id
    SELECT id INTO v_period_id
    FROM n8n_booking_time_periods
    WHERE name = p_period_name
      AND business_id = p_business_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT NULL::text, NULL::time, NULL::time, NULL::integer, NULL::bigint, NULL::integer, NULL::jsonb, NULL::jsonb WHERE FALSE;
        RETURN;
    END IF;

    RETURN QUERY
    WITH local_bookings AS (
        -- 轉換預約時間到商家時區
        SELECT
            b.*,
            (b.booking_start_time AT TIME ZONE v_business_timezone)::date as local_date
        FROM n8n_booking_bookings b
        WHERE b.status = 'confirmed'
          AND b.period_id = v_period_id
    ),
    booking_info AS (
        SELECT
            b.id,
            jsonb_build_object(
                'booking_id', b.id,
                'customer_name', b.customer_name,
                'customer_email', b.customer_email,
                'customer_phone', b.customer_phone,
                'booking_created_at', b.booking_created_at,
                'status', b.status,
                'service_id', b.service_id,
                'service_name', s.name,
                'notes', b.notes,
                'local_time', b.booking_start_time AT TIME ZONE v_business_timezone
            ) AS booking_detail
        FROM local_bookings b
        JOIN n8n_booking_services s ON s.id = b.service_id
        WHERE b.local_date = p_booking_date
    ),
    restriction_info AS (
        SELECT
            jsonb_agg(
                jsonb_build_object(
                    'service_id', s.id,
                    'service_name', s.name,
                    'is_allowed', COALESCE(r.is_allowed, true)
                )
            ) AS restrictions
        FROM n8n_booking_services s
        LEFT JOIN n8n_booking_service_period_restrictions r
            ON r.service_id = s.id AND r.period_id = v_period_id
        WHERE s.business_id = p_business_id
          AND s.is_active = true
    )
    SELECT
        tp.name AS period_name,
        tp.start_time,
        tp.end_time,
        tp.max_capacity,
        COUNT(bi.id) AS booked_slots,
        tp.max_capacity - COUNT(bi.id)::integer AS available_slots,
        COALESCE(jsonb_agg(bi.booking_detail) FILTER (WHERE bi.id IS NOT NULL), '[]'::jsonb) AS bookings,
        COALESCE((SELECT ri.restrictions FROM restriction_info ri), '[]'::jsonb) AS service_restrictions
    FROM
        n8n_booking_time_periods tp
    LEFT JOIN booking_info bi ON true
    WHERE
        tp.id = v_period_id
        AND tp.business_id = p_business_id
        AND tp.is_active = true
    GROUP BY
        tp.id, tp.name, tp.start_time, tp.end_time, tp.max_capacity;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_detailed_availability.sql ---

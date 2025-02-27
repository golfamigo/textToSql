--- START OF FILE get_service_period_restrictions.sql ---
-- 取得服務的時段限制 (使用服務名稱)
-- 函數功能：獲取特定服務的時段限制
-- 參數:
--   p_business_id uuid: 商家 ID
--   p_service_name text: 服務名稱
-- 返回值:
--   TABLE: 包含服務時段限制資訊的表格
-- 先刪除現有函數


CREATE OR REPLACE FUNCTION get_service_period_restrictions(
    p_business_id uuid,
    p_service_name text  -- 使用服務名稱
)
RETURNS TABLE (
    restriction_id uuid,
    period_id uuid,
    period_name text,
    start_time time,
    end_time time,
    max_capacity integer,
    is_allowed boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    has_future_bookings boolean,
    matched_service_name text
) AS $$
DECLARE
    v_service_id uuid;
BEGIN
    -- 查找服務 ID
     SELECT service_id, matched_name
     from find_service(p_business_id => p_business_id, p_service_name => p_service_name)
     INTO v_service_id, matched_service_name;

    IF v_service_id IS NULL THEN
      RETURN QUERY SELECT
        CAST(NULL as UUID),
        CAST(NULL as UUID),
        CAST(NULL as TEXT),
        CAST(NULL as TIME),
        CAST(NULL as TIME),
        CAST(NULL as INTEGER),
        CAST(NULL as BOOLEAN),
        CAST(NULL as timestamp with time zone),
        CAST(NULL as timestamp with time zone),
        CAST(NULL as BOOLEAN),
        CAST(NULL as TEXT)
        WHERE FALSE;
    END IF;

    RETURN QUERY
    WITH future_bookings AS (
        SELECT 
            b.period_id,
            COUNT(*) > 0 as has_bookings
        FROM n8n_booking_bookings b
        WHERE b.service_id = v_service_id  -- 使用找到的 service_id
          AND b.booking_date >= CURRENT_DATE
          AND b.status = 'confirmed'
        GROUP BY b.period_id
    )
    SELECT 
        r.id as restriction_id,
        tp.id as period_id,
        tp.name as period_name,
        tp.start_time,
        tp.end_time,
        tp.max_capacity,
        COALESCE(r.is_allowed, true) as is_allowed,
        r.created_at,
        r.updated_at,
        COALESCE(fb.has_bookings, false) as has_future_bookings,
        matched_service_name as matched_service_name
    FROM n8n_booking_time_periods tp
    LEFT JOIN n8n_booking_service_period_restrictions r 
        ON r.period_id = tp.id 
        AND r.service_id = v_service_id  -- 使用找到的 service_id
    LEFT JOIN future_bookings fb ON fb.period_id = tp.id
    WHERE tp.is_active = true
    ORDER BY tp.start_time;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_service_period_restrictions.sql ---
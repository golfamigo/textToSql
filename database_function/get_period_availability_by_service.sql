--- START OF FILE get_period_availability_by_service.sql ---
-- 先刪除現有函數
DROP FUNCTION IF EXISTS get_period_availability_by_service(uuid, text, date[]);

-- 函數功能：獲取特定服務在多個日期的可用時段
-- 參數:
--   p_business_id uuid: 商家 ID
--   p_service_name text: 服務名稱
--   p_booking_dates date[]: 預約日期陣列
-- 返回值:
--   TABLE: 包含服務在指定日期的時段可用性資訊的表格
CREATE OR REPLACE FUNCTION get_period_availability_by_service(
    p_business_id uuid,
    p_service_name text,
    p_booking_dates date[]
)
RETURNS TABLE (
    booking_date date,
    period_name text,
    start_time time,
    end_time time,
    max_capacity integer,
    booked_slots bigint,
    available_slots integer,
    is_allowed boolean,
    matched_service_name text,
    is_date_valid boolean,
    is_advance_time_met boolean
)
AS $$
DECLARE
    v_service_id uuid;
    v_matched_name text;
    v_min_lead_time interval;
    v_current_date date := CURRENT_DATE;
    v_current_timestamp timestamp with time zone := CURRENT_TIMESTAMP;
    v_valid_dates date[] := ARRAY[]::date[];
BEGIN
    -- 使用 find_service 函數
    SELECT * FROM find_service(p_business_id => p_business_id, p_service_name => p_service_name)
    INTO v_service_id, v_matched_name;

    IF v_service_id IS NULL THEN
        RETURN QUERY SELECT 
            NULL::date, 
            NULL::text, 
            NULL::time, 
            NULL::time, 
            NULL::integer, 
            NULL::bigint, 
            NULL::integer, 
            NULL::boolean,
            NULL::text,
            NULL::boolean,
            NULL::boolean
        WHERE FALSE;
        RETURN;
    END IF;
    
    -- 獲取服務特定的提前預約時間，若無則使用商家默認設定
    SELECT COALESCE(s.min_booking_lead_time, b.min_booking_lead_time) INTO v_min_lead_time
    FROM n8n_booking_services s
    JOIN n8n_booking_businesses b ON s.business_id = b.id
    WHERE s.id = v_service_id;
    
    -- 過濾有效日期
    FOR i IN 1..array_length(p_booking_dates, 1) LOOP
        BEGIN
            -- 檢查是否為有效日期
            IF p_booking_dates[i] IS NOT NULL THEN
                v_valid_dates := array_append(v_valid_dates, p_booking_dates[i]);
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- 忽略無效日期
        END;
    END LOOP;

    -- 使用 WITH 子句先計算預約數量
    RETURN QUERY
    WITH booking_counts AS (
        SELECT
            d.date::date as booking_date,
            tp.id as period_id,
            tp.name AS period_name,
            tp.start_time,
            tp.end_time,
            tp.max_capacity,
            COUNT(b.id) AS booked_slots,
            -- 檢查提前預約時間是否足夠
            (v_current_timestamp + v_min_lead_time) <= 
                (d.date + tp.start_time::time)::timestamp with time zone AS is_advance_time_met
        FROM
            unnest(v_valid_dates) AS d(date)
        CROSS JOIN
            n8n_booking_time_periods tp
        LEFT JOIN
            n8n_booking_bookings b ON
                b.period_id = tp.id
                AND b.service_id = v_service_id
                AND b.booking_date = d.date
                AND b.status = 'confirmed'
        WHERE
            tp.business_id = p_business_id
            AND tp.is_active = true
        GROUP BY
            d.date,
            tp.id,
            tp.name,
            tp.start_time,
            tp.end_time,
            tp.max_capacity
    )
    SELECT
        bc.booking_date,
        bc.period_name,
        bc.start_time,
        bc.end_time,
        bc.max_capacity,
        bc.booked_slots,
        bc.max_capacity - bc.booked_slots::integer AS available_slots,
        COALESCE(r.is_allowed, true) as is_allowed,
        v_matched_name as matched_service_name,
        TRUE as is_date_valid,  -- 有效日期
        bc.is_advance_time_met
    FROM
        booking_counts bc
    LEFT JOIN
        n8n_booking_service_period_restrictions r ON 
            r.period_id = bc.period_id 
            AND r.service_id = v_service_id
    WHERE
        COALESCE(r.is_allowed, true) = true
    ORDER BY
        bc.booking_date,
        bc.start_time;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_period_availability_by_service.sql ---
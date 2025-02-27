DROP FUNCTION IF EXISTS get_period_availability_with_staff CASCADE;

--- START OF FILE get_period_availability_with_staff.sql ---
-- 查詢特定服務在特定日期的可用時段和可用員工
-- 函數功能：查詢特定服務在特定日期的可用時段和可用員工
-- 參數:
--   p_business_id UUID: 商家 ID
--   p_service_name TEXT: 服務名稱
--   p_booking_dates DATE[]: 預約日期陣列
-- 返回值:
--   TABLE: 包含每日時段的可用時段和可用員工資訊的表格
CREATE OR REPLACE FUNCTION get_period_availability_with_staff(
    p_business_id UUID,
    p_service_name TEXT,
    p_booking_dates DATE[]
) RETURNS TABLE (
    booking_date DATE,
    period_name TEXT,
    start_time TIME,
    end_time TIME,
    available_slots INTEGER,
    available_staff JSONB  -- 包含可用員工的信息
) AS $$
DECLARE
    v_service_id UUID;
    v_matched_name TEXT;
    v_service_duration INTEGER;
BEGIN
    -- 查找服務 ID
    SELECT * FROM find_service(p_business_id => p_business_id, p_service_name => p_service_name)
    INTO v_service_id, v_matched_name;

    IF v_service_id IS NULL THEN
        RAISE EXCEPTION '找不到該服務，請確認服務名稱是否正確';
    END IF;

    -- 獲取服務時長
    SELECT duration INTO v_service_duration
    FROM n8n_booking_services
    WHERE id = v_service_id;

    -- 查詢可用時段和可用員工
    RETURN QUERY
    WITH available_periods AS (
        -- 查詢可用時段
        SELECT
            d.booking_date,
            p.id AS period_id,
            p.name AS period_name,
            p.start_time,
            p.end_time,
            p.max_capacity - COALESCE(
                (SELECT SUM(b.number_of_people)
                FROM n8n_booking_bookings b
                WHERE b.service_id = v_service_id
                AND b.status = 'confirmed'
                AND b.booking_date = d.booking_date
                AND b.period_id = p.id
                ), 0
            ) AS available_slots
        FROM (SELECT unnest(p_booking_dates) AS booking_date) d
        JOIN n8n_booking_time_periods p ON p.business_id = p_business_id AND p.is_active = true
        LEFT JOIN n8n_booking_service_period_restrictions r
            ON r.service_id = v_service_id AND r.period_id = p.id
        WHERE COALESCE(r.is_allowed, true) = true  -- 檢查服務時段限制
    ),
    staff_with_service AS (
        -- 查詢可以提供此服務的員工
        SELECT
            ss.staff_id,
            u.name AS staff_name,
            ss.is_primary,
            ss.proficiency_level
        FROM n8n_booking_staff_services ss
        JOIN n8n_booking_users u ON ss.staff_id = u.id
        WHERE ss.service_id = v_service_id
        AND u.is_active = true
        AND u.role = 'staff'
    )
    SELECT
        ap.booking_date,
        ap.period_name,
        ap.start_time,
        ap.end_time,
        ap.available_slots,
        (
            -- 查詢每個時段的可用員工
            SELECT jsonb_agg(jsonb_build_object(
                'staff_id', s.staff_id,
                'staff_name', s.staff_name,
                'is_primary', s.is_primary,
                'proficiency_level', s.proficiency_level
            ))
            FROM staff_with_service s
            WHERE NOT EXISTS (  -- 檢查員工是否已有預約
                SELECT 1
                FROM n8n_booking_bookings b
                WHERE b.staff_id = s.staff_id
                AND b.status = 'confirmed'
                AND b.booking_date = ap.booking_date
                AND (
                    -- 檢查時間是否有衝突
                    (b.booking_start_time::time BETWEEN ap.start_time AND ap.end_time) OR
                    ((b.booking_start_time + b.booking_duration)::time BETWEEN ap.start_time AND ap.end_time) OR
                    (ap.start_time BETWEEN b.booking_start_time::time AND (b.booking_start_time + b.booking_duration)::time)
                )
            )
            AND EXISTS (  -- 檢查員工在這個時段是否設定為可用
                SELECT 1
                FROM n8n_booking_staff_availability sa
                WHERE sa.staff_id = s.staff_id
                AND sa.availability_type = 'available'
                AND (
                    (sa.is_recurring = true AND sa.day_of_week = EXTRACT(DOW FROM ap.booking_date)) OR
                    (sa.is_recurring = false AND sa.specific_date = ap.booking_date)
                )
                AND sa.start_time <= ap.start_time
                AND sa.end_time >= ap.end_time
            )
            AND NOT EXISTS (  -- 檢查員工是否有設定這個時段為不可用
                SELECT 1
                FROM n8n_booking_staff_availability sa
                WHERE sa.staff_id = s.staff_id
                AND sa.availability_type = 'unavailable'
                AND (
                    (sa.is_recurring = true AND sa.day_of_week = EXTRACT(DOW FROM ap.booking_date)) OR
                    (sa.is_recurring = false AND sa.specific_date = ap.booking_date)
                )
                AND (
                    (sa.start_time <= ap.start_time AND sa.end_time >= ap.start_time) OR
                    (sa.start_time <= ap.end_time AND sa.end_time >= ap.end_time) OR
                    (ap.start_time <= sa.start_time AND ap.end_time >= sa.end_time)
                )
            )
        ) AS available_staff
    FROM available_periods ap
    WHERE ap.available_slots > 0
    ORDER BY ap.booking_date, ap.start_time;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE get_period_availability_with_staff.sql ---

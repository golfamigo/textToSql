--- START OF FILE update_booking.sql ---
-- 先刪除現有函數
DROP FUNCTION IF EXISTS update_booking CASCADE;

-- 函數功能：更新預約資訊
-- 參數:
--   p_booking_id uuid: 預約 ID
--   p_new_date date (optional, default: NULL): 新的預約日期
--   p_new_period_name text (optional, default: NULL): 新的時段名稱
--   p_new_service_name text (optional, default: NULL): 新的服務名稱
--   p_new_number_of_people integer (optional, default: NULL): 新的預約人數
--   p_new_phone text (optional, default: NULL): 新的顧客電話
--   p_new_email text (optional, default: NULL): 新的顧客 Email
-- 返回值:
--   JSON: 包含操作結果
CREATE OR REPLACE FUNCTION update_booking(
    p_booking_id uuid,
    p_new_date date DEFAULT NULL,
    p_new_period_name text DEFAULT NULL,
    p_new_service_name text DEFAULT NULL,  -- 改為使用服務名稱
    p_new_number_of_people integer DEFAULT NULL,
    p_new_phone text DEFAULT NULL,
    p_new_email text DEFAULT NULL
)
RETURNS json
AS $$
DECLARE
    v_result json;
    v_available_slots integer;
    v_period_id uuid;
    v_old_status text;
    v_new_service_max_capacity integer;
    v_cleaned_phone text;
    v_current_booking n8n_booking_bookings%ROWTYPE;
    v_business_timezone text;
    v_current_local_date date;
    v_local_current_time timestamp;
    v_service_id uuid;
    v_matched_name text;
    v_business_id uuid;
BEGIN
    -- 先獲取預約資訊
    SELECT * INTO v_current_booking
    FROM n8n_booking_bookings
    WHERE id = p_booking_id;

    IF NOT FOUND THEN
        RETURN json_build_object('success', false, 'message', '找不到指定的預約');
    END IF;

    -- 如果要更改服務
    IF p_new_service_name IS NOT NULL THEN
        -- 使用現有的 business_id
        SELECT * FROM find_service(p_business_id => v_current_booking.business_id, p_service_name => p_new_service_name)
        INTO v_service_id, v_matched_name;

        IF v_service_id IS NULL THEN
            RETURN json_build_object(
                'success', false,
                'message', '找不到該服務，請確認服務名稱是否正確'
            );
        END IF;

        -- 檢查新的服務容量
        SELECT max_capacity INTO v_new_service_max_capacity
        FROM n8n_booking_services
        WHERE id = v_service_id;

        IF NOT FOUND THEN
            RETURN json_build_object('success', false, 'message', '找不到該服務');
        END IF;
    END IF;

    -- 獲取商家時區
    SELECT timezone INTO v_business_timezone
    FROM n8n_booking_businesses
    WHERE id = v_current_booking.business_id;

    -- 計算當前本地時間
    v_local_current_time := CURRENT_TIMESTAMP AT TIME ZONE v_business_timezone;
    v_current_local_date := v_local_current_time::date;

    -- 檢查預約狀態
    v_old_status := v_current_booking.status;
    IF v_old_status != 'confirmed' THEN
        RETURN json_build_object('success', false, 'message', '只能修改狀態為confirmed的預約');
    END IF;

    -- 日期驗證（使用本地時間）
    IF p_new_date IS NOT NULL THEN
        IF p_new_date <= v_current_local_date THEN
            RETURN json_build_object('success', false, 'message', '修改預約請至少提前一天');
        END IF;

        IF p_new_date > v_current_local_date + interval '1 year' THEN
            RETURN json_build_object('success', false, 'message', '無法預約超過一年後的日期');
        END IF;
    END IF;

    -- 取得新時段的 period_id
    IF p_new_period_name IS NOT NULL THEN
        SELECT id INTO v_period_id
        FROM n8n_booking_time_periods
        WHERE name = p_new_period_name
          AND business_id = v_current_booking.business_id;

        IF v_period_id IS NULL THEN
            RETURN json_build_object('success', false, 'message', '找不到該時段');
        END IF;
    END IF;

    -- 驗證預約人數
    IF p_new_number_of_people IS NOT NULL THEN
        IF p_new_number_of_people <= 0 THEN
            RETURN json_build_object('success', false, 'message', '預約人數必須是正整數');
        END IF;

        -- 使用本地時間檢查容量
        WITH local_bookings AS (
            SELECT COUNT(b.id) as booked_count
            FROM n8n_booking_bookings b
            WHERE b.booking_date = COALESCE(p_new_date, v_current_booking.booking_date)
              AND b.period_id = COALESCE(v_period_id, v_current_booking.period_id)
              AND b.service_id = COALESCE(v_service_id, v_current_booking.service_id)
              AND b.status = 'confirmed'
              AND b.id != p_booking_id
        )
        SELECT tp.max_capacity - COALESCE(lb.booked_count, 0)
        INTO v_available_slots
        FROM n8n_booking_time_periods tp
        CROSS JOIN local_bookings lb
        WHERE tp.id = COALESCE(v_period_id, v_current_booking.period_id);

        -- 如果沒有任何預約，使用時段的最大容量
        IF v_available_slots IS NULL THEN
            SELECT max_capacity INTO v_available_slots
            FROM n8n_booking_time_periods
            WHERE id = COALESCE(v_period_id, v_current_booking.period_id);
        END IF;

        IF v_available_slots < p_new_number_of_people THEN
            RETURN json_build_object('success', false, 'message', '該時段已無足夠空位容納這麼多人數');
        END IF;
    END IF;

    -- 電話號碼處理
    IF p_new_phone IS NOT NULL THEN
        v_cleaned_phone := regexp_replace(p_new_phone, '[^0-9]', '', 'g');

        IF length(v_cleaned_phone) < 8 OR length(v_cleaned_phone) > 10 THEN
            RETURN json_build_object('success', false, 'message', '電話號碼長度必須在8到10位數之間');
        END IF;
    END IF;

    -- Email 格式驗證
    IF p_new_email IS NOT NULL THEN
        IF p_new_email !~ '^[\w.%+-]+@[\w.-]+\.[a-zA-Z]{2,}$' THEN
            RETURN json_build_object('success', false, 'message', '無效的電子郵件格式');
        END IF;
    END IF;

    -- 更新預約
    UPDATE n8n_booking_bookings
    SET booking_date = COALESCE(p_new_date, booking_date),
        period_id = COALESCE(v_period_id, period_id),
        service_id = COALESCE(v_service_id, service_id),
        updated_at = v_local_current_time,
        number_of_people = COALESCE(p_new_number_of_people, number_of_people),
        customer_phone = COALESCE(v_cleaned_phone, customer_phone),
        customer_email = COALESCE(p_new_email, customer_email)
    WHERE id = p_booking_id;

    -- 記錄修改歷史（使用本地時間）
    INSERT INTO n8n_booking_history (
        booking_id,
        previous_status,
        new_status,
        reason,
        created_at
    ) VALUES (
        p_booking_id,
        v_old_status,
        'modified',
        CASE
            WHEN p_new_service_name IS NOT NULL THEN
                '客戶修改預約服務為：' || v_matched_name
            ELSE
                '客戶修改預約'
        END,
        v_local_current_time
    );

    RETURN json_build_object(
        'success', true,
        'message', '預約修改成功',
        'service_name', COALESCE(v_matched_name, NULL)
    );

EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('success', false, 'message', SQLERRM);
END;
$$ LANGUAGE plpgsql;
--- END OF FILE update_booking.sql ---

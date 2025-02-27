DROP FUNCTION IF EXISTS create_booking CASCADE;

--- START OF FILE create_booking.sql ---
-- 函數功能：創建新的預約
-- 參數:
--   p_customer_name text: 顧客姓名
--   p_customer_email text: 顧客 email
--   p_customer_phone text: 顧客電話
--   p_business_id uuid: 商家 ID
--   p_service_name text: 服務名稱
--   p_booking_start_time timestamp with time zone: 預約開始時間 (timestamp with time zone)
--   p_number_of_people integer (optional, default: 1): 預約人數
-- 返回值:
--   JSON: 包含操作結果，包括 success (boolean), booking_id (uuid), message (text), service_name (text)
CREATE OR REPLACE FUNCTION create_booking(
    p_customer_name text,
    p_customer_email text,
    p_customer_phone text,
    p_business_id uuid,
    p_service_name text,  -- 改為只使用服務名稱
    p_booking_start_time timestamp with time zone,
    p_number_of_people integer DEFAULT 1
)
RETURNS json
AS $$
DECLARE
    v_booking_id uuid;
    v_available_slots integer;
    v_existing_booking boolean;
    v_service_max_capacity integer;
    v_period_id uuid;
    v_service_duration interval;
    v_cleaned_phone text;
    v_business_timezone text;
    v_local_time timestamp;
    v_booking_minutes integer;
    v_is_allowed boolean;
    v_service_id uuid;
    v_matched_name text;
    v_min_lead_time interval;
BEGIN
    -- 先查找服務
    SELECT * FROM find_service(p_business_id => p_business_id, p_service_name => p_service_name)
    INTO v_service_id, v_matched_name;

    IF v_service_id IS NULL THEN
        RETURN json_build_object(
            'success', false,
            'message', '找不到該服務，請確認服務名稱是否正確'
        );
    END IF;
    
    -- 獲取服務特定的提前預約時間，若無則使用商家默認設定
    SELECT COALESCE(s.min_booking_lead_time, b.min_booking_lead_time) INTO v_min_lead_time
    FROM n8n_booking_services s
    JOIN n8n_booking_businesses b ON b.id = p_business_id
    WHERE s.id = v_service_id;

    -- 記錄執行開始
    RAISE NOTICE 'create_booking 開始執行 - 參數：%', json_build_object(
        'customer_name', p_customer_name,
        'email', p_customer_email,
        'phone', p_customer_phone,
        'business_id', p_business_id,
        'service_name', p_service_name,
        'matched_service_name', v_matched_name,
        'service_id', v_service_id,
        'booking_start_time', p_booking_start_time,
        'number_of_people', p_number_of_people
    );

    -- 基本資料驗證
    IF p_customer_name IS NULL OR length(trim(p_customer_name)) < 2 THEN
        RETURN json_build_object('success', false, 'message', '姓名至少需要2個字元');
    END IF;

    IF p_customer_email !~ '^[\w.%+-]+@[\w.-]+\.[a-zA-Z]{2,}$' THEN
        RETURN json_build_object('success', false, 'message', '無效的電子郵件格式');
    END IF;

    -- 電話號碼驗證
    v_cleaned_phone := regexp_replace(p_customer_phone, '[^0-9]', '', 'g');
    IF length(v_cleaned_phone) < 8 OR length(v_cleaned_phone) > 10 THEN
        RETURN json_build_object('success', false, 'message', '電話號碼長度必須在8到10位數字之間');
    END IF;

    IF p_number_of_people IS NULL OR p_number_of_people <= 0 THEN
        RETURN json_build_object('success', false, 'message', '預約人數必須是正整數');
    END IF;

    -- 獲取商家時區
    SELECT timezone INTO v_business_timezone
    FROM n8n_booking_businesses 
    WHERE id = p_business_id;

    IF NOT FOUND THEN
        RETURN json_build_object('success', false, 'message', '找不到該商家');
    END IF;

    -- 將UTC時間轉換為商家所在時區的時間
    v_local_time := p_booking_start_time AT TIME ZONE v_business_timezone;
    
    -- 檢查服務是否存在及其容量
    SELECT max_capacity, duration
    INTO v_service_max_capacity, v_service_duration
    FROM n8n_booking_services
    WHERE id = v_service_id AND business_id = p_business_id;

    IF NOT FOUND THEN
        RETURN json_build_object('success', false, 'message', '找不到該服務');
    END IF;

    -- 計算本地時間的分鐘數
    v_booking_minutes := EXTRACT(HOUR FROM v_local_time) * 60 + 
                        EXTRACT(MINUTE FROM v_local_time);
    v_service_duration := (v_service_duration::text || ' minutes')::interval;

    RAISE NOTICE 'Local time: %, Booking minutes: %', v_local_time, v_booking_minutes;

    -- 時間驗證
    IF p_booking_start_time < CURRENT_TIMESTAMP - interval '1 second' THEN
        RETURN json_build_object('success', false, 'message', '無法預約過去的時間');
    END IF;

    IF p_booking_start_time > CURRENT_TIMESTAMP + interval '1 year' THEN
        RETURN json_build_object('success', false, 'message', '無法預約超過一年後的日期');
    END IF;

    -- 使用計算得到的提前預約時間進行檢查
    IF p_booking_start_time <= CURRENT_TIMESTAMP + v_min_lead_time THEN
        RETURN json_build_object('success', false, 'message', 
            '此服務需要提前 ' || 
            EXTRACT(EPOCH FROM v_min_lead_time)/3600 || ' 小時預約');
    END IF;

    -- 檢查是否在營業時段內
    SELECT id 
    INTO v_period_id
    FROM n8n_booking_time_periods
    WHERE business_id = p_business_id
      AND is_active = TRUE
      AND start_minutes <= v_booking_minutes
      AND end_minutes >= v_booking_minutes;

    IF v_period_id IS NULL THEN
        RETURN json_build_object(
            'success', false, 
            'message', '所選時間不在任何有效時段內',
            'debug', json_build_object(
                'booking_minutes', v_booking_minutes,
                'booking_time', p_booking_start_time,
                'local_time', v_local_time
            )
        );
    END IF;

    -- 檢查時段限制
    SELECT COALESCE(r.is_allowed, true) INTO v_is_allowed
    FROM n8n_booking_service_period_restrictions r
    WHERE r.period_id = v_period_id
      AND r.service_id = v_service_id;

    IF v_is_allowed = false THEN
        RETURN json_build_object(
            'success', false,
            'message', '所選服務在此时段不可預約，請選擇其他時段'
        );
    END IF;

    -- 檢查重複預約
    SELECT EXISTS (
        SELECT 1
        FROM n8n_booking_bookings b
        WHERE b.service_id = v_service_id
          AND b.status = 'confirmed'
          AND tstzrange(b.booking_start_time, b.booking_start_time + b.booking_duration) && 
              tstzrange(p_booking_start_time, p_booking_start_time + v_service_duration)
          AND b.customer_email = p_customer_email
    ) INTO v_existing_booking;

    IF v_existing_booking THEN
        RETURN json_build_object('success', false, 'message', '您選擇的時間已與現有預約衝突，請選擇其他時間');
    END IF;

    -- 檢查服務容量
    SELECT v_service_max_capacity - COALESCE(
        (SELECT SUM(number_of_people)
         FROM n8n_booking_bookings
         WHERE service_id = v_service_id
           AND status = 'confirmed'
           AND tstzrange(booking_start_time, booking_start_time + booking_duration) && 
               tstzrange(p_booking_start_time, p_booking_start_time + v_service_duration)
        ), 0
    ) INTO v_available_slots;

    IF v_available_slots < p_number_of_people THEN
        RETURN json_build_object('success', false, 'message', '您選擇的時間已無足夠名額');
    END IF;



    -- 建立預約
    INSERT INTO n8n_booking_bookings (
        customer_name,
        customer_email,
        customer_phone,
        business_id,
        service_id,
        booking_date,
        booking_start_time,
        booking_duration,
        status,
        number_of_people,
        period_id
    ) VALUES (
        p_customer_name,
        p_customer_email,
        v_cleaned_phone,
        p_business_id,
        v_service_id,
        DATE(v_local_time),
        p_booking_start_time,
        v_service_duration,
        'confirmed',
        p_number_of_people,
        v_period_id
    ) RETURNING id INTO v_booking_id;

    RETURN json_build_object(
        'success', true,
        'booking_id', v_booking_id,
        'message', '預約成功',
        'service_name', v_matched_name
    );

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'create_booking 發生錯誤: % - %', SQLSTATE, SQLERRM;
        RAISE NOTICE '錯誤詳情: %', json_build_object(
            'customer_name', p_customer_name,
            'email', p_customer_email,
            'phone', p_customer_phone,
            'business_id', p_business_id,
            'service_name', p_service_name,
            'matched_service_name', v_matched_name,
            'service_id', v_service_id,
            'booking_start_time', p_booking_start_time,
            'booking_duration', v_service_duration,
            'number_of_people', p_number_of_people,
            'period_id', v_period_id
        );

        RETURN json_build_object(
            'success', false,
            'message', '預約過程發生錯誤',
            'error_code', SQLSTATE,
            'error_message', SQLERRM
        );
END;
$$ LANGUAGE plpgsql;
--- END OF FILE create_booking.sql ---
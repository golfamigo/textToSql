DROP FUNCTION IF EXISTS create_period CASCADE;

--- START OF FILE create_period.sql ---
-- 函數功能：創建新的時段
-- 參數:
--   p_business_id uuid: 商家 ID
--   p_name text: 時段名稱
--   p_start_time time without time zone: 時段開始時間 (time without time zone)
--   p_end_time time without time zone: 時段結束時間 (time without time zone)
--   p_max_capacity integer: 最大容量
--   p_is_active boolean (optional, default: true): 是否啟用
-- 返回值:
--   JSON: 包含操作結果，包括 success (boolean), period_id (uuid), message (text)
CREATE OR REPLACE FUNCTION create_period(
    p_business_id uuid,
    p_name text,
    p_start_time time without time zone,
    p_end_time time without time zone,
    p_max_capacity integer,
    p_is_active boolean DEFAULT true
)
RETURNS json
AS $$
DECLARE
    v_period_id uuid;
    v_start_minutes integer;  -- 新增變數
    v_end_minutes integer;    -- 新增變數
BEGIN
    -- Validate inputs (這部分保持不變)
    IF p_business_id IS NULL THEN
        RETURN json_build_object('success', false, 'message', 'Business ID cannot be null.');
    END IF;
    IF p_name IS NULL OR trim(p_name) = '' THEN
        RETURN json_build_object('success', false, 'message', 'Period name cannot be empty.');
    END IF;
    IF p_start_time IS NULL THEN
        RETURN json_build_object('success', false, 'message', 'Start time cannot be null.');
    END IF;
    IF p_end_time IS NULL THEN
        RETURN json_build_object('success', false, 'message', 'End time cannot be null.');
    END IF;
    IF p_start_time >= p_end_time THEN
        RETURN json_build_object('success', false, 'message', 'Start time must be before end time.');
    END IF;
    IF p_max_capacity <= 0 THEN
        RETURN json_build_object('success', false, 'message', 'Max capacity must be a positive integer.');
    END IF;

    -- 計算 start_minutes 和 end_minutes
    v_start_minutes := EXTRACT(HOUR FROM p_start_time) * 60 + EXTRACT(MINUTE FROM p_start_time);
    v_end_minutes := EXTRACT(HOUR FROM p_end_time) * 60 + EXTRACT(MINUTE FROM p_end_time);

    -- Insert new time period record (包含 start_minutes 和 end_minutes)
    INSERT INTO n8n_booking_time_periods (
        business_id,
        name,
        start_time,
        end_time,
        max_capacity,
        is_active,
        start_minutes,  -- 新增欄位
        end_minutes     -- 新增欄位
    ) VALUES (
        p_business_id,
        p_name,
        p_start_time,
        p_end_time,
        p_max_capacity,
        p_is_active,
        v_start_minutes,  -- 新增值
        v_end_minutes     -- 新增值
    ) RETURNING id INTO v_period_id;

    RETURN json_build_object(
        'success', true,
        'period_id', v_period_id,
        'message', 'Time period created successfully.'
    );

EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('success', false, 'message', SQLERRM);
END;
$$ LANGUAGE plpgsql;
--- END OF FILE create_period.sql ---

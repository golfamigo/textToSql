DROP FUNCTION IF EXISTS update_period CASCADE;

--- START OF FILE update_period.sql ---
-- 函數功能：更新時段信息
-- 參數:
--   p_period_id uuid: 時段 ID
--   p_name text (optional, default: NULL): 時段名稱
--   p_start_time time without time zone (optional, default: NULL): 開始時間
--   p_end_time time without time zone (optional, default: NULL): 結束時間
--   p_max_capacity integer (optional, default: NULL): 最大容量
--   p_is_active boolean (optional, default: NULL): 是否啟用
-- 返回值:
--   JSON: 包含操作結果，包括 success (boolean), period_id (uuid), message (text)
CREATE OR REPLACE FUNCTION update_period(
    p_period_id uuid,
    p_name text DEFAULT NULL,                  -- 設為可空，預設為 NULL
    p_start_time time without time zone DEFAULT NULL, -- 設為可空，預設為 NULL
    p_end_time time without time zone DEFAULT NULL,   -- 設為可空，預設為 NULL
    p_max_capacity integer DEFAULT NULL,         -- 設為可空，預設為 NULL
    p_is_active boolean DEFAULT NULL            -- 設為可空，預設為 NULL
)
RETURNS json
AS $$
DECLARE
    v_period_exists boolean;
    v_current_period record;  -- 變數用於儲存現有時段資料
BEGIN
    -- 檢查時段是否存在
    SELECT EXISTS(SELECT 1 FROM n8n_booking_time_periods WHERE id = p_period_id) INTO v_period_exists;
    IF NOT v_period_exists THEN
        RETURN json_build_object('success', false, 'message', '找不到時段.');
    END IF;

    -- 取得現有時段資料
    SELECT * INTO v_current_period
    FROM n8n_booking_time_periods
    WHERE id = p_period_id;

    -- 驗證輸入 (針對必要欄位，名稱、開始時間、結束時間、容量) - 針對最終要更新的值驗證
    IF COALESCE(p_name, v_current_period.name) IS NULL OR trim(COALESCE(p_name, v_current_period.name)) = '' THEN
        RETURN json_build_object('success', false, 'message', '時段名稱不能為空.');
    END IF;
    IF COALESCE(p_start_time, v_current_period.start_time) IS NULL THEN
        RETURN json_build_object('success', false, 'message', '開始時間不能為空.');
    END IF;
    IF COALESCE(p_end_time, v_current_period.end_time) IS NULL THEN
        RETURN json_build_object('success', false, 'message', '結束時間不能為空.');
    END IF;
    IF COALESCE(p_start_time, v_current_period.start_time) >= COALESCE(p_end_time, v_current_period.end_time) THEN
        RETURN json_build_object('success', false, 'message', '開始時間必須在結束時間之前.');
    END IF;
    IF COALESCE(p_max_capacity, v_current_period.max_capacity) <= 0 THEN
        RETURN json_build_object('success', false, 'message', '最大容量必須是正整數.');
    END IF;

    -- 更新時段記錄 - 只有在 p_parameter 不是 NULL 時才更新
    UPDATE n8n_booking_time_periods
    SET
        name = COALESCE(p_name, v_current_period.name),                 -- 如果 p_name 有提供新值，就用新值，否則沿用舊值
        start_time = COALESCE(p_start_time, v_current_period.start_time),     -- 同上
        end_time = COALESCE(p_end_time, v_current_period.end_time),         -- 同上
        max_capacity = COALESCE(p_max_capacity, v_current_period.max_capacity),     -- 同上
        is_active = COALESCE(p_is_active, v_current_period.is_active)         -- 同上
    WHERE id = p_period_id;

    RETURN json_build_object(
        'success', true,
        'period_id', p_period_id,
        'message', '時段更新成功.'
    );

EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('success', false, 'message', SQLERRM);
END;
$$ LANGUAGE plpgsql;
--- END OF FILE update_period.sql ---

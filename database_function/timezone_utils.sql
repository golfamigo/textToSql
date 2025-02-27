DROP FUNCTION IF EXISTS convert_timezone CASCADE;

--- START OF FILE timezone_utils.sql ---
CREATE OR REPLACE FUNCTION convert_timezone(
    p_timestamp timestamp with time zone,
    p_from_timezone text,
    p_to_timezone text
) RETURNS timestamp with time zone AS $$
BEGIN
    RETURN p_timestamp AT TIME ZONE p_from_timezone AT TIME ZONE p_to_timezone;
END;
$$ LANGUAGE plpgsql;
-- 時區轉換函數
DROP FUNCTION IF EXISTS convert_timezone CASCADE;

-- 函數功能：轉換時區
-- 參數:
--   p_timestamp timestamp with time zone: 帶時區的時間戳
--   p_from_timezone text: 原始時區
--   p_to_timezone text: 目標時區
-- 返回值:
--   timestamp with time zone: 轉換時區後的時間戳
CREATE OR REPLACE FUNCTION convert_timezone(
    p_timestamp timestamp with time zone,
    p_from_timezone text,
    p_to_timezone text
) RETURNS timestamp with time zone AS $$
BEGIN
    RETURN p_timestamp AT TIME ZONE p_from_timezone AT TIME ZONE p_to_timezone;
END;
$$ LANGUAGE plpgsql;

-- 分鐘轉換函數
DROP FUNCTION IF EXISTS time_to_minutes CASCADE;

-- 函數功能：將 time 類型轉換為分鐘數
-- 參數:
--   p_time time: 時間
-- 返回值:
--   integer: 分鐘數
CREATE OR REPLACE FUNCTION time_to_minutes(p_time time) RETURNS integer AS $$
BEGIN
    RETURN EXTRACT(HOUR FROM p_time) * 60 + EXTRACT(MINUTE FROM p_time);
END;
$$ LANGUAGE plpgsql;

-- 分鐘轉回時間函數
DROP FUNCTION IF EXISTS minutes_to_time CASCADE;

-- 函數功能：將分鐘數轉換回 time 類型
-- 參數:
--   p_minutes integer: 分鐘數
-- 返回值:
--   time: 時間
CREATE OR REPLACE FUNCTION minutes_to_time(p_minutes integer) RETURNS time AS $$
BEGIN
    RETURN (p_minutes / 60 || ':' || p_minutes % 60 || ':00')::time;
END;
$$ LANGUAGE plpgsql;
--- END OF FILE timezone_utils.sql ---
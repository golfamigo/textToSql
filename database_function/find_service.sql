DROP FUNCTION IF EXISTS find_service CASCADE;

-- 函數功能：查找服務
-- 參數:
--   p_business_id uuid: 商家 ID
--   p_service_name text: 服務名稱
-- 返回值:
--   服務ID、名稱和相似度
CREATE OR REPLACE FUNCTION find_service(
    p_business_id uuid,
    p_service_name text
)
RETURNS TABLE (
    service_id uuid,
    matched_name text,
    similarity_score float
)
AS $function$
BEGIN
    -- 1. 嘗試完全匹配
    RETURN QUERY
    SELECT
        id,
        name,
        1.0::float
    FROM n8n_booking_services
    WHERE business_id = p_business_id
      AND LOWER(name) = LOWER(p_service_name)
      AND is_active = true;

    -- 2. 如果沒有完全匹配，嘗試部分匹配
    IF NOT FOUND THEN
        RETURN QUERY
        SELECT
            id,
            name,
            similarity(LOWER(name), LOWER(p_service_name))::float
        FROM n8n_booking_services
        WHERE business_id = p_business_id
          AND is_active = true
          AND (
              LOWER(name) LIKE LOWER('%' || p_service_name || '%')
              OR
              similarity(LOWER(name), LOWER(p_service_name)) > 0.3
          )
        ORDER BY
            similarity(LOWER(name), LOWER(p_service_name)) DESC,
            name
        LIMIT 1;
    END IF;

    -- 如果還是沒找到，返回 NULL
    IF NOT FOUND THEN
        service_id := NULL;
        matched_name := NULL;
        similarity_score := NULL;
        RETURN NEXT;
    END IF;
END;
$function$ LANGUAGE plpgsql;

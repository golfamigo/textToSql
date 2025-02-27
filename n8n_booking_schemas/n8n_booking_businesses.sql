CREATE TABLE public.n8n_booking_businesses (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    name varchar NOT NULL,
    description text,
    address text,
    contact_email varchar,
    contact_phone varchar,
    business_hours jsonb,
    timezone varchar DEFAULT 'Asia/Taipei'::varchar NOT NULL,
    min_booking_lead_time interval,
    owner_id uuid,
    settings jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    subscription_status varchar,
    subscription_end_date date,
    linebot_destination varchar
);

COMMENT ON TABLE public.n8n_booking_businesses IS '商家信息表';

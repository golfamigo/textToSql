CREATE TABLE public.n8n_booking_services (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    business_id uuid REFERENCES public.n8n_booking_businesses(id),
    name varchar NOT NULL,
    description text,
    duration integer NOT NULL, -- duration in minutes
    price numeric,
    max_capacity integer,
    is_active boolean DEFAULT true,
    image_url varchar,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    business_hours_override_id uuid REFERENCES public.n8n_booking_businesses(id),
    min_booking_lead_time interval
);

COMMENT ON TABLE public.n8n_booking_services IS '服務項目表';

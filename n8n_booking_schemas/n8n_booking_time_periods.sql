CREATE TABLE public.n8n_booking_time_periods (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    business_id uuid REFERENCES public.n8n_booking_businesses(id),
    name varchar NOT NULL,
    start_time time,
    end_time time,
    start_minutes integer,
    end_minutes integer,
    max_capacity integer,
    is_active boolean DEFAULT true
);

COMMENT ON TABLE public.n8n_booking_time_periods IS '預約時段表';

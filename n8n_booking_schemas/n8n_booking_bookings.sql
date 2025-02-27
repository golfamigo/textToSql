CREATE TABLE public.n8n_booking_bookings (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    booking_created_at timestamp with time zone DEFAULT now(),
    booking_date date,
    booking_duration interval,
    booking_start_time time with time zone NOT NULL,
    business_id uuid REFERENCES public.n8n_booking_businesses(id),
    customer_email varchar NOT NULL,
    customer_name varchar NOT NULL,
    customer_notes text,
    customer_phone varchar,
    line_user_id varchar,
    notes text,
    notification_status jsonb,
    number_of_people integer DEFAULT 1,
    period_id uuid REFERENCES public.n8n_booking_time_periods(id),
    service_id uuid REFERENCES public.n8n_booking_services(id),
    staff_id uuid REFERENCES public.n8n_booking_users(id),
    status varchar DEFAULT 'confirmed',
    updated_at timestamp with time zone,
    user_id uuid
);

COMMENT ON TABLE public.n8n_booking_bookings IS '预约表';

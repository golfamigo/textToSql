CREATE TYPE public.availability_type AS ENUM ('available', 'unavailable');

CREATE TABLE public.n8n_booking_staff_availability (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    staff_id uuid REFERENCES public.n8n_booking_users(id),
    business_id uuid REFERENCES public.n8n_booking_businesses(id),
    day_of_week integer, -- 0=Sunday, 1=Monday, ..., 6=Saturday
    specific_date date,
    start_time time NOT NULL,
    end_time time NOT NULL,
    is_recurring boolean DEFAULT true,
    availability_type public.availability_type DEFAULT 'available'::public.availability_type,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);

COMMENT ON TABLE public.n8n_booking_staff_availability IS '员工可用时间表';

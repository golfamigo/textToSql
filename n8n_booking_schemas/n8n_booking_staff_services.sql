CREATE TABLE public.n8n_booking_staff_services (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    staff_id uuid REFERENCES public.n8n_booking_users(id),
    service_id uuid REFERENCES public.n8n_booking_services(id),
    is_primary boolean DEFAULT false,
    proficiency_level integer,
    notes text,
    created_at timestamp with time zone DEFAULT now()
);

COMMENT ON TABLE public.n8n_booking_staff_services IS '員工可提供的服務關聯表';

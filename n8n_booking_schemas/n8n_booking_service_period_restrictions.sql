CREATE TABLE public.n8n_booking_service_period_restrictions (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    service_id uuid REFERENCES public.n8n_booking_services(id),
    period_id uuid REFERENCES public.n8n_booking_time_periods(id),
    is_allowed boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);

COMMENT ON TABLE public.n8n_booking_service_period_restrictions IS '服務與時段限制關係表';

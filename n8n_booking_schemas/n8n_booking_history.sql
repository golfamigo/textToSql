CREATE TABLE public.n8n_booking_history (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    booking_id uuid REFERENCES public.n8n_booking_bookings(id),
    previous_status varchar,
    new_status varchar,
    changed_by uuid,
    reason text,
    created_at timestamp with time zone DEFAULT now()
);

COMMENT ON TABLE public.n8n_booking_history IS '預約狀態變更歷史記錄';

CREATE TYPE public.user_role AS ENUM ('admin', 'staff', 'customer');

CREATE TABLE public.n8n_booking_users (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    name varchar NOT NULL,
    email varchar,
    phone varchar,
    line_user_id varchar,
    role public.user_role NOT NULL,
    password_hash varchar,
    business_id uuid REFERENCES public.n8n_booking_businesses(id),
    is_active boolean DEFAULT true,
    notes text,
    settings jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    last_login timestamp with time zone
);

COMMENT ON TABLE public.n8n_booking_users IS '系統用戶表';

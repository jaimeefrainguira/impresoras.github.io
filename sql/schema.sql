CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    whatsapp_number VARCHAR(30) UNIQUE NOT NULL,
    full_name VARCHAR(120),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TYPE order_status AS ENUM (
    'file_received',
    'options_selected',
    'price_sent',
    'payment_pending',
    'payment_review',
    'approved_for_print',
    'printing',
    'ready_for_pickup'
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id),
    status order_status NOT NULL DEFAULT 'file_received',
    file_path TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_mime VARCHAR(100),
    size VARCHAR(10),
    print_type VARCHAR(20),
    material VARCHAR(50),
    pages INT NOT NULL DEFAULT 1,
    color_percentage NUMERIC(5,2),
    total_price NUMERIC(10,2),
    conversation_step VARCHAR(50) NOT NULL DEFAULT 'awaiting_size',
    requires_human BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE print_prices (
    id SERIAL PRIMARY KEY,
    size VARCHAR(10) NOT NULL,
    print_type VARCHAR(20) NOT NULL,
    material VARCHAR(50) NOT NULL,
    price_color NUMERIC(10,2) NOT NULL,
    price_bw NUMERIC(10,2) NOT NULL,
    base_price NUMERIC(10,2) NOT NULL
);

CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id),
    receipt_path TEXT NOT NULL,
    amount_reported NUMERIC(10,2),
    status VARCHAR(30) NOT NULL DEFAULT 'pending_review',
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO print_prices (size, print_type, material, price_color, price_bw, base_price) VALUES
('A4', 'color', 'Papel Bond', 0.25, 0.10, 0.50),
('A4', 'black_white', 'Papel Bond', 0.25, 0.10, 0.50),
('A3', 'color', 'Papel Bond', 0.40, 0.15, 0.75),
('A3', 'black_white', 'Papel Bond', 0.40, 0.15, 0.75);

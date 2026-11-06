CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    nfc_chip_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50),
    manual_data JSONB
);

CREATE TABLE IF NOT EXISTS production_routes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    equipment_id INTEGER
);

CREATE TABLE IF NOT EXISTS equipment (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    description TEXT
);

CREATE TABLE IF NOT EXISTS complaints (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    detail_id INTEGER,
    description TEXT,
    status VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS instructions (
    id SERIAL PRIMARY KEY,
    equipment_id INTEGER REFERENCES equipment(id),
    content TEXT,
    file_path VARCHAR(255)
);
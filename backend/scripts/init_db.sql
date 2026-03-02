-- AgroPulse AI - Database Initialization Script
-- Run by PostgreSQL on first container startup

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Farmers table
CREATE TABLE IF NOT EXISTS farmers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cognito_sub VARCHAR(256) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    village VARCHAR(100),
    land_area_hectares FLOAT DEFAULT 1.0,
    preferred_language VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_farmers_cognito_sub ON farmers(cognito_sub);
CREATE INDEX IF NOT EXISTS idx_farmers_district ON farmers(district);

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farmer_id UUID REFERENCES farmers(id) ON DELETE SET NULL,
    prediction_type VARCHAR(50) NOT NULL,
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    confidence_score FLOAT,
    model_version VARCHAR(50) DEFAULT 'v1',
    explanation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_farmer_id ON predictions(farmer_id);
CREATE INDEX IF NOT EXISTS idx_predictions_type ON predictions(prediction_type);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farmer_id UUID NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message VARCHAR(2000) NOT NULL,
    risk_score FLOAT NOT NULL,
    metadata JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_farmer_id ON alerts(farmer_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);

-- Weather records table
CREATE TABLE IF NOT EXISTS weather_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    district VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    temperature_celsius FLOAT NOT NULL,
    humidity_percent FLOAT NOT NULL,
    rainfall_mm FLOAT DEFAULT 0.0,
    wind_speed_kmh FLOAT DEFAULT 0.0,
    weather_condition VARCHAR(100),
    raw_data JSONB,
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weather_district ON weather_records(district);
CREATE INDEX IF NOT EXISTS idx_weather_recorded_at ON weather_records(recorded_at);

-- Market prices table
CREATE TABLE IF NOT EXISTS market_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commodity VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    market VARCHAR(200) NOT NULL,
    variety VARCHAR(100),
    min_price FLOAT NOT NULL,
    max_price FLOAT NOT NULL,
    modal_price FLOAT NOT NULL,
    unit VARCHAR(20) DEFAULT 'Quintal',
    price_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(commodity, state, district, market, price_date)
);

CREATE INDEX IF NOT EXISTS idx_market_commodity ON market_prices(commodity);
CREATE INDEX IF NOT EXISTS idx_market_state_district ON market_prices(state, district);
CREATE INDEX IF NOT EXISTS idx_market_price_date ON market_prices(price_date);

-- Sample data for development
INSERT INTO farmers (cognito_sub, name, phone, state, district, village, land_area_hectares)
VALUES
    ('demo-sub-001', 'Ramesh Kumar', '+91-9876543210', 'Maharashtra', 'Pune', 'Hadapsar', 2.5),
    ('demo-sub-002', 'Sunita Devi', '+91-9876543211', 'Punjab', 'Ludhiana', 'Jamalpur', 4.0),
    ('demo-sub-003', 'Raju Yadav', '+91-9876543212', 'Uttar Pradesh', 'Agra', 'Kheragarh', 1.5)
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agropulse;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agropulse;

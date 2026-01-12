-- Инициализация базы данных для Voskhod AI

-- Создание расширения для UUID (если не существует)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица для API ключей
CREATE TABLE IF NOT EXISTS keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_value VARCHAR(64) UNIQUE NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    telegram_id VARCHAR(50),  -- Telegram ID, для которого предназначен ключ
    tag VARCHAR(100),  -- Тег пользователя, активировавшего ключ
    count_requests INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_keys_key_value ON keys(key_value);
CREATE INDEX IF NOT EXISTS idx_keys_active ON keys(active);
CREATE INDEX IF NOT EXISTS idx_keys_tag ON keys(tag);
CREATE INDEX IF NOT EXISTS idx_keys_created_at ON keys(created_at);

-- Миграция: добавление поля tag для существующих таблиц
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'keys' AND column_name = 'tag') THEN
        ALTER TABLE keys ADD COLUMN tag VARCHAR(100);
        CREATE INDEX IF NOT EXISTS idx_keys_tag ON keys(tag);
    END IF;
END $$;

-- Миграция: добавление поля telegram_id для привязки ключа к Telegram ID
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'keys' AND column_name = 'telegram_id') THEN
        ALTER TABLE keys ADD COLUMN telegram_id VARCHAR(50);
        CREATE INDEX IF NOT EXISTS idx_keys_telegram_id ON keys(telegram_id);
    END IF;
END $$;

-- Таблица для логов чата (опционально, для аналитики)
CREATE TABLE IF NOT EXISTS chat_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key_id UUID REFERENCES keys(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    rag_used BOOLEAN DEFAULT FALSE,
    sources_count INTEGER DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_time_ms INTEGER
);

-- Индексы для логов
CREATE INDEX IF NOT EXISTS idx_chat_logs_api_key ON chat_logs(api_key_id);
CREATE INDEX IF NOT EXISTS idx_chat_logs_timestamp ON chat_logs(timestamp);

-- Создание тестового ключа (опционально, для разработки)
-- INSERT INTO keys (key_value, active) VALUES ('TEST_KEY_1234567890', true)
-- ON CONFLICT (key_value) DO NOTHING;

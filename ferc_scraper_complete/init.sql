-- FERC Scraper Database Initialization Script

-- Create schema for FERC data
CREATE SCHEMA IF NOT EXISTS ferc_schema;

-- Grant permissions to ferc_user
GRANT ALL PRIVILEGES ON SCHEMA ferc_schema TO ferc_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ferc_schema TO ferc_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ferc_schema TO ferc_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA ferc_schema GRANT ALL ON TABLES TO ferc_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA ferc_schema GRANT ALL ON SEQUENCES TO ferc_user;

-- Create documents table for SCD1/SCD2
CREATE TABLE IF NOT EXISTS ferc_schema.documents (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    published_at TIMESTAMP,
    content_text TEXT,
    content_hash VARCHAR(64),
    extra JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_current BOOLEAN DEFAULT TRUE,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP DEFAULT '9999-12-31 23:59:59',
    UNIQUE(document_id, valid_from)
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_documents_document_id ON ferc_schema.documents(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_source ON ferc_schema.documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_published_at ON ferc_schema.documents(published_at);
CREATE INDEX IF NOT EXISTS idx_documents_is_current ON ferc_schema.documents(is_current);

-- Create raw data table for ingested datasets
CREATE TABLE IF NOT EXISTS ferc_schema.ferc_raw (
    id SERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    dataset_name VARCHAR(255),
    row_data JSONB,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_hash VARCHAR(64)
);

-- Create index for raw data
CREATE INDEX IF NOT EXISTS idx_ferc_raw_source_url ON ferc_schema.ferc_raw(source_url);
CREATE INDEX IF NOT EXISTS idx_ferc_raw_dataset_name ON ferc_schema.ferc_raw(dataset_name);

-- Create function to update timestamp
CREATE OR REPLACE FUNCTION ferc_schema.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON ferc_schema.documents 
    FOR EACH ROW EXECUTE FUNCTION ferc_schema.update_updated_at_column();

-- Create function for SCD2 updates
CREATE OR REPLACE FUNCTION ferc_schema.update_document_scd2(
    p_source VARCHAR(50),
    p_document_id VARCHAR(255),
    p_url TEXT,
    p_title TEXT,
    p_published_at TIMESTAMP,
    p_content_text TEXT DEFAULT NULL,
    p_content_hash VARCHAR(64) DEFAULT NULL,
    p_extra JSONB DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    -- Close current version if exists
    UPDATE ferc_schema.documents 
    SET is_current = FALSE, valid_to = CURRENT_TIMESTAMP
    WHERE document_id = p_document_id AND is_current = TRUE;
    
    -- Insert new version
    INSERT INTO ferc_schema.documents (
        source, document_id, url, title, published_at, 
        content_text, content_hash, extra, valid_from
    ) VALUES (
        p_source, p_document_id, p_url, p_title, p_published_at,
        p_content_text, p_content_hash, p_extra, CURRENT_TIMESTAMP
    ) RETURNING id INTO v_id;
    
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION ferc_schema.update_updated_at_column() TO ferc_user;
GRANT EXECUTE ON FUNCTION ferc_schema.update_document_scd2(VARCHAR, VARCHAR, TEXT, TEXT, TIMESTAMP, TEXT, VARCHAR, JSONB) TO ferc_user;

-- Insert sample data for testing
INSERT INTO ferc_schema.documents (source, document_id, url, title, published_at, extra) VALUES
('FERC_DB', 'sample-form-1.zip', 'https://www.ferc.gov/dataset/sample-form-1.zip', 'Sample Form 1 Data', CURRENT_TIMESTAMP, '{"version": "1.0", "type": "sample"}')
ON CONFLICT (document_id, valid_from) DO NOTHING;

COMMIT;
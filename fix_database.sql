-- SQL script to manually add missing custom_data columns
-- Run this directly on Railway's PostgreSQL database

-- Add custom_data to crm_lead table
ALTER TABLE crm_lead ADD COLUMN IF NOT EXISTS custom_data JSONB DEFAULT '{}' NOT NULL;

-- Add custom_data to crm_contact table
ALTER TABLE crm_contact ADD COLUMN IF NOT EXISTS custom_data JSONB DEFAULT '{}' NOT NULL;

-- Add department to crm_contact table
ALTER TABLE crm_contact ADD COLUMN IF NOT EXISTS department VARCHAR(100) DEFAULT '' NOT NULL;

-- Verify the columns were added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'crm_lead' AND column_name = 'custom_data';

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'crm_contact' AND column_name IN ('custom_data', 'department');

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'crm_deal' AND column_name = 'custom_data';

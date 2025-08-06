-- sample_data.sql
-- This script inserts some sample records into the Property table.
-- Make sure you have run schema.sql first.

-- Use the correct database
USE property_db;

-- Insert sample records
INSERT INTO Property (address, type, monthly_rent, status) VALUES
('123 Main St, Anytown, USA', 'Apartment', 1250.00, 'Available'),
('45 High St, Sometown, USA', 'Shop', 2100.00, 'Occupied'),
('789 Lake Rd, Newville, USA', 'Villa', 3500.50, 'Available'),
('101 Business Blvd, Corp City, USA', 'Office', 4000.00, 'Under Maintenance'),
('222 Suburbia Ln, Residia, USA', 'House', 1800.00, 'Occupied');
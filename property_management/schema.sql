-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS property_db;

-- Switch to the new database
USE property_db;

-- Create the main table for properties
CREATE TABLE IF NOT EXISTS Property (
    id INT AUTO_INCREMENT PRIMARY KEY,
    address VARCHAR(255) NOT NULL,
    type VARCHAR(50),
    monthly_rent DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50)
);

-- Create the table for the AI-powered compliance checklists
CREATE TABLE IF NOT EXISTS PropertyCompliance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT,
    rule_description TEXT NOT NULL,
    is_completed BOOLEAN DEFAULT 0,
    FOREIGN KEY (property_id) 
        REFERENCES Property(id) 
        ON DELETE CASCADE
);

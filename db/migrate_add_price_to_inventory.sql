-- Migration script to add price column to Inventory table
-- and remove price column from Products table

-- Step 1: Add price column to Inventory table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'inventory' AND column_name = 'price'
    ) THEN
        ALTER TABLE Inventory ADD COLUMN price DECIMAL(12,2) NOT NULL DEFAULT 0.0 CHECK (price >= 0);
        
        -- Update existing inventory items with a default price
        -- You may want to set this to a more appropriate default value
        UPDATE Inventory SET price = 100.0 WHERE price = 0.0;
        
        -- Remove the default after setting values
        ALTER TABLE Inventory ALTER COLUMN price DROP DEFAULT;
    END IF;
END $$;

-- Step 2: Remove price column from Products table if it exists
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'products' AND column_name = 'price'
    ) THEN
        ALTER TABLE Products DROP COLUMN price;
    END IF;
END $$;


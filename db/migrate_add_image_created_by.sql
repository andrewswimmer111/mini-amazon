-- Migration script to add image and created_by columns to Products table

-- Step 1: Add image column to Products table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'products' AND column_name = 'image'
    ) THEN
        ALTER TABLE Products ADD COLUMN image TEXT;
    END IF;
END $$;

-- Step 2: Add created_by column to Products table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'products' AND column_name = 'created_by'
    ) THEN
        ALTER TABLE Products ADD COLUMN created_by INT;
        ALTER TABLE Products ADD CONSTRAINT products_created_by_fkey 
            FOREIGN KEY (created_by) REFERENCES Users(id);
    END IF;
END $$;


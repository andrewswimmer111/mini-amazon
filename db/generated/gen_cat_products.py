import csv
import os
import uuid
import requests
import random
from faker import Faker

STATIC_DIR = "app/static/product_images"   # or "static/product_images" depending on your structure
os.makedirs(STATIC_DIR, exist_ok=True)

def download_and_save_image(url):
    try:
        r = requests.get(url, timeout=6)
        if r.status_code != 200:
            print(f"Failed to fetch {url}")
            return None
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(STATIC_DIR, filename)

        # Save file
        with open(filepath, "wb") as f:
            f.write(r.content)

        # Return the URL path Flask will serve
        print(f"Saved image to {filename}")
        return f"/static/product_images/{filename}"
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def gen_cat_products(output_file="db/generated/Products.csv", max_cats=1500, sayings=None):
    """
    Generate a CSV file of cat products using the CATAAS API.
    
    Args:
        output_file (str): Path to output CSV file
        max_cats (int): Maximum number of cat products to generate
        sayings (list): List of sayings for cats. Defaults to ["meow", "hello", "goodbye", "prr"]
    
    Returns:
        int: Number of products generated
    
    Raises:
        Exception: If fetching cats from API fails
    """
    if sayings is None:
        sayings = ["meow", "hello", "goodbye", "prr"]
    
    fake = Faker()
    
    # Fetch cats
    print("Fetching cats from CATAAS (this may take a few seconds)...")
    
    try:
        cats = requests.get(f"https://cataas.com/api/cats?limit={max_cats}").json()
    except Exception as e:
        raise Exception(f"Failed to fetch cats: {e}")
    
    if not isinstance(cats, list):
        raise Exception(f"Unexpected response format: {cats}")
    
    print(f"Retrieved {len(cats)} cats.\n")
    
    # CSV setup
    csv_file = open(output_file, "w", newline="", encoding="utf-8")
    writer = csv.writer(csv_file)
    writer.writerow(["id", "name", "description", "image", "category", "created_by"])
    
    # Generate product rows
    cat_id = 1
    products = {}
    
    for cat in cats:
        if cat_id > max_cats:
            break
        
        # Check malform
        acceptable = ["image/jpeg", "image/png", "image/jpg"]
        
        image_id = cat.get("id")
        image_type = cat.get("mimetype")
        if not image_id:
            continue  # skip malformed records
        if image_type not in acceptable:
            continue
        
        # Take the first tag (or fallback)
        tags = cat.get("tags", [])
        first_tag = tags[0] if tags else "unknown"
        
        parts = first_tag.split()
        if parts and parts[-1] == "cat":
            first_tag = " ".join(parts[:-1])
        
        # Generate product fields
        name = fake.first_name()
        product = first_tag + " " + name
        
        while product in products:  # Generate a new name
            name = fake.first_name()
            product = first_tag + " " + name
        
        products[product] = True
        
        saying = random.choice(sayings)
        description = f"{first_tag} cat saying {saying} named {name}"
        created_by = random.randint(1, 50)
        
        # Stable image URL (never changes)
        external_url = f"https://cataas.com/cat/{image_id}/says/{saying}"

        # UNCOMMENT BELOW FOR CACHED IMAGES 9may take 20-30 min to run
        # local_image_path = download_and_save_image(external_url)

        # # If download fails, skip this product
        # if not local_image_path:
        #     continue
        
        # writer.writerow([
        #     cat_id,
        #     product,
        #     description,
        #     local_image_path,
        #     saying,
        #     created_by
        # ])

        # COMMENT BELOW IF YOU UNCOMMENT ABOVE
        writer.writerow([
            cat_id,
            product,
            description,
            external_url,
            saying,
            created_by
        ])
        
        
        cat_id += 1
    
    csv_file.close()
    
    products_generated = cat_id - 1
    print(f"Done! Generated {products_generated} cat products into {output_file}.")
    
    return products_generated
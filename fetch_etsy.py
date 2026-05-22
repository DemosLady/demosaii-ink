"""
demosaii ink — Etsy Listings Fetcher
Pulls all active listings + images from your Etsy shop and saves as products.json
Run this whenever you add/change products, then push the site.
"""
import os
import sys
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# ===== ENV =====
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
API_KEY = os.getenv("ETSY_API_KEY")

if not API_KEY:
    print("[ERROR] ETSY_API_KEY not found in .env")
    print(f"  Looked in: {env_path}")
    sys.exit(1)

BASE_URL = "https://openapi.etsy.com/v3/application"
HEADERS = {"x-api-key": API_KEY}
SHOP_NAME = "demosaii"
OUTPUT_DIR = Path(__file__).parent


def api_get(endpoint, params=None):
    """Make GET request to Etsy API with rate limit handling."""
    url = f"{BASE_URL}{endpoint}"
    for attempt in range(3):
        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            wait = 5 * (attempt + 1)
            print(f"  [RATE LIMIT] Waiting {wait}s...")
            time.sleep(wait)
        else:
            print(f"  [ERROR] {resp.status_code}: {resp.text[:200]}")
            return None
    print("[ERROR] Max retries reached")
    return None


def get_shop_id():
    """Get numeric shop ID from shop name."""
    print(f"[1/4] Looking up shop: {SHOP_NAME}")
    data = api_get("/shops", params={"shop_name": SHOP_NAME})
    if data and data.get("results"):
        shop = data["results"][0]
        shop_id = shop["shop_id"]
        print(f"  Found: {shop['shop_name']} (ID: {shop_id})")
        return shop_id
    print("[ERROR] Shop not found")
    return None


def get_active_listings(shop_id):
    """Fetch all active listings with pagination."""
    print(f"[2/4] Fetching active listings...")
    all_listings = []
    offset = 0
    limit = 100

    while True:
        data = api_get(
            f"/shops/{shop_id}/listings/active",
            params={"limit": limit, "offset": offset}
        )
        if not data or not data.get("results"):
            break

        results = data["results"]
        all_listings.extend(results)
        print(f"  Fetched {len(all_listings)} / {data.get('count', '?')} listings")

        if len(results) < limit:
            break
        offset += limit
        time.sleep(0.5)  # be nice to the API

    return all_listings


def get_listing_images(listing_ids):
    """Fetch images for listings using batch endpoint."""
    print(f"[3/4] Fetching images for {len(listing_ids)} listings...")
    images_map = {}

    # Batch endpoint supports up to 100 IDs at a time
    for i in range(0, len(listing_ids), 100):
        batch = listing_ids[i:i+100]
        ids_str = ",".join(str(lid) for lid in batch)
        data = api_get(
            "/listings/batch",
            params={"listing_ids": ids_str, "includes": "Images"}
        )
        if data and data.get("results"):
            for listing in data["results"]:
                lid = listing["listing_id"]
                imgs = listing.get("images", [])
                if imgs:
                    images_map[lid] = [
                        {
                            "url_570xN": img.get("url_570xN", ""),
                            "url_fullxfull": img.get("url_fullxfull", ""),
                            "url_75x75": img.get("url_75x75", ""),
                        }
                        for img in imgs
                    ]
            print(f"  Processed batch {i//100 + 1} ({len(batch)} listings)")
        time.sleep(0.5)

    return images_map


def categorize_listing(title, tags):
    """Auto-categorize based on title and tags."""
    title_lower = title.lower()
    tags_lower = [t.lower() for t in tags] if tags else []
    all_text = title_lower + " " + " ".join(tags_lower)

    # BTS Shirts
    if any(w in all_text for w in ["t-shirt", "tee", "shirt", "hoodie", "apparel"]):
        if any(w in all_text for w in ["bts", "kpop", "k-pop", "bangtan", "army"]):
            return "bts-shirts"
        return "bts-shirts"  # all shirts are kpop for now

    # eBooks & Guides
    if any(w in all_text for w in ["ebook", "e-book", "guide", "journal", "coloring book", "workbook"]):
        return "ebooks"

    # Digital Products
    if any(w in all_text for w in ["planner", "spreadsheet", "template", "tracker", "checklist", "calendar"]):
        return "digital"

    # BTS Prints
    if any(w in all_text for w in ["bts", "kpop", "k-pop", "bangtan", "army", "concert", "idol", "singer"]):
        return "bts-prints"

    # Other Prints (default for print sets, wall art, etc.)
    return "prints"


def build_products_json(listings, images_map):
    """Transform Etsy data into our site's product format."""
    print(f"[4/4] Building products.json...")
    products = []

    for listing in listings:
        lid = listing["listing_id"]
        title = listing.get("title", "Untitled")
        price_raw = listing.get("price", {})
        tags = listing.get("tags", [])

        # Price
        amount = price_raw.get("amount")
        divisor = price_raw.get("divisor", 100)
        currency = price_raw.get("currency_code", "USD")
        if amount is not None:
            price_val = amount / divisor
            price_str = f"${price_val:.2f}"
        else:
            price_str = "Price varies"

        # Images
        listing_images = images_map.get(lid, [])
        main_image = listing_images[0]["url_570xN"] if listing_images else ""
        all_image_urls = [img["url_570xN"] for img in listing_images]

        # Category
        section = categorize_listing(title, tags)

        # Etsy URL
        etsy_url = listing.get("url", f"https://www.etsy.com/listing/{lid}")

        product = {
            "id": lid,
            "name": title,
            "section": section,
            "price": price_str,
            "etsy_url": etsy_url,
            "image": main_image,
            "images": all_image_urls,
            "tags": tags[:5],
            "quantity": listing.get("quantity", 0),
            "views": listing.get("views", 0),
            "favorites": listing.get("num_favorers", 0),
        }
        products.append(product)

    # Sort: most favorites first within each section
    products.sort(key=lambda p: (-p["favorites"], p["section"]))

    return products


def main():
    print("=" * 50)
    print("  demosaii ink — Etsy Listings Fetcher")
    print("=" * 50)
    print()

    # Step 1: Get shop ID
    shop_id = get_shop_id()
    if not shop_id:
        sys.exit(1)

    # Step 2: Get all active listings
    listings = get_active_listings(shop_id)
    if not listings:
        print("[ERROR] No active listings found")
        sys.exit(1)

    # Step 3: Get images
    listing_ids = [l["listing_id"] for l in listings]
    images_map = get_listing_images(listing_ids)

    # Step 4: Build and save JSON
    products = build_products_json(listings, images_map)

    output_file = OUTPUT_DIR / "products.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print()
    print(f"  Saved {len(products)} products to: {output_file}")
    print()

    # Summary by section
    sections = {}
    for p in products:
        s = p["section"]
        sections[s] = sections.get(s, 0) + 1
    print("  Breakdown:")
    for s, count in sorted(sections.items()):
        print(f"    {s}: {count}")
    print()
    print("  Done! Now push the site with PUSH_SITE.bat")
    print("=" * 50)


if __name__ == "__main__":
    main()

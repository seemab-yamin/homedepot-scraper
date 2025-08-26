import json
import pandas as pd
import os, re
from lxml import html
from utils import extract_reviews, crawl_category, html_request
import time
import argparse


BASE_URL = "https://www.homedepot.com"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def process_category(category_url):
    category_name = category_url.split("/")[-2].split("/N-")[0]

    category_id = category_url.split("/N-")[-1]
    store_id = "106"
    delivery_zip = "33101"
    category_products_file = os.path.join(
        OUTPUT_DIR,
        f"{category_name}_{category_id}_{store_id}_{delivery_zip}_products.json",
    )
    if os.path.exists(category_products_file):
        print(f"Loading existing file: {category_products_file}")
        cat_products_df = pd.read_json(category_products_file)
        # replace nan with empty string
        cat_products_df = cat_products_df.fillna("")
    else:
        print(f"Crawling category: {category_name}, {category_id}")
        page_size = 48
        start_index = 0
        total_products = float("inf")
        master_products = []
        while start_index < total_products:
            products, total_products = crawl_category(
                category_id,
                store_id,
                delivery_zip,
                str(page_size),
                str(start_index),
            )
            print(f"Total Products Count::\t{total_products}")
            start_index = start_index + page_size
            master_products.extend(products)
            time.sleep(0.5)

        cat_products_df = pd.DataFrame(master_products)
        cat_products_df.to_json(category_products_file, index=False)
    return cat_products_df


def process_product(row):
    product_url = row["URL"]
    print("* Variants Count:\t", row["variants_count"])

    raw_html = html_request(product_url)
    # Parse HTML with lxml
    tree = html.fromstring(raw_html)
    # Use XPath to find script elements containing 'ROOT_QUERY'
    script_elements = tree.xpath("//script[contains(text(), 'ROOT_QUERY')]")

    for script in script_elements:
        script_content = script.text_content().strip()
        # Find the JSON object that contains ROOT_QUERY
        json_match = re.search(r'({.*"ROOT_QUERY".*})', script_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                script_data = json.loads(json_str)
                print("Found ROOT_QUERY script data using XPath")
                break
            except json.JSONDecodeError:
                continue
            except json.JSONDecodeError:
                continue

    pr = script_data.get(f"base-catalog-{row['item_id']}")
    identifiers = pr.get("identifiers", {})
    row["oms_thd_sku"] = identifiers.get("omsThdSku")
    row["UPC"] = identifiers.get("upc")
    row["upc_gtin13"] = identifiers.get("upcGtin13")
    for item in pr.get("specificationGroup"):
        for value in item.get("specifications"):
            row[value.get("specName")] = value.get("specValue")

    row["ColorVariation"] = bool(row.get("Finish"))
    row["Description"] = pr.get("details").get("description")
    row["Highlights"] = pr.get("details").get("highlights", [])
    row["descriptiveAttributes"] = [
        item.get("value")
        for item in pr.get("details").get("descriptiveAttributes", [])
        if item.get("value")
    ]
    media = pr.get("media")

    row["Videos"] = [
        {
            "type": vid.get("type"),
            "title": vid.get("title"),
            "dateModified": vid.get("dateModified"),
            "uploadDate": vid.get("uploadDate"),
            "videoStill": vid.get("videoStill"),
            "thumbnail": vid.get("thumbnail"),
            "shortDescription": vid.get("shortDescription"),
            "url": vid.get("url"),
        }
        for vid in media.get("video")
        if vid.get("title")
    ]

    row["ImageURL"] = [
        img.get("url").replace("<SIZE>", "1000")
        for img in media.get("images")
        if img.get("url")
    ]

    df = pd.DataFrame()

    sort_by_filters = [
        "newest",
        "oldest",
        "mosthelpfull",
        "photoreview",
        "lowestrating",
        "highestrating",
    ]
    for sort_by in sort_by_filters:
        print(f"Extracting reviews sorted by {sort_by}...")
        er_data = extract_reviews(row, sort_by)
        df = pd.concat([df, pd.DataFrame(er_data)], ignore_index=True)
        print(f"Reviews so far: {len(df)}")

        review_count = row.get("ReviewCount", 0) if row.get("ReviewCount", 0) else 0
        if int(review_count) <= 511:
            break

    if "review_id" in df.columns:
        df.drop_duplicates(subset=["review_id"], inplace=True)

    if "Helpful" in df.columns:
        df["Helpful count"] = df["Helpful"].sum()

    # Find boolean columns and convert them to Yes/No
    for col in df.columns:
        if df[col].dtype == "bool":
            df[col] = df[col].map({True: "Yes", False: "No"})

    if "Recommended" in df.columns:
        df["Recommended"] = df["Recommended"].map({True: "Yes", False: "No"})

    if "CustomerImages" in df.columns:
        df.loc[:, "CustomerImages"] = df.loc[:, "CustomerImages"].apply(
            lambda x: x if len(x) > 0 else ""
        )

    if "Videos" in df.columns:
        df.loc[:, "Videos"] = df.loc[:, "Videos"].apply(
            lambda x: x if len(x) > 0 else ""
        )

    if "variant" in df.columns:
        df.loc[:, "variant"] = df.loc[:, "variant"].apply(
            lambda x: x if len(x) > 0 else ""
        )

    # Keep only the first row and remove all others
    for col in [
        "Description",
        "Highlights",
        "descriptiveAttributes",
        "Videos",
        "ImageURL",
    ]:
        if col in df.columns:
            df.loc[
                1:,
                col,
            ] = None

    return df


def main():
    parser = argparse.ArgumentParser(description="HomeDepot Reviews Scraper")
    parser.add_argument("category_url", help="Input Category URL")
    args = parser.parse_args()

    already_processed_products_file = os.path.join(OUTPUT_DIR, "processed_products.txt")
    if os.path.exists(already_processed_products_file):
        with open(already_processed_products_file, "r") as f:
            already_processed_products = set(line.strip() for line in f)
    else:
        already_processed_products = set()

    # Step 1: Process Category
    category_url = args.category_url
    cat_products_df = process_category(category_url)
    print(f"Total products in category: {cat_products_df.shape}")

    # Step 2: Process each product for reviews
    category_products_reviews_file = os.path.join(
        OUTPUT_DIR,
        f"products_reviews_{category_url.split('/')[-2].split('/N-')[0]}.csv",
    )

    # remove records that are already processed
    cat_products_df = cat_products_df[
        ~cat_products_df["URL"].isin(already_processed_products)
    ]

    for _, row in cat_products_df.iterrows():
        try:
            pr_df = process_product(row)
        except Exception as e:
            print(f"Error processing product {row['URL']}: {e}")
            continue

        print(f"Total reviews for {row['URL']}: {pr_df.shape}")
        if os.path.exists(category_products_reviews_file):
            product_reviews_df = pd.read_csv(category_products_reviews_file)
            product_reviews_df = pd.concat(
                [product_reviews_df, pr_df], ignore_index=True
            )
            product_reviews_df.to_csv(category_products_reviews_file, index=False)
        else:
            pr_df.to_csv(category_products_reviews_file, index=False)

        with open(already_processed_products_file, "a") as f:
            f.write(row["URL"] + "\n")
        already_processed_products.add(row["URL"])


if __name__ == "__main__":
    main()

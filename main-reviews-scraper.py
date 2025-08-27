import json
import pandas as pd
import os, re
from lxml import html
from utils import extract_reviews, crawl_category, html_request
import time
import argparse
import warnings
import logging
from logging.handlers import RotatingFileHandler

warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

# GLOBAL VARIABLES
TMP_DIR = "./tmp"
os.makedirs(TMP_DIR, exist_ok=True)  # Ensure tmp directory exists
# Shared log file for all scraper modules
LOG_FILE = os.path.join(TMP_DIR, "scraper.log")
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5  # Keep up to 5 old log files


def setup_logging() -> logging.Logger:
    """Configure and return shared logger to avoid duplication across modules"""
    logger = logging.getLogger("homedepot")
    if not logger.handlers:  # configure once
        logger.setLevel(logging.INFO)
        # Set up formatter with more readable format
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # Console handler with explicit stream (stdout)
        stream_h = logging.StreamHandler()
        stream_h.setLevel(logging.INFO)
        stream_h.setFormatter(fmt)

        # File handler
        file_h = RotatingFileHandler(
            LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
        )
        file_h.setLevel(logging.INFO)
        file_h.setFormatter(fmt)

        logger.addHandler(stream_h)
        logger.addHandler(file_h)

        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
    return logger


BASE_URL = "https://www.homedepot.com"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Setup logging
logger = setup_logging()


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
        cat_products_df = pd.read_json(category_products_file)
        # replace nan with empty string
        cat_products_df = cat_products_df.fillna("")
    else:
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
            start_index = start_index + page_size
            master_products.extend(products)
            time.sleep(0.5)

        cat_products_df = pd.DataFrame(master_products)
        cat_products_df.to_json(category_products_file, index=False)
    return cat_products_df


def process_product(row):
    product_url = row["URL"]
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

                # Safely extract product data with null checks
                pr = script_data.get(f"base-catalog-{row['item_id']}")
                if pr:
                    # Extract identifiers safely
                    identifiers = pr.get("identifiers", {})
                    row["oms_thd_sku"] = identifiers.get("omsThdSku")
                    row["UPC"] = identifiers.get("upc")
                    row["upc_gtin13"] = identifiers.get("upcGtin13")

                    # Extract specifications safely
                    specification_group = pr.get("specificationGroup", [])
                    if specification_group:
                        for item in specification_group:
                            if item and item.get("specifications"):
                                for value in item.get("specifications", []):
                                    if (
                                        value
                                        and value.get("specName")
                                        and value.get("specValue")
                                    ):
                                        row[value.get("specName")] = value.get(
                                            "specValue"
                                        )

                    row["ColorVariation"] = bool(row.get("Finish"))

                    # Extract details safely
                    details = pr.get("details", {})
                    if details:
                        row["Description"] = details.get("description")
                        row["Highlights"] = details.get("highlights", [])
                        descriptive_attrs = details.get("descriptiveAttributes", [])
                        row["descriptiveAttributes"] = [
                            item.get("value")
                            for item in descriptive_attrs
                            if item and item.get("value")
                        ]

                    # Extract media safely
                    media = pr.get("media", {})
                    if media:
                        videos = media.get("video", [])
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
                            for vid in videos
                            if vid and vid.get("title")
                        ]

                        images = media.get("images", [])
                        row["ImageURL"] = [
                            img.get("url").replace("<SIZE>", "1000")
                            for img in images
                            if img and img.get("url")
                        ]

                break

            except json.JSONDecodeError as e:
                logger.warning(
                    f"Failed to parse JSON for product {row.get('item_id', 'unknown')}: {e}"
                )
                continue
            except Exception as e:
                logger.error(
                    f"Unexpected error processing script data for product {row.get('item_id', 'unknown')}: {e}"
                )
                continue

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
        loggermsg = f"Processing reviews for product {row.get('item_id', 'unknown')} sorted by {sort_by}"
        logger.info(loggermsg)
        er_data = extract_reviews(row, sort_by)
        df = pd.concat([df, pd.DataFrame(er_data)], ignore_index=True)
        review_count = (
            row.get("ReviewCount", 0).replace("(empty)", "0")
            if row.get("ReviewCount", 0)
            else 0
        )
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
    print("Program Started...")
    parser = argparse.ArgumentParser(description="HomeDepot Reviews Scraper")
    parser.add_argument("category_url", help="Input Category URL")
    args = parser.parse_args()

    category_url = args.category_url
    category_products_reviews_file = os.path.join(
        OUTPUT_DIR,
        f"products_reviews_{category_url.split('/')[-2].split('/N-')[0]}.csv",
    )
    if os.path.exists(category_products_reviews_file):
        already_processed_products = (
            pd.read_csv(category_products_reviews_file, usecols=["URL"])["URL"]
            .unique()
            .tolist()
        )
    else:
        already_processed_products = set()

    # Step 1: Process Category
    try:
        category_url = category_url.split("?")[0]
        cat_products_df = process_category(category_url)
    except Exception as e:
        logger.error(f"Error processing category {category_url}: {e}")
        return
    logger.info(f"Total products in category: {cat_products_df.shape}")

    # Step 2: Process each product for reviews
    # remove records that are already processed
    cat_products_df = cat_products_df[
        ~cat_products_df["URL"].isin(already_processed_products)
    ]

    logger.info(f"Products to process: {cat_products_df.shape}")

    for _, row in cat_products_df.iterrows():
        try:
            pr_df = process_product(row)
        except Exception as e:
            logger.error(f"Error processing product {row['URL']}: {e}")
            continue

        if os.path.exists(category_products_reviews_file):
            product_reviews_df = pd.read_csv(category_products_reviews_file)
            product_reviews_df = pd.concat(
                [product_reviews_df, pr_df], ignore_index=True
            )
            product_reviews_df.to_csv(category_products_reviews_file, index=False)
        else:
            pr_df.to_csv(category_products_reviews_file, index=False)

        already_processed_products.add(row["URL"])
    print("Program Completed...")


if __name__ == "__main__":
    main()

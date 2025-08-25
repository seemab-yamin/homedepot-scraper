## Documentation

### Install Libraries
```bash
pip install -r requirements.txt
```

### Run script
Replace `{category_url}` with actual category page link. This script will generate dataset CSV file in the `output` folder with `products_review-category-name.csv` name.
```bash
python main-reviews-scraper.py {category_url}
```

### Workflow
The crawler follows following workflow.
- Crawl all the products from the category API by following all the pagination.
- Process each product by
    - First making HTML request and fetch some data from page source.
    - Crawl 510 reviews sorting by [ "newest", "oldest", "mosthelpfull", "photoreview", "lowestrating", "highestrating" ] using reviews API.
    - Drop duplicates by using review_id to remove product review duplicates.
- Appending Each scraped product data in the output file [`products_review-category-name.csv`] after every successful product scraping.
- `already_processed_products_file.txt` holds the products that are already processed to avoid duplicate data.

--- 


### Categories to process
Category Name	Category Path	Link	Approved?

Electronic Door Locks	Hardware->Door Hardware->Electronic Door Locks	https://www.homedepot.com/b/Hardware-Door-Hardware-Door-Locks-Electronic-Door-Locks/N-5yc1vZc2bd	Yes

Door Lock Combo Packs	Hardware->Door Hardware->Door Lock Combo Packs	https://www.homedepot.com/b/Hardware-Door-Hardware-Door-Locks-Door-Lock-Combo-Packs/N-5yc1vZc2g4	Yes

Deadbolts	Hardware->Door Hardware->Door Locks->Deadbolts	https://www.homedepot.com/b/Hardware-Door-Hardware-Door-Locks-Deadbolts/N-5yc1vZcjqk	Yes

Smart Locks	Hardware->Door Hardware->Smart Locks	https://www.homedepot.com/b/Smart-Home-Smart-Devices-Smart-Home-Security-Smart-Locks/N-5yc1vZc7by	Yes

Electronic Locksets	Hardware->Door Hardware->Door Locks->Electronic Door Locks->Electronic Locksets	https://www.homedepot.com/b/Hardware-Door-Hardware-Door-Locks-Electronic-Door-Locks-Electronic-Locksets/N-5yc1vZ2fkp3gk	Yes


### Notes:
Scraping Customer Name is critical and can cause lawsuits because through customer name we can Identify an individual.
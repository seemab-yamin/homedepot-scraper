import requests
from requests.exceptions import TooManyRedirects, RequestException
import time
import logging

# Use shared project logger
logger = logging.getLogger("homedepot")

BASE_URL = "https://www.homedepot.com"
HEADERS = {
    "accept": "*/*",
    "accept-language": "en-GB,en;q=0.9",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://www.homedepot.com",
    "priority": "u=1, i",
    "referer": "https://www.homedepot.com/",
    "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "x-api-cookies": "{}",
    "x-cloud-trace-context": "4156eda4b04547e8b906d835eeae412f/1;o=1",
    "x-current-url": "/b/Hardware-Door-Hardware-Door-Locks-Electronic-Door-Locks/N-5yc1vZc2bd",
    "x-debug": "false",
    "x-experience-name": "general-merchandise",
    "x-hd-dc": "origin",
    "x-parent-trace-id": "c6655c2a3a2754cf7929858289866bd9/12563341903835392272",
    "x-thd-customer-token": "",
    "Cookie": "bm_s=YAAQGpM2Fxt2ALqYAQAA/uYA5QOUTAMo7dxCiuft13uCwMHh7jQf263FFOfWBAElVhTHcpWeBNGgk4RZh5UJYz32nOlbMoiAIrmwIwchqfgEdQkwqlRo0VPmR/Ukgie3i0qPn2vssUJ4UP1+cSO9zusQ5zkSW3ib1/j7XLrlOvJputTxVPYeTSh++1rqfdRI62NWsxPJVlid7qYlwI0MKfuGY+knaJsmBPtrO1Hz3BtVSQIw0WydOR/19Du8IL6dE3/lzdD6XUJl8URCuzguSO7REjXCaqkdCQBmcwEDrumZiFhHunASEhySXB6LWvt5Q5RHPI1TYnCGMSDUQ4+zFxQVzWr9prEeCrajlCzV/yHM0xibZbOZMniYZqexI1LIkJxjUy4dsIxIwvds3Y8BUVaFgl4Yt8GW4p2CvZFVigV5xqsk6ihor0MVhz2qjmh4+sI1qDWdFK0SeLESmA7CJjFtqlk16TeeD8wrkIEtdLdnIk0Co64fe6Z9S/tvUMG0qkPb31je0PeS2Jn/yA057DnOZZJyNZwQKCoRJ01u8fCpEjDruxuS",
}


def api_request(url, payload):
    try:
        response = requests.request("POST", url, headers=HEADERS, data=payload)
        response.raise_for_status()
        if len(response.content) < 500:
            logger.warning(
                f"[API] Response size for {url} is unusually small: {len(response.content)} bytes"
            )
        logger.info(
            f"[API] POST {url} OK {response.status_code} | {len(response.content)} bytes"
        )
        return response.json()
    except TooManyRedirects:
        logger.error(f"[API] Too many redirects (exceeded 30) for URL: {url}")
        raise
    except RequestException as e:
        logger.error(f"[API] Request failed for URL: {url}. Error: {str(e)}")
        raise


def html_request(url):
    try:
        response = requests.request("GET", url, headers=HEADERS)
        response.raise_for_status()
        if len(response.content) < 500:
            logger.warning(
                f"[HTML] Response size for {url} is unusually small: {len(response.content)} bytes"
            )
        logger.info(
            f"[HTML] GET {url} OK {response.status_code} | {len(response.content)} bytes"
        )
        return response.text
    except TooManyRedirects:
        logger.error(f"[HTML] Too many redirects (exceeded 30) for URL: {url}")
        raise
    except RequestException as e:
        logger.error(f"[HTML] Request failed for URL: {url}. Error: {str(e)}")
        raise


def crawl_category(
    category_id,
    store_id,
    delivery_zip,
    page_size,
    start_index="0",
):

    url = (
        "https://apionline.homedepot.com/federation-gateway/graphql?opname=searchModel"
    )

    payload = '{"query":"query searchModel($storeId: String, $zipCode: String, $skipInstallServices: Boolean = true, $startIndex: Int, $pageSize: Int, $orderBy: ProductSort, $filter: ProductFilter, $isBrandPricingPolicyCompliant: Boolean, $skipFavoriteCount: Boolean = false, $keyword: String, $navParam: String, $storefilter: StoreFilter = ALL, $channel: Channel = DESKTOP, $additionalSearchParams: AdditionalParams, $loyaltyMembershipInput: LoyaltyMembershipInput, $dataSource: String, $skipDiscoveryZones: Boolean = true, $skipBuyitagain: Boolean = true) {\\n  searchModel(\\n    keyword: $keyword\\n    navParam: $navParam\\n    storefilter: $storefilter\\n    isBrandPricingPolicyCompliant: $isBrandPricingPolicyCompliant\\n    storeId: $storeId\\n    channel: $channel\\n    additionalSearchParams: $additionalSearchParams\\n    loyaltyMembershipInput: $loyaltyMembershipInput\\n  ) {\\n    metadata {\\n      hasPLPBanner\\n      categoryID\\n      analytics {\\n        semanticTokens\\n        dynamicLCA\\n        __typename\\n      }\\n      canonicalUrl\\n      searchRedirect\\n      clearAllRefinementsURL\\n      contentType\\n      h1Tag\\n      isStoreDisplay\\n      productCount {\\n        inStore\\n        __typename\\n      }\\n      stores {\\n        storeId\\n        storeName\\n        address {\\n          postalCode\\n          __typename\\n        }\\n        nearByStores {\\n          storeId\\n          storeName\\n          distance\\n          address {\\n            postalCode\\n            __typename\\n          }\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    products(\\n      startIndex: $startIndex\\n      pageSize: $pageSize\\n      orderBy: $orderBy\\n      filter: $filter\\n    ) {\\n      identifiers {\\n        storeSkuNumber\\n        specialOrderSku\\n        canonicalUrl\\n        brandName\\n        itemId\\n        productLabel\\n        productType\\n        parentId\\n        modelNumber\\n        isSuperSku\\n        sampleId\\n        __typename\\n      }\\n      installServices(storeId: $storeId, zipCode: $zipCode) @skip(if: $skipInstallServices) {\\n        scheduleAMeasure\\n        gccCarpetDesignAndOrderEligible\\n        __typename\\n      }\\n      info {\\n        sponsoredMetadata {\\n          sponsoredId\\n          trackSource\\n          campaignId\\n          placementId\\n          slotId\\n          __typename\\n        }\\n        sponsoredBeacon {\\n          onClickBeacons\\n          onViewBeacons\\n          onClickBeacon\\n          onViewBeacon\\n          __typename\\n        }\\n        minimumOrderQuantity\\n        isSponsored\\n        productSubType {\\n          name\\n          link\\n          __typename\\n        }\\n        augmentedReality\\n        globalCustomConfigurator {\\n          customExperience\\n          __typename\\n        }\\n        hidePrice\\n        ecoRebate\\n        quantityLimit\\n        categoryHierarchy\\n        sskMin\\n        sskMax\\n        unitOfMeasureCoverage\\n        wasMaxPriceRange\\n        wasMinPriceRange\\n        swatches {\\n          isSelected\\n          itemId\\n          label\\n          swatchImgUrl\\n          url\\n          value\\n          __typename\\n        }\\n        totalNumberOfOptions\\n        customerSignal {\\n          previouslyPurchased\\n          __typename\\n        }\\n        isBuryProduct\\n        isGenericProduct\\n        returnable\\n        samplesAvailable\\n        isLiveGoodsProduct\\n        classNumber\\n        hasSubscription\\n        productDepartment\\n        __typename\\n      }\\n      itemId\\n      dataSources\\n      media {\\n        images {\\n          url\\n          type\\n          subType\\n          sizes\\n          __typename\\n        }\\n        __typename\\n      }\\n      pricing(\\n        storeId: $storeId\\n        isBrandPricingPolicyCompliant: $isBrandPricingPolicyCompliant\\n      ) {\\n        value\\n        original\\n        preferredPriceFlag\\n        promotion {\\n          dates {\\n            start\\n            end\\n            __typename\\n          }\\n          description {\\n            shortDesc\\n            longDesc\\n            __typename\\n          }\\n          experienceTag\\n          subExperienceTag\\n          type\\n          dollarOff\\n          percentageOff\\n          promotionTag\\n          savingsCenter\\n          savingsCenterPromos\\n          specialBuySavings\\n          specialBuyDollarOff\\n          specialBuyPercentageOff\\n          __typename\\n        }\\n        conditionalPromotions {\\n          promotionId\\n          skuItemGroup\\n          promotionTags\\n          eligibilityCriteria {\\n            itemGroup\\n            minThresholdVal\\n            thresholdType\\n            __typename\\n          }\\n          reward {\\n            tiers {\\n              minThresholdVal\\n              thresholdType\\n              rewardVal\\n              rewardType\\n              rewardLevel\\n              maxAllowedRewardAmount\\n              __typename\\n            }\\n            __typename\\n          }\\n          __typename\\n        }\\n        alternatePriceDisplay\\n        alternate {\\n          bulk {\\n            pricePerUnit\\n            thresholdQuantity\\n            value\\n            __typename\\n          }\\n          unit {\\n            caseUnitOfMeasure\\n            unitsOriginalPrice\\n            unitsPerCase\\n            value\\n            __typename\\n          }\\n          __typename\\n        }\\n        mapAboveOriginalPrice\\n        mapDetail {\\n          percentageOff\\n          dollarOff\\n          mapPolicy\\n          mapOriginalPriceViolation\\n          mapSpecialPriceViolation\\n          __typename\\n        }\\n        message\\n        specialBuy\\n        unitOfMeasure\\n        clearance {\\n          value\\n          dollarOff\\n          percentageOff\\n          unitsClearancePrice\\n          __typename\\n        }\\n        __typename\\n      }\\n      reviews {\\n        ratingsReviews {\\n          averageRating\\n          totalReviews\\n          __typename\\n        }\\n        __typename\\n      }\\n      badges(storeId: $storeId) {\\n        name\\n        label\\n        __typename\\n      }\\n      dataSource\\n      favoriteDetail @skip(if: $skipFavoriteCount) {\\n        count\\n        __typename\\n      }\\n      taxonomy {\\n        breadCrumbs {\\n          label\\n          __typename\\n        }\\n        __typename\\n      }\\n      details {\\n        installation {\\n          serviceType\\n          __typename\\n        }\\n        collection {\\n          name\\n          url\\n          __typename\\n        }\\n        __typename\\n      }\\n      fulfillment(storeId: $storeId, zipCode: $zipCode) {\\n        anchorStoreStatus\\n        anchorStoreStatusType\\n        backordered\\n        backorderedShipDate\\n        bossExcludedShipStates\\n        excludedShipStates\\n        seasonStatusEligible\\n        fulfillmentOptions {\\n          type\\n          fulfillable\\n          services {\\n            deliveryTimeline\\n            deliveryDates {\\n              startDate\\n              endDate\\n              __typename\\n            }\\n            deliveryCharge\\n            dynamicEta {\\n              hours\\n              minutes\\n              __typename\\n            }\\n            hasFreeShipping\\n            freeDeliveryThreshold\\n            locations {\\n              curbsidePickupFlag\\n              isBuyInStoreCheckNearBy\\n              distance\\n              inventory {\\n                isOutOfStock\\n                isInStock\\n                isLimitedQuantity\\n                isUnavailable\\n                quantity\\n                maxAllowedBopisQty\\n                minAllowedBopisQty\\n                __typename\\n              }\\n              isAnchor\\n              locationId\\n              state\\n              storeName\\n              storePhone\\n              type\\n              __typename\\n            }\\n            type\\n            totalCharge\\n            earliestDeliveryDate\\n            deliveryMessage\\n            shipFromFastestLocation\\n            optimalFulfillment\\n            __typename\\n          }\\n          __typename\\n        }\\n        onlineStoreStatus\\n        onlineStoreStatusType\\n        fulfillmentBundleMessage\\n        sthExcludedShipState\\n        __typename\\n      }\\n      availabilityType {\\n        type\\n        discontinued\\n        buyable\\n        status\\n        __typename\\n      }\\n      bundleFlag\\n      specificationGroup {\\n        specifications {\\n          specName\\n          specValue\\n          __typename\\n        }\\n        specTitle\\n        __typename\\n      }\\n      bundleItems {\\n        id\\n        quantity\\n        __typename\\n      }\\n      __typename\\n    }\\n    id\\n    searchReport {\\n      totalProducts\\n      didYouMean\\n      correctedKeyword\\n      keyword\\n      pageSize\\n      searchUrl\\n      sortBy\\n      sortOrder\\n      startIndex\\n      __typename\\n    }\\n    relatedResults {\\n      universalSearch {\\n        title\\n        __typename\\n      }\\n      relatedServices {\\n        label\\n        __typename\\n      }\\n      visualNavs {\\n        label\\n        imageId\\n        webUrl\\n        categoryId\\n        imageURL\\n        __typename\\n      }\\n      visualNavContainsEvents\\n      relatedKeywords {\\n        keyword\\n        __typename\\n      }\\n      __typename\\n    }\\n    taxonomy {\\n      brandLinkUrl\\n      breadCrumbs {\\n        browseUrl\\n        creativeIconUrl\\n        deselectUrl\\n        dimensionId\\n        dimensionName\\n        label\\n        refinementKey\\n        url\\n        __typename\\n      }\\n      __typename\\n    }\\n    templates\\n    discoveryZones @skip(if: $skipDiscoveryZones) {\\n      products(dataSource: $dataSource) {\\n        itemId\\n        dataSources\\n        badges(storeId: $storeId) {\\n          name\\n          __typename\\n        }\\n        info {\\n          isSponsored\\n          sponsoredMetadata {\\n            campaignId\\n            placementId\\n            slotId\\n            sponsoredId\\n            trackSource\\n            __typename\\n          }\\n          sponsoredBeacon {\\n            onClickBeacon\\n            onViewBeacon\\n            onClickBeacons\\n            onViewBeacons\\n            __typename\\n          }\\n          productSubType {\\n            name\\n            __typename\\n          }\\n          augmentedReality\\n          globalCustomConfigurator {\\n            customExperience\\n            __typename\\n          }\\n          swatches {\\n            isSelected\\n            itemId\\n            label\\n            swatchImgUrl\\n            url\\n            value\\n            __typename\\n          }\\n          totalNumberOfOptions\\n          hidePrice\\n          ecoRebate\\n          quantityLimit\\n          categoryHierarchy\\n          sskMin\\n          sskMax\\n          unitOfMeasureCoverage\\n          wasMaxPriceRange\\n          wasMinPriceRange\\n          __typename\\n        }\\n        identifiers {\\n          canonicalUrl\\n          productType\\n          productLabel\\n          modelNumber\\n          storeSkuNumber\\n          itemId\\n          brandName\\n          parentId\\n          __typename\\n        }\\n        media {\\n          images {\\n            url\\n            type\\n            subType\\n            sizes\\n            __typename\\n          }\\n          __typename\\n        }\\n        dataSource\\n        details {\\n          collection {\\n            name\\n            url\\n            __typename\\n          }\\n          __typename\\n        }\\n        pricing(\\n          storeId: $storeId\\n          isBrandPricingPolicyCompliant: $isBrandPricingPolicyCompliant\\n        ) {\\n          alternatePriceDisplay\\n          alternate {\\n            bulk {\\n              pricePerUnit\\n              thresholdQuantity\\n              value\\n              __typename\\n            }\\n            unit {\\n              caseUnitOfMeasure\\n              unitsOriginalPrice\\n              unitsPerCase\\n              value\\n              __typename\\n            }\\n            __typename\\n          }\\n          original\\n          mapAboveOriginalPrice\\n          mapDetail {\\n            percentageOff\\n            dollarOff\\n            mapPolicy\\n            mapOriginalPriceViolation\\n            mapSpecialPriceViolation\\n            __typename\\n          }\\n          message\\n          preferredPriceFlag\\n          promotion {\\n            type\\n            description {\\n              shortDesc\\n              longDesc\\n              __typename\\n            }\\n            dollarOff\\n            percentageOff\\n            promotionTag\\n            savingsCenter\\n            savingsCenterPromos\\n            specialBuySavings\\n            specialBuyDollarOff\\n            specialBuyPercentageOff\\n            __typename\\n          }\\n          specialBuy\\n          unitOfMeasure\\n          value\\n          __typename\\n        }\\n        taxonomy {\\n          breadCrumbs {\\n            label\\n            __typename\\n          }\\n          __typename\\n        }\\n        reviews {\\n          ratingsReviews {\\n            averageRating\\n            totalReviews\\n            __typename\\n          }\\n          __typename\\n        }\\n        __typename\\n      }\\n      metadata {\\n        zone\\n        zoneTitle\\n        zoneSponsored\\n        __typename\\n      }\\n      __typename\\n    }\\n    dimensions {\\n      label\\n      refinements {\\n        url\\n        refinementKey\\n        label\\n        recordCount\\n        selected\\n        imgUrl\\n        nestedRefinements {\\n          label\\n          url\\n          recordCount\\n          refinementKey\\n          __typename\\n        }\\n        __typename\\n      }\\n      collapse\\n      dimensionId\\n      isVisualNav\\n      isVisualDimension\\n      isNumericFilter\\n      isColorSwatch\\n      nestedRefinementsLimit\\n      visualNavSequence\\n      __typename\\n    }\\n    orangeGraph {\\n      universalSearchArray {\\n        pods {\\n          title\\n          description\\n          imageUrl\\n          link\\n          isProContent\\n          recordType\\n          __typename\\n        }\\n        info {\\n          title\\n          __typename\\n        }\\n        __typename\\n      }\\n      productTypes\\n      intents\\n      orderNumber\\n      __typename\\n    }\\n    appliedDimensions {\\n      label\\n      refinements {\\n        label\\n        refinementKey\\n        url\\n        __typename\\n      }\\n      isNumericFilter\\n      __typename\\n    }\\n    primaryFilters {\\n      collapse\\n      dimensionId\\n      isVisualNav\\n      isVisualDimension\\n      isNumericFilter\\n      isColorSwatch\\n      label\\n      nestedRefinementsLimit\\n      refinements {\\n        label\\n        refinementKey\\n        recordCount\\n        selected\\n        imgUrl\\n        url\\n        nestedRefinements {\\n          label\\n          url\\n          recordCount\\n          refinementKey\\n          __typename\\n        }\\n        __typename\\n      }\\n      visualNavSequence\\n      __typename\\n    }\\n    buyitagain(dataSource: $dataSource) @skip(if: $skipBuyitagain) {\\n      itemId\\n      dataSources\\n      badges(storeId: $storeId) {\\n        name\\n        __typename\\n      }\\n      info {\\n        isSponsored\\n        sponsoredMetadata {\\n          campaignId\\n          placementId\\n          slotId\\n          sponsoredId\\n          trackSource\\n          __typename\\n        }\\n        sponsoredBeacon {\\n          onClickBeacon\\n          onViewBeacon\\n          onClickBeacons\\n          onViewBeacons\\n          __typename\\n        }\\n        productSubType {\\n          name\\n          link\\n          __typename\\n        }\\n        augmentedReality\\n        globalCustomConfigurator {\\n          customExperience\\n          __typename\\n        }\\n        customerSignal {\\n          previouslyPurchased\\n          __typename\\n        }\\n        isBuryProduct\\n        isGenericProduct\\n        returnable\\n        hidePrice\\n        ecoRebate\\n        quantityLimit\\n        categoryHierarchy\\n        sskMin\\n        sskMax\\n        unitOfMeasureCoverage\\n        wasMaxPriceRange\\n        wasMinPriceRange\\n        __typename\\n      }\\n      identifiers {\\n        canonicalUrl\\n        productType\\n        productLabel\\n        modelNumber\\n        storeSkuNumber\\n        itemId\\n        brandName\\n        specialOrderSku\\n        __typename\\n      }\\n      media {\\n        images {\\n          url\\n          type\\n          subType\\n          sizes\\n          __typename\\n        }\\n        __typename\\n      }\\n      details {\\n        installation {\\n          serviceType\\n          __typename\\n        }\\n        collection {\\n          name\\n          url\\n          __typename\\n        }\\n        __typename\\n      }\\n      fulfillment(storeId: $storeId, zipCode: $zipCode) {\\n        anchorStoreStatus\\n        anchorStoreStatusType\\n        backordered\\n        backorderedShipDate\\n        bossExcludedShipStates\\n        excludedShipStates\\n        seasonStatusEligible\\n        fulfillmentOptions {\\n          type\\n          fulfillable\\n          services {\\n            deliveryTimeline\\n            deliveryDates {\\n              startDate\\n              endDate\\n              __typename\\n            }\\n            deliveryCharge\\n            dynamicEta {\\n              hours\\n              minutes\\n              __typename\\n            }\\n            hasFreeShipping\\n            freeDeliveryThreshold\\n            locations {\\n              curbsidePickupFlag\\n              isBuyInStoreCheckNearBy\\n              distance\\n              inventory {\\n                isOutOfStock\\n                isInStock\\n                isLimitedQuantity\\n                isUnavailable\\n                quantity\\n                maxAllowedBopisQty\\n                minAllowedBopisQty\\n                __typename\\n              }\\n              isAnchor\\n              locationId\\n              state\\n              storeName\\n              storePhone\\n              type\\n              __typename\\n            }\\n            type\\n            totalCharge\\n            __typename\\n          }\\n          __typename\\n        }\\n        onlineStoreStatus\\n        onlineStoreStatusType\\n        __typename\\n      }\\n      installServices(storeId: $storeId, zipCode: $zipCode) @skip(if: $skipInstallServices) {\\n        scheduleAMeasure\\n        gccCarpetDesignAndOrderEligible\\n        __typename\\n      }\\n      taxonomy {\\n        breadCrumbs {\\n          label\\n          __typename\\n        }\\n        __typename\\n      }\\n      pricing(\\n        storeId: $storeId\\n        isBrandPricingPolicyCompliant: $isBrandPricingPolicyCompliant\\n      ) {\\n        alternatePriceDisplay\\n        alternate {\\n          bulk {\\n            pricePerUnit\\n            thresholdQuantity\\n            value\\n            __typename\\n          }\\n          unit {\\n            caseUnitOfMeasure\\n            unitsOriginalPrice\\n            unitsPerCase\\n            value\\n            __typename\\n          }\\n          __typename\\n        }\\n        original\\n        mapAboveOriginalPrice\\n        mapDetail {\\n          percentageOff\\n          dollarOff\\n          mapPolicy\\n          mapOriginalPriceViolation\\n          mapSpecialPriceViolation\\n          __typename\\n        }\\n        message\\n        preferredPriceFlag\\n        promotion {\\n          type\\n          description {\\n            shortDesc\\n            longDesc\\n            __typename\\n          }\\n          dollarOff\\n          percentageOff\\n          promotionTag\\n          savingsCenter\\n          savingsCenterPromos\\n          specialBuySavings\\n          specialBuyDollarOff\\n          specialBuyPercentageOff\\n          __typename\\n        }\\n        specialBuy\\n        unitOfMeasure\\n        value\\n        __typename\\n      }\\n      dataSource\\n      __typename\\n    }\\n    __typename\\n  }\\n}","variables":{"skipInstallServices":false,"skipFavoriteCount":false,"storefilter":"ALL","channel":"DESKTOP","skipDiscoveryZones":false,"skipBuyitagain":true,"additionalSearchParams":{"deliveryZip":"delivery_zip","multiStoreIds":[]},"filter":{},"isBrandPricingPolicyCompliant":false,"navParam":"category_id","orderBy":{"field":"TOP_SELLERS","order":"ASC"},"pageSize":page_size,"startIndex":start_index,"storeId":"store_id"}}'

    payload = payload.replace("delivery_zip", str(delivery_zip))
    payload = payload.replace("category_id", str(category_id))
    payload = payload.replace("store_id", str(store_id))
    payload = payload.replace("page_size", str(page_size))
    payload = payload.replace("start_index", str(start_index))

    try:
        data = api_request(url, payload)

        search_model = data.get("data", {}).get("searchModel", {})
        if not search_model:
            logger.error(f"[Category] No searchModel found in API response")
            return [], 0

        total_products = search_model.get("searchReport", {}).get("totalProducts", 0)

        master_list = []
        products = search_model.get("products", [])

        for product in products:
            try:
                # Safely extract identifiers
                identifiers = product.get("identifiers", {})
                canonical_url = identifiers.get("canonicalUrl")
                if not canonical_url:
                    logger.warning(f"[Product] Missing canonical URL, skipping product")
                    continue

                # Safely extract reviews data
                reviews = product.get("reviews", {})
                ratings_reviews = reviews.get("ratingsReviews", {})

                # Safely extract pricing data
                pricing = product.get("pricing", {})
                promotion = pricing.get("promotion") or {}

                # Safely extract info data
                info = product.get("info", {})

                # Safely extract fulfillment data
                fulfillment = product.get("fulfillment", {})

                prod_dict = {
                    "URL": BASE_URL + canonical_url,
                    "Title": identifiers.get("productLabel", ""),
                    "SKU": identifiers.get("storeSkuNumber", ""),
                    "parent_id": identifiers.get("parentId", ""),
                    "item_id": identifiers.get("itemId", ""),
                    "Model": identifiers.get("modelNumber", ""),
                    "Brand": identifiers.get("brandName", ""),
                    "ProductType": identifiers.get("productType", ""),
                    "ProductRating": ratings_reviews.get("averageRating"),
                    "ReviewCount": ratings_reviews.get("totalReviews"),
                    "is_super_sku": identifiers.get("isSuperSku", False),
                    "original_price": pricing.get("original"),
                    "total_price": pricing.get("value"),
                    "savings": promotion.get("dollarOff"),
                    "category": info.get("categoryHierarchy"),
                    "variants_count": info.get("totalNumberOfOptions", 1),
                    "variant": [
                        {
                            "url": BASE_URL + sw.get("url", ""),
                            "label": sw.get("label", ""),
                            "itemId": sw.get("itemId", ""),
                        }
                        for sw in info.get("swatches", [])
                        if sw and sw.get("url")
                    ],
                    "returnable": info.get("returnable", 1),
                    "product_department": info.get("productDepartment", 1),
                }

                # Safely handle category extraction
                if (
                    prod_dict["category"]
                    and isinstance(prod_dict["category"], list)
                    and len(prod_dict["category"]) > 0
                ):
                    prod_dict["category"] = prod_dict["category"][-1]
                else:
                    prod_dict["category"] = None

                # Safely handle fulfillment options
                fulfillment_options = fulfillment.get("fulfillmentOptions")
                if fulfillment_options:
                    try:
                        prod_dict["item_inventory"] = []
                        for item in fulfillment_options:
                            if (
                                item
                                and item.get("services")
                                and len(item.get("services", [])) > 0
                                and item.get("services")[0]
                                and item.get("services")[0].get("locations")
                                and len(item.get("services")[0].get("locations", []))
                                > 0
                                and item.get("services")[0].get("locations")[0]
                                and item.get("services")[0]
                                .get("locations")[0]
                                .get("inventory")
                            ):

                                inventory_data = {
                                    item.get("type", "unknown"): item.get("services")[0]
                                    .get("locations")[0]
                                    .get("inventory")
                                    .get("quantity")
                                }
                                prod_dict["item_inventory"].append(inventory_data)
                    except (AttributeError, IndexError, TypeError) as e:
                        logger.warning(
                            f"[Product] Error processing inventory for {prod_dict.get('item_id', 'unknown')}: {e}"
                        )
                        prod_dict["item_inventory"] = []
                elif product.get("bundleFlag"):
                    # handle bundle product
                    try:
                        bundle_items = product.get("bundleItems", [])
                        prod_dict["bundle_inventory"] = [
                            {item.get("id", "unknown"): item.get("quantity", 0)}
                            for item in bundle_items
                            if item
                        ]
                    except (AttributeError, TypeError) as e:
                        logger.warning(
                            f"[Product] Error processing bundle inventory for {prod_dict.get('item_id', 'unknown')}: {e}"
                        )
                        prod_dict["bundle_inventory"] = []
                else:
                    # handle no inventory
                    pass

                master_list.append(prod_dict)

            except Exception as e:
                logger.error(f"[Product] Error processing product: {e}")
                continue

        return master_list, total_products

    except TooManyRedirects:
        logger.error(f"[Category] Too many redirects for category {category_id}")
        raise
    except RequestException as e:
        logger.error(f"[Category] Request failed for category {category_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(
            f"[Category] Unexpected error crawling category {category_id}: {e}"
        )
        raise


def extract_reviews(product, sort_by):
    url = "https://apionline.homedepot.com/federation-gateway/graphql?opname=reviews"
    payload = '{"query":"query reviews($itemId: String!, $excludeFamily: Boolean, $searchTerm: String, $sortBy: String, $startIndex: Int, $recfirstpage: String, $pagesize: String, $filters: ReviewsFilterInput) {\\n  reviews(\\n    itemId: $itemId\\n    excludeFamily: $excludeFamily\\n    searchTerm: $searchTerm\\n    sortBy: $sortBy\\n    startIndex: $startIndex\\n    recfirstpage: $recfirstpage\\n    pagesize: $pagesize\\n    filters: $filters\\n  ) {\\n    Results {\\n      AuthorId\\n      Badges {\\n        DIY {\\n          BadgeType\\n          __typename\\n        }\\n        top250Contributor {\\n          BadgeType\\n          __typename\\n        }\\n        IncentivizedReview {\\n          BadgeType\\n          __typename\\n        }\\n        EarlyReviewerIncentive {\\n          BadgeType\\n          __typename\\n        }\\n        top1000Contributor {\\n          BadgeType\\n          __typename\\n        }\\n        VerifiedPurchaser {\\n          BadgeType\\n          __typename\\n        }\\n        __typename\\n      }\\n      BadgesOrder\\n      CampaignId\\n      ContextDataValues {\\n        Age {\\n          Value\\n          __typename\\n        }\\n        VerifiedPurchaser {\\n          Value\\n          __typename\\n        }\\n        __typename\\n      }\\n      ContextDataValuesOrder\\n      Id\\n      IsRecommended\\n      IsSyndicated\\n      Photos {\\n        Id\\n        Sizes {\\n          normal {\\n            Url\\n            __typename\\n          }\\n          thumbnail {\\n            Url\\n            __typename\\n          }\\n          __typename\\n        }\\n        __typename\\n      }\\n      ProductId\\n      SubmissionTime\\n      TagDimensions {\\n        Pro {\\n          Values\\n          __typename\\n        }\\n        Con {\\n          Values\\n          __typename\\n        }\\n        __typename\\n      }\\n      Title\\n      TotalNegativeFeedbackCount\\n      TotalPositiveFeedbackCount\\n      ClientResponses {\\n        Response\\n        Date\\n        Department\\n        __typename\\n      }\\n      Rating\\n      RatingRange\\n      ReviewText\\n      SecondaryRatings {\\n        Quality {\\n          Label\\n          Value\\n          __typename\\n        }\\n        Value {\\n          Label\\n          Value\\n          __typename\\n        }\\n        EnergyEfficiency {\\n          Label\\n          Value\\n          __typename\\n        }\\n        Features {\\n          Label\\n          Value\\n          __typename\\n        }\\n        Appearance {\\n          Label\\n          Value\\n          __typename\\n        }\\n        EaseOfInstallation {\\n          Label\\n          Value\\n          __typename\\n        }\\n        EaseOfUse {\\n          Label\\n          Value\\n          __typename\\n        }\\n        __typename\\n      }\\n      SecondaryRatingsOrder\\n      SyndicationSource {\\n        LogoImageUrl\\n        Name\\n        ContentLink\\n        __typename\\n      }\\n      UserNickname\\n      UserLocation\\n      Videos {\\n        VideoId\\n        VideoThumbnailUrl\\n        VideoUrl\\n        __typename\\n      }\\n      __typename\\n    }\\n    Includes {\\n      Products {\\n        store {\\n          Id\\n          FilteredReviewStatistics {\\n            AverageOverallRating\\n            TotalReviewCount\\n            TotalRecommendedCount\\n            RecommendedCount\\n            NotRecommendedCount\\n            SecondaryRatingsAveragesOrder\\n            RatingDistribution {\\n              RatingValue\\n              Count\\n              __typename\\n            }\\n            ContextDataDistribution {\\n              Age {\\n                Values {\\n                  Value\\n                  Count\\n                  __typename\\n                }\\n                __typename\\n              }\\n              Gender {\\n                Values {\\n                  Value\\n                  Count\\n                  __typename\\n                }\\n                __typename\\n              }\\n              Expertise {\\n                Values {\\n                  Value\\n                  __typename\\n                }\\n                __typename\\n              }\\n              HomeGoodsProfile {\\n                Values {\\n                  Value\\n                  Count\\n                  __typename\\n                }\\n                __typename\\n              }\\n              VerifiedPurchaser {\\n                Values {\\n                  Value\\n                  Count\\n                  __typename\\n                }\\n                __typename\\n              }\\n              __typename\\n            }\\n            __typename\\n          }\\n          __typename\\n        }\\n        items {\\n          Id\\n          FilteredReviewStatistics {\\n            AverageOverallRating\\n            TotalReviewCount\\n            TotalRecommendedCount\\n            RecommendedCount\\n            NotRecommendedCount\\n            SecondaryRatingsAveragesOrder\\n            RatingDistribution {\\n              RatingValue\\n              Count\\n              __typename\\n            }\\n            ContextDataDistribution {\\n              Age {\\n                Values {\\n                  Value\\n                  Count\\n                  __typename\\n                }\\n                __typename\\n              }\\n              Gender {\\n                Values {\\n                  Value\\n                  Count\\n                  __typename\\n                }\\n                __typename\\n              }\\n              Expertise {\\n                Values {\\n                  Value\\n                  __typename\\n                }\\n                __typename\\n              }\\n              HomeGoodsProfile {\\n                Values {\\n                  Value\\n                  Count\\n                  __typename\\n                }\\n                __typename\\n              }\\n              VerifiedPurchaser {\\n                Values {\\n                  Value\\n                  Count\\n                  __typename\\n                }\\n                __typename\\n              }\\n              __typename\\n            }\\n            __typename\\n          }\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    FilterSelected {\\n      StarRatings {\\n        is5Star\\n        is4Star\\n        is3Star\\n        is2Star\\n        is1Star\\n        __typename\\n      }\\n      VerifiedPurchaser\\n      SearchText\\n      __typename\\n    }\\n    pagination {\\n      previousPage {\\n        label\\n        isNextPage\\n        isPreviousPage\\n        isSelectedPage\\n        __typename\\n      }\\n      pages {\\n        label\\n        isNextPage\\n        isPreviousPage\\n        isSelectedPage\\n        __typename\\n      }\\n      nextPage {\\n        label\\n        isNextPage\\n        isPreviousPage\\n        isSelectedPage\\n        __typename\\n      }\\n      __typename\\n    }\\n    SortBy {\\n      mosthelpfull\\n      newest\\n      oldest\\n      highestrating\\n      lowestrating\\n      photoreview\\n      __typename\\n    }\\n    TotalResults\\n    __typename\\n  }\\n}","variables":{"excludeFamily":false,"filters":{"isVerifiedPurchase":false,"prosCons":null,"starRatings":null},"itemId":"item_id","pagesize":"page_size","recfirstpage":"page_size","searchTerm":null,"sortBy":"sort_by","startIndex":start_index}}'

    page_size = "10"
    start_index = "-9"
    current_page = 0
    total_review_pages = float("inf")
    master_rev_data = []

    try:
        payload = payload.replace("item_id", str(product.get("item_id", ""))).replace(
            "sort_by", sort_by
        )

        while current_page < total_review_pages:
            start_index = str(int(start_index) + int(page_size))

            try:
                product_review = api_request(
                    url,
                    payload.replace("page_size", str(page_size)).replace(
                        "start_index", str(start_index)
                    ),
                )
            except TooManyRedirects:
                logger.error(
                    f"[Reviews] Too many redirects for item {product.get('item_id', 'unknown')} page {current_page+1}"
                )
                break
            except RequestException as e:
                logger.error(
                    f"[Reviews] Request failed for item {product.get('item_id', 'unknown')} page {current_page+1}: {str(e)}"
                )
                break
            try:
                data = product_review.get("data", {})
                if not data:
                    logger.error(
                        f"[Reviews] No data found in API response for item {product.get('item_id', 'unknown')} page {current_page+1}"
                    )
                    break
                reviews = data.get("reviews", {})

                pagination_pages = reviews.get("pagination", {})
                if isinstance(total_review_pages, float) and pagination_pages:
                    try:
                        pagination_pages = pagination_pages.get("pages", [])
                        if pagination_pages and len(pagination_pages) > 0:
                            last_page_label = pagination_pages[-1].get("label", "1")
                            total_review_pages = int(last_page_label)
                        else:
                            total_review_pages = 0
                    except (ValueError, TypeError, IndexError) as e:
                        logger.warning(
                            f"[Reviews] Error parsing pagination for item {product.get('item_id', 'unknown')}: {e}"
                        )
                        total_review_pages = 0
                else:
                    total_review_pages = 0

                if current_page == 0:
                    logger.info(
                        f"[Reviews] Found {total_review_pages} pages for item {product.get('item_id')}"
                    )

                # Safely extract product statistics
                try:
                    includes = reviews.get("Includes", {})
                    products_data = includes.get("Products", {})

                    if products_data and products_data.get("store"):
                        stats = products_data.get("store", {}).get(
                            "FilteredReviewStatistics", {}
                        )
                        product["VariantRating"] = stats.get("AverageOverallRating")
                        product["TotalReviewCount"] = stats.get("TotalReviewCount")
                        product["VariantTotalRecommendedCount"] = stats.get(
                            "TotalRecommendedCount", 0
                        )
                        product["VariantRecommendedCount"] = stats.get(
                            "RecommendedCount"
                        )
                        product["VariantNotRecommendedCount"] = stats.get(
                            "NotRecommendedCount"
                        )

                        try:
                            recommended_count = product["VariantRecommendedCount"] or 0
                            total_recommended = (
                                product["VariantTotalRecommendedCount"] or 0
                            )
                            if total_recommended > 0:
                                product["Recommended, %"] = round(
                                    (recommended_count / total_recommended) * 100, 2
                                )
                            else:
                                product["Recommended, %"] = 0
                        except (ZeroDivisionError, TypeError):
                            product["Recommended, %"] = 0

                        context_distribution = stats.get("ContextDataDistribution", {})
                        for key, value in context_distribution.items():
                            if isinstance(value, dict):
                                product[f"{key}Distribution"] = {
                                    item.get("Value"): item.get("Count")
                                    for item in value.get("Values", [])
                                    if item and item.get("Value") is not None
                                }

                        product["RatingDistribution"] = [
                            {
                                "RatingValue": item.get("RatingValue"),
                                "Count": item.get("Count"),
                            }
                            for item in stats.get("RatingDistribution", [])
                            if isinstance(item, dict)
                        ]
                    else:
                        # Set default values when no stats available
                        product["VariantRating"] = None
                        product["TotalReviewCount"] = 0
                        product["VariantTotalRecommendedCount"] = 0
                        product["VariantRecommendedCount"] = 0
                        product["VariantNotRecommendedCount"] = 0
                        product["Recommended, %"] = 0
                except Exception as e:
                    logger.warning(
                        f"[Reviews] Error processing review statistics for item {product.get('item_id', 'unknown')}: {e}"
                    )
                    # Set default values
                    product["VariantRating"] = None
                    product["TotalReviewCount"] = 0
                    product["VariantTotalRecommendedCount"] = 0
                    product["VariantRecommendedCount"] = 0
                    product["VariantNotRecommendedCount"] = 0
                    product["Recommended, %"] = 0

                product["VariantReviewCount"] = reviews.get("TotalResults", 0)
                review_results = reviews.get("Results", [])

                if not review_results:
                    logger.info(f"No reviews found for item {product.get('item_id')}")
                    if master_rev_data:
                        return master_rev_data
                    else:
                        return [product]

                # Process each review with error handling
                for review in review_results:
                    try:
                        rev_data = {**product}
                        rev_data["review_id"] = review.get("Id")

                        badges_order = review.get("BadgesOrder", [])
                        rev_data["VerifiedPurchase"] = (
                            "verifiedPurchaser" in badges_order
                        )

                        # Safely extract age data
                        context_data_values = review.get("ContextDataValues", {})
                        age_data = context_data_values.get("Age")
                        rev_data["Age"] = age_data.get("Value", "") if age_data else ""

                        rev_data["Helpful"] = bool(
                            review.get("TotalPositiveFeedbackCount")
                        )
                        rev_data["Recommended"] = review.get("IsRecommended")

                        # Safely extract photos
                        photos = review.get("Photos", [])
                        rev_data["CustomerImages"] = [
                            item.get("Sizes", {}).get("normal", {}).get("Url", "")
                            for item in photos
                            if item
                            and item.get("Sizes", {}).get("normal", {}).get("Url")
                        ]

                        rev_data["Date"] = review.get("SubmissionTime")

                        # Safely extract variation info
                        product_variant = product.get("variant", [])
                        if product_variant:
                            matching_variants = [
                                item.get("label")
                                for item in product_variant
                                if item
                                and item.get("itemId") == review.get("ProductId")
                            ]
                            rev_data["ReviewForVariation"] = (
                                matching_variants[0]
                                if matching_variants
                                else product.get("Title", "")
                            )
                        else:
                            rev_data["ReviewForVariation"] = product.get("Title", "")

                        rev_data["ReviewTitle"] = review.get("Title")
                        rev_data["ReviewDescription"] = review.get("ReviewText")
                        rev_data["ReviewStars"] = review.get("Rating")

                        # Safely extract secondary ratings
                        secondary_ratings = review.get("SecondaryRatings", {})
                        rating_data = {
                            k + " Rating": v.get("Value")
                            for k, v in secondary_ratings.items()
                            if isinstance(v, dict) and v.get("Value") is not None
                        }
                        rev_data.update(rating_data)

                        rev_data["CustomerName"] = review.get("UserNickname")
                        rev_data["CustomerLocation"] = review.get("UserLocation")

                        # Safely extract client responses
                        client_responses = review.get("ClientResponses", [])
                        rev_data["ResponseDepartment"] = ""
                        rev_data["ResponseDate"] = ""
                        rev_data["ResponseText"] = ""

                        for item in client_responses:
                            if isinstance(item, dict):
                                rev_data["ResponseDepartment"] = item.get(
                                    "Department", ""
                                )
                                rev_data["ResponseDate"] = item.get("Date", "")
                                response_text = item.get("Response", "")
                                if response_text:
                                    rev_data["ResponseText"] = (
                                        response_text.rstrip(
                                            "<!--[if ReviewResponse]><![endif]-->"
                                        )
                                        .replace("<br />", "\n")
                                        .strip()
                                    )
                                break

                        # Safely extract syndication source
                        source = review.get("SyndicationSource")
                        if source:
                            rev_data["ReviewOnSite"] = source.get("Name", "")
                            site_name = source.get("Name", "")
                            rev_data["ReviewSitePhrase"] = (
                                f"Customer review from {site_name}" if site_name else ""
                            )

                            try:
                                if rev_data["ReviewOnSite"]:
                                    rev_data["ResponseFrom"] = rev_data[
                                        "ReviewOnSite"
                                    ].rsplit(".", 1)[-2]
                                else:
                                    rev_data["ResponseFrom"] = ""
                            except (IndexError, AttributeError):
                                rev_data["ResponseFrom"] = rev_data["ReviewOnSite"]

                            rev_data["ReviewSiteContentLink"] = source.get(
                                "ContentLink", ""
                            )
                            rev_data["ReviewSiteLogoImageURL"] = source.get(
                                "LogoImageUrl", ""
                            )
                        else:
                            rev_data["ReviewOnSite"] = ""
                            rev_data["ReviewSitePhrase"] = ""
                            rev_data["ResponseFrom"] = ""
                            rev_data["ReviewSiteContentLink"] = ""
                            rev_data["ReviewSiteLogoImageURL"] = ""

                        rev_data["ReviewFromSite"] = bool(rev_data.get("ReviewOnSite"))
                        master_rev_data.append(rev_data)

                    except Exception as e:
                        logger.error(
                            f"[Reviews] Error processing individual review for item {product.get('item_id', 'unknown')}: {e}"
                        )
                        continue

                logger.info(
                    f"[Reviews] Page {current_page+1}/{total_review_pages} collected; total reviews so far: {len(master_rev_data)}"
                )
                current_page += 1

                time.sleep(0.5)  # Be polite and avoid hitting the server too hard

            except Exception as e:
                logger.error(
                    f"[Reviews] Unexpected error processing reviews for item {product.get('item_id', 'unknown')} page {current_page+1}: {e}"
                )
                break

        logger.info(
            f"[Reviews] Completed {len(master_rev_data)} reviews across {total_review_pages} pages for item {product.get('item_id')}"
        )
        return master_rev_data

    except Exception as e:
        logger.error(
            f"[Reviews] Fatal error in extract_reviews for item {product.get('item_id', 'unknown')}: {e}"
        )
        return [product]

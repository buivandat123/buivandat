from dto.index import *

CONFIG = {
    "paths": {
        "saveDir": "assets/cache",
    },
    "download": {
        "maxAttempts": 3,
        "timeout": 5,
        "minSize": 1024,
    },
    "api": {
        "defaultLimit": 15,
    }
}

def ParsePinterestArgs(parts: list[str]):
    if len(parts) < 2:
        return "", CONFIG["api"]["defaultLimit"]

    args = parts[1:]
    limit = CONFIG["api"]["defaultLimit"]

    if args and args[0].isdigit():
        limit = max(1, int(args[0]))
        args = args[1:]
    elif args and args[-1].isdigit():
        limit = max(1, int(args[-1]))
        args = args[:-1]

    keyword = " ".join(args).strip()
    return keyword, limit

def HandleOriginalPinterest(query: str, limit: int) -> list[str]:
    try:
        encodedQuery = quote(query)
        searchUrl = "https://www.pinterest.com/resource/BaseSearchResource/get/"

        data = {
            "options": {
                "applied_unified_filters": None,
                "appliedProductFilters": "---",
                "article": None,
                "auto_correction_disabled": False,
                "corpus": None,
                "customized_rerank_type": None,
                "domains": None,
                "dynamicPageSizeExpGroup": None,
                "filters": None,
                "journey_depth": None,
                "page_size": limit,
                "price_max": None,
                "price_min": None,
                "query_pin_sigs": None,
                "query": query,
                "redux_normalize_feed": True,
                "request_params": None,
                "rs": "typed",
                "scope": "pins",
                "selected_one_bar_modules": None,
                "seoDrawerEnabled": False,
                "source_id": None,
                "source_module_id": None,
                "source_url": f"/search/pins/?q={encodedQuery}&rs=typed",
                "top_pin_id": None,
                "top_pin_ids": None,
            },
            "context": {},
        }

        headers = {
            "Accept": "application/json, text/javascript, */*, q=0.01",
            "Referer": "https://www.pinterest.com/",
            "x-app-version": "9237374",
            "x-pinterest-appstate": "active",
            "x-pinterest-source-url": f"/search/pins/?q={encodedQuery}&rs=typed",
            "x-requested-with": "XMLHttpRequest",
            "x-pinterest-pws-handler": "www/search/[scope].js",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        }

        params = {
            "source_url": f"/search/pins/?q={encodedQuery}&rs=typed",
            "data": json.dumps(data),
            "_": int(time.time() * 1000),
        }

        resp = requests.get(
            searchUrl,
            headers=headers,
            params=params,
            timeout=CONFIG["download"]["timeout"] * 2
        )

        if resp.status_code != 200:
            return []

        payload = resp.json()
        resource = payload.get("resource_response", {}).get("data", {})
        results = resource.get("results", [])

        imageUrls = []

        for pin in results:
            if not pin or "images" not in pin:
                continue

            images = pin["images"]
            url = (
                images.get("orig", {}).get("url") or
                images.get("1200x", {}).get("url") or
                images.get("736x", {}).get("url") or
                images.get("600x", {}).get("url") or
                images.get("474x", {}).get("url")
            )

            if url:
                imageUrls.append(url)

        return imageUrls[:limit]

    except Exception as err:
        print("Pinterest error:", err)
        return []
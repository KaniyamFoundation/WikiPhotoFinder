"""MediaWiki API client for querying Tamil and English Wikipedia."""

import time
from typing import Dict, List, Optional, Any, Tuple
import requests


DEFAULT_USER_AGENT = (
    "WikiPhotoFinder/1.0 (https://ta.wikipedia.org; Tamil Wikipedia Photo Contributor Tool; "
    "mailto:contributor@example.org)"
)


class MediaWikiClient:
    """Client for interacting with MediaWiki Action APIs (ta.wikipedia.org, en.wikipedia.org)

    with rate limiting, maxlag etiquette, and exponential backoff.
    """

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        request_delay: float = 1.0,
        timeout: float = 30.0,
        maxlag: int = 5,
        max_retries: int = 5,
    ):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.request_delay = request_delay
        self.timeout = timeout
        self.maxlag = maxlag
        self.max_retries = max_retries

    @staticmethod
    def get_api_url(wiki: str) -> str:
        """Return the API endpoint for a given language code (e.g. 'ta', 'en')."""
        wiki_code = wiki.lower().strip()
        return f"https://{wiki_code}.wikipedia.org/w/api.php"

    def _request(self, method: str, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP request with Wikimedia etiquette, rate limiting, and maxlag backoff."""
        payload = dict(payload)
        payload["format"] = "json"

        # Handle maxlag parameter:
        # If explicitly passed as None or <= 0, remove it.
        # For Wikidata read-only queries (like wbgetentities), avoid default maxlag
        # because WDQS query service replication lag triggers false positives.
        if "maxlag" in payload:
            if payload["maxlag"] is None or payload["maxlag"] <= 0:
                del payload["maxlag"]
        elif self.maxlag > 0:
            is_wikidata_read = "wikidata.org" in url and payload.get("action") == "wbgetentities"
            if not is_wikidata_read:
                payload["maxlag"] = self.maxlag

        last_error = "unknown error"
        for attempt in range(self.max_retries):
            # Polite delay between consecutive requests to avoid overwhelming servers
            if self.request_delay > 0:
                time.sleep(self.request_delay)

            try:
                if method.upper() == "POST":
                    response = self.session.post(url, data=payload, timeout=self.timeout)
                else:
                    response = self.session.get(url, params=payload, timeout=self.timeout)

                # Handle HTTP 429 (Too Many Requests) or 503 (Service Unavailable)
                if response.status_code in (429, 503):
                    last_error = f"HTTP {response.status_code}"
                    retry_header = response.headers.get("Retry-After")
                    wait_time = int(retry_header) if retry_header and retry_header.isdigit() else max(5, 2 ** attempt)
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                json_data = response.json()

                # Handle Wikimedia database replication lag (maxlag)
                if "error" in json_data and json_data["error"].get("code") == "maxlag":
                    lag_info = json_data["error"].get("info", "Database lag")
                    last_error = f"maxlag: {lag_info}"
                    retry_header = response.headers.get("Retry-After")
                    wait_time = int(retry_header) if retry_header and retry_header.isdigit() else 5
                    time.sleep(wait_time)
                    continue

                return json_data

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_error = str(e)
                if attempt == self.max_retries - 1:
                    raise
                time.sleep((2 ** attempt) * 2)

        raise RuntimeError(f"Wikimedia API request failed after {self.max_retries} attempts ({last_error}): {url}")

    def _get(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GET request with error handling and rate limiting."""
        return self._request("GET", url, params)

    def _post(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a POST request with error handling and rate limiting.

        Uses POST to avoid HTTP 414 (URI Too Long) when querying many titles.
        """
        return self._request("POST", url, data)

    def get_category_members(
        self,
        wiki: str,
        category: str,
        cmtype: str = "page|subcat",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch members of a category (pages and/or subcategories).

        Args:
            wiki: Wiki language code ('ta' or 'en').
            category: Category name (e.g. 'பகுப்பு:தமிழக விளையாட்டு வீரர்கள்' or 'Category:Tamil writers').
            cmtype: 'page', 'subcat', or 'page|subcat'.
            limit: Maximum number of members to fetch (None for all).

        Returns:
            List of member dicts containing 'pageid', 'ns', and 'title'.
        """
        url = self.get_api_url(wiki)
        members: List[Dict[str, Any]] = []

        params: Dict[str, Any] = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmtype": cmtype,
            "cmlimit": 500,  # Max allowed per request
        }

        while True:
            # Use POST to avoid HTTP 414 URI Too Long with long file names
            data = self._post(url, params)
            current_batch = data.get("query", {}).get("categorymembers", [])
            members.extend(current_batch)

            if limit is not None and len(members) >= limit:
                return members[:limit]

            if "continue" in data and "cmcontinue" in data["continue"]:
                params["cmcontinue"] = data["continue"]["cmcontinue"]
            else:
                break

        return members

    def get_pages_info(
        self,
        wiki: str,
        titles: List[str],
        target_lang: Optional[str] = None,
        chunk_size: int = 50,
        progress_callback: Optional[Any] = None,
        progress_stage: str = "checking_articles",
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch page details including pageimages, pageprops (Wikidata ID), and langlinks.

        Args:
            wiki: Wiki language code ('ta' or 'en').
            titles: List of page titles to inspect.
            target_lang: Optional target language code for langlinks (e.g. 'en' or 'ta').
            chunk_size: Maximum titles per request (MediaWiki max is 50 for non-bots).
            progress_callback: Optional callback(stage, current, total).
            progress_stage: Stage name to report in progress_callback.

        Returns:
            Dict mapping page title (both original queried and canonical) to its metadata.
        """
        if not titles:
            return {}

        url = self.get_api_url(wiki)
        results: Dict[str, Dict[str, Any]] = {}

        # Chunk titles
        for i in range(0, len(titles), chunk_size):
            chunk = titles[i : i + chunk_size]
            params: Dict[str, Any] = {
                "action": "query",
                "prop": "pageimages|pageprops|langlinks",
                "titles": "|".join(chunk),
                "piprop": "original|thumbnail|name",
                "pilicense": "any",
                "redirects": 1,
            }
            if target_lang:
                params["lllang"] = target_lang

            # Use POST to avoid HTTP 414 URI Too Long with multi-byte Unicode titles
            data = self._post(url, params)
            query_obj = data.get("query", {})

            # Build normalization and redirect lookup tables
            title_alias_map: Dict[str, str] = {}
            for norm in query_obj.get("normalized", []):
                title_alias_map[norm["from"]] = norm["to"]
            for red in query_obj.get("redirects", []):
                title_alias_map[red["from"]] = red["to"]

            pages = query_obj.get("pages", {})
            for page_id, page_data in pages.items():
                title = page_data.get("title", "")
                is_missing = "missing" in page_data

                # Extract image info
                has_image = False
                image_name: Optional[str] = None
                image_url: Optional[str] = None
                thumbnail_url: Optional[str] = None

                # Check pageimages
                if "pageimage" in page_data:
                    has_image = True
                    image_name = page_data["pageimage"]
                elif "thumbnail" in page_data:
                    has_image = True
                elif "pageprops" in page_data:
                    props = page_data["pageprops"]
                    if "page_image_free" in props:
                        has_image = True
                        image_name = props["page_image_free"]
                    elif "page_image" in props:
                        has_image = True
                        image_name = props["page_image"]

                if "original" in page_data:
                    image_url = page_data["original"].get("source")
                if "thumbnail" in page_data:
                    thumbnail_url = page_data["thumbnail"].get("source")

                # Extract Wikidata ID
                wikidata_id = page_data.get("pageprops", {}).get("wikibase_item")

                # Extract langlinks
                langlinks: Dict[str, str] = {}
                for ll in page_data.get("langlinks", []):
                    lang = ll.get("lang")
                    linked_title = ll.get("*")
                    if lang and linked_title:
                        langlinks[lang] = linked_title

                info: Dict[str, Any] = {
                    "title": title,
                    "pageid": int(page_id) if page_id.isdigit() else None,
                    "missing": is_missing,
                    "has_image": has_image,
                    "image_name": image_name,
                    "image_url": image_url,
                    "image_thumbnail_url": thumbnail_url,
                    "wikidata_id": wikidata_id,
                    "langlinks": langlinks,
                }

                results[title] = info

            # Also ensure queried chunk titles map to their canonical entry
            for original_title in chunk:
                if original_title not in results:
                    canonical = original_title
                    while canonical in title_alias_map:
                        canonical = title_alias_map[canonical]
                    if canonical in results:
                        results[original_title] = results[canonical]

            if progress_callback:
                progress_callback(progress_stage, min(i + chunk_size, len(titles)), len(titles))

        return results

    def get_images_info(
        self,
        wiki: str,
        image_names: List[str],
        chunk_size: int = 50,
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch file metadata to determine if files are hosted on Commons or locally.

        Args:
            wiki: Wiki language code ('en' or 'ta').
            image_names: List of image filenames (with or without 'File:' prefix).
            chunk_size: Maximum titles per request.

        Returns:
            Dict mapping filename to metadata (repository, url, descriptionurl).
        """
        if not image_names:
            return {}

        url = self.get_api_url(wiki)
        results: Dict[str, Dict[str, Any]] = {}

        # Normalize file titles to include File:
        normalized_titles = []
        name_map: Dict[str, List[str]] = {}
        for name in set(image_names):
            if not name:
                continue
            clean = name
            for prefix in ("File:", "Image:", "படிமம்:", "கோப்பு:"):
                if clean.startswith(prefix):
                    clean = clean[len(prefix):]
            file_title = f"File:{clean}"
            normalized_titles.append(file_title)
            name_map.setdefault(file_title, []).append(name)
            name_map.setdefault(clean, []).append(name)

        for i in range(0, len(normalized_titles), chunk_size):
            chunk = normalized_titles[i : i + chunk_size]
            params = {
                "action": "query",
                "prop": "imageinfo",
                "titles": "|".join(chunk),
                "iiprop": "url|mime|size",
            }
            # Use POST to avoid HTTP 414 URI Too Long with long file names
            data = self._post(url, params)
            query_obj = data.get("query", {})
            pages = query_obj.get("pages", {})

            # Map from normalized originals
            norm_map: Dict[str, str] = {}
            for norm in query_obj.get("normalized", []):
                norm_map[norm["to"]] = norm["from"]

            for page_id, page_data in pages.items():
                title = page_data.get("title", "")
                repo = page_data.get("imagerepository", "unknown")
                imageinfo_list = page_data.get("imageinfo", [])

                file_url = None
                desc_url = None
                if imageinfo_list:
                    info = imageinfo_list[0]
                    file_url = info.get("url")
                    desc_url = info.get("descriptionurl")

                meta = {
                    "title": title,
                    "repository": repo,  # 'shared' is Commons, 'local' is enwiki
                    "url": file_url,
                    "description_url": desc_url,
                }

                # Register all variations (with/without File:, with spaces, with underscores)
                raw_name = title.replace("File:", "")
                variants = {
                    title,
                    title.replace(" ", "_"),
                    title.replace("_", " "),
                    raw_name,
                    raw_name.replace(" ", "_"),
                    raw_name.replace("_", " "),
                }

                # Check if this title was normalized from another title
                if title in norm_map:
                    orig_from = norm_map[title]
                    variants.add(orig_from)
                    variants.add(orig_from.replace("File:", ""))
                    variants.add(orig_from.replace(" ", "_"))

                for v in list(variants):
                    results[v] = meta
                    if v in name_map:
                        for original_input in name_map[v]:
                            results[original_input] = meta

        return results

    def get_category_langlink(
        self, category: str, from_wiki: str = "en", to_lang: str = "ta"
    ) -> Optional[str]:
        """Find the corresponding category title in another language."""
        url = self.get_api_url(from_wiki)
        params = {
            "action": "query",
            "prop": "langlinks",
            "titles": category,
            "lllang": to_lang,
        }
        data = self._get(url, params)
        pages = data.get("query", {}).get("pages", {})
        for page_data in pages.values():
            for ll in page_data.get("langlinks", []):
                if ll.get("lang") == to_lang:
                    return ll.get("*")
        return None

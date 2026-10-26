"""Core logic to find Tamil Wikipedia articles missing photos while English articles have them."""

from collections import deque
import re
from typing import List, Set, Optional, Callable, Dict, Any
from urllib.parse import quote

from .api import MediaWikiClient
from .models import ArticleResult
from .wikidata import WikidataClient, INDIC_WIKIS


# Common placeholder images to ignore if they somehow appear as pageimages
PLACEHOLDER_IMAGE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"no[ _]?photo",
        r"no[ _]?image",
        r"missing[ _]?image",
        r"replace[ _]?this[ _]?image",
        r"silhouette",
        r"silueta",
        r"flag[ _]of",
        r"map[ _]of",
        r"question[ _]?mark",
        r"ambox",
        r"stub",
    ]
]


def is_placeholder_image(image_name: Optional[str]) -> bool:
    """Check if an image filename is a known generic placeholder or icon."""
    if not image_name:
        return True
    return any(p.search(image_name) for p in PLACEHOLDER_IMAGE_PATTERNS)


def has_tamil_characters(text: str) -> bool:
    """Check if text contains Tamil Unicode characters (U+0B80 to U+0BFF)."""
    return any("\u0b80" <= ch <= "\u0bff" for ch in text)


def normalize_category_title(category: str, wiki: str) -> str:
    """Ensure category title has the appropriate namespace prefix for the language."""
    cat = category.strip()
    if wiki == "ta":
        if not cat.startswith("பகுப்பு:"):
            # If user provided 'Category:Foo' but wiki is ta, replace with பகுப்பு:
            if cat.startswith("Category:"):
                cat = "பகுப்பு:" + cat[len("Category:") :].strip()
            else:
                cat = "பகுப்பு:" + cat
    elif wiki == "en":
        if not cat.startswith("Category:"):
            if cat.startswith("பகுப்பு:"):
                cat = "Category:" + cat[len("பகுப்பு:") :].strip()
            else:
                cat = "Category:" + cat
    return cat


class WikiPhotoFinder:
    """Finder for articles with missing photos in Tamil Wikipedia and present photos in English Wikipedia."""

    def __init__(self, client: Optional[MediaWikiClient] = None):
        self.client = client or MediaWikiClient()

    def detect_category_language(self, category: str, explicit_wiki: Optional[str] = None) -> str:
        """Detect whether the category is in Tamil or English."""
        if explicit_wiki and explicit_wiki.lower() in ("ta", "en"):
            return explicit_wiki.lower()
        if category.startswith("பகுப்பு:") or has_tamil_characters(category):
            return "ta"
        return "en"

    def traverse_category(
        self,
        wiki: str,
        initial_category: str,
        depth: int = 0,
        limit: Optional[int] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[str]:
        """Traverse category and subcategories up to specified depth, returning article titles.

        Args:
            wiki: 'ta' or 'en'
            initial_category: Root category title
            depth: Subcategory depth (0 = only the specified category)
            limit: Maximum articles to collect (None for unlimited)
            progress_callback: Optional callback for progress reporting (stage, current, total)

        Returns:
            List of article titles.
        """
        category_title = normalize_category_title(initial_category, wiki)
        articles: List[str] = []
        seen_articles: Set[str] = set()
        visited_categories: Set[str] = set()

        queue = deque([(category_title, 0)])

        while queue:
            current_cat, current_depth = queue.popleft()
            if current_cat in visited_categories:
                continue
            visited_categories.add(current_cat)

            if progress_callback:
                progress_callback("crawling_category", len(visited_categories), len(queue) + len(visited_categories))

            # Fetch subcategories if within depth limit
            fetch_subcats = current_depth < depth
            cmtype = "page|subcat" if fetch_subcats else "page"

            members = self.client.get_category_members(wiki, current_cat, cmtype=cmtype)

            for member in members:
                ns = member.get("ns")
                title = member.get("title")
                if not title:
                    continue

                if ns == 0:  # Main namespace article
                    if title not in seen_articles:
                        seen_articles.add(title)
                        articles.append(title)
                        if limit is not None and len(articles) >= limit:
                            return articles
                elif ns == 14 and fetch_subcats:  # Category namespace
                    if title not in visited_categories:
                        queue.append((title, current_depth + 1))

        return articles

    def find_missing_photos(
        self,
        category: str,
        wiki: str = "auto",
        depth: int = 0,
        limit: Optional[int] = None,
        commons_only: bool = False,
        check_linked_wikis: bool = False,
        target_wikis: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[ArticleResult]:
        """Find articles missing photos in Tamil Wikipedia that have photos in English Wikipedia.

        Args:
            category: Category title in Tamil or English
            wiki: 'auto', 'ta', or 'en'
            depth: Subcategory traversal depth (0 for root only)
            limit: Max articles to inspect (None for unlimited)
            commons_only: If True, only return results whose photo is hosted on Wikimedia Commons
            check_linked_wikis: If True, inspect other language editions for missing photos
            target_wikis: Specific language codes to inspect (e.g. ['ml', 'te', 'kn'])
            progress_callback: Callback function(stage: str, current: int, total: int)

        Returns:
            List of ArticleResult objects.
        """
        source_wiki = self.detect_category_language(category, None if wiki == "auto" else wiki)
        norm_cat = normalize_category_title(category, source_wiki)

        if progress_callback:
            progress_callback("start", 0, 0)

        results: List[ArticleResult] = []

        if source_wiki == "ta":
            results = self._find_from_tamil(
                norm_cat, depth=depth, limit=limit, progress_callback=progress_callback
            )
        else:
            results = self._find_from_english(
                norm_cat, depth=depth, limit=limit, progress_callback=progress_callback
            )

        if commons_only:
            results = [r for r in results if r.is_on_commons]

        if check_linked_wikis and results:
            try:
                self.check_linked_wikis_for_results(
                    results,
                    target_wikis=target_wikis,
                    progress_callback=progress_callback,
                )
            except Exception:
                # Sibling check is an enrichment step; never lose the primary results
                pass

        if progress_callback:
            progress_callback("complete", len(results), len(results))

        return results

    def check_linked_wikis_for_results(
        self,
        results: List[ArticleResult],
        target_wikis: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> None:
        """Inspect other language Wikipedia editions for matched articles to see if they also lack photos.

        Args:
            results: List of ArticleResult objects to enrich in-place
            target_wikis: List of language codes to inspect (e.g. ['ml', 'te', 'kn', 'hi']).
                If None, defaults to INDIC_WIKIS. If ['all'], inspects all linked wikis.
            progress_callback: Optional callback(stage, current, total)
        """
        if not results:
            return

        wd_client = WikidataClient(client=self.client)
        qids = [r.wikidata_id for r in results if r.wikidata_id]

        if not qids:
            return

        is_all = target_wikis == ["all"] or (target_wikis and "all" in target_wikis)
        filter_wikis = None if is_all else (target_wikis or INDIC_WIKIS)

        if progress_callback:
            progress_callback("fetching_sitelinks", 0, len(qids))

        try:
            sitelinks_by_qid = wd_client.get_sitelinks(qids, target_wikis=filter_wikis)
        except Exception:
            # If Wikidata sitelinks batch query fails, return gracefully
            return

        # Map QID to ArticleResult
        results_by_qid: Dict[str, List[ArticleResult]] = {}
        for r in results:
            if r.wikidata_id:
                results_by_qid.setdefault(r.wikidata_id, []).append(r)

        # Group titles to check by target wiki
        titles_by_wiki: Dict[str, Dict[str, str]] = {}  # {wiki: {title: qid}}
        for qid, sitelinks in sitelinks_by_qid.items():
            for wiki, title in sitelinks.items():
                if wiki not in ("en", "ta"):  # en and ta are already checked
                    titles_by_wiki.setdefault(wiki, {})[title] = qid

        # Check each target wiki
        total_wikis = len(titles_by_wiki)
        for w_idx, (wiki, title_map) in enumerate(titles_by_wiki.items(), 1):
            if progress_callback:
                progress_callback(f"checking_{wiki}_wiki", w_idx, total_wikis)

            titles = list(title_map.keys())
            try:
                page_info = self.client.get_pages_info(wiki, titles)
                for title, info in page_info.items():
                    qid = title_map.get(title)
                    if qid and qid in results_by_qid:
                        encoded = quote(title.replace(" ", "_"), safe="/:@&=+$,?#")
                        entry = {
                            "wiki": wiki,
                            "title": title,
                            "has_image": info.get("has_image", False),
                            "image_name": info.get("image_name"),
                            "image_url": info.get("image_url"),
                            "url": f"https://{wiki}.wikipedia.org/wiki/{encoded}",
                            "missing": info.get("missing", False),
                        }
                        for r in results_by_qid[qid]:
                            r.linked_wikis[wiki] = entry
            except Exception:
                # If an individual wiki API query fails, continue with remaining wikis
                pass

    def _find_from_tamil(
        self,
        category: str,
        depth: int = 0,
        limit: Optional[int] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[ArticleResult]:
        """Process starting from Tamil Wikipedia category."""
        # 1. Fetch articles from Tamil category
        ta_articles = self.traverse_category(
            "ta", category, depth=depth, limit=limit, progress_callback=progress_callback
        )

        if not ta_articles:
            return []

        if progress_callback:
            progress_callback("category_articles_total", len(ta_articles), len(ta_articles))

        # 2. Get Tamil article info (check image + find English langlink)
        if progress_callback:
            progress_callback("checking_ta_articles", 0, len(ta_articles))

        ta_info = self.client.get_pages_info(
            "ta",
            ta_articles,
            target_lang="en",
            progress_callback=progress_callback,
            progress_stage="checking_ta_articles",
        )

        # Filter: Tamil article has NO image, but DOES have an English link
        candidates: Dict[str, Dict[str, Any]] = {}
        for ta_title, info in ta_info.items():
            if not info.get("has_image"):
                en_title = info.get("langlinks", {}).get("en")
                if en_title:
                    candidates[ta_title] = {
                        "ta_title": ta_title,
                        "en_title": en_title,
                        "wikidata_id": info.get("wikidata_id"),
                    }

        if not candidates:
            return []

        # 3. Check English articles for photos
        en_titles = [c["en_title"] for c in candidates.values()]
        if progress_callback:
            progress_callback("checking_en_articles", 0, len(en_titles))

        en_info = self.client.get_pages_info(
            "en",
            en_titles,
            progress_callback=progress_callback,
            progress_stage="checking_en_articles",
        )

        # Match: English article HAS an image
        matches: List[Dict[str, Any]] = []
        for ta_title, cdata in candidates.items():
            en_title = cdata["en_title"]
            en_page = en_info.get(en_title)
            if en_page and en_page.get("has_image"):
                img_name = en_page.get("image_name")
                if not is_placeholder_image(img_name):
                    matches.append(
                        {
                            "ta_title": ta_title,
                            "en_title": en_title,
                            "image_name": img_name,
                            "image_url": en_page.get("image_url"),
                            "image_thumbnail_url": en_page.get("image_thumbnail_url"),
                            "wikidata_id": cdata["wikidata_id"] or en_page.get("wikidata_id"),
                        }
                    )

        if not matches:
            return []

        # 4. Check image repository (Commons vs local enwiki)
        image_names = [m["image_name"] for m in matches if m["image_name"]]
        image_info = self.client.get_images_info("en", image_names)

        results: List[ArticleResult] = []
        for m in matches:
            img_name = m["image_name"]
            meta = image_info.get(img_name, {})
            repo = meta.get("repository", "unknown")
            resolved_url = meta.get("url") or m.get("image_url")

            results.append(
                ArticleResult(
                    ta_title=m["ta_title"],
                    en_title=m["en_title"],
                    image_name=img_name,
                    image_url=resolved_url,
                    image_thumbnail_url=m.get("image_thumbnail_url"),
                    image_repository=repo,
                    wikidata_id=m["wikidata_id"],
                    source_category=category,
                )
            )

        return results

    def _find_from_english(
        self,
        category: str,
        depth: int = 0,
        limit: Optional[int] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[ArticleResult]:
        """Process starting from English Wikipedia category."""
        # 1. Fetch articles from English category
        en_articles = self.traverse_category(
            "en", category, depth=depth, limit=limit, progress_callback=progress_callback
        )

        if not en_articles:
            return []

        if progress_callback:
            progress_callback("category_articles_total", len(en_articles), len(en_articles))

        # 2. Get English article info (check image + find Tamil langlink)
        if progress_callback:
            progress_callback("checking_en_articles", 0, len(en_articles))

        en_info = self.client.get_pages_info(
            "en",
            en_articles,
            target_lang="ta",
            progress_callback=progress_callback,
            progress_stage="checking_en_articles",
        )

        # Filter: English article HAS image, and HAS Tamil counterpart
        candidates: Dict[str, Dict[str, Any]] = {}
        for en_title, info in en_info.items():
            if info.get("has_image"):
                img_name = info.get("image_name")
                if not is_placeholder_image(img_name):
                    ta_title = info.get("langlinks", {}).get("ta")
                    if ta_title:
                        candidates[ta_title] = {
                            "ta_title": ta_title,
                            "en_title": en_title,
                            "image_name": img_name,
                            "image_url": info.get("image_url"),
                            "image_thumbnail_url": info.get("image_thumbnail_url"),
                            "wikidata_id": info.get("wikidata_id"),
                        }

        if not candidates:
            return []

        # 3. Check Tamil articles to ensure they LACK photos
        ta_titles = list(candidates.keys())
        if progress_callback:
            progress_callback("checking_ta_articles", 0, len(ta_titles))

        ta_info = self.client.get_pages_info(
            "ta",
            ta_titles,
            progress_callback=progress_callback,
            progress_stage="checking_ta_articles",
        )

        matches: List[Dict[str, Any]] = []
        for ta_title, cdata in candidates.items():
            ta_page = ta_info.get(ta_title)
            # Only matches if Tamil article does NOT have an image
            if ta_page and not ta_page.get("has_image"):
                matches.append(
                    {
                        "ta_title": ta_title,
                        "en_title": cdata["en_title"],
                        "image_name": cdata["image_name"],
                        "image_url": cdata["image_url"],
                        "image_thumbnail_url": cdata["image_thumbnail_url"],
                        "wikidata_id": cdata["wikidata_id"] or ta_page.get("wikidata_id"),
                    }
                )

        if not matches:
            return []

        # 4. Check image repository (Commons vs local enwiki)
        image_names = [m["image_name"] for m in matches if m["image_name"]]
        image_info = self.client.get_images_info("en", image_names)

        results: List[ArticleResult] = []
        for m in matches:
            img_name = m["image_name"]
            meta = image_info.get(img_name, {})
            repo = meta.get("repository", "unknown")
            resolved_url = meta.get("url") or m.get("image_url")

            results.append(
                ArticleResult(
                    ta_title=m["ta_title"],
                    en_title=m["en_title"],
                    image_name=img_name,
                    image_url=resolved_url,
                    image_thumbnail_url=m.get("image_thumbnail_url"),
                    image_repository=repo,
                    wikidata_id=m["wikidata_id"],
                    source_category=category,
                )
            )

        return results

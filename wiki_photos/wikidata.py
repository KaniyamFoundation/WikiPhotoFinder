"""Wikidata API client for checking and updating Property P18 (image)."""

import json
from typing import Dict, List, Optional, Tuple, Any, Set
import requests
from .api import DEFAULT_USER_AGENT, MediaWikiClient

INDIC_WIKIS: List[str] = [
    "ta", "ml", "te", "kn", "hi", "bn", "mr", "gu", "pa", "or", "as", "ur", "sa"
]

DRAVIDIAN_WIKIS: List[str] = ["ta", "ml", "te", "kn"]

EXCLUDED_SITELINKS: Set[str] = {
    "commonswiki",
    "specieswiki",
    "sourceswiki",
    "metawiki",
    "incubatorwiki",
    "foundationwiki",
    "mediawikiwiki",
    "wikidatawiki",
}


class WikidataClient:
    """Client for querying and updating Wikidata entities (property P18 image)."""

    WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"

    def __init__(
        self,
        client: Optional[MediaWikiClient] = None,
        user_agent: str = DEFAULT_USER_AGENT,
        request_delay: float = 1.0,
        timeout: float = 30.0,
        maxlag: int = 5,
    ):
        self.mw_client = client or MediaWikiClient(
            user_agent=user_agent,
            request_delay=request_delay,
            timeout=timeout,
            maxlag=maxlag,
        )
        self.session = self.mw_client.session
        self.csrf_token: Optional[str] = None
        self.logged_in_user: Optional[str] = None

    def get_login_token(self) -> str:
        """Fetch login token from wikidata.org."""
        params = {
            "action": "query",
            "meta": "tokens",
            "type": "login",
            "format": "json",
        }
        res = self.session.get(self.WIKIDATA_API_URL, params=params, timeout=self.mw_client.timeout)
        res.raise_for_status()
        return res.json()["query"]["tokens"]["logintoken"]

    def login(self, username: str, password: str) -> bool:
        """Log in to Wikidata using a Wikimedia Bot Password."""
        token = self.get_login_token()
        data = {
            "action": "login",
            "lgname": username.strip(),
            "lgpassword": password.strip(),
            "lgtoken": token,
            "format": "json",
        }
        res = self.session.post(self.WIKIDATA_API_URL, data=data, timeout=self.mw_client.timeout)
        res.raise_for_status()
        resp = res.json().get("login", {})

        if resp.get("result") == "Success":
            self.logged_in_user = resp.get("lgusername", username)
            self.csrf_token = self.get_csrf_token()
            return True
        else:
            reason = resp.get("reason", "Unknown login failure on Wikidata")
            raise RuntimeError(f"Wikidata login failed: {resp.get('result')} - {reason}")

    def get_csrf_token(self) -> str:
        """Fetch CSRF edit token from wikidata.org."""
        params = {
            "action": "query",
            "meta": "tokens",
            "type": "csrf",
            "format": "json",
        }
        res = self.session.get(self.WIKIDATA_API_URL, params=params, timeout=self.mw_client.timeout)
        res.raise_for_status()
        token = res.json().get("query", {}).get("tokens", {}).get("csrftoken")
        if not token or token == "+\\":
            raise RuntimeError("Failed to obtain valid CSRF token from Wikidata.")
        return token

    def get_sitelinks(
        self,
        qids: List[str],
        target_wikis: Optional[List[str]] = None,
        chunk_size: int = 50,
    ) -> Dict[str, Dict[str, str]]:
        """Batch query Wikidata entities for Wikipedia sitelinks across languages.

        Args:
            qids: List of Wikidata QIDs (e.g. ['Q3531820'])
            target_wikis: Optional list of language codes to filter (e.g. ['ml', 'te', 'kn'])
            chunk_size: Batch size per Wikidata API request (default 50)

        Returns:
            Dict mapping QID to a Dict of {lang_code: article_title}
        """
        results: Dict[str, Dict[str, str]] = {qid: {} for qid in qids if qid}
        valid_qids = [q for q in set(qids) if q and q.startswith("Q")]
        target_set = set(target_wikis) if target_wikis else None

        for i in range(0, len(valid_qids), chunk_size):
            chunk = valid_qids[i : i + chunk_size]
            data = {
                "action": "wbgetentities",
                "ids": "|".join(chunk),
                "props": "sitelinks",
                "format": "json",
                "maxlag": None,
            }
            res = self.mw_client._post(self.WIKIDATA_API_URL, data)
            entities = res.get("entities", {})

            for qid, edata in entities.items():
                sitelinks = edata.get("sitelinks", {})
                wiki_links: Dict[str, str] = {}
                for site_key, site_info in sitelinks.items():
                    if (
                        site_key.endswith("wiki")
                        and site_key not in EXCLUDED_SITELINKS
                        and not any(
                            p in site_key
                            for p in ("source", "voyage", "quote", "books", "news", "versity")
                        )
                    ):
                        lang = site_key[:-4]
                        if target_set is None or lang in target_set:
                            title = site_info.get("title")
                            if title:
                                wiki_links[lang] = title
                results[qid] = wiki_links

        return results

    def get_entity_sitelinks(
        self,
        qid: str,
        target_wikis: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """Fetch Wikipedia sitelinks for a single Wikidata entity."""
        res = self.get_sitelinks([qid], target_wikis=target_wikis)
        return res.get(qid, {})

    def get_p18_images(self, qids: List[str], chunk_size: int = 50) -> Dict[str, Optional[str]]:
        """Batch query Wikidata entities to find their P18 (image) values.

        Returns:
            Dict mapping QID to its P18 image filename (or None if missing).
        """
        results: Dict[str, Optional[str]] = {qid: None for qid in qids if qid}
        valid_qids = [q for q in set(qids) if q and q.startswith("Q")]

        for i in range(0, len(valid_qids), chunk_size):
            chunk = valid_qids[i : i + chunk_size]
            data = {
                "action": "wbgetentities",
                "ids": "|".join(chunk),
                "props": "claims",
                "format": "json",
                "maxlag": None,
            }
            res = self.mw_client._post(self.WIKIDATA_API_URL, data)
            entities = res.get("entities", {})

            for qid, edata in entities.items():
                claims = edata.get("claims", {})
                if "P18" in claims and claims["P18"]:
                    try:
                        p18_val = claims["P18"][0]["mainsnak"]["datavalue"]["value"]
                        results[qid] = str(p18_val).strip()
                    except (KeyError, IndexError, TypeError):
                        results[qid] = None
                else:
                    results[qid] = None

        return results

    def has_p18_image(self, qid: str) -> Tuple[bool, Optional[str]]:
        """Check whether a single Wikidata entity has Property P18 (image).

        Returns:
            (has_image: bool, image_name: Optional[str])
        """
        res_map = self.get_p18_images([qid])
        img = res_map.get(qid)
        return (img is not None), img

    def add_p18_image(
        self,
        qid: str,
        image_name: str,
        summary: str = "Add image P18 (via WikiPhotoFinder)",
        bot: bool = False,
    ) -> Dict[str, Any]:
        """Add Property P18 (image) claim to a Wikidata entity.

        Args:
            qid: Wikidata Item ID (e.g. 'Q3531820')
            image_name: Filename on Wikimedia Commons
            summary: Edit summary
            bot: Mark as bot edit

        Returns:
            API response dictionary.
        """
        if not self.csrf_token:
            self.csrf_token = self.get_csrf_token()

        clean_name = image_name
        for prefix in ("File:", "Image:", "படிமம்:", "கோப்பு:"):
            if clean_name.startswith(prefix):
                clean_name = clean_name[len(prefix):]
        clean_name = clean_name.replace("_", " ").strip()

        data: Dict[str, Any] = {
            "action": "wbcreateclaim",
            "entity": qid,
            "property": "P18",
            "snaktype": "value",
            "value": json.dumps(clean_name),
            "token": self.csrf_token,
            "summary": summary,
            "format": "json",
        }
        if bot:
            data["bot"] = 1

        if self.mw_client.request_delay > 0:
            import time
            time.sleep(self.mw_client.request_delay)

        res = self.mw_client._post(self.WIKIDATA_API_URL, data)

        if "error" in res:
            err = res["error"]
            raise RuntimeError(f"Wikidata edit failed on '{qid}': {err.get('info')} ({err.get('code')})")

        return res

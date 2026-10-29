"""MediaWiki login and automated/semi-automated page updater for Wikipedia across languages."""

import difflib
import re
import time
from typing import Dict, Optional, Tuple, Any, List
import requests
from .api import DEFAULT_USER_AGENT, MediaWikiClient

WIKI_IMAGE_PREFIXES: Dict[str, str] = {
    "ta": "படிமம்",
    "ml": "പ്രമാണം",
    "te": "దస్త్రం",
    "kn": "ಚಿತ್ರ",
    "hi": "चित्र",
    "bn": "চিত্র",
    "mr": "चित्र",
    "gu": "ચિત્ર",
    "pa": "ਤਸਵੀਰ",
    "ur": "تصویر",
    "or": "ଚିତ୍ର",
    "as": "চিত্ৰ",
    "sa": "चित्रम्",
    "en": "File",
    "fr": "Fichier",
    "de": "Datei",
    "es": "Archivo",
}

DEFAULT_EDIT_SUMMARIES: Dict[str, str] = {
    "ta": "படிமம் சேர்த்தல் (via WikiPhotoFinder)",
    "ml": "ചിത്രം ചേർക്കൽ (via WikiPhotoFinder)",
    "te": "చిత్రం చేర్చడం (via WikiPhotoFinder)",
    "kn": "ಚಿತ್ರ ಸೇರಿಸಲಾಗಿದೆ (via WikiPhotoFinder)",
    "hi": "चित्र जोड़ा (via WikiPhotoFinder)",
    "bn": "ছবি যোগ (via WikiPhotoFinder)",
    "mr": "चित्र जोडले (via WikiPhotoFinder)",
    "gu": "ચિત્ર ઉમેર્યું (via WikiPhotoFinder)",
    "pa": "ਤਸਵੀਰ ਜੋੜੀ (via WikiPhotoFinder)",
    "ur": "تصویر شامل کی گئی (via WikiPhotoFinder)",
    "en": "Add image (via WikiPhotoFinder)",
}


class WikiUpdater:
    """Handles authentication and publishing photo additions to Wikipedia across languages."""

    def __init__(
        self,
        client: Optional[MediaWikiClient] = None,
        wiki: str = "ta",
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.wiki = wiki.lower().strip()
        self.client = client or MediaWikiClient(user_agent=user_agent)
        self.session = self.client.session
        self.api_url = MediaWikiClient.get_api_url(self.wiki)
        self.csrf_token: Optional[str] = None
        self.logged_in_user: Optional[str] = None

    def get_login_token(self) -> str:
        """Fetch login token required for action=login."""
        params = {
            "action": "query",
            "meta": "tokens",
            "type": "login",
            "format": "json",
        }
        res = self.session.get(self.api_url, params=params, timeout=30)
        res.raise_for_status()
        data = res.json()
        return data["query"]["tokens"]["logintoken"]

    def login(self, username: str, password: str) -> bool:
        """Log in to Wikipedia using Bot Password (e.g. 'Username@botname').

        Args:
            username: Your username or bot username (e.g. 'MyName@PhotoUpdater')
            password: The generated bot password

        Returns:
            True if login succeeded, raises RuntimeError otherwise.
        """
        login_token = self.get_login_token()

        data = {
            "action": "login",
            "lgname": username.strip(),
            "lgpassword": password.strip(),
            "lgtoken": login_token,
            "format": "json",
        }
        res = self.session.post(self.api_url, data=data, timeout=30)
        res.raise_for_status()
        resp_data = res.json()

        login_result = resp_data.get("login", {})
        status = login_result.get("result")

        if status == "Success":
            self.logged_in_user = login_result.get("lgusername", username)
            # Obtain CSRF token for future edits
            self.csrf_token = self.get_csrf_token()
            return True
        else:
            reason = login_result.get("reason", "Unknown login failure")
            raise RuntimeError(f"Login failed on {self.wiki}.wikipedia.org: {status} - {reason}")

    def get_csrf_token(self) -> str:
        """Fetch CSRF edit token."""
        params = {
            "action": "query",
            "meta": "tokens",
            "type": "csrf",
            "format": "json",
        }
        res = self.session.get(self.api_url, params=params, timeout=30)
        res.raise_for_status()
        data = res.json()
        token = data.get("query", {}).get("tokens", {}).get("csrftoken")
        if not token or token == "+\\":
            raise RuntimeError(f"Failed to obtain valid CSRF token on {self.wiki}.wikipedia.org. Make sure you are logged in.")
        return token

    def get_page_content(self, title: str) -> Tuple[Optional[str], Optional[int]]:
        """Fetch current wikitext and base revision ID of a page.

        Returns:
            (content, rev_id) or (None, None) if page doesn't exist.
        """
        params = {
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvprop": "content|ids",
            "rvslots": "main",
            "format": "json",
        }
        res = self.session.get(self.api_url, params=params, timeout=30)
        res.raise_for_status()
        pages = res.json().get("query", {}).get("pages", {})

        for pid, pdata in pages.items():
            if "missing" in pdata or pid == "-1":
                return None, None
            revisions = pdata.get("revisions", [])
            if revisions:
                rev = revisions[0]
                content = rev.get("slots", {}).get("main", {}).get("*")
                revid = rev.get("revid")
                return content, revid
        return None, None

    @staticmethod
    def clean_image_filename(image_name: str) -> str:
        """Strip namespace prefix and normalize underscores/spaces."""
        name = image_name
        for prefix in (
            "File:", "Image:",
            "படிமம்:", "கோப்பு:",
            "പ്രമാണം:", "ദస్త్రം:",
            "ಚಿತ್ರ:", "चित्र:",
            "ছবি:", "તસવીર:", "تصویر:",
            "Fichier:", "Datei:", "Archivo:",
        ):
            if name.startswith(prefix):
                name = name[len(prefix):]
        return name.strip()

    @classmethod
    def apply_image_to_wikitext(
        cls,
        content: str,
        title: str,
        image_name: str,
        wiki: str = "ta",
    ) -> str:
        """Intelligently insert the photo into the wikitext (in infobox or at top)."""
        clean_name = cls.clean_image_filename(image_name)

        # 1. If an empty image parameter exists in an infobox, fill it
        empty_param_pattern = (
            r"(^[ \t]*\|[ \t]*(?:image|photo|picture|படம்|படிமம்|ചിത്രം|చిత్రం|ಚಿತ್ರ|चित्र|ছবি|تصویر|image_name|img)"
            r"[ \t]*=[ \t]*)$"
        )
        if re.search(empty_param_pattern, content, re.MULTILINE | re.IGNORECASE):
            return re.sub(
                empty_param_pattern,
                rf"\g<1>{clean_name}",
                content,
                count=1,
                flags=re.MULTILINE | re.IGNORECASE,
            )

        # 2. If an infobox template exists and doesn't already have a filled image parameter,
        # insert | image = filename after template opening
        infobox_pattern = (
            r"(\{\{\s*(?:Infobox[^\n|]+|[^}\n|]+(?:தகவல்சட்டம்|விவரപ്പെട്ടി|సమాచారపెట్టె|ಮಾಹಿತಿ\s*ಚೌಕಟ್ಟು|ज्ञानसन्दूक|তথ্যছক)[^\n|]*)\n)"
        )
        m = re.search(infobox_pattern, content, re.IGNORECASE)
        if m:
            header = m.group(1)
            # Check if this infobox already has an image parameter
            header_end = m.end(1)
            next_lines = content[header_end : header_end + 1000]
            if not re.search(r"^[ \t]*\|[ \t]*(?:image|photo|picture|படம்|படிமம்|ചിത്രം|చిత్రం|ಚಿತ್ರ|चित्र|ছবি|image_name)[ \t]*=[ \t]*\S+", next_lines, re.MULTILINE | re.IGNORECASE):
                insertion = f"{header}| image = {clean_name}\n"
                return content.replace(header, insertion, 1)

        # 3. Otherwise prepend lead image snippet at top of article
        prefix = WIKI_IMAGE_PREFIXES.get(wiki, "File")
        snippet = f"[[{prefix}:{clean_name}|thumb|{title}]]\n\n"
        return snippet + content

    @staticmethod
    def generate_diff(old_text: str, new_text: str, title: str) -> str:
        """Generate unified diff showing changes."""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{title}",
            tofile=f"b/{title}",
        )
        return "".join(diff)

    def edit_page(
        self,
        title: str,
        new_content: str,
        summary: Optional[str] = None,
        baserevid: Optional[int] = None,
        minor: bool = False,
    ) -> Dict[str, Any]:
        """Publish updated content to Wikipedia.

        Args:
            title: Article title
            new_content: Full updated wikitext
            summary: Edit summary (defaults to language-specific standard summary)
            baserevid: Base revision ID to prevent edit conflicts
            minor: Mark as minor edit

        Returns:
            API edit response dict.
        """
        if not self.csrf_token:
            self.csrf_token = self.get_csrf_token()

        edit_summary = summary or DEFAULT_EDIT_SUMMARIES.get(
            self.wiki, DEFAULT_EDIT_SUMMARIES["en"]
        )

        data: Dict[str, Any] = {
            "action": "edit",
            "title": title,
            "text": new_content,
            "summary": edit_summary,
            "token": self.csrf_token,
            "format": "json",
            "maxlag": self.client.maxlag,
        }
        if baserevid is not None:
            data["baserevid"] = baserevid
        if minor:
            data["minor"] = 1

        max_edit_attempts = 4
        last_error = "unknown error"
        for attempt in range(max_edit_attempts):
            if self.client.request_delay > 0:
                time.sleep(self.client.request_delay)

            res = self.session.post(self.api_url, data=data, timeout=self.client.timeout)
            res.raise_for_status()
            resp_data = res.json()

            if "error" in resp_data:
                err = resp_data["error"]
                code = err.get("code")
                info = err.get("info", "")
                last_error = f"{info} ({code})"

                # Handle Wikimedia rate limiting (exponential backoff)
                if code == "ratelimited" and attempt < max_edit_attempts - 1:
                    retry_header = res.headers.get("Retry-After")
                    wait_sec = int(retry_header) if retry_header and retry_header.isdigit() else max(10, 5 * (attempt + 1))
                    print(f"    [!] Rate limited on {self.wiki}.wikipedia.org. Backing off for {wait_sec}s before retry (attempt {attempt + 1}/{max_edit_attempts})...")
                    time.sleep(wait_sec)
                    continue

                # Handle Wikimedia database replication lag (maxlag)
                if code == "maxlag" and attempt < max_edit_attempts - 1:
                    retry_header = res.headers.get("Retry-After")
                    wait_sec = int(retry_header) if retry_header and retry_header.isdigit() else 5
                    print(f"    [!] Database replication lag on {self.wiki}.wikipedia.org. Waiting {wait_sec}s before retry...")
                    time.sleep(wait_sec)
                    continue

                # Handle CSRF token expiration
                if code in ("badtoken", "notoken") and attempt < max_edit_attempts - 1:
                    self.csrf_token = self.get_csrf_token()
                    data["token"] = self.csrf_token
                    continue

                raise RuntimeError(f"Edit failed on '{title}' ({self.wiki}.wikipedia.org): {info} ({code})")

            return resp_data.get("edit", {})

        raise RuntimeError(f"Edit failed on '{title}' ({self.wiki}.wikipedia.org) after {max_edit_attempts} attempts: {last_error}")


# Backward-compatibility alias
TamilWikiUpdater = WikiUpdater


class MultiWikiUpdater:
    """Manages WikiUpdater instances across multiple language editions using shared credentials."""

    def __init__(
        self,
        client: Optional[MediaWikiClient] = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.client = client or MediaWikiClient(user_agent=user_agent)
        self.updaters: Dict[str, WikiUpdater] = {}
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    def set_credentials(self, username: str, password: str) -> None:
        """Store bot credentials for authenticating across wikis."""
        self.username = username
        self.password = password

    def get_updater(self, wiki: str) -> WikiUpdater:
        """Get or create an authenticated WikiUpdater for the specified language."""
        wiki_code = wiki.lower().strip()
        if wiki_code not in self.updaters:
            updater = WikiUpdater(client=self.client, wiki=wiki_code)
            if self.username and self.password:
                updater.login(self.username, self.password)
            self.updaters[wiki_code] = updater
        return self.updaters[wiki_code]

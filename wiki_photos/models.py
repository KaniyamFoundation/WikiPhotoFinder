"""Data models for Wikipedia photo finder."""

from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List
from urllib.parse import quote


@dataclass
class ArticleResult:
    """Represents a matched article where Tamil Wikipedia lacks a photo
    but English Wikipedia has one. Also tracks other linked language wikis.
    """
    ta_title: str
    en_title: str
    image_name: str
    image_url: Optional[str] = None
    image_thumbnail_url: Optional[str] = None
    image_repository: str = "shared"  # 'shared' = Commons, 'local' = enwiki
    wikidata_id: Optional[str] = None
    source_category: Optional[str] = None
    linked_wikis: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @property
    def clean_image_name(self) -> str:
        """Return image filename without 'File:' or 'Image:' prefix."""
        name = self.image_name
        for prefix in ("File:", "Image:", "படிமம்:", "கோப்பு:"):
            if name.startswith(prefix):
                name = name[len(prefix):]
        return name.replace("_", " ").strip()

    @property
    def clean_image_filename(self) -> str:
        """Return image filename with underscores for URLs."""
        return self.clean_image_name.replace(" ", "_")

    @property
    def is_on_commons(self) -> bool:
        """True if the image is hosted on Wikimedia Commons."""
        return self.image_repository.lower() == "shared"

    @property
    def ta_url(self) -> str:
        """Full URL for Tamil Wikipedia article."""
        formatted_title = self.ta_title.replace(" ", "_")
        return f"https://ta.wikipedia.org/wiki/{quote(formatted_title, safe='/:@&=+$,?#')}"

    @property
    def en_url(self) -> str:
        """Full URL for English Wikipedia article."""
        formatted_title = self.en_title.replace(" ", "_")
        return f"https://en.wikipedia.org/wiki/{quote(formatted_title, safe='/:@&=+$,?#')}"

    @property
    def file_page_url(self) -> str:
        """URL to the file description page (Commons or English Wikipedia)."""
        filename = quote(self.clean_image_filename, safe='/:@&=+$,?#')
        if self.is_on_commons:
            return f"https://commons.wikimedia.org/wiki/File:{filename}"
        return f"https://en.wikipedia.org/wiki/File:{filename}"

    @property
    def wikidata_url(self) -> Optional[str]:
        """URL to Wikidata item page if available."""
        if self.wikidata_id:
            return f"https://www.wikidata.org/wiki/{self.wikidata_id}"
        return None

    @property
    def wikitext_snippet(self) -> str:
        """Wikitext code to embed this image in a Tamil Wikipedia article."""
        return f"[[படிமம்:{self.clean_image_name}|mini|{self.ta_title}]]"

    @property
    def infobox_snippet(self) -> str:
        """Infobox parameter line to insert into a Tamil Wikipedia infobox."""
        return f"| படம் = {self.clean_image_name}"

    @property
    def missing_wikis(self) -> List[str]:
        """Return list of language codes for linked wikis that exist but lack a photo."""
        missing = []
        # Tamil is always missing in this result
        missing.append("ta")
        for lang, info in self.linked_wikis.items():
            if lang != "ta" and not info.get("has_image") and not info.get("missing", False):
                missing.append(lang)
        return missing

    @property
    def present_wikis(self) -> List[str]:
        """Return list of language codes for linked wikis that already have a photo."""
        present = []
        if self.en_title:
            present.append("en")
        for lang, info in self.linked_wikis.items():
            if lang != "en" and info.get("has_image"):
                present.append(lang)
        return present

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary with derived URLs and snippets."""
        data = asdict(self)
        data["ta_url"] = self.ta_url
        data["en_url"] = self.en_url
        data["file_page_url"] = self.file_page_url
        data["wikidata_url"] = self.wikidata_url
        data["is_on_commons"] = self.is_on_commons
        data["wikitext_snippet"] = self.wikitext_snippet
        data["infobox_snippet"] = self.infobox_snippet
        data["clean_image_name"] = self.clean_image_name
        data["missing_wikis"] = self.missing_wikis
        data["present_wikis"] = self.present_wikis
        return data

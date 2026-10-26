"""Persistent progress tracking for resumable Wikipedia updates."""

from datetime import datetime, timezone
import json
import os
import tempfile
from typing import Dict, Any, Optional, Tuple


class UpdateProgressManager:
    """Manages persistent progress state so large update sessions can be resumed with breaks."""

    def __init__(self, state_file: str):
        self.state_file = state_file
        self.data: Dict[str, Any] = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "items": {},
        }
        self.load()

    def load(self) -> None:
        """Load state from disk if it exists."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                    if "items" not in self.data:
                        self.data["items"] = {}
            except Exception:
                # If corrupt or unreadable, start fresh
                self.data = {"items": {}}

    def save(self) -> None:
        """Atomically save state to disk."""
        self.data["last_updated"] = datetime.now(timezone.utc).isoformat()
        dir_name = os.path.dirname(os.path.abspath(self.state_file))
        os.makedirs(dir_name, exist_ok=True)

        # Write to temporary file first then replace atomically
        tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".progress_tmp_")
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.state_file)

    def is_processed(self, title: str, retry_skipped: bool = False) -> bool:
        """Check if an article title has already been processed."""
        item = self.data.get("items", {}).get(title)
        if not item:
            return False
        status = item.get("status")
        if status == "updated":
            return True
        if status == "skipped":
            return not retry_skipped
        return False

    def mark_updated(self, title: str, image: str, revid: Optional[int] = None) -> None:
        """Mark article as updated and persist."""
        self.data["items"][title] = {
            "status": "updated",
            "image": image,
            "revid": revid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.save()

    def mark_skipped(self, title: str, image: str, reason: Optional[str] = None) -> None:
        """Mark article as skipped and persist."""
        self.data["items"][title] = {
            "status": "skipped",
            "image": image,
            "reason": reason or "user_skipped",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.save()

    def get_counts(self) -> Tuple[int, int]:
        """Return (updated_count, skipped_count)."""
        items = self.data.get("items", {})
        updated = sum(1 for it in items.values() if it.get("status") == "updated")
        skipped = sum(1 for it in items.values() if it.get("status") == "skipped")
        return updated, skipped

    def reset(self) -> None:
        """Clear progress state and remove file."""
        self.data = {"items": {}}
        if os.path.exists(self.state_file):
            try:
                os.remove(self.state_file)
            except OSError:
                pass

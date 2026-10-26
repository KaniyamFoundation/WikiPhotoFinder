"""Unit tests for UpdateProgressManager."""

import os
import tempfile
from wiki_photos.state import UpdateProgressManager


def test_progress_manager_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "test.progress.json")
        mgr = UpdateProgressManager(state_file)

        assert mgr.is_processed("Article A") is False
        assert mgr.get_counts() == (0, 0)

        # Mark updated
        mgr.mark_updated("Article A", "PhotoA.jpg", revid=123)
        assert mgr.is_processed("Article A") is True
        assert mgr.get_counts() == (1, 0)

        # Mark skipped
        mgr.mark_skipped("Article B", "PhotoB.jpg")
        assert mgr.is_processed("Article B") is True
        # If retry_skipped=True, skipped article should be re-processed
        assert mgr.is_processed("Article B", retry_skipped=True) is False
        assert mgr.get_counts() == (1, 1)

        # Reload from disk
        mgr2 = UpdateProgressManager(state_file)
        assert mgr2.is_processed("Article A") is True
        assert mgr2.is_processed("Article B") is True
        assert mgr2.get_counts() == (1, 1)

        # Reset
        mgr2.reset()
        assert mgr2.is_processed("Article A") is False
        assert os.path.exists(state_file) is False

"""Tests for CueStore sync import methods: import_cue and import_reply."""
import sys
import os
import shutil
import time
import tempfile
from pathlib import Path

# Use isolated temp dir — never touch real ~/.clavus
_TEST_CLAVUS_DIR = tempfile.mkdtemp(suffix="_clavus_test")

sys.path.insert(0, os.path.expanduser("~/Developer/clavus"))

from clavus.cues import CueStore, Cue, CueReply
from clavus.store import BlobStore, ClavusProject


def setup_module():
    """One-time test setup: create a project."""
    store = BlobStore(Path(_TEST_CLAVUS_DIR))
    store.init()
    proj = ClavusProject(
        name="SyncImportTest",
        root_als="/tmp/test_sync.als",
        created_at=time.time(),
    )
    store.set_index(proj)
    store.update_ref("HEAD", "abc123")


def teardown_module():
    """Clean up temp dir after all tests."""
    shutil.rmtree(_TEST_CLAVUS_DIR, ignore_errors=True)


# Reusable store factory
def make_store():
    """Return a CueStore for the test project."""
    return CueStore("SyncImportTest", store=BlobStore(Path(_TEST_CLAVUS_DIR)))
    """Return a CueStore for the test project."""
    return CueStore("SyncImportTest", store=BlobStore())


# ── import_cue tests ──


def test_import_cue_adds_new_cue():
    """import_cue should persist a cue that doesn't exist yet."""
    cues = make_store()
    cue = Cue(
        id="test-new-cue-001",
        position="1.1.1",
        text="New cue from sync",
        author="alice",
        timestamp=1000.0,
    )
    cues.import_cue(cue)

    loaded = cues.get_cue("test-new-cue-001")
    assert loaded is not None, f"Cue not found, cues in store: {[c.id for c in cues.list_cues()]}"
    assert loaded.text == "New cue from sync"
    assert loaded.author == "alice"
    assert loaded.timestamp == 1000.0


def test_import_cue_skips_older_existing_cue():
    """import_cue should NOT overwrite an existing cue that has a newer timestamp."""
    cues = make_store()
    cue_id = "test-skip-older"

    # Add the original cue with an old timestamp
    old_cue = Cue(
        id=cue_id,
        position="1.1.1",
        text="Original text",
        author="bob",
        timestamp=2000.0,
    )
    cues._save_cue(old_cue)

    # Try importing a newer-timestamped cue via import_cue - but it's actually older (1000 < 2000)
    incoming_cue = Cue(
        id=cue_id,
        position="2.2.2",
        text="Should be skipped (older timestamp)",
        author="charlie",
        timestamp=1000.0,  # older than existing 2000.0
    )
    cues.import_cue(incoming_cue)

    loaded = cues.get_cue(cue_id)
    assert loaded is not None
    # Original should remain unchanged
    assert loaded.text == "Original text"
    assert loaded.author == "bob"
    assert loaded.timestamp == 2000.0


def test_import_cue_overwrites_newer_incoming():
    """import_cue SHOULD overwrite when the incoming cue has a newer timestamp."""
    cues = make_store()
    cue_id = "test-overwrite-newer"

    # Add the original cue with an older timestamp
    old_cue = Cue(
        id=cue_id,
        position="1.1.1",
        text="Old text",
        author="bob",
        timestamp=1000.0,
    )
    cues._save_cue(old_cue)

    # Import a newer cue
    incoming_cue = Cue(
        id=cue_id,
        position="3.3.3",
        text="New text from sync",
        author="dave",
        timestamp=3000.0,  # newer than existing 1000.0
    )
    cues.import_cue(incoming_cue)

    loaded = cues.get_cue(cue_id)
    assert loaded is not None
    assert loaded.text == "New text from sync"
    assert loaded.author == "dave"
    assert loaded.timestamp == 3000.0


def test_import_cue_same_timestamp_overwrites():
    """import_cue should overwrite when timestamps are equal (not strictly greater)."""
    cues = make_store()
    cue_id = "test-same-timestamp"

    old_cue = Cue(
        id=cue_id,
        position="1.1.1",
        text="Original",
        author="eve",
        timestamp=5000.0,
    )
    cues._save_cue(old_cue)

    incoming_cue = Cue(
        id=cue_id,
        position="4.4.4",
        text="Same timestamp replacement",
        author="frank",
        timestamp=5000.0,  # same timestamp
    )
    cues.import_cue(incoming_cue)

    loaded = cues.get_cue(cue_id)
    assert loaded is not None
    assert loaded.text == "Same timestamp replacement"
    assert loaded.author == "frank"


# ── import_reply tests ──


def test_import_reply_adds_reply():
    """import_reply should add a reply to an existing cue."""
    cues = make_store()
    cue_id = "test-reply-add"

    # Create a cue
    cue = Cue(
        id=cue_id,
        position="1.1.1",
        text="Cue for reply test",
        author="grace",
        timestamp=1000.0,
    )
    cues._save_cue(cue)

    # Import a reply
    reply = CueReply(
        id="reply-001",
        text="Great point!",
        author="heidi",
        timestamp=1100.0,
    )
    result = cues.import_reply(cue_id, reply)
    assert result is True

    loaded = cues.get_cue(cue_id)
    assert loaded is not None
    assert len(loaded.replies) == 1
    assert loaded.replies[0].text == "Great point!"
    assert loaded.replies[0].author == "heidi"


def test_import_reply_skips_duplicate():
    """import_reply should skip a reply that matches timestamp AND author."""
    cues = make_store()
    cue_id = "test-reply-dup"

    cue = Cue(
        id=cue_id,
        position="1.1.1",
        text="Cue for duplicate test",
        author="ivan",
        timestamp=1000.0,
    )
    cues._save_cue(cue)

    # Add the reply once
    reply1 = CueReply(
        id="reply-dup",
        text="First reply",
        author="judy",
        timestamp=1200.0,
    )
    result1 = cues.import_reply(cue_id, reply1)
    assert result1 is True

    # Try adding the same timestamp+author again (different id/text)
    reply2 = CueReply(
        id="reply-dup-2",
        text="This should be a duplicate check",
        author="judy",
        timestamp=1200.0,  # same timestamp + author
    )
    result2 = cues.import_reply(cue_id, reply2)
    assert result2 is False  # duplicate

    loaded = cues.get_cue(cue_id)
    assert loaded is not None
    assert len(loaded.replies) == 1  # still only 1 reply


def test_import_reply_allows_same_timestamp_different_author():
    """import_reply should NOT skip replies with same timestamp but different author."""
    cues = make_store()
    cue_id = "test-reply-diff-author"

    cue = Cue(
        id=cue_id,
        position="1.1.1",
        text="Cue for diff author test",
        author="karl",
        timestamp=1000.0,
    )
    cues._save_cue(cue)

    reply1 = CueReply(
        id="reply-author-1",
        text="From alice",
        author="alice",
        timestamp=1300.0,
    )
    assert cues.import_reply(cue_id, reply1) is True

    reply2 = CueReply(
        id="reply-author-2",
        text="From bob (same time)",
        author="bob",
        timestamp=1300.0,  # same timestamp, different author
    )
    result2 = cues.import_reply(cue_id, reply2)
    assert result2 is True  # not a duplicate

    loaded = cues.get_cue(cue_id)
    assert loaded is not None
    assert len(loaded.replies) == 2


def test_import_reply_returns_false_for_missing_cue():
    """import_reply should return False when the cue_id doesn't exist."""
    cues = make_store()
    reply = CueReply(
        id="reply-orphan",
        text="Nobody home",
        author="mallory",
        timestamp=9999.0,
    )
    result = cues.import_reply("nonexistent-cue-id", reply)
    assert result is False

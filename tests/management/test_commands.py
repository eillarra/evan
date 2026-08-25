"""Tests for the small management commands.

The commands are invoked via call_command. External dependencies (cache, S3)
are mocked at the boundary.
"""

import hashlib
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command


class TestClearcacheCommand:
    """clearcache clears the Django cache."""

    def test_clearcache_calls_cache_clear(self):
        """The command delegates to cache.clear()."""
        with patch("evan.management.commands.clearcache.cache") as mock_cache:
            call_command("clearcache", stdout=StringIO())

        mock_cache.clear.assert_called_once()


class TestShaCommand:
    """sha prints a SHA256 hash of a random string."""

    def test_sha_outputs_a_64_char_hex_hash(self, capsys):
        """The command prints a valid 64-char hex SHA256 digest."""
        call_command("sha")
        captured = capsys.readouterr()

        output = captured.out.strip()
        assert len(output) == 64
        # must be valid hex
        int(output, 16)

    def test_sha_outputs_different_hashes_on_repeated_calls(self, capsys):
        """Two invocations produce different hashes (random input)."""
        call_command("sha")
        first = capsys.readouterr().out.strip()
        call_command("sha")
        second = capsys.readouterr().out.strip()

        assert first != second

    def test_sha_matches_secrets_and_hashlib(self, capsys):
        """The output equals sha256(token_urlsafe(64)) when the inputs match."""
        fixed_token = "fixed-token-value"
        expected = hashlib.sha256(fixed_token.encode("utf-8")).hexdigest()

        with patch("evan.management.commands.sha.secrets.token_urlsafe", return_value=fixed_token):
            call_command("sha")

        assert capsys.readouterr().out.strip() == expected


class TestS3Command:
    """s3 lists all files in the bucket."""

    def test_s3_lists_files_from_bucket(self):
        """The command writes each file key returned by list_bucket_files."""
        with patch("evan.management.commands.s3.list_bucket_files", return_value=["a.txt", "b.txt"]):
            out = StringIO()
            call_command("s3", stdout=out)

        text = out.getvalue()
        assert "a.txt" in text
        assert "b.txt" in text
        assert "Done." in text

    def test_s3_handles_empty_bucket(self):
        """An empty bucket still prints the start and done messages."""
        with patch("evan.management.commands.s3.list_bucket_files", return_value=[]):
            out = StringIO()
            call_command("s3", stdout=out)

        text = out.getvalue()
        assert "Listing all files" in text
        assert "Done." in text

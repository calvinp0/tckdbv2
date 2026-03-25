"""Tests for artifact validation and content-addressed storage."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.db.models.common import ArtifactKind
from app.services.artifact_storage import (
    ArtifactValidationError,
    content_addressed_path,
    store_artifact,
    validate_artifact,
    validate_total_upload_size,
    MAX_ARTIFACT_BYTES,
    MAX_TOTAL_UPLOAD_BYTES,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
GAUSSIAN_OPT_LOG = FIXTURES / "gaussian" / "opt_g09.log"
GAUSSIAN_FREQ_LOG = FIXTURES / "gaussian" / "freq_g09.log"
ORCA_OPT_LOG = FIXTURES / "orca" / "opt_orca.out"


# ---------------------------------------------------------------------------
# Signature validation
# ---------------------------------------------------------------------------


class TestOutputLogSignatureValidation:
    """output_log artifacts must match a known ESS header."""

    def test_gaussian_log_accepted(self):
        content = GAUSSIAN_OPT_LOG.read_bytes()
        sha = validate_artifact(content, ArtifactKind.output_log)
        assert len(sha) == 64

    def test_gaussian_freq_log_accepted(self):
        content = GAUSSIAN_FREQ_LOG.read_bytes()
        sha = validate_artifact(content, ArtifactKind.output_log)
        assert len(sha) == 64

    def test_orca_log_accepted(self):
        content = ORCA_OPT_LOG.read_bytes()
        sha = validate_artifact(content, ArtifactKind.output_log)
        assert len(sha) == 64

    def test_unknown_ess_rejected(self):
        content = b"This is not a real ESS output log file.\n" * 10
        with pytest.raises(ArtifactValidationError, match="does not match any known ESS"):
            validate_artifact(content, ArtifactKind.output_log)

    def test_python_script_rejected(self):
        content = b"#!/usr/bin/env python3\nimport os\nos.system('rm -rf /')\n"
        with pytest.raises(ArtifactValidationError, match="does not match any known ESS"):
            validate_artifact(content, ArtifactKind.output_log)


# ---------------------------------------------------------------------------
# Integrity checks
# ---------------------------------------------------------------------------


class TestIntegrityValidation:
    """SHA-256 and size declarations must match content."""

    def test_correct_sha256_accepted(self):
        content = GAUSSIAN_OPT_LOG.read_bytes()
        expected_sha = hashlib.sha256(content).hexdigest()
        sha = validate_artifact(
            content, ArtifactKind.output_log, declared_sha256=expected_sha
        )
        assert sha == expected_sha

    def test_wrong_sha256_rejected(self):
        content = GAUSSIAN_OPT_LOG.read_bytes()
        with pytest.raises(ArtifactValidationError, match="SHA-256 mismatch"):
            validate_artifact(
                content, ArtifactKind.output_log, declared_sha256="a" * 64
            )

    def test_correct_size_accepted(self):
        content = GAUSSIAN_OPT_LOG.read_bytes()
        validate_artifact(
            content, ArtifactKind.output_log, declared_bytes=len(content)
        )

    def test_wrong_size_rejected(self):
        content = GAUSSIAN_OPT_LOG.read_bytes()
        with pytest.raises(ArtifactValidationError, match="Size mismatch"):
            validate_artifact(
                content, ArtifactKind.output_log, declared_bytes=len(content) + 1
            )


# ---------------------------------------------------------------------------
# Size limits
# ---------------------------------------------------------------------------


class TestSizeLimits:
    def test_empty_file_rejected(self):
        with pytest.raises(ArtifactValidationError, match="empty"):
            validate_artifact(b"", ArtifactKind.output_log)

    def test_oversized_file_rejected(self):
        # Construct content just over the limit — don't allocate real memory
        # Just check the validation logic with a mock-sized content
        content = b"Entering Gaussian System\n" + b"x" * (MAX_ARTIFACT_BYTES + 1 - 25)
        with pytest.raises(ArtifactValidationError, match="exceeds maximum size"):
            validate_artifact(content, ArtifactKind.output_log)

    def test_total_upload_size_accepted(self):
        validate_total_upload_size([1000, 2000, 3000])

    def test_total_upload_size_rejected(self):
        with pytest.raises(ArtifactValidationError, match="Total artifact upload size"):
            validate_total_upload_size([MAX_TOTAL_UPLOAD_BYTES, 1])


# ---------------------------------------------------------------------------
# Text validation
# ---------------------------------------------------------------------------


class TestTextValidation:
    """Text artifact kinds must be valid UTF-8."""

    def test_valid_utf8_accepted(self):
        content = b"Entering Gaussian System\nSCF Done\n"
        validate_artifact(content, ArtifactKind.output_log)

    def test_binary_in_text_kind_rejected(self):
        content = b"Entering Gaussian System\n\xff\xfe\x00\x01"
        with pytest.raises(ArtifactValidationError, match="valid UTF-8"):
            validate_artifact(content, ArtifactKind.output_log)

    def test_binary_checkpoint_accepted(self):
        """checkpoint kind allows binary content (no text check)."""
        content = b"\x00\x01\x02\x03\xff\xfe binary checkpoint data"
        # No ESS signature check for checkpoint kind either
        validate_artifact(content, ArtifactKind.checkpoint)


# ---------------------------------------------------------------------------
# Non-log kinds (no signature required)
# ---------------------------------------------------------------------------


class TestNonLogKinds:
    def test_input_file_no_signature_required(self):
        content = b"%mem=32GB\n%nproc=8\n#p wb97xd/def2tzvp opt\n\ntitle\n\n0 1\n"
        sha = validate_artifact(content, ArtifactKind.input)
        assert len(sha) == 64

    def test_ancillary_no_signature_required(self):
        content = b"some ancillary data\n"
        sha = validate_artifact(content, ArtifactKind.ancillary)
        assert len(sha) == 64


# ---------------------------------------------------------------------------
# Content-addressed storage
# ---------------------------------------------------------------------------


class TestContentAddressedStorage:
    def test_path_layout(self, tmp_path):
        sha = "a577811dc7167bfc1234567890abcdef1234567890abcdef1234567890abcdef"
        path = content_addressed_path(sha, artifact_dir=tmp_path)
        assert path == tmp_path / "a5" / sha

    def test_store_and_dedup(self, tmp_path):
        content = GAUSSIAN_OPT_LOG.read_bytes()
        sha = hashlib.sha256(content).hexdigest()

        # First store
        path1 = store_artifact(content, sha, artifact_dir=tmp_path)
        assert path1.exists()
        assert path1.read_bytes() == content
        assert path1 == tmp_path / sha[:2] / sha

        # Second store (same content) — dedup, same path
        path2 = store_artifact(content, sha, artifact_dir=tmp_path)
        assert path1 == path2

"""Artifact validation and content-addressed storage.

Validates uploaded calculation artifacts (ESS output logs, input files,
checkpoints) and writes them to a content-addressed local store.

Security measures:
- Content signature validation: output_log artifacts must match a known
  ESS header (Gaussian, ORCA, etc.) or be rejected.
- SHA-256 integrity: declared hash must match computed hash.
- Size limits: per-artifact and per-upload caps.
- Content-addressed paths: the server constructs storage paths from the
  content hash, never from user-supplied URIs.  Path traversal is impossible.
- Artifacts are stored as inert blobs, never executed.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from app.db.models.common import ArtifactKind

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

#: Default root directory for artifact storage.
#: In Docker: ``/app/data/artifacts`` (backed by a named volume).
#: Override via ``TCKDB_ARTIFACT_DIR`` environment variable.
DEFAULT_ARTIFACT_DIR = Path(os.environ.get("TCKDB_ARTIFACT_DIR", "/app/data/artifacts"))

#: Maximum size for a single artifact (bytes).  50 MB.
MAX_ARTIFACT_BYTES = 50 * 1024 * 1024

#: Maximum total upload size across all artifacts in one request (bytes). 200 MB.
MAX_TOTAL_UPLOAD_BYTES = 200 * 1024 * 1024

# ---------------------------------------------------------------------------
# ESS output signatures — first ~4 KB of a legitimate log must contain one.
# ---------------------------------------------------------------------------

#: Map of ESS name → byte string that must appear in the first 4 KB.
OUTPUT_LOG_SIGNATURES: dict[str, bytes] = {
    "gaussian": b"Entering Gaussian System",
    "orca": b"O   R   C   A",
    "qchem": b"Q-Chem",
    "molpro": b"MOLPRO",
    "psi4": b"Psi4",
    "nwchem": b"Northwest Computational Chemistry Package",
    "turbomole": b"TURBOMOLE",
    "cfour": b"CFOUR",
}

#: How many bytes to inspect for signature detection.
_SIGNATURE_WINDOW = 4096

# ---------------------------------------------------------------------------
# Kinds that must be valid UTF-8 text (no binary allowed).
# ---------------------------------------------------------------------------

_TEXT_KINDS = {
    ArtifactKind.output_log,
    ArtifactKind.input,
    ArtifactKind.formatted_checkpoint,
}

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ArtifactValidationError(ValueError):
    """Raised when an artifact fails validation."""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_artifact(
    content: bytes,
    kind: ArtifactKind,
    *,
    declared_sha256: str | None = None,
    declared_bytes: int | None = None,
) -> str:
    """Validate artifact content and return its SHA-256 hash.

    :param content: Raw file content.
    :param kind: Declared artifact kind.
    :param declared_sha256: Optional SHA-256 declared by the uploader.
    :param declared_bytes: Optional file size declared by the uploader.
    :returns: Computed SHA-256 hex digest.
    :raises ArtifactValidationError: On any validation failure.
    """
    # -- Size check --
    if len(content) > MAX_ARTIFACT_BYTES:
        raise ArtifactValidationError(
            f"Artifact exceeds maximum size: {len(content):,} bytes "
            f"(limit: {MAX_ARTIFACT_BYTES:,} bytes)."
        )

    if len(content) == 0:
        raise ArtifactValidationError("Artifact is empty (0 bytes).")

    # -- Integrity check --
    computed_sha = hashlib.sha256(content).hexdigest()

    if declared_sha256 is not None and computed_sha != declared_sha256:
        raise ArtifactValidationError(
            f"SHA-256 mismatch: declared {declared_sha256}, "
            f"computed {computed_sha}."
        )

    if declared_bytes is not None and len(content) != declared_bytes:
        raise ArtifactValidationError(
            f"Size mismatch: declared {declared_bytes:,} bytes, "
            f"actual {len(content):,} bytes."
        )

    # -- Text check for text-expected kinds --
    if kind in _TEXT_KINDS:
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            raise ArtifactValidationError(
                f"Artifact kind '{kind.value}' must be valid UTF-8 text, "
                f"but the content contains invalid byte sequences."
            )

    # -- Output log signature check --
    if kind == ArtifactKind.output_log:
        _validate_output_log_signature(content)

    return computed_sha


def _validate_output_log_signature(content: bytes) -> None:
    """Verify that an output_log artifact contains a recognized ESS header."""
    head = content[:_SIGNATURE_WINDOW]
    for ess_name, signature in OUTPUT_LOG_SIGNATURES.items():
        if signature in head:
            return

    known = ", ".join(sorted(OUTPUT_LOG_SIGNATURES))
    raise ArtifactValidationError(
        f"Output log does not match any known ESS signature in the "
        f"first {_SIGNATURE_WINDOW} bytes. Supported: {known}. "
        f"If this is a valid output file from a supported ESS, the "
        f"signature detection may need updating."
    )


def validate_total_upload_size(artifacts_bytes: list[int]) -> None:
    """Check that the total size of all artifacts in one request is within limits.

    :param artifacts_bytes: List of individual artifact sizes.
    :raises ArtifactValidationError: If total exceeds MAX_TOTAL_UPLOAD_BYTES.
    """
    total = sum(artifacts_bytes)
    if total > MAX_TOTAL_UPLOAD_BYTES:
        raise ArtifactValidationError(
            f"Total artifact upload size {total:,} bytes exceeds limit "
            f"of {MAX_TOTAL_UPLOAD_BYTES:,} bytes."
        )


# ---------------------------------------------------------------------------
# Content-addressed storage
# ---------------------------------------------------------------------------


def content_addressed_path(sha256: str, artifact_dir: Path | None = None) -> Path:
    """Compute the storage path for an artifact by its SHA-256 hash.

    Layout: ``{artifact_dir}/{sha256[:2]}/{sha256}``

    The two-character prefix subdirectory prevents any single directory
    from accumulating too many files.
    """
    root = artifact_dir or DEFAULT_ARTIFACT_DIR
    return root / sha256[:2] / sha256


def store_artifact(
    content: bytes,
    sha256: str,
    artifact_dir: Path | None = None,
) -> Path:
    """Write artifact content to the content-addressed store.

    If a file with the same SHA-256 already exists, this is a no-op
    (content-addressed dedup).

    :param content: Validated file content.
    :param sha256: Pre-computed SHA-256 hex digest (from validate_artifact).
    :param artifact_dir: Override the default artifact directory.
    :returns: Absolute path where the artifact is stored.
    """
    dest = content_addressed_path(sha256, artifact_dir)

    if dest.exists():
        # Content-addressed dedup: same hash = same content
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    # Write atomically via temp file to avoid partial writes
    tmp = dest.with_suffix(".tmp")
    try:
        tmp.write_bytes(content)
        tmp.rename(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

    return dest

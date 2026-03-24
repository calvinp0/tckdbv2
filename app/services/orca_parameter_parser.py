"""Parse ORCA log files to extract execution parameters.

Pure-function parser: takes text, returns structured dicts compatible with
the CalculationParameter model.  No DB dependency.

ORCA input structure (echoed in log file):
  - ``! keyword1 keyword2 ...`` — keyword line(s)
  - ``%section ... end`` — block settings
  - ``%maxcore N`` — single-line block
  - ``* xyz charge mult`` — coordinate header
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Canonical key mapping — ORCA-specific entries
# ---------------------------------------------------------------------------

#: Maps (section, raw_key) → (canonical_key, canonical_value)
#: Uses the same canonical vocabulary as the Gaussian parser where
#: semantics overlap (e.g. scf_convergence, nproc).
_CANONICAL_MAP: dict[tuple[str, str], tuple[str, str | None]] = {
    # SCF convergence keywords (from ! line, section="scf")
    ("scf", "tightscf"): ("scf_convergence", "tight"),
    ("scf", "verytightscf"): ("scf_convergence", "very_tight"),
    ("scf", "loosescf"): ("scf_convergence", "loose"),
    ("scf", "normalscf"): ("scf_convergence", "normal"),
    ("scf", "scfconv"): ("scf_convergence", None),
    ("scf", "maxiter"): ("scf_max_cycles", None),
    # PNO truncation (from ! line, section="pno")
    ("pno", "tightpno"): ("pno_truncation", "tight"),
    ("pno", "normalpno"): ("pno_truncation", "normal"),
    ("pno", "loosepno"): ("pno_truncation", "loose"),
    # Grid keywords (from ! line, section="grid")
    ("grid", "defgrid1"): ("grid_quality", "defgrid1"),
    ("grid", "defgrid2"): ("grid_quality", "defgrid2"),
    ("grid", "defgrid3"): ("grid_quality", "defgrid3"),
    ("grid", "grid4"): ("grid_quality", "grid4"),
    ("grid", "grid5"): ("grid_quality", "grid5"),
    ("grid", "grid6"): ("grid_quality", "grid6"),
    ("grid", "grid7"): ("grid_quality", "grid7"),
    # Resource (from %maxcore, %pal)
    ("resource", "maxcore"): ("maxcore_mb", None),
    ("resource", "nprocs"): ("nproc", None),
}


def _lookup_canonical(
    section: str, raw_key: str
) -> tuple[str | None, str | None]:
    """Return (canonical_key, canonical_value) for a given section+raw_key."""
    key = (section.lower(), raw_key.lower())
    if key in _CANONICAL_MAP:
        return _CANONICAL_MAP[key]
    return None, None


# ---------------------------------------------------------------------------
# Classification sets — what belongs in LoT vs parameters
# ---------------------------------------------------------------------------

#: Job types — these define Calculation.type, not parameters.
_JOB_TYPES = frozenset({
    "sp", "opt", "copt", "zopt", "freq", "numfreq", "neb", "neb-ts",
    "neb-ci", "irc", "md", "goat",
})

#: Known method keywords — belong in level_of_theory, not parameters.
_METHOD_PREFIXES = (
    "hf", "uhf", "rhf", "rohf",
    "dft", "b3lyp", "pbe", "pbe0", "bp86", "tpss", "m06",
    "mp2", "ri-mp2", "dlpno-mp2",
    "ccsd", "ccsd(t)", "dlpno-ccsd", "dlpno-ccsd(t)", "dlpno-ccsd(t1)",
    "casscf", "nevpt2", "dlpno-nevpt2",
    "wb97x", "wb97x-d3", "wb97x-d3bj", "cam-b3lyp",
    "r2scan", "r2scan-3c",
)

#: Known basis set patterns — belong in level_of_theory.
_BASIS_PATTERNS = re.compile(
    r"^("
    r"def2-[a-z]+p?|"              # def2-SVP, def2-TZVP, def2-TZVPP, etc.
    r"cc-pv[dtq56]z(-f12)?|"       # cc-pVDZ, cc-pVTZ-F12, etc.
    r"aug-cc-pv[dtq56]z(/c)?|"     # aug-cc-pVTZ, aug-cc-pVTZ/C
    r"cc-pv[dtq56]z-f12-cabs|"     # CABS basis sets
    r"6-31[g+\*]+|"                # Pople basis sets
    r"sto-3g|"
    r"ma-def2-[a-z]+p?"            # minimally augmented
    r")$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Section classifiers for ! line keywords
# ---------------------------------------------------------------------------

_SCF_KEYWORDS = frozenset({
    "tightscf", "verytightscf", "loosescf", "normalscf",
    "scfconv", "nori", "rijcosx", "rijonx", "rijk",
    "noiter", "conv", "unconventionalscf",
})

_PNO_KEYWORDS = frozenset({
    "tightpno", "normalpno", "loosepno",
})

_GRID_KEYWORDS = frozenset({
    "defgrid1", "defgrid2", "defgrid3",
    "grid4", "grid5", "grid6", "grid7",
    "nofinalgrid", "nofinalgridx",
})


def _classify_keyword(kw: str) -> str | None:
    """Classify an ORCA ! keyword into a section, or None to skip.

    Returns None for LoT keywords and job types (they don't become
    parameter rows).
    """
    kw_lower = kw.lower()

    # Job types → skip
    if kw_lower in _JOB_TYPES:
        return None

    # Method → skip (LoT territory)
    if kw_lower in _METHOD_PREFIXES:
        return None

    # Basis → skip
    if _BASIS_PATTERNS.match(kw_lower):
        return None

    # SCF keywords
    if kw_lower in _SCF_KEYWORDS:
        return "scf"

    # PNO keywords
    if kw_lower in _PNO_KEYWORDS:
        return "pno"

    # Grid keywords
    if kw_lower in _GRID_KEYWORDS:
        return "grid"

    # Everything else: store as general parameter
    return "general"


# ---------------------------------------------------------------------------
# Input block extraction
# ---------------------------------------------------------------------------

_INPUT_DELIM = re.compile(r"^={60,}$")
_INPUT_LINE = re.compile(r"^\|\s*\d+>\s*(.*)$")


def _extract_input_block(text: str) -> list[str]:
    """Extract the echoed ORCA input from the log file.

    ORCA echoes the input between ``INPUT FILE`` and ``****END OF INPUT****``
    markers.  Each line has the format: ``|  N> content``.
    """
    lines = text.splitlines()
    in_input = False
    input_lines: list[str] = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        if "INPUT FILE" in stripped:
            in_input = True
            continue

        if in_input and "****END OF INPUT****" in stripped:
            break

        if in_input:
            m = _INPUT_LINE.match(stripped)
            if m:
                input_lines.append(m.group(1))

    return input_lines


# ---------------------------------------------------------------------------
# Keyword line parsing
# ---------------------------------------------------------------------------


def _parse_keyword_lines(input_lines: list[str]) -> list[dict]:
    """Parse all ``! keyword ...`` lines from the ORCA input.

    Returns parameter dicts for keywords that are not LoT or job types.
    """
    params: list[dict] = []

    for line in input_lines:
        stripped = line.strip()
        if not stripped.startswith("!"):
            continue

        # Strip the ! and optional leading space
        keywords_str = stripped.lstrip("!").strip()
        if not keywords_str:
            continue

        for kw in keywords_str.split():
            section = _classify_keyword(kw)
            if section is None:
                # LoT or job type — skip
                continue

            ck, cv = _lookup_canonical(section, kw)
            params.append({
                "raw_key": kw,
                "canonical_key": ck,
                "raw_value": "true",
                "canonical_value": cv,
                "section": section,
                "value_type": "bool",
            })

    return params


# ---------------------------------------------------------------------------
# Block section parsing
# ---------------------------------------------------------------------------

_BLOCK_START = re.compile(r"^%(\w+)\s*(.*?)$", re.IGNORECASE)


def _parse_block_sections(input_lines: list[str]) -> list[dict]:
    """Parse ``%section ... end`` blocks from the ORCA input.

    Handles:
    - Single-line blocks: ``%maxcore 4096``
    - Multi-line blocks: ``%pal\\n  nprocs 8\\nend``
    - Comments: ``# ...`` stripped
    """
    params: list[dict] = []
    i = 0

    while i < len(input_lines):
        line = input_lines[i].strip()

        # Strip inline comments
        if "#" in line:
            line = line[:line.index("#")].strip()

        m = _BLOCK_START.match(line)
        if not m:
            i += 1
            continue

        block_name = m.group(1).lower()
        rest = m.group(2).strip()

        # Single-line block: %maxcore 4096
        if rest and rest.lower() != "end":
            params.extend(_parse_block_content(block_name, [rest]))
            i += 1
            continue

        # Multi-line block: collect until "end"
        block_lines: list[str] = []
        i += 1
        while i < len(input_lines):
            bline = input_lines[i].strip()
            # Strip inline comments
            if "#" in bline:
                bline = bline[:bline.index("#")].strip()

            if bline.lower() == "end":
                i += 1
                break
            if bline:
                block_lines.append(bline)
            i += 1

        params.extend(_parse_block_content(block_name, block_lines))

    return params


def _parse_block_content(block_name: str, lines: list[str]) -> list[dict]:
    """Parse key-value pairs from within an ORCA block section."""
    params: list[dict] = []

    # Map block names to parameter sections
    section_map = {
        "maxcore": "resource",
        "pal": "resource",
        "scf": "scf",
        "mdci": "correlation",
        "method": "general",
        "basis": "general",
        "geom": "opt",
        "rel": "relativity",
    }
    section = section_map.get(block_name, block_name)

    for line in lines:
        parts = line.split(None, 1)
        if not parts:
            continue

        raw_key = parts[0]
        raw_value = parts[1] if len(parts) > 1 else "true"

        # Special case: %maxcore has the value directly
        if block_name == "maxcore":
            raw_key = "maxcore"
            raw_value = line.strip()

        ck, cv = _lookup_canonical(section, raw_key)
        params.append({
            "raw_key": raw_key,
            "canonical_key": ck,
            "raw_value": raw_value,
            "canonical_value": cv,
            "section": section,
            "value_type": _guess_value_type(raw_value),
        })

    return params


# ---------------------------------------------------------------------------
# Charge / multiplicity
# ---------------------------------------------------------------------------


def parse_charge_multiplicity(text: str) -> dict | None:
    """Extract charge and multiplicity from ORCA coordinate header."""
    input_lines = _extract_input_block(text)
    for line in input_lines:
        stripped = line.strip()
        # ``* xyz charge mult`` or ``* int charge mult``
        if stripped.startswith("*") and ("xyz" in stripped.lower() or "int" in stripped.lower()):
            parts = stripped.split()
            if len(parts) >= 4:
                try:
                    return {
                        "charge": int(parts[2]),
                        "multiplicity": int(parts[3]),
                    }
                except ValueError:
                    pass
    return None


# ---------------------------------------------------------------------------
# Software version extraction
# ---------------------------------------------------------------------------

_VERSION_RE = re.compile(r"Program\s+Version\s+(\d+\.\d+\.\d+)")


def parse_software_version(text: str) -> dict | None:
    """Extract ORCA software version from log text.

    Matches: ``Program Version 5.0.4 -  RELEASE  -``
    """
    m = _VERSION_RE.search(text)
    if m:
        return {
            "name": "orca",
            "version": m.group(1),
            "build": None,
            "release_date_raw": None,
        }
    return None


# ---------------------------------------------------------------------------
# Method/basis extraction
# ---------------------------------------------------------------------------


def parse_method_basis(text: str) -> dict | None:
    """Extract method and basis from ORCA ! keyword line.

    Returns dict with method, basis, aux_basis, cabs_basis keys.
    Classification:
    - ``-cabs`` suffix → CABS basis (F12 complementary auxiliary)
    - ``/c`` suffix → auxiliary correlation fitting basis
    - first orbital basis → primary basis
    - remaining → aux_basis
    """
    input_lines = _extract_input_block(text)

    method = None
    basis = None
    aux_basis = None
    cabs_basis = None

    for line in input_lines:
        stripped = line.strip()
        if not stripped.startswith("!"):
            continue

        for kw in stripped.lstrip("!").strip().split():
            kw_lower = kw.lower()

            # Method detection
            if kw_lower in _METHOD_PREFIXES:
                method = kw

            # Basis detection
            elif _BASIS_PATTERNS.match(kw_lower):
                if "-cabs" in kw_lower:
                    cabs_basis = kw
                elif "/c" in kw_lower:
                    aux_basis = kw
                elif basis is None:
                    basis = kw
                elif aux_basis is None:
                    aux_basis = kw

    if method or basis:
        return {
            "method": method,
            "basis": basis,
            "aux_basis": aux_basis,
            "cabs_basis": cabs_basis,
        }
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _guess_value_type(val: str) -> str:
    """Guess the type hint for a raw value string."""
    if val.lower() in ("true", "false", "on", "off", "yes", "no"):
        return "bool"
    try:
        int(val)
        return "int"
    except ValueError:
        pass
    try:
        float(val)
        return "float"
    except ValueError:
        pass
    return "string"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def parse_orca_log(
    text: str | None = None,
    path: str | Path | None = None,
) -> dict:
    """Parse an ORCA log file and return structured parameter data.

    :param text: Raw log text (provide one of text or path).
    :param path: Path to log file.
    :returns: Dict with keys: parameters, parameters_json, software,
              charge_multiplicity, method_basis, parser_version.
    """
    if text is None and path is not None:
        text = Path(path).read_text()
    if text is None:
        raise ValueError("Provide text or path")

    input_lines = _extract_input_block(text)

    # Parse all parameter sources
    keyword_params = _parse_keyword_lines(input_lines)
    block_params = _parse_block_sections(input_lines)
    all_params = keyword_params + block_params

    return {
        "parameters": all_params,
        "parameters_json": {
            "input_lines": input_lines,
            "parameters": all_params,
        },
        "software": parse_software_version(text),
        "charge_multiplicity": parse_charge_multiplicity(text),
        "method_basis": parse_method_basis(text),
        "parser_version": "orca_v1",
    }

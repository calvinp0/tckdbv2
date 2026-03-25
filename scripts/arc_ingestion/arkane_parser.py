"""Parse kinetics from Arkane output.py files.

Extracts the final ``kinetics(...)`` block which contains the fitted
modified Arrhenius parameters (with tunneling included).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ArkaneKinetics:
    """Parsed modified Arrhenius kinetics from an Arkane output."""

    label: str
    a: float
    a_units: str  # e.g. "cm^3/(mol*s)", "s^-1"
    n: float
    ea: float
    ea_units: str  # e.g. "kJ/mol"
    tmin_k: float
    tmax_k: float
    comment: str | None = None


# Unit string → TCKDB ArrheniusAUnits token
_A_UNITS_MAP: dict[str, str] = {
    "s^-1": "per_s",
    "cm^3/(mol*s)": "cm3_mol_s",
    "cm^3/(molecule*s)": "cm3_molecule_s",
    "m^3/(mol*s)": "m3_mol_s",
    "cm^6/(mol^2*s)": "cm6_mol2_s",
}

# Unit string → TCKDB ActivationEnergyUnits token
_EA_UNITS_MAP: dict[str, str] = {
    "J/mol": "j_mol",
    "kJ/mol": "kj_mol",
    "cal/mol": "cal_mol",
    "kcal/mol": "kcal_mol",
}


def parse_arkane_kinetics(text: str) -> ArkaneKinetics:
    """Parse the ``kinetics(...)`` block from Arkane output.py text.

    The block looks like::

        kinetics(
            label = '...',
            kinetics = Arrhenius(
                A = (1.18095e-06, 'cm^3/(mol*s)'),
                n = 4.78345,
                Ea = (16.6022, 'kJ/mol'),
                T0 = (1, 'K'),
                Tmin = (300, 'K'),
                Tmax = (3000, 'K'),
                comment = '...',
            ),
        )
    """
    # Find the kinetics(...) block — take the last one in the file
    # Use a simple approach: find "kinetics(" at the start of a line
    blocks = list(re.finditer(r"^kinetics\(", text, re.MULTILINE))
    if not blocks:
        raise ValueError("No kinetics() block found in Arkane output.")

    block_start = blocks[-1].start()
    block_text = text[block_start:]

    # Extract label
    label_m = re.search(r"label\s*=\s*['\"](.+?)['\"]", block_text)
    label = label_m.group(1) if label_m else ""

    # Extract A = (value, 'units')
    a_m = re.search(r"A\s*=\s*\(\s*([-\d.eE+]+)\s*,\s*['\"](.+?)['\"]\s*\)", block_text)
    if not a_m:
        raise ValueError("Could not parse A parameter from kinetics block.")
    a_val = float(a_m.group(1))
    a_units = a_m.group(2)

    # Extract n = value
    n_m = re.search(r"\bn\s*=\s*([-\d.eE+]+)", block_text)
    if not n_m:
        raise ValueError("Could not parse n parameter from kinetics block.")
    n_val = float(n_m.group(1))

    # Extract Ea = (value, 'units')
    ea_m = re.search(r"Ea\s*=\s*\(\s*([-\d.eE+]+)\s*,\s*['\"](.+?)['\"]\s*\)", block_text)
    if not ea_m:
        raise ValueError("Could not parse Ea parameter from kinetics block.")
    ea_val = float(ea_m.group(1))
    ea_units = ea_m.group(2)

    # Extract Tmin = (value, 'K')
    tmin_m = re.search(r"Tmin\s*=\s*\(\s*([-\d.eE+]+)\s*,\s*['\"]K['\"]\s*\)", block_text)
    tmin_k = float(tmin_m.group(1)) if tmin_m else 300.0

    # Extract Tmax = (value, 'K')
    tmax_m = re.search(r"Tmax\s*=\s*\(\s*([-\d.eE+]+)\s*,\s*['\"]K['\"]\s*\)", block_text)
    tmax_k = float(tmax_m.group(1)) if tmax_m else 3000.0

    # Extract comment
    comment_m = re.search(r"comment\s*=\s*['\"](.+?)['\"]", block_text, re.DOTALL)
    comment = comment_m.group(1).strip() if comment_m else None

    return ArkaneKinetics(
        label=label,
        a=a_val,
        a_units=a_units,
        n=n_val,
        ea=ea_val,
        ea_units=ea_units,
        tmin_k=tmin_k,
        tmax_k=tmax_k,
        comment=comment,
    )


def parse_arkane_kinetics_from_file(path: str | Path) -> ArkaneKinetics:
    text = Path(path).read_text()
    return parse_arkane_kinetics(text)


def map_a_units(raw: str) -> str:
    """Map Arkane A-units string to TCKDB ArrheniusAUnits enum value."""
    token = _A_UNITS_MAP.get(raw)
    if token is None:
        raise ValueError(f"Unknown A-units: {raw!r}. Known: {list(_A_UNITS_MAP)}")
    return token


def map_ea_units(raw: str) -> str:
    """Map Arkane Ea-units string to TCKDB ActivationEnergyUnits enum value."""
    token = _EA_UNITS_MAP.get(raw)
    if token is None:
        raise ValueError(f"Unknown Ea-units: {raw!r}. Known: {list(_EA_UNITS_MAP)}")
    return token

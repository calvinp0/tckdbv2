from __future__ import annotations

from enum import Enum


class MoleculeKind(str, Enum):
    molecule = "molecule"
    pseudo = "pseudo"


class StationaryPointKind(str, Enum):
    conformer = "conformer"
    minimum = "minimum"
    vdw_complex = "vdw_complex"


class ScientificOriginKind(str, Enum):
    computed = "computed"
    experimental = "experimental"
    estimated = "estimated"


class ContributorRole(str, Enum):
    submitted = "submitted"
    curated = "curated"
    computed = "computed"
    linked = "linked"


class ReactionRole(str, Enum):
    reactant = "reactant"
    product = "product"


class CalculationType(str, Enum):
    opt = "opt"
    freq = "freq"
    sp = "sp"
    irc = "irc"
    scan = "scan"
    neb = "neb"
    conf = "conf"


class CalculationQuality(str, Enum):
    raw = "raw"
    curated = "curated"
    rejected = "rejected"


class ArtifactKind(str, Enum):
    input = "input"
    output_log = "output_log"
    checkpoint = "checkpoint"
    formatted_checkpoint = "formatted_checkpoint"
    ancillary = "ancillary"


class TransitionStateEntryStatus(str, Enum):
    guess = "guess"
    optimized = "optimized"
    validated = "validated"
    rejected = "rejected"


class ThermoCalculationRole(str, Enum):
    opt = "opt"
    freq = "freq"
    sp = "sp"
    composite = "composite"
    imported = "imported"


class KineticsModelKind(str, Enum):
    arrhenius = "arrhenius"
    modified_arrhenius = "modified_arrhenius"


class KineticsCalculationRole(str, Enum):
    reactant_energy = "reactant_energy"
    product_energy = "product_energy"
    ts_energy = "ts_energy"
    freq = "freq"
    irc = "irc"
    master_equation = "master_equation"
    fit_source = "fit_source"


class NetworkSpeciesRole(str, Enum):
    well = "well"
    reactant = "reactant"
    product = "product"
    bath_gas = "bath_gas"


class LiteratureKind(str, Enum):
    article = "article"
    book = "book"
    thesis = "thesis"
    report = "report"
    dataset = "dataset"
    webpage = "webpage"


class AppUserRole(str, Enum):
    user = "user"
    curator = "curator"
    admin = "admin"

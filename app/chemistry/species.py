from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import inchi

from app.db.models.common import MoleculeKind
from app.schemas.fragments.identity import SpeciesEntryIdentityPayload


def formal_charge(mol: Chem.Mol) -> int:
    """Return the total formal charge of an RDKit molecule.

    :param mol: RDKit molecule to inspect.
    :returns: Sum of per-atom formal charges.
    """

    return sum(atom.GetFormalCharge() for atom in mol.GetAtoms())


def spin_multiplicity(mol: Chem.Mol) -> int:
    """Estimate spin multiplicity from radical electrons.

    :param mol: RDKit molecule to inspect.
    :returns: ``total_radical_electrons + 1``.
    """

    total_radicals = sum(atom.GetNumRadicalElectrons() for atom in mol.GetAtoms())
    return total_radicals + 1


def identity_mol_from_smiles(smiles: str) -> Chem.Mol:
    """Build a canonicalized identity molecule from SMILES.

    :param smiles: Input SMILES string for the uploaded species identity.
    :returns: Sanitized RDKit molecule with atom maps removed and hydrogens stripped.
    :raises ValueError: If RDKit cannot parse the SMILES string.
    """

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("RDKit failed to parse species_entry.smiles")

    ident = Chem.Mol(mol)
    for atom in ident.GetAtoms():
        atom.SetAtomMapNum(0)
    ident = Chem.RemoveHs(ident)
    Chem.SanitizeMol(ident)
    return ident


def canonical_species_identity(
    payload: SpeciesEntryIdentityPayload,
) -> tuple[str, str]:
    """Canonicalize upload identity data into species-level keys.

    :param payload: Upload-facing species-entry identity payload.
    :returns: ``(canonical_smiles, inchi_key)`` for the graph identity.
    :raises ValueError:
        If the payload is not a supported molecule upload or if the stated
        charge/multiplicity disagrees with the parsed SMILES identity.
    """

    if payload.molecule_kind != MoleculeKind.molecule:
        raise ValueError("Conformer upload currently supports only molecule species")

    ident = identity_mol_from_smiles(payload.smiles)
    charge = formal_charge(ident)
    multiplicity = spin_multiplicity(ident)

    if charge != payload.charge:
        raise ValueError(
            f"species_entry.charge={payload.charge} does not match SMILES charge {charge}"
        )
    if multiplicity != payload.multiplicity:
        raise ValueError(
            "species_entry.multiplicity does not match multiplicity implied by SMILES"
        )

    canonical_smiles = Chem.MolToSmiles(ident, canonical=True)
    inchi_key = inchi.MolToInchiKey(ident)
    return canonical_smiles, inchi_key

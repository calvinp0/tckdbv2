"""Workflow orchestrator for the computed reaction upload.

Processes one complete Arkane-style kinetics run in a single transaction:
species → conformers → calculations → reaction → TS → thermo → kinetics fits.

Follows the same key-resolution pattern as the network PDep workflow.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

import app.db.models  # noqa: F401
from app.chemistry.geometry import parse_xyz
from app.chemistry.units import convert_ea_to_kj_mol
from app.db.models.calculation import Calculation, CalculationOutputGeometry
from app.db.models.common import (
    CalculationGeometryRole,
    CalculationType,
    KineticsCalculationRole,
    ReactionRole,
)
from app.db.models.kinetics import Kinetics, KineticsSourceCalculation
from app.db.models.reaction import ReactionEntry, ReactionEntryStructureParticipant
from app.db.models.species import ConformerObservation
from app.db.models.thermo import Thermo, ThermoNASA, ThermoPoint
from app.db.models.transition_state import TransitionState, TransitionStateEntry
from app.schemas.workflows.computed_reaction_upload import ComputedReactionUploadRequest
from app.schemas.workflows.network_pdep_upload import CalculationIn
from app.schemas.workflows.reaction_upload import ReactionUploadRequest
from app.services.calculation_resolution import (
    resolve_level_of_theory_ref,
    resolve_software_release_ref,
    resolve_workflow_tool_release_ref,
)
from app.services.conformer_resolution import resolve_conformer_group
from app.services.geometry_resolution import resolve_geometry_payload
from app.services.kinetics_resolution import resolve_kinetics_upload
from app.services.literature_resolution import resolve_or_create_literature
from app.services.reaction_resolution import (
    compress_species_stoichiometry,
    resolve_chem_reaction,
)
from app.services.species_resolution import resolve_species_entry
from app.schemas.fragments.geometry import GeometryPayload
from app.schemas.workflows.kinetics_upload import (
    KineticsReactionParticipantUpload,
    KineticsReactionUpload,
    KineticsUploadRequest,
)


def _persist_calculation(
    session: Session,
    calc_in: CalculationIn,
    *,
    species_entry_id: int | None = None,
    transition_state_entry_id: int | None = None,
    geometry_id: int | None = None,
    geometry_key_map: dict[str, int],
    created_by: int | None = None,
) -> Calculation:
    """Create a calculation row with optional result and geometry link.

    Reuses the same pattern as the network_pdep workflow.
    """
    software_release = resolve_software_release_ref(session, calc_in.software_release)
    lot = resolve_level_of_theory_ref(session, calc_in.level_of_theory)
    workflow_tool_release = resolve_workflow_tool_release_ref(
        session, calc_in.workflow_tool_release
    )

    calculation = Calculation(
        type=calc_in.type,
        species_entry_id=species_entry_id,
        transition_state_entry_id=transition_state_entry_id,
        software_release_id=software_release.id,
        lot_id=lot.id,
        workflow_tool_release_id=(
            workflow_tool_release.id if workflow_tool_release else None
        ),
        created_by=created_by,
    )
    session.add(calculation)
    session.flush()

    # Inline results
    from app.db.models.calculation import (
        CalculationFreqResult,
        CalculationOptResult,
        CalculationSPResult,
    )

    if calc_in.sp_electronic_energy_hartree is not None:
        session.add(
            CalculationSPResult(
                calculation_id=calculation.id,
                electronic_energy_hartree=calc_in.sp_electronic_energy_hartree,
            )
        )
    if calc_in.opt_converged is not None or calc_in.opt_final_energy_hartree is not None:
        session.add(
            CalculationOptResult(
                calculation_id=calculation.id,
                converged=calc_in.opt_converged,
                n_steps=calc_in.opt_n_steps,
                final_energy_hartree=calc_in.opt_final_energy_hartree,
            )
        )
    if calc_in.freq_n_imag is not None or calc_in.freq_imag_freq_cm1 is not None:
        session.add(
            CalculationFreqResult(
                calculation_id=calculation.id,
                n_imag=calc_in.freq_n_imag,
                imag_freq_cm1=calc_in.freq_imag_freq_cm1,
                zpe_hartree=calc_in.freq_zpe_hartree,
            )
        )

    # Geometry link
    resolved_geom_id = geometry_id
    if calc_in.geometry_key is not None:
        resolved_geom_id = geometry_key_map.get(calc_in.geometry_key, geometry_id)

    if resolved_geom_id is not None:
        session.add(
            CalculationOutputGeometry(
                calculation_id=calculation.id,
                geometry_id=resolved_geom_id,
                output_order=1,
                role=CalculationGeometryRole.final,
            )
        )

    return calculation


def persist_computed_reaction_upload(
    session: Session,
    request: ComputedReactionUploadRequest,
    *,
    created_by: int | None = None,
) -> dict:
    """Persist a complete computed reaction upload in one transaction.

    Returns a summary dict with the created row IDs.
    """

    # Key → resolved object maps
    species_key_to_entry: dict[str, object] = {}
    geometry_key_to_id: dict[str, int] = {}
    calculation_key_to_id: dict[str, int] = {}

    # ------------------------------------------------------------------
    # 1. Resolve species + conformers + calculations
    # ------------------------------------------------------------------
    for sp in request.species:
        species_entry = resolve_species_entry(
            session, sp.species_entry, created_by=created_by
        )
        species_key_to_entry[sp.key] = species_entry

        # Conformers
        for conf in sp.conformers:
            geom_payload = GeometryPayload(xyz_text=conf.geometry.xyz_text)
            geometry = resolve_geometry_payload(session, geom_payload)
            geometry_key_to_id[conf.geometry.key] = geometry.id

            calculation = _persist_calculation(
                session,
                conf.calculation,
                species_entry_id=species_entry.id,
                geometry_id=geometry.id,
                geometry_key_map=geometry_key_to_id,
                created_by=created_by,
            )
            calculation_key_to_id[conf.calculation.key] = calculation.id

            parsed = parse_xyz(GeometryPayload(xyz_text=conf.geometry.xyz_text))
            conformer_group, fingerprint, scheme = resolve_conformer_group(
                session, species_entry, label=conf.label, created_by=created_by,
                smiles=sp.species_entry.smiles, xyz_atoms=parsed.atoms,
            )
            observation = ConformerObservation(
                conformer_group_id=conformer_group.id,
                calculation_id=calculation.id,
                scientific_origin=conf.scientific_origin,
                note=conf.note,
                created_by=created_by,
                assignment_scheme_id=scheme.id if scheme else None,
                torsion_fingerprint_json=(
                    fingerprint.to_dict() if fingerprint else None
                ),
            )
            session.add(observation)
            session.flush()

            # Anchor primary calc to this conformer observation
            calculation.conformer_observation_id = observation.id

        # Additional calculations (freq, sp at higher LOT)
        for calc_in in sp.calculations:
            calculation = _persist_calculation(
                session,
                calc_in,
                species_entry_id=species_entry.id,
                geometry_key_map=geometry_key_to_id,
                created_by=created_by,
            )
            calculation_key_to_id[calc_in.key] = calculation.id

            # Anchor additional calcs to the conformer observation too
            # (auto-resolve if exactly one exists for this species entry)
            if sp.conformers:
                # The last conformer observation created for this species
                calculation.conformer_observation_id = observation.id

    session.flush()

    # ------------------------------------------------------------------
    # 2. Resolve reaction
    # ------------------------------------------------------------------
    reactant_entries = [species_key_to_entry[k] for k in request.reactant_keys]
    product_entries = [species_key_to_entry[k] for k in request.product_keys]

    chem_reaction = resolve_chem_reaction(
        session,
        reversible=request.reversible,
        reaction_family=request.reaction_family,
        reaction_family_source_note=request.reaction_family_source_note,
        reactant_stoichiometry=compress_species_stoichiometry(reactant_entries),
        product_stoichiometry=compress_species_stoichiometry(product_entries),
    )

    # We create one reaction entry for the bundle's canonical direction
    canonical_reaction_entry = ReactionEntry(
        reaction_id=chem_reaction.id, created_by=created_by
    )
    session.add(canonical_reaction_entry)
    session.flush()

    for idx, key in enumerate(request.reactant_keys, start=1):
        session.add(
            ReactionEntryStructureParticipant(
                reaction_entry_id=canonical_reaction_entry.id,
                species_entry_id=species_key_to_entry[key].id,
                role=ReactionRole.reactant,
                participant_index=idx,
                created_by=created_by,
            )
        )
    for idx, key in enumerate(request.product_keys, start=1):
        session.add(
            ReactionEntryStructureParticipant(
                reaction_entry_id=canonical_reaction_entry.id,
                species_entry_id=species_key_to_entry[key].id,
                role=ReactionRole.product,
                participant_index=idx,
                created_by=created_by,
            )
        )
    session.flush()

    # ------------------------------------------------------------------
    # 3. Transition state (optional)
    # ------------------------------------------------------------------
    ts_entry = None
    if request.transition_state:
        ts_in = request.transition_state
        ts = TransitionState(
            reaction_entry_id=canonical_reaction_entry.id,
            label=ts_in.label,
            note=ts_in.note,
            created_by=created_by,
        )
        session.add(ts)
        session.flush()

        ts_entry = TransitionStateEntry(
            transition_state_id=ts.id,
            charge=ts_in.charge,
            multiplicity=ts_in.multiplicity,
            unmapped_smiles=ts_in.unmapped_smiles,
            created_by=created_by,
        )
        session.add(ts_entry)
        session.flush()

        ts_geom = resolve_geometry_payload(
            session, GeometryPayload(xyz_text=ts_in.geometry.xyz_text)
        )
        geometry_key_to_id[ts_in.geometry.key] = ts_geom.id

        ts_calc = _persist_calculation(
            session,
            ts_in.calculation,
            transition_state_entry_id=ts_entry.id,
            geometry_id=ts_geom.id,
            geometry_key_map=geometry_key_to_id,
            created_by=created_by,
        )
        calculation_key_to_id[ts_in.calculation.key] = ts_calc.id

        for calc_in in ts_in.calculations:
            calc = _persist_calculation(
                session,
                calc_in,
                transition_state_entry_id=ts_entry.id,
                geometry_key_map=geometry_key_to_id,
                created_by=created_by,
            )
            calculation_key_to_id[calc_in.key] = calc.id

    # ------------------------------------------------------------------
    # 4. Thermo (per species, if provided)
    # ------------------------------------------------------------------
    thermo_ids = []
    for sp in request.species:
        if sp.thermo is not None:
            species_entry = species_key_to_entry[sp.key]
            t = sp.thermo

            thermo = Thermo(
                species_entry_id=species_entry.id,
                scientific_origin=t.scientific_origin,
                h298_kj_mol=t.h298_kj_mol,
                s298_j_mol_k=t.s298_j_mol_k,
                tmin_k=t.tmin_k,
                tmax_k=t.tmax_k,
                note=t.note,
                created_by=created_by,
            )
            session.add(thermo)
            session.flush()
            thermo_ids.append(thermo.id)

            if t.nasa is not None:
                session.add(ThermoNASA(thermo_id=thermo.id, **t.nasa.model_dump()))

            for pt in t.points:
                session.add(ThermoPoint(thermo_id=thermo.id, **pt.model_dump()))

    session.flush()

    # ------------------------------------------------------------------
    # 5. Kinetics fits
    # ------------------------------------------------------------------
    kinetics_ids = []
    for kin in request.kinetics:
        # Each kinetics fit may have a different direction (fwd/rev),
        # so it gets its own reaction entry with the correct participant order.
        kin_reactant_entries = [species_key_to_entry[k] for k in kin.reactant_keys]
        kin_product_entries = [species_key_to_entry[k] for k in kin.product_keys]

        kin_chem_rxn = resolve_chem_reaction(
            session,
            reversible=request.reversible,
            reaction_family=request.reaction_family,
            reaction_family_source_note=request.reaction_family_source_note,
            reactant_stoichiometry=compress_species_stoichiometry(kin_reactant_entries),
            product_stoichiometry=compress_species_stoichiometry(kin_product_entries),
        )

        kin_entry = ReactionEntry(
            reaction_id=kin_chem_rxn.id, created_by=created_by
        )
        session.add(kin_entry)
        session.flush()

        for idx, key in enumerate(kin.reactant_keys, start=1):
            session.add(
                ReactionEntryStructureParticipant(
                    reaction_entry_id=kin_entry.id,
                    species_entry_id=species_key_to_entry[key].id,
                    role=ReactionRole.reactant,
                    participant_index=idx,
                    created_by=created_by,
                )
            )
        for idx, key in enumerate(kin.product_keys, start=1):
            session.add(
                ReactionEntryStructureParticipant(
                    reaction_entry_id=kin_entry.id,
                    species_entry_id=species_key_to_entry[key].id,
                    role=ReactionRole.product,
                    participant_index=idx,
                    created_by=created_by,
                )
            )
        session.flush()

        ea_kj_mol = (
            convert_ea_to_kj_mol(kin.reported_ea, kin.reported_ea_units)
            if kin.reported_ea is not None
            else None
        )

        # Resolve bundle-level provenance
        literature = (
            resolve_or_create_literature(session, request.literature)
            if request.literature is not None
            else None
        )
        software_release = (
            resolve_software_release_ref(session, request.software_release)
            if request.software_release is not None
            else None
        )
        workflow_tool_release = resolve_workflow_tool_release_ref(
            session, request.workflow_tool_release
        )

        kinetics = Kinetics(
            reaction_entry_id=kin_entry.id,
            scientific_origin=kin.scientific_origin,
            model_kind=kin.model_kind,
            literature_id=literature.id if literature else None,
            software_release_id=software_release.id if software_release else None,
            workflow_tool_release_id=(
                workflow_tool_release.id if workflow_tool_release else None
            ),
            a=kin.a,
            a_units=kin.a_units,
            n=kin.n,
            ea_kj_mol=ea_kj_mol,
            tmin_k=kin.tmin_k,
            tmax_k=kin.tmax_k,
            tunneling_model=kin.tunneling_model,
            note=kin.note,
            created_by=created_by,
        )
        session.add(kinetics)
        session.flush()
        kinetics_ids.append(kinetics.id)

        # Auto-link SP source calculations for each participant
        # Find SPs at the highest LOT available on each species
        for key, role in [
            *[(k, KineticsCalculationRole.reactant_energy) for k in kin.reactant_keys],
            *[(k, KineticsCalculationRole.product_energy) for k in kin.product_keys],
        ]:
            se = species_key_to_entry[key]
            # Find SP calcs created for this species in this bundle
            sp_calc_ids = [
                cid
                for ckey, cid in calculation_key_to_id.items()
                if any(
                    c.key == ckey and c.type == CalculationType.sp
                    for sp in request.species
                    if sp.key == key
                    for c in sp.calculations
                )
            ]
            if sp_calc_ids:
                # Link the first SP found (unambiguous within one bundle)
                session.add(
                    KineticsSourceCalculation(
                        kinetics_id=kinetics.id,
                        calculation_id=sp_calc_ids[0],
                        role=role,
                    )
                )

    session.flush()

    return {
        "reaction_entry_id": canonical_reaction_entry.id,
        "reaction_id": chem_reaction.id,
        "transition_state_entry_id": ts_entry.id if ts_entry else None,
        "kinetics_ids": kinetics_ids,
        "thermo_ids": thermo_ids,
        "species_entry_ids": [e.id for e in species_key_to_entry.values()],
        "species_count": len(request.species),
    }

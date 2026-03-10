"""create intial schema

Revision ID: d861dfd60891
Revises: 60b67e360daf
Create Date: 2026-03-07 20:04:50.330495

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d861dfd60891"
down_revision: Union[str, Sequence[str], None] = "60b67e360daf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # enums
    op.execute("""
               CREATE TYPE molecule_kind AS ENUM ('molecule', 'pseudo');
               """)

    op.execute("""
               CREATE TYPE stationary_point_kind AS ENUM ('conformer',
                                                          'minimum',
                                                          'vdw_complex');
               
               """)

    op.execute("""
               CREATE TYPE scientific_origin_kind AS ENUM ('computed',
                                                          'experimental',
                                                          'estimated');
               
               """)

    op.execute("""
               CREATE TYPE contributor_role AS ENUM ('submitted',
                                                     'curated',
                                                     'computed',
                                                     'linked');
               
               """)

    op.execute("""
               CREATE TYPE reaction_role AS ENUM ('reactant',
                                                  'product');
                                         """)

    op.execute("""
               CREATE TYPE calc_type AS ENUM ('opt',
                                              'freq',
                                              'sp',
                                              'irc',
                                              'scan',
                                              'neb',
                                              'conf');
               
               """)

    op.execute("""
               CREATE TYPE calculation_quality AS ENUM ('raw',
                                              'curated',
                                              'rejected');

               """)

    op.execute("""
               CREATE TYPE calc_geom_role AS ENUM ('initial',
                                                   'final',
                                                   'intermediate',
                                                   'scan_point',
                                                   'irc_forward',
                                                   'irc_reverse',
                                                   'neb_image');

               """)

    op.execute("""
               CREATE TYPE calc_dependency_role AS ENUM ('optimized_from',
                                                         'freq_on',
                                                         'single_point_on',
                                                         'arkane_source',
                                                         'irc_start',
                                                         'irc_followup',
                                                         'scan_parent',
                                                         'neb_parent');

               """)

    op.execute("""
               CREATE TYPE artifact_kind AS ENUM ('input',
                                                     'output_log',
                                                     'checkpoint',
                                                     'formatted_checkpoint',
                                                     'ancillary');
               
               """)

    op.execute("""
                CREATE TYPE thermo_calc_role AS ENUM (
                    'opt',
                    'freq',
                    'sp',
                    'composite',
                        'imported'
                    );
               """)

    op.execute("""
CREATE TYPE kinetics_model_kind AS ENUM (
  'arrhenius',
  'modified_arrhenius'
                    );
               """)

    op.execute("""
        CREATE TYPE kinetics_calc_role AS ENUM (
  'reactant_energy',
  'product_energy',
  'ts_energy',
  'freq',
  'irc',
  'master_equation',
  'fit_source'
);
        """)

    op.execute("""
        CREATE TYPE network_species_role AS ENUM (
  'well',
  'reactant',
  'product',
  'bath_gas'
);
        """)

    op.execute("""
CREATE TYPE literature_kind AS ENUM (
  'article',
  'book',
  'thesis',
  'report',
  'dataset',
  'webpage'
);
        """)

    op.execute("""
CREATE TYPE app_user_role AS ENUM (
  'user',
  'curator',
  'admin'
);
        """)
    op.execute("""
CREATE TYPE transition_state_entry_status AS ENUM (
  'guess',
  'optimized',
  'validated',
  'rejected'
);
        """)

    # base tables
    op.execute("""
CREATE TABLE species (
  "id" integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "kind" molecule_kind NOT NULL,
  "smiles" text NOT NULL,
  "inchi_key" char(27) NOT NULL,
  "charge" smallint NOT NULL,
  "multiplicity" smallint NOT NULL,
  "created_at" timestamp NOT NULL DEFAULT now()
);           
           """)

    # dependent tables
    op.execute("""
CREATE TABLE "species_entry" (
  "id" integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "species_id" integer NOT NULL,
  "kind" stationary_point_kind NOT NULL,
  "mol" mol,
  "preferred_calculation_id" bigint,
  "created_by" bigint,
  "created_at" timestamp NOT NULL DEFAULT now()
);
               """)

    op.execute("""so 
           CREATE TABLE "transport" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "species_id" integer NOT NULL,
  "scientific_origin" scientific_origin_kind NOT NULL,
  "literature_id" bigint,
  "software_id" bigint,
  "workflow_tool_id" bigint,
  "sigma_angstrom" DOUBLE PRECISION,
  "epsilon_over_k_k" DOUBLE PRECISION,
  "dipole_debye" DOUBLE PRECISION,
  "polarizability_angstrom3" DOUBLE PRECISION,
  "rotational_relaxation" DOUBLE PRECISION,
  "note" text,
  "created_by" bigint,
  "created_at" timestamp
);
           """)

    op.execute("""
CREATE TABLE "species_entry_contributor" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "species_entry_id" integer NOT NULL,
  "user_id" bigint NOT NULL,
  "role" contributor_role NOT NULL,
  "created_at" timestamp
);""")
    op.execute("""
CREATE TABLE "geometry" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "natoms" int NOT NULL,
  "geom_hash" char(64) NOT NULL,
  "xyz_text" text,
  "created_at" timestamp
);""")
    op.execute("""
CREATE TABLE "geometry_atom" (
  "geometry_id" bigint NOT NULL,
  "atom_index" int NOT NULL,
  "element" char(2) NOT NULL,
  "x" DOUBLE PRECISION NOT NULL,
  "y" DOUBLE PRECISION NOT NULL,
  "z" DOUBLE PRECISION NOT NULL,
  PRIMARY KEY ("geometry_id", "atom_index")
);""")
    op.execute("""
CREATE TABLE "chem_reaction" (
  "id" integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "stoichiometry_hash" char(64) UNIQUE,
  "reversible" BOOLEAN NOT NULL,
  "created_at" timestamp
);""")
    op.execute("""
CREATE TABLE "reaction_participant" (
  "reaction_id" integer,
  "species_id" integer,
  "role" reaction_role NOT NULL,
  "stoichiometry" smallint NOT NULL,
  PRIMARY KEY ("reaction_id", "species_id", "role")
);""")
    op.execute("""
CREATE TABLE "reaction_entry" (
  "id" integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "reaction_id" integer NOT NULL,
  "preferred_ts_entry_id" bigint,
  "created_by" bigint,
  "created_at" timestamp
);""")
    op.execute("""
CREATE TABLE "transition_state" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "reaction_entry_id" integer NOT NULL,
  "label" text,
  "note" text,
  "created_by" bigint,
  "created_at" timestamp
);""")
    op.execute("""
CREATE TABLE "transition_state_entry" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "transition_state_id" bigint NOT NULL,
  "mol" mol,
  "unmapped_smiles" text,
  "preferred_calculation_id" bigint,
  "status" transition_state_entry_status NOT NULL DEFAULT 'optimized',
  "created_by" bigint,
  "created_at" timestamp
);""")
    op.execute("""
CREATE TABLE "software" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "name" text NOT NULL,
  "version" text,
  "build" text,
  "created_at" timestamp
);""")
    op.execute("""
CREATE TABLE "level_of_theory" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "method" text NOT NULL,
  "basis" text,
  "aux_basis" text,
  "dispersion" text,
  "solvent" text,
  "solvent_model" text,
  "keywords" text,
  "lot_hash" char(64) NOT NULL,
  "created_at" timestamp
);""")
    op.execute("""
CREATE TABLE "calculation" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "type" calc_type NOT NULL,
  "quality" calculation_quality NOT NULL DEFAULT 'raw',
  "species_entry_id" integer,
  "transition_state_entry_id" bigint,
  "software_id" bigint,
  "workflow_tool_id" bigint,
  "lot_id" bigint,
  "literature_id" bigint,
  "created_by" bigint,
  "created_at" timestamp NOT NULL DEFAULT now(),
  CONSTRAINT "ck_calculation_exactly_one_owner" CHECK (
    ("species_entry_id" IS NOT NULL AND "transition_state_entry_id" IS NULL)
    OR
    ("species_entry_id" IS NULL AND "transition_state_entry_id" IS NOT NULL)
  )
);""")
    op.execute("""
CREATE TABLE "calculation_output_geometry" (
  "calculation_id" bigint NOT NULL,
  "geometry_id" bigint NOT NULL,
  "output_order" int NOT NULL DEFAULT 1,
  "role" calc_geom_role,
  PRIMARY KEY ("calculation_id", "output_order"),
  CONSTRAINT "uq_calculation_output_geometry_calculation_id" UNIQUE ("calculation_id", "geometry_id")
);""")
    op.execute("""
CREATE TABLE "calculation_dependency" (
  "parent_calculation_id" bigint NOT NULL,
  "child_calculation_id" bigint NOT NULL,
  "dependency_role" calc_dependency_role,
  PRIMARY KEY ("parent_calculation_id", "child_calculation_id"),
  CHECK ("parent_calculation_id" <> "child_calculation_id")
);""")
    op.execute("""
CREATE TABLE "calc_sp_result" (
  "calculation_id" bigint PRIMARY KEY,
  "electronic_energy_hartree" DOUBLE PRECISION
);""")
    op.execute("""
CREATE TABLE "calc_opt_result" (
  "calculation_id" bigint PRIMARY KEY,
  "converged" BOOLEAN,
  "n_steps" int,
  "final_energy_hartree" DOUBLE PRECISION
);""")
    op.execute("""
CREATE TABLE "calc_freq_results" (
  "calculation_id" bigint PRIMARY KEY,
  "n_imag" int,
  "img_freq_cm1" DOUBLE PRECISION,
  "zpe_hartree" DOUBLE PRECISION
);""")
    op.execute("""
CREATE TABLE "calculation_artifact" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "calculation_id" bigint NOT NULL,
  "kind" artifact_kind NOT NULL,
  "uri" text NOT NULL,
  "sha256" char(64),
  "bytes" bigint,
  "created_at" timestamp
);""")
    op.execute("""
CREATE TABLE "thermo" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "species_entry_id" integer NOT NULL,
  "scientific_origin" scientific_origin_kind NOT NULL,
  "literature_id" bigint,
  "workflow_tool_id" bigint,
  "software_id" bigint,
  "created_by" bigint,
  "created_at" timestamp,
  "h298_kj_mol" DOUBLE PRECISION,
  "s298_j_mol_k" DOUBLE PRECISION,
  "note" text
);""")
    op.execute("""
CREATE TABLE "thermo_point" (
  "thermo_id" bigint NOT NULL,
  "temperature_k" DOUBLE PRECISION NOT NULL,
  "cp_j_mol_k" DOUBLE PRECISION,
  "h_kj_mol" DOUBLE PRECISION,
  "s_j_mol_k" DOUBLE PRECISION,
  "g_kj_mol" DOUBLE PRECISION,
  PRIMARY KEY ("thermo_id", "temperature_k")
);""")
    op.execute("""
CREATE TABLE "thermo_source_calculation" (
  "thermo_id" bigint NOT NULL,
  "calculation_id" bigint NOT NULL,
  "role" thermo_calc_role NOT NULL,
  PRIMARY KEY ("thermo_id", "calculation_id", "role")
);""")
    op.execute("""
CREATE TABLE "kinetics" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "reaction_entry_id" integer NOT NULL,
  "scientific_origin" scientific_origin_kind NOT NULL,
  "model_kind" kinetics_model_kind NOT NULL DEFAULT 'modified_arrhenius',
  "literature_id" bigint,
  "workflow_tool_id" bigint,
  "software_id" bigint,
  "created_by" bigint,
  "created_at" timestamp,
  "a" DOUBLE PRECISION,
  "a_units" text,
  "n" DOUBLE PRECISION,
  "ea_kj_mol" DOUBLE PRECISION,
  "tmin_k" DOUBLE PRECISION,
  "tmax_k" DOUBLE PRECISION,
  "degeneracy" DOUBLE PRECISION,
  "tunneling_model" text,
  "note" text
);""")
    op.execute("""
CREATE TABLE "kinetics_source_calculation" (
  "kinetics_id" bigint NOT NULL,
  "calculation_id" bigint NOT NULL,
  "role" kinetics_calc_role NOT NULL,
  PRIMARY KEY ("kinetics_id", "calculation_id", "role")
);""")
    op.execute("""
CREATE TABLE "network" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "name" text,
  "description" text,
  "literature_id" bigint,
  "software_id" bigint,
  "workflow_tool_id" bigint,
  "created_by" bigint,
  "created_at" timestamp
);""")
    op.execute("""
CREATE TABLE "network_reaction" (
  "network_id" bigint,
  "reaction_entry_id" integer,
  PRIMARY KEY ("network_id", "reaction_entry_id")
);""")
    op.execute("""
CREATE TABLE "network_species" (
  "network_id" bigint,
  "species_id" integer,
  "role" network_species_role,
  PRIMARY KEY ("network_id", "species_id")
);""")
    op.execute("""
CREATE TABLE "literature" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "kind" literature_kind NOT NULL,
  "title" text NOT NULL,
  "journal" text,
  "year" int,
  "volume" text,
  "issue" text,
  "pages" text,
  "doi" text,
  "isbn" text,
  "url" text,
  "publisher" text,
  "institution" text,
  "created_at" timestamp
);""")
    op.execute("""
CREATE TABLE "author" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "given_name" text,
  "family_name" text NOT NULL,
  "full_name" text NOT NULL,
  "orcid" char(19),
  "created_at" timestamp
);""")
    op.execute("""
CREATE TABLE "literature_author" (
  "literature_id" bigint NOT NULL,
  "author_id" bigint NOT NULL,
  "author_order" int NOT NULL
);""")
    op.execute("""
CREATE TABLE "workflow_tool" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "name" text NOT NULL,
  "version" text,
  "description" text,
  "created_at" timestamp
);""")
    op.execute("""
CREATE TABLE "app_user" (
  "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "username" text NOT NULL,
  "email" text,
  "full_name" text,
  "affiliation" text,
  "orcid" char(19),
  "role" app_user_role NOT NULL DEFAULT 'user',
  "created_at" timestamp
);""")
    # indexes
    op.execute("""
CREATE UNIQUE INDEX "species_inchi_key_uq" ON "species" ("inchi_key");""")
    op.execute(
        """
CREATE UNIQUE INDEX "species_entry_contrib_uq" ON "species_entry_contributor" ("species_entry_id", "user_id", "role");"""
    )
    op.execute("""
CREATE UNIQUE INDEX "geometry_geom_hash_uq" ON "geometry" USING btree ("geom_hash");""")
    op.execute("""
CREATE UNIQUE INDEX "software_name_version_uq" ON "software" ("name", "version");""")
    op.execute("""
CREATE UNIQUE INDEX "lot_hash_uq" ON "level_of_theory" ("lot_hash");""")
    op.execute(
        """
CREATE INDEX "calc_art_kind_idx" ON "calculation_artifact" ("calculation_id", "kind");"""
    )
    op.execute("""
CREATE INDEX "artifact_sha_idx" ON "calculation_artifact" ("sha256");""")
    op.execute("""
CREATE INDEX "literature_doi_idx" ON "literature" ("doi");""")
    op.execute("""
CREATE INDEX "literature_isbn_idx" ON "literature" ("isbn");""")
    op.execute(
        """
CREATE UNIQUE INDEX "literature_doi_uq" ON "literature" ("doi") WHERE "doi" IS NOT NULL;"""
    )
    op.execute(
        """
CREATE UNIQUE INDEX "literature_isbn_uq" ON "literature" ("isbn") WHERE "isbn" IS NOT NULL;"""
    )
    op.execute("""
CREATE UNIQUE INDEX "author_orcid_uq" ON "author" ("orcid");""")
    op.execute(
        """
CREATE UNIQUE INDEX "literature_author_order_uq" ON "literature_author" ("literature_id", "author_order");"""
    )
    op.execute(
        """
CREATE UNIQUE INDEX "literature_author_unique_uq" ON "literature_author" ("literature_id", "author_id");"""
    )
    op.execute(
        """
CREATE UNIQUE INDEX "workflow_tool_name_version_uq" ON "workflow_tool" ("name", "version");"""
    )
    op.execute("""
CREATE UNIQUE INDEX "app_user_username_uq" ON "app_user" ("username");""")
    op.execute("""
CREATE UNIQUE INDEX "app_user_email_uq" ON "app_user" ("email");""")
    op.execute("""
CREATE UNIQUE INDEX "app_user_orcid_uq" ON "app_user" ("orcid");""")
    # comments
    op.execute(
        """
COMMENT ON COLUMN "species_entry"."mol" IS 'rdkit cartridge representation of stationary-point identity';"""
    )
    op.execute("""
COMMENT ON COLUMN "geometry"."geom_hash" IS 'sha256 canonical XYZ';""")
    op.execute(
        """
COMMENT ON COLUMN "geometry"."xyz_text" IS 'original upload, good for hashing, and easy to return without round trip';"""
    )
    op.execute("""
COMMENT ON COLUMN "geometry_atom"."atom_index" IS '1..natoms';""")
    op.execute("""
COMMENT ON COLUMN "software"."build" IS 'optional';""")
    op.execute("""
COMMENT ON COLUMN "level_of_theory"."dispersion" IS 'D3BJ';""")
    op.execute("""
COMMENT ON COLUMN "level_of_theory"."solvent_model" IS 'smd, cpcm';""")
    op.execute("""
COMMENT ON COLUMN "level_of_theory"."keywords" IS 'optional';""")
    op.execute(
        """
COMMENT ON COLUMN "calculation_artifact"."uri" IS 'file:///data/tckdb/artifacts/..., s3://tckdb-prod/artifacts/..., gs://..., https://...';"""
    )
    op.execute(
        """
COMMENT ON COLUMN "transition_state_entry"."mol" IS 'rdkit cartridge representation of TS candidate identity';"""
    )
    op.execute(
        """
COMMENT ON COLUMN "transition_state_entry"."unmapped_smiles" IS 'canonical de-mapped TS string for display/search';"""
    )
    # foreign keys
    op.execute(
        """
ALTER TABLE "species_entry" ADD FOREIGN KEY ("species_id") REFERENCES "species" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "species_entry" ADD FOREIGN KEY ("preferred_calculation_id") REFERENCES "calculation" ("id") DEFERRABLE INITIALLY DEFERRED;"""
    )
    op.execute(
        """
ALTER TABLE "species_entry" ADD FOREIGN KEY ("created_by") REFERENCES "app_user" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "transport" ADD FOREIGN KEY ("species_id") REFERENCES "species" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "transport" ADD FOREIGN KEY ("literature_id") REFERENCES "literature" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "transport" ADD FOREIGN KEY ("software_id") REFERENCES "software" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "transport" ADD FOREIGN KEY ("workflow_tool_id") REFERENCES "workflow_tool" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "transport" ADD FOREIGN KEY ("created_by") REFERENCES "app_user" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "species_entry_contributor" ADD FOREIGN KEY ("species_entry_id") REFERENCES "species_entry" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "species_entry_contributor" ADD FOREIGN KEY ("user_id") REFERENCES "app_user" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "geometry_atom" ADD FOREIGN KEY ("geometry_id") REFERENCES "geometry" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "reaction_participant" ADD FOREIGN KEY ("reaction_id") REFERENCES "chem_reaction" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "reaction_participant" ADD FOREIGN KEY ("species_id") REFERENCES "species" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "reaction_entry" ADD FOREIGN KEY ("reaction_id") REFERENCES "chem_reaction" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "reaction_entry" ADD FOREIGN KEY ("preferred_ts_entry_id") REFERENCES "transition_state_entry" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "reaction_entry" ADD FOREIGN KEY ("created_by") REFERENCES "app_user" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calculation" ADD FOREIGN KEY ("species_entry_id") REFERENCES "species_entry" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calculation" ADD FOREIGN KEY ("transition_state_entry_id") REFERENCES "transition_state_entry" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calculation" ADD FOREIGN KEY ("software_id") REFERENCES "software" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "transition_state" ADD FOREIGN KEY ("reaction_entry_id") REFERENCES "reaction_entry" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "transition_state" ADD FOREIGN KEY ("created_by") REFERENCES "app_user" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "transition_state_entry" ADD FOREIGN KEY ("transition_state_id") REFERENCES "transition_state" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "transition_state_entry" ADD FOREIGN KEY ("preferred_calculation_id") REFERENCES "calculation" ("id") DEFERRABLE INITIALLY DEFERRED;"""
    )
    op.execute(
        """
ALTER TABLE "transition_state_entry" ADD FOREIGN KEY ("created_by") REFERENCES "app_user" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calculation" ADD FOREIGN KEY ("workflow_tool_id") REFERENCES "workflow_tool" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calculation" ADD FOREIGN KEY ("lot_id") REFERENCES "level_of_theory" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calculation" ADD FOREIGN KEY ("literature_id") REFERENCES "literature" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calculation" ADD FOREIGN KEY ("created_by") REFERENCES "app_user" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calc_sp_result" ADD FOREIGN KEY ("calculation_id") REFERENCES "calculation" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calc_opt_result" ADD FOREIGN KEY ("calculation_id") REFERENCES "calculation" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calc_freq_results" ADD FOREIGN KEY ("calculation_id") REFERENCES "calculation" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calculation_artifact" ADD FOREIGN KEY ("calculation_id") REFERENCES "calculation" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calculation_output_geometry" ADD FOREIGN KEY ("calculation_id") REFERENCES "calculation" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calculation_output_geometry" ADD FOREIGN KEY ("geometry_id") REFERENCES "geometry" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calculation_dependency" ADD FOREIGN KEY ("parent_calculation_id") REFERENCES "calculation" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "calculation_dependency" ADD FOREIGN KEY ("child_calculation_id") REFERENCES "calculation" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "thermo" ADD FOREIGN KEY ("species_entry_id") REFERENCES "species_entry" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "thermo" ADD FOREIGN KEY ("literature_id") REFERENCES "literature" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "thermo" ADD FOREIGN KEY ("workflow_tool_id") REFERENCES "workflow_tool" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "thermo" ADD FOREIGN KEY ("software_id") REFERENCES "software" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "thermo" ADD FOREIGN KEY ("created_by") REFERENCES "app_user" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "thermo_point" ADD FOREIGN KEY ("thermo_id") REFERENCES "thermo" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "thermo_source_calculation" ADD FOREIGN KEY ("thermo_id") REFERENCES "thermo" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "thermo_source_calculation" ADD FOREIGN KEY ("calculation_id") REFERENCES "calculation" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "kinetics" ADD FOREIGN KEY ("reaction_entry_id") REFERENCES "reaction_entry" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "kinetics" ADD FOREIGN KEY ("literature_id") REFERENCES "literature" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "kinetics" ADD FOREIGN KEY ("workflow_tool_id") REFERENCES "workflow_tool" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "kinetics" ADD FOREIGN KEY ("software_id") REFERENCES "software" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "kinetics" ADD FOREIGN KEY ("created_by") REFERENCES "app_user" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "kinetics_source_calculation" ADD FOREIGN KEY ("kinetics_id") REFERENCES "kinetics" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "kinetics_source_calculation" ADD FOREIGN KEY ("calculation_id") REFERENCES "calculation" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "network" ADD FOREIGN KEY ("literature_id") REFERENCES "literature" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "network" ADD FOREIGN KEY ("software_id") REFERENCES "software" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "network" ADD FOREIGN KEY ("workflow_tool_id") REFERENCES "workflow_tool" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "network" ADD FOREIGN KEY ("created_by") REFERENCES "app_user" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "network_reaction" ADD FOREIGN KEY ("network_id") REFERENCES "network" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "network_reaction" ADD FOREIGN KEY ("reaction_entry_id") REFERENCES "reaction_entry" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "network_species" ADD FOREIGN KEY ("network_id") REFERENCES "network" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "network_species" ADD FOREIGN KEY ("species_id") REFERENCES "species" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute(
        """
ALTER TABLE "literature_author" ADD FOREIGN KEY ("literature_id") REFERENCES "literature" ("id") DEFERRABLE INITIALLY IMMEDIATE;"""
    )
    op.execute("""
ALTER TABLE "literature_author" ADD FOREIGN KEY ("author_id") REFERENCES "author" ("id") DEFERRABLE INITIALLY IMMEDIATE;
""")


def downgrade() -> None:
    """Downgrade schema."""
    # Break FK cycles introduced by preferred-pointer links before dropping tables.
    op.execute(
        'ALTER TABLE "reaction_entry" DROP CONSTRAINT IF EXISTS "reaction_entry_preferred_ts_entry_id_fkey";'
    )
    op.execute(
        'ALTER TABLE "species_entry" DROP CONSTRAINT IF EXISTS "species_entry_preferred_calculation_id_fkey";'
    )
    op.execute(
        'ALTER TABLE "transition_state_entry" DROP CONSTRAINT IF EXISTS "transition_state_entry_preferred_calculation_id_fkey";'
    )

    # Drop tables in reverse dependency order.
    op.execute('DROP TABLE IF EXISTS "calculation_dependency";')
    op.execute('DROP TABLE IF EXISTS "calculation_output_geometry";')
    op.execute('DROP TABLE IF EXISTS "kinetics_source_calculation";')
    op.execute('DROP TABLE IF EXISTS "thermo_source_calculation";')
    op.execute('DROP TABLE IF EXISTS "thermo_point";')
    op.execute('DROP TABLE IF EXISTS "calc_freq_results";')
    op.execute('DROP TABLE IF EXISTS "calc_opt_result";')
    op.execute('DROP TABLE IF EXISTS "calc_sp_result";')
    op.execute('DROP TABLE IF EXISTS "calculation_artifact";')
    op.execute('DROP TABLE IF EXISTS "network_reaction";')
    op.execute('DROP TABLE IF EXISTS "network_species";')
    op.execute('DROP TABLE IF EXISTS "reaction_participant";')
    op.execute('DROP TABLE IF EXISTS "literature_author";')
    op.execute('DROP TABLE IF EXISTS "species_entry_contributor";')
    op.execute('DROP TABLE IF EXISTS "kinetics";')
    op.execute('DROP TABLE IF EXISTS "thermo";')
    op.execute('DROP TABLE IF EXISTS "calculation";')
    op.execute('DROP TABLE IF EXISTS "transition_state_entry";')
    op.execute('DROP TABLE IF EXISTS "transition_state";')
    op.execute('DROP TABLE IF EXISTS "reaction_entry";')
    op.execute('DROP TABLE IF EXISTS "transport";')
    op.execute('DROP TABLE IF EXISTS "network";')
    op.execute('DROP TABLE IF EXISTS "chem_reaction";')
    op.execute('DROP TABLE IF EXISTS "species_entry";')
    op.execute('DROP TABLE IF EXISTS "geometry_atom";')
    op.execute('DROP TABLE IF EXISTS "workflow_tool";')
    op.execute('DROP TABLE IF EXISTS "software";')
    op.execute('DROP TABLE IF EXISTS "level_of_theory";')
    op.execute('DROP TABLE IF EXISTS "literature";')
    op.execute('DROP TABLE IF EXISTS "author";')
    op.execute('DROP TABLE IF EXISTS "species";')
    op.execute('DROP TABLE IF EXISTS "geometry";')
    op.execute('DROP TABLE IF EXISTS "app_user";')

    # Drop enum types in reverse creation order.
    op.execute("DROP TYPE IF EXISTS transition_state_entry_status;")
    op.execute("DROP TYPE IF EXISTS app_user_role;")
    op.execute("DROP TYPE IF EXISTS literature_kind;")
    op.execute("DROP TYPE IF EXISTS network_species_role;")
    op.execute("DROP TYPE IF EXISTS kinetics_calc_role;")
    op.execute("DROP TYPE IF EXISTS kinetics_model_kind;")
    op.execute("DROP TYPE IF EXISTS thermo_calc_role;")
    op.execute("DROP TYPE IF EXISTS artifact_kind;")
    op.execute("DROP TYPE IF EXISTS calc_dependency_role;")
    op.execute("DROP TYPE IF EXISTS calc_geom_role;")
    op.execute("DROP TYPE IF EXISTS calculation_quality;")
    op.execute("DROP TYPE IF EXISTS calc_type;")
    op.execute("DROP TYPE IF EXISTS reaction_role;")
    op.execute("DROP TYPE IF EXISTS contributor_role;")
    op.execute("DROP TYPE IF EXISTS scientific_origin_kind;")
    op.execute("DROP TYPE IF EXISTS stationary_point_kind;")
    op.execute("DROP TYPE IF EXISTS molecule_kind;")

--
-- PostgreSQL database dump
--

\restrict Pjc0PLdNVvrseDo0MsHPJKxwLmS24j9kvh3pjPZ6EztUfSlgwKiBOuPaIp6BuT2

-- Dumped from database version 17.5 (Debian 17.5-1)
-- Dumped by pg_dump version 18.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'SQL_ASCII';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: tckdb
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO tckdb;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: tckdb
--

COMMENT ON SCHEMA public IS '';


--
-- Name: rdkit; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS rdkit WITH SCHEMA public;


--
-- Name: EXTENSION rdkit; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION rdkit IS 'Cheminformatics functionality for PostgreSQL.';


--
-- Name: app_user_role; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.app_user_role AS ENUM (
    'user',
    'curator',
    'admin'
);


ALTER TYPE public.app_user_role OWNER TO tckdb;

--
-- Name: artifact_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.artifact_kind AS ENUM (
    'input',
    'output_log',
    'checkpoint',
    'formatted_checkpoint',
    'ancillary'
);


ALTER TYPE public.artifact_kind OWNER TO tckdb;

--
-- Name: calc_quality; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.calc_quality AS ENUM (
    'raw',
    'curated',
    'rejected'
);


ALTER TYPE public.calc_quality OWNER TO tckdb;

--
-- Name: calc_type; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.calc_type AS ENUM (
    'opt',
    'freq',
    'sp',
    'irc',
    'scan',
    'neb',
    'conf'
);


ALTER TYPE public.calc_type OWNER TO tckdb;

--
-- Name: calculation_dependency_role; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.calculation_dependency_role AS ENUM (
    'optimized_from',
    'freq_on',
    'single_point_on',
    'arkane_source',
    'irc_start',
    'irc_followup',
    'scan_parent',
    'neb_parent'
);


ALTER TYPE public.calculation_dependency_role OWNER TO tckdb;

--
-- Name: calculation_geometry_role; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.calculation_geometry_role AS ENUM (
    'final',
    'initial',
    'scan_point',
    'irc_forward',
    'irc_reverse',
    'neb_image'
);


ALTER TYPE public.calculation_geometry_role OWNER TO tckdb;

--
-- Name: conformer_assignment_scope_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.conformer_assignment_scope_kind AS ENUM (
    'canonical',
    'imported',
    'experimental',
    'custom'
);


ALTER TYPE public.conformer_assignment_scope_kind OWNER TO tckdb;

--
-- Name: conformer_selection_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.conformer_selection_kind AS ENUM (
    'display_default',
    'curator_pick',
    'lowest_energy',
    'benchmark_reference',
    'preferred_for_thermo',
    'preferred_for_kinetics',
    'representative_geometry'
);


ALTER TYPE public.conformer_selection_kind OWNER TO tckdb;

--
-- Name: kinetics_calc_role; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.kinetics_calc_role AS ENUM (
    'reactant_energy',
    'product_energy',
    'ts_energy',
    'freq',
    'irc',
    'master_equation',
    'fit_source'
);


ALTER TYPE public.kinetics_calc_role OWNER TO tckdb;

--
-- Name: kinetics_model_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.kinetics_model_kind AS ENUM (
    'arrhenius',
    'modified_arrhenius'
);


ALTER TYPE public.kinetics_model_kind OWNER TO tckdb;

--
-- Name: literature_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.literature_kind AS ENUM (
    'article',
    'book',
    'thesis',
    'report',
    'dataset',
    'webpage'
);


ALTER TYPE public.literature_kind OWNER TO tckdb;

--
-- Name: molecule_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.molecule_kind AS ENUM (
    'molecule',
    'pseudo'
);


ALTER TYPE public.molecule_kind OWNER TO tckdb;

--
-- Name: network_species_role; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.network_species_role AS ENUM (
    'well',
    'reactant',
    'product',
    'bath_gas'
);


ALTER TYPE public.network_species_role OWNER TO tckdb;

--
-- Name: reaction_role; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.reaction_role AS ENUM (
    'reactant',
    'product'
);


ALTER TYPE public.reaction_role OWNER TO tckdb;

--
-- Name: rigid_rotor_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.rigid_rotor_kind AS ENUM (
    'atom',
    'linear',
    'spherical_top',
    'symmetric_top',
    'asymmetric_top'
);


ALTER TYPE public.rigid_rotor_kind OWNER TO tckdb;

--
-- Name: scientific_origin_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.scientific_origin_kind AS ENUM (
    'computed',
    'experimental',
    'estimated'
);


ALTER TYPE public.scientific_origin_kind OWNER TO tckdb;

--
-- Name: species_entry_review_role; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.species_entry_review_role AS ENUM (
    'curator',
    'reviewer',
    'validator',
    'linker'
);


ALTER TYPE public.species_entry_review_role OWNER TO tckdb;

--
-- Name: species_entry_state_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.species_entry_state_kind AS ENUM (
    'ground',
    'excited'
);


ALTER TYPE public.species_entry_state_kind OWNER TO tckdb;

--
-- Name: species_entry_stereo_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.species_entry_stereo_kind AS ENUM (
    'unspecified',
    'achiral',
    'enantiomer',
    'diastereomer',
    'ez_isomer'
);


ALTER TYPE public.species_entry_stereo_kind OWNER TO tckdb;

--
-- Name: stationary_point_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.stationary_point_kind AS ENUM (
    'minimum',
    'vdw_complex'
);


ALTER TYPE public.stationary_point_kind OWNER TO tckdb;

--
-- Name: statmech_calc_role; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.statmech_calc_role AS ENUM (
    'opt',
    'freq',
    'sp',
    'scan',
    'composite',
    'imported'
);


ALTER TYPE public.statmech_calc_role OWNER TO tckdb;

--
-- Name: statmech_treatment_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.statmech_treatment_kind AS ENUM (
    'rrho',
    'rrho_1d',
    'rrho_nd',
    'rrho_1d_nd',
    'rrho_ad',
    'rrao'
);


ALTER TYPE public.statmech_treatment_kind OWNER TO tckdb;

--
-- Name: thermo_calc_role; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.thermo_calc_role AS ENUM (
    'opt',
    'freq',
    'sp',
    'composite',
    'imported'
);


ALTER TYPE public.thermo_calc_role OWNER TO tckdb;

--
-- Name: torsion_treatment_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.torsion_treatment_kind AS ENUM (
    'hindered_rotor',
    'free_rotor',
    'rigid_top',
    'hindered_rotor_dos'
);


ALTER TYPE public.torsion_treatment_kind OWNER TO tckdb;

--
-- Name: transition_state_entry_status; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.transition_state_entry_status AS ENUM (
    'guess',
    'optimized',
    'validated',
    'rejected'
);


ALTER TYPE public.transition_state_entry_status OWNER TO tckdb;

--
-- Name: transition_state_selection_kind; Type: TYPE; Schema: public; Owner: tckdb
--

CREATE TYPE public.transition_state_selection_kind AS ENUM (
    'display_default',
    'curator_pick',
    'validated_reference',
    'preferred_for_kinetics',
    'benchmark_reference',
    'representative_geometry'
);


ALTER TYPE public.transition_state_selection_kind OWNER TO tckdb;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO tckdb;

--
-- Name: app_user; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.app_user (
    id bigint NOT NULL,
    username text NOT NULL,
    email text,
    full_name text,
    affiliation text,
    orcid character(19),
    role public.app_user_role DEFAULT 'user'::public.app_user_role NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.app_user OWNER TO tckdb;

--
-- Name: app_user_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.app_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.app_user_id_seq OWNER TO tckdb;

--
-- Name: app_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.app_user_id_seq OWNED BY public.app_user.id;


--
-- Name: author; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.author (
    id bigint NOT NULL,
    given_name text,
    family_name text NOT NULL,
    full_name text NOT NULL,
    orcid character(19),
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.author OWNER TO tckdb;

--
-- Name: author_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.author_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.author_id_seq OWNER TO tckdb;

--
-- Name: author_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.author_id_seq OWNED BY public.author.id;


--
-- Name: calc_freq_result; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.calc_freq_result (
    calculation_id bigint NOT NULL,
    n_imag integer,
    imag_freq_cm1 double precision,
    zpe_hartree double precision
);


ALTER TABLE public.calc_freq_result OWNER TO tckdb;

--
-- Name: calc_opt_result; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.calc_opt_result (
    calculation_id bigint NOT NULL,
    converged boolean,
    n_steps integer,
    final_energy_hartree double precision
);


ALTER TABLE public.calc_opt_result OWNER TO tckdb;

--
-- Name: calc_sp_result; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.calc_sp_result (
    calculation_id bigint NOT NULL,
    electronic_energy_hartree double precision
);


ALTER TABLE public.calc_sp_result OWNER TO tckdb;

--
-- Name: calculation; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.calculation (
    id bigint NOT NULL,
    type public.calc_type NOT NULL,
    quality public.calc_quality DEFAULT 'raw'::public.calc_quality NOT NULL,
    species_entry_id bigint,
    transition_state_entry_id bigint,
    software_release_id bigint,
    workflow_tool_release_id bigint,
    lot_id bigint,
    literature_id bigint,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint,
    CONSTRAINT ck_calculation_exactly_one_owner CHECK ((((transition_state_entry_id IS NOT NULL) AND (species_entry_id IS NULL)) OR ((transition_state_entry_id IS NULL) AND (species_entry_id IS NOT NULL))))
);


ALTER TABLE public.calculation OWNER TO tckdb;

--
-- Name: calculation_artifact; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.calculation_artifact (
    id bigint NOT NULL,
    calculation_id bigint NOT NULL,
    kind public.artifact_kind NOT NULL,
    uri text NOT NULL,
    sha256 character(64),
    bytes bigint,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.calculation_artifact OWNER TO tckdb;

--
-- Name: calculation_artifact_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.calculation_artifact_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.calculation_artifact_id_seq OWNER TO tckdb;

--
-- Name: calculation_artifact_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.calculation_artifact_id_seq OWNED BY public.calculation_artifact.id;


--
-- Name: calculation_dependency; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.calculation_dependency (
    parent_calculation_id bigint NOT NULL,
    child_calculation_id bigint NOT NULL,
    dependency_role public.calculation_dependency_role,
    CONSTRAINT ck_calculation_dependency_calculation_dependency_not_self CHECK ((parent_calculation_id <> child_calculation_id))
);


ALTER TABLE public.calculation_dependency OWNER TO tckdb;

--
-- Name: calculation_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.calculation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.calculation_id_seq OWNER TO tckdb;

--
-- Name: calculation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.calculation_id_seq OWNED BY public.calculation.id;


--
-- Name: calculation_input_geometry; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.calculation_input_geometry (
    calculation_id bigint NOT NULL,
    geometry_id bigint NOT NULL,
    input_order integer DEFAULT 1 NOT NULL,
    CONSTRAINT ck_calculation_input_geometry_calculation_input_order_ge_1 CHECK ((input_order >= 1))
);


ALTER TABLE public.calculation_input_geometry OWNER TO tckdb;

--
-- Name: calculation_output_geometry; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.calculation_output_geometry (
    calculation_id bigint NOT NULL,
    geometry_id bigint NOT NULL,
    output_order integer NOT NULL,
    role public.calculation_geometry_role
);


ALTER TABLE public.calculation_output_geometry OWNER TO tckdb;

--
-- Name: chem_reaction; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.chem_reaction (
    id bigint NOT NULL,
    stoichiometry_hash character(64),
    reversible boolean NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.chem_reaction OWNER TO tckdb;

--
-- Name: chem_reaction_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.chem_reaction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chem_reaction_id_seq OWNER TO tckdb;

--
-- Name: chem_reaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.chem_reaction_id_seq OWNED BY public.chem_reaction.id;


--
-- Name: conformer_assignment_scheme; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.conformer_assignment_scheme (
    id bigint NOT NULL,
    name character varying(128) NOT NULL,
    version character varying(64) NOT NULL,
    scope public.conformer_assignment_scope_kind DEFAULT 'canonical'::public.conformer_assignment_scope_kind NOT NULL,
    description text,
    parameters_json jsonb,
    code_commit character varying(64),
    is_default boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint
);


ALTER TABLE public.conformer_assignment_scheme OWNER TO tckdb;

--
-- Name: conformer_assignment_scheme_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.conformer_assignment_scheme_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.conformer_assignment_scheme_id_seq OWNER TO tckdb;

--
-- Name: conformer_assignment_scheme_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.conformer_assignment_scheme_id_seq OWNED BY public.conformer_assignment_scheme.id;


--
-- Name: conformer_group; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.conformer_group (
    id bigint NOT NULL,
    species_entry_id bigint NOT NULL,
    label character varying(64),
    note text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint
);


ALTER TABLE public.conformer_group OWNER TO tckdb;

--
-- Name: conformer_group_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.conformer_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.conformer_group_id_seq OWNER TO tckdb;

--
-- Name: conformer_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.conformer_group_id_seq OWNED BY public.conformer_group.id;


--
-- Name: conformer_observation; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.conformer_observation (
    id bigint NOT NULL,
    conformer_group_id bigint NOT NULL,
    calculation_id bigint NOT NULL,
    assignment_scheme_id bigint,
    scientific_origin public.scientific_origin_kind DEFAULT 'computed'::public.scientific_origin_kind NOT NULL,
    note text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint
);


ALTER TABLE public.conformer_observation OWNER TO tckdb;

--
-- Name: conformer_observation_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.conformer_observation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.conformer_observation_id_seq OWNER TO tckdb;

--
-- Name: conformer_observation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.conformer_observation_id_seq OWNED BY public.conformer_observation.id;


--
-- Name: conformer_selection; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.conformer_selection (
    id bigint NOT NULL,
    conformer_group_id bigint NOT NULL,
    assignment_scheme_id bigint,
    selection_kind public.conformer_selection_kind NOT NULL,
    note text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint
);


ALTER TABLE public.conformer_selection OWNER TO tckdb;

--
-- Name: conformer_selection_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.conformer_selection_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.conformer_selection_id_seq OWNER TO tckdb;

--
-- Name: conformer_selection_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.conformer_selection_id_seq OWNED BY public.conformer_selection.id;


--
-- Name: geometry; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.geometry (
    id bigint NOT NULL,
    natoms integer NOT NULL,
    geom_hash character(64) NOT NULL,
    xyz_text text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.geometry OWNER TO tckdb;

--
-- Name: geometry_atom; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.geometry_atom (
    geometry_id bigint NOT NULL,
    atom_index integer NOT NULL,
    element character(2) NOT NULL,
    x double precision NOT NULL,
    y double precision NOT NULL,
    z double precision NOT NULL
);


ALTER TABLE public.geometry_atom OWNER TO tckdb;

--
-- Name: geometry_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.geometry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.geometry_id_seq OWNER TO tckdb;

--
-- Name: geometry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.geometry_id_seq OWNED BY public.geometry.id;


--
-- Name: kinetics; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.kinetics (
    id bigint NOT NULL,
    reaction_entry_id bigint NOT NULL,
    scientific_origin public.scientific_origin_kind NOT NULL,
    model_kind public.kinetics_model_kind DEFAULT 'modified_arrhenius'::public.kinetics_model_kind NOT NULL,
    literature_id bigint,
    workflow_tool_release_id bigint,
    software_release_id bigint,
    a double precision,
    a_units text,
    n double precision,
    ea_kj_mol double precision,
    tmin_k double precision,
    tmax_k double precision,
    degeneracy double precision,
    tunneling_model text,
    note text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint,
    CONSTRAINT ck_kinetics_kinetics_tmax_k_gt_0 CHECK (((tmax_k IS NULL) OR (tmax_k > (0)::double precision))),
    CONSTRAINT ck_kinetics_kinetics_tmin_k_gt_0 CHECK (((tmin_k IS NULL) OR (tmin_k > (0)::double precision))),
    CONSTRAINT ck_kinetics_kinetics_tmin_le_tmax CHECK (((tmin_k IS NULL) OR (tmax_k IS NULL) OR (tmin_k <= tmax_k)))
);


ALTER TABLE public.kinetics OWNER TO tckdb;

--
-- Name: kinetics_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.kinetics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.kinetics_id_seq OWNER TO tckdb;

--
-- Name: kinetics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.kinetics_id_seq OWNED BY public.kinetics.id;


--
-- Name: kinetics_source_calculation; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.kinetics_source_calculation (
    kinetics_id bigint NOT NULL,
    calculation_id bigint NOT NULL,
    role public.kinetics_calc_role NOT NULL
);


ALTER TABLE public.kinetics_source_calculation OWNER TO tckdb;

--
-- Name: level_of_theory; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.level_of_theory (
    id bigint NOT NULL,
    method text NOT NULL,
    basis text,
    aux_basis text,
    dispersion text,
    solvent text,
    solvent_model text,
    keywords text,
    lot_hash character(64) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.level_of_theory OWNER TO tckdb;

--
-- Name: level_of_theory_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.level_of_theory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.level_of_theory_id_seq OWNER TO tckdb;

--
-- Name: level_of_theory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.level_of_theory_id_seq OWNED BY public.level_of_theory.id;


--
-- Name: literature; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.literature (
    id bigint NOT NULL,
    kind public.literature_kind NOT NULL,
    title text NOT NULL,
    journal text,
    year integer,
    volume text,
    issue text,
    pages text,
    doi text,
    isbn text,
    url text,
    publisher text,
    institution text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.literature OWNER TO tckdb;

--
-- Name: literature_author; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.literature_author (
    literature_id bigint NOT NULL,
    author_id bigint NOT NULL,
    author_order integer NOT NULL
);


ALTER TABLE public.literature_author OWNER TO tckdb;

--
-- Name: literature_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.literature_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.literature_id_seq OWNER TO tckdb;

--
-- Name: literature_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.literature_id_seq OWNED BY public.literature.id;


--
-- Name: network; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.network (
    id bigint NOT NULL,
    name text,
    description text,
    literature_id bigint,
    software_release_id bigint,
    workflow_tool_release_id bigint,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint
);


ALTER TABLE public.network OWNER TO tckdb;

--
-- Name: network_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.network_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.network_id_seq OWNER TO tckdb;

--
-- Name: network_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.network_id_seq OWNED BY public.network.id;


--
-- Name: network_reaction; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.network_reaction (
    network_id bigint NOT NULL,
    reaction_entry_id bigint NOT NULL
);


ALTER TABLE public.network_reaction OWNER TO tckdb;

--
-- Name: network_species; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.network_species (
    network_id bigint NOT NULL,
    species_entry_id bigint NOT NULL,
    role public.network_species_role NOT NULL
);


ALTER TABLE public.network_species OWNER TO tckdb;

--
-- Name: reaction_entry; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.reaction_entry (
    id bigint NOT NULL,
    reaction_id bigint NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint
);


ALTER TABLE public.reaction_entry OWNER TO tckdb;

--
-- Name: reaction_entry_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.reaction_entry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reaction_entry_id_seq OWNER TO tckdb;

--
-- Name: reaction_entry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.reaction_entry_id_seq OWNED BY public.reaction_entry.id;


--
-- Name: reaction_entry_structure_participant; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.reaction_entry_structure_participant (
    id bigint NOT NULL,
    reaction_entry_id bigint NOT NULL,
    species_entry_id bigint NOT NULL,
    role public.reaction_role NOT NULL,
    participant_index integer NOT NULL,
    note text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint
);


ALTER TABLE public.reaction_entry_structure_participant OWNER TO tckdb;

--
-- Name: reaction_entry_structure_participant_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.reaction_entry_structure_participant_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reaction_entry_structure_participant_id_seq OWNER TO tckdb;

--
-- Name: reaction_entry_structure_participant_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.reaction_entry_structure_participant_id_seq OWNED BY public.reaction_entry_structure_participant.id;


--
-- Name: reaction_participant; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.reaction_participant (
    reaction_id bigint NOT NULL,
    species_id bigint NOT NULL,
    role public.reaction_role NOT NULL,
    stoichiometry smallint NOT NULL
);


ALTER TABLE public.reaction_participant OWNER TO tckdb;

--
-- Name: software; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.software (
    id bigint NOT NULL,
    name text NOT NULL,
    website text,
    description text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.software OWNER TO tckdb;

--
-- Name: software_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.software_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.software_id_seq OWNER TO tckdb;

--
-- Name: software_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.software_id_seq OWNED BY public.software.id;


--
-- Name: software_release; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.software_release (
    id bigint NOT NULL,
    software_id bigint NOT NULL,
    version text,
    revision text,
    build text,
    release_date date,
    notes text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.software_release OWNER TO tckdb;

--
-- Name: software_release_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.software_release_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.software_release_id_seq OWNER TO tckdb;

--
-- Name: software_release_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.software_release_id_seq OWNED BY public.software_release.id;


--
-- Name: species; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.species (
    id bigint NOT NULL,
    kind public.molecule_kind NOT NULL,
    smiles text NOT NULL,
    inchi_key character(27) NOT NULL,
    charge smallint NOT NULL,
    multiplicity smallint NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.species OWNER TO tckdb;

--
-- Name: species_entry; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.species_entry (
    id bigint NOT NULL,
    species_id bigint NOT NULL,
    kind public.stationary_point_kind DEFAULT 'minimum'::public.stationary_point_kind NOT NULL,
    mol public.mol,
    unmapped_smiles text,
    stereo_kind public.species_entry_stereo_kind DEFAULT 'unspecified'::public.species_entry_stereo_kind NOT NULL,
    stereo_label character varying(64),
    electronic_state_kind public.species_entry_state_kind DEFAULT 'ground'::public.species_entry_state_kind NOT NULL,
    electronic_state_label character varying(8),
    term_symbol_raw character varying(64),
    term_symbol character varying(64),
    isotopologue_label character varying(64),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint
);


ALTER TABLE public.species_entry OWNER TO tckdb;

--
-- Name: species_entry_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.species_entry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.species_entry_id_seq OWNER TO tckdb;

--
-- Name: species_entry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.species_entry_id_seq OWNED BY public.species_entry.id;


--
-- Name: species_entry_review; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.species_entry_review (
    id bigint NOT NULL,
    species_entry_id bigint NOT NULL,
    user_id bigint NOT NULL,
    role public.species_entry_review_role NOT NULL,
    note text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.species_entry_review OWNER TO tckdb;

--
-- Name: species_entry_review_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.species_entry_review_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.species_entry_review_id_seq OWNER TO tckdb;

--
-- Name: species_entry_review_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.species_entry_review_id_seq OWNED BY public.species_entry_review.id;


--
-- Name: species_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.species_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.species_id_seq OWNER TO tckdb;

--
-- Name: species_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.species_id_seq OWNED BY public.species.id;


--
-- Name: statmech; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.statmech (
    id bigint NOT NULL,
    species_entry_id bigint NOT NULL,
    scientific_origin public.scientific_origin_kind NOT NULL,
    literature_id bigint,
    workflow_tool_release_id bigint,
    software_release_id bigint,
    external_symmetry smallint,
    point_group text,
    is_linear boolean,
    rigid_rotor_kind public.rigid_rotor_kind,
    statmech_treatment public.statmech_treatment_kind,
    freq_scale_factor double precision,
    uses_projected_frequencies boolean,
    note text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint,
    CONSTRAINT ck_statmech_statmech_external_symmetry_ge_1 CHECK (((external_symmetry IS NULL) OR (external_symmetry >= 1)))
);


ALTER TABLE public.statmech OWNER TO tckdb;

--
-- Name: statmech_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.statmech_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.statmech_id_seq OWNER TO tckdb;

--
-- Name: statmech_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.statmech_id_seq OWNED BY public.statmech.id;


--
-- Name: statmech_source_calculation; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.statmech_source_calculation (
    statmech_id bigint NOT NULL,
    calculation_id bigint NOT NULL,
    role public.statmech_calc_role NOT NULL
);


ALTER TABLE public.statmech_source_calculation OWNER TO tckdb;

--
-- Name: statmech_torsion; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.statmech_torsion (
    id bigint NOT NULL,
    statmech_id bigint NOT NULL,
    torsion_index integer NOT NULL,
    symmetry_number smallint,
    treatment_kind public.torsion_treatment_kind,
    dimension integer NOT NULL,
    top_description text,
    invalidated_reason text,
    note text,
    source_scan_calculation_id bigint,
    CONSTRAINT ck_statmech_torsion_statmech_torsion_dimension_ge_1 CHECK ((dimension >= 1))
);


ALTER TABLE public.statmech_torsion OWNER TO tckdb;

--
-- Name: statmech_torsion_definition; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.statmech_torsion_definition (
    torsion_id bigint NOT NULL,
    coordinate_index integer NOT NULL,
    atom1_index integer NOT NULL,
    atom2_index integer NOT NULL,
    atom3_index integer NOT NULL,
    atom4_index integer NOT NULL,
    CONSTRAINT ck_statmech_torsion_definition_statmech_torsion_atom1_ge_1 CHECK ((atom1_index >= 1)),
    CONSTRAINT ck_statmech_torsion_definition_statmech_torsion_atom2_ge_1 CHECK ((atom2_index >= 1)),
    CONSTRAINT ck_statmech_torsion_definition_statmech_torsion_atom3_ge_1 CHECK ((atom3_index >= 1)),
    CONSTRAINT ck_statmech_torsion_definition_statmech_torsion_atom4_ge_1 CHECK ((atom4_index >= 1)),
    CONSTRAINT ck_statmech_torsion_definition_statmech_torsion_coord_i_800c CHECK ((coordinate_index >= 1))
);


ALTER TABLE public.statmech_torsion_definition OWNER TO tckdb;

--
-- Name: statmech_torsion_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.statmech_torsion_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.statmech_torsion_id_seq OWNER TO tckdb;

--
-- Name: statmech_torsion_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.statmech_torsion_id_seq OWNED BY public.statmech_torsion.id;


--
-- Name: thermo; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.thermo (
    id bigint NOT NULL,
    species_entry_id bigint NOT NULL,
    scientific_origin public.scientific_origin_kind NOT NULL,
    literature_id bigint,
    workflow_tool_release_id bigint,
    software_release_id bigint,
    h298_kj_mol double precision,
    s298_j_mol_k double precision,
    note text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint
);


ALTER TABLE public.thermo OWNER TO tckdb;

--
-- Name: thermo_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.thermo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.thermo_id_seq OWNER TO tckdb;

--
-- Name: thermo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.thermo_id_seq OWNED BY public.thermo.id;


--
-- Name: thermo_nasa; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.thermo_nasa (
    thermo_id bigint NOT NULL,
    t_low double precision,
    t_mid double precision,
    t_high double precision,
    a1 double precision,
    a2 double precision,
    a3 double precision,
    a4 double precision,
    a5 double precision,
    a6 double precision,
    a7 double precision,
    b1 double precision,
    b2 double precision,
    b3 double precision,
    b4 double precision,
    b5 double precision,
    b6 double precision,
    b7 double precision
);


ALTER TABLE public.thermo_nasa OWNER TO tckdb;

--
-- Name: thermo_point; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.thermo_point (
    thermo_id bigint NOT NULL,
    temperature_k double precision NOT NULL,
    cp_j_mol_k double precision,
    h_kj_mol double precision,
    s_j_mol_k double precision,
    g_kj_mol double precision
);


ALTER TABLE public.thermo_point OWNER TO tckdb;

--
-- Name: thermo_source_calculation; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.thermo_source_calculation (
    thermo_id bigint NOT NULL,
    calculation_id bigint NOT NULL,
    role public.thermo_calc_role NOT NULL
);


ALTER TABLE public.thermo_source_calculation OWNER TO tckdb;

--
-- Name: transition_state; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.transition_state (
    id bigint NOT NULL,
    reaction_entry_id bigint NOT NULL,
    label text,
    note text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint
);


ALTER TABLE public.transition_state OWNER TO tckdb;

--
-- Name: transition_state_entry; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.transition_state_entry (
    id bigint NOT NULL,
    transition_state_id bigint NOT NULL,
    charge smallint NOT NULL,
    multiplicity smallint NOT NULL,
    mol public.mol,
    unmapped_smiles text,
    status public.transition_state_entry_status DEFAULT 'optimized'::public.transition_state_entry_status NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint
);


ALTER TABLE public.transition_state_entry OWNER TO tckdb;

--
-- Name: transition_state_entry_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.transition_state_entry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transition_state_entry_id_seq OWNER TO tckdb;

--
-- Name: transition_state_entry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.transition_state_entry_id_seq OWNED BY public.transition_state_entry.id;


--
-- Name: transition_state_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.transition_state_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transition_state_id_seq OWNER TO tckdb;

--
-- Name: transition_state_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.transition_state_id_seq OWNED BY public.transition_state.id;


--
-- Name: transition_state_selection; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.transition_state_selection (
    id bigint NOT NULL,
    transition_state_id bigint NOT NULL,
    transition_state_entry_id bigint NOT NULL,
    selection_kind public.transition_state_selection_kind NOT NULL,
    note text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint
);


ALTER TABLE public.transition_state_selection OWNER TO tckdb;

--
-- Name: transition_state_selection_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.transition_state_selection_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transition_state_selection_id_seq OWNER TO tckdb;

--
-- Name: transition_state_selection_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.transition_state_selection_id_seq OWNED BY public.transition_state_selection.id;


--
-- Name: transport; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.transport (
    id bigint NOT NULL,
    species_entry_id bigint NOT NULL,
    scientific_origin public.scientific_origin_kind NOT NULL,
    literature_id bigint,
    software_release_id bigint,
    workflow_tool_release_id bigint,
    sigma_angstrom double precision,
    epsilon_over_k_k double precision,
    dipole_debye double precision,
    polarizability_angstrom3 double precision,
    rotational_relaxation double precision,
    note text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by bigint
);


ALTER TABLE public.transport OWNER TO tckdb;

--
-- Name: transport_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.transport_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transport_id_seq OWNER TO tckdb;

--
-- Name: transport_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.transport_id_seq OWNED BY public.transport.id;


--
-- Name: workflow_tool; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.workflow_tool (
    id bigint NOT NULL,
    name text NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.workflow_tool OWNER TO tckdb;

--
-- Name: workflow_tool_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.workflow_tool_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workflow_tool_id_seq OWNER TO tckdb;

--
-- Name: workflow_tool_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.workflow_tool_id_seq OWNED BY public.workflow_tool.id;


--
-- Name: workflow_tool_release; Type: TABLE; Schema: public; Owner: tckdb
--

CREATE TABLE public.workflow_tool_release (
    id bigint NOT NULL,
    workflow_tool_id bigint NOT NULL,
    version text,
    git_commit character(40),
    release_date date,
    notes text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.workflow_tool_release OWNER TO tckdb;

--
-- Name: workflow_tool_release_id_seq; Type: SEQUENCE; Schema: public; Owner: tckdb
--

CREATE SEQUENCE public.workflow_tool_release_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workflow_tool_release_id_seq OWNER TO tckdb;

--
-- Name: workflow_tool_release_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tckdb
--

ALTER SEQUENCE public.workflow_tool_release_id_seq OWNED BY public.workflow_tool_release.id;


--
-- Name: app_user id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.app_user ALTER COLUMN id SET DEFAULT nextval('public.app_user_id_seq'::regclass);


--
-- Name: author id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.author ALTER COLUMN id SET DEFAULT nextval('public.author_id_seq'::regclass);


--
-- Name: calculation id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation ALTER COLUMN id SET DEFAULT nextval('public.calculation_id_seq'::regclass);


--
-- Name: calculation_artifact id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_artifact ALTER COLUMN id SET DEFAULT nextval('public.calculation_artifact_id_seq'::regclass);


--
-- Name: chem_reaction id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.chem_reaction ALTER COLUMN id SET DEFAULT nextval('public.chem_reaction_id_seq'::regclass);


--
-- Name: conformer_assignment_scheme id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_assignment_scheme ALTER COLUMN id SET DEFAULT nextval('public.conformer_assignment_scheme_id_seq'::regclass);


--
-- Name: conformer_group id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_group ALTER COLUMN id SET DEFAULT nextval('public.conformer_group_id_seq'::regclass);


--
-- Name: conformer_observation id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_observation ALTER COLUMN id SET DEFAULT nextval('public.conformer_observation_id_seq'::regclass);


--
-- Name: conformer_selection id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_selection ALTER COLUMN id SET DEFAULT nextval('public.conformer_selection_id_seq'::regclass);


--
-- Name: geometry id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.geometry ALTER COLUMN id SET DEFAULT nextval('public.geometry_id_seq'::regclass);


--
-- Name: kinetics id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.kinetics ALTER COLUMN id SET DEFAULT nextval('public.kinetics_id_seq'::regclass);


--
-- Name: level_of_theory id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.level_of_theory ALTER COLUMN id SET DEFAULT nextval('public.level_of_theory_id_seq'::regclass);


--
-- Name: literature id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.literature ALTER COLUMN id SET DEFAULT nextval('public.literature_id_seq'::regclass);


--
-- Name: network id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.network ALTER COLUMN id SET DEFAULT nextval('public.network_id_seq'::regclass);


--
-- Name: reaction_entry id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.reaction_entry ALTER COLUMN id SET DEFAULT nextval('public.reaction_entry_id_seq'::regclass);


--
-- Name: reaction_entry_structure_participant id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.reaction_entry_structure_participant ALTER COLUMN id SET DEFAULT nextval('public.reaction_entry_structure_participant_id_seq'::regclass);


--
-- Name: software id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.software ALTER COLUMN id SET DEFAULT nextval('public.software_id_seq'::regclass);


--
-- Name: software_release id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.software_release ALTER COLUMN id SET DEFAULT nextval('public.software_release_id_seq'::regclass);


--
-- Name: species id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.species ALTER COLUMN id SET DEFAULT nextval('public.species_id_seq'::regclass);


--
-- Name: species_entry id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.species_entry ALTER COLUMN id SET DEFAULT nextval('public.species_entry_id_seq'::regclass);


--
-- Name: species_entry_review id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.species_entry_review ALTER COLUMN id SET DEFAULT nextval('public.species_entry_review_id_seq'::regclass);


--
-- Name: statmech id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech ALTER COLUMN id SET DEFAULT nextval('public.statmech_id_seq'::regclass);


--
-- Name: statmech_torsion id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech_torsion ALTER COLUMN id SET DEFAULT nextval('public.statmech_torsion_id_seq'::regclass);


--
-- Name: thermo id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo ALTER COLUMN id SET DEFAULT nextval('public.thermo_id_seq'::regclass);


--
-- Name: transition_state id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state ALTER COLUMN id SET DEFAULT nextval('public.transition_state_id_seq'::regclass);


--
-- Name: transition_state_entry id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state_entry ALTER COLUMN id SET DEFAULT nextval('public.transition_state_entry_id_seq'::regclass);


--
-- Name: transition_state_selection id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state_selection ALTER COLUMN id SET DEFAULT nextval('public.transition_state_selection_id_seq'::regclass);


--
-- Name: transport id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transport ALTER COLUMN id SET DEFAULT nextval('public.transport_id_seq'::regclass);


--
-- Name: workflow_tool id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.workflow_tool ALTER COLUMN id SET DEFAULT nextval('public.workflow_tool_id_seq'::regclass);


--
-- Name: workflow_tool_release id; Type: DEFAULT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.workflow_tool_release ALTER COLUMN id SET DEFAULT nextval('public.workflow_tool_release_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.alembic_version (version_num) FROM stdin;
d861dfd60891
\.


--
-- Data for Name: app_user; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.app_user (id, username, email, full_name, affiliation, orcid, role, created_at) FROM stdin;
\.


--
-- Data for Name: author; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.author (id, given_name, family_name, full_name, orcid, created_at) FROM stdin;
\.


--
-- Data for Name: calc_freq_result; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.calc_freq_result (calculation_id, n_imag, imag_freq_cm1, zpe_hartree) FROM stdin;
\.


--
-- Data for Name: calc_opt_result; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.calc_opt_result (calculation_id, converged, n_steps, final_energy_hartree) FROM stdin;
\.


--
-- Data for Name: calc_sp_result; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.calc_sp_result (calculation_id, electronic_energy_hartree) FROM stdin;
\.


--
-- Data for Name: calculation; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.calculation (id, type, quality, species_entry_id, transition_state_entry_id, software_release_id, workflow_tool_release_id, lot_id, literature_id, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: calculation_artifact; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.calculation_artifact (id, calculation_id, kind, uri, sha256, bytes, created_at) FROM stdin;
\.


--
-- Data for Name: calculation_dependency; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.calculation_dependency (parent_calculation_id, child_calculation_id, dependency_role) FROM stdin;
\.


--
-- Data for Name: calculation_input_geometry; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.calculation_input_geometry (calculation_id, geometry_id, input_order) FROM stdin;
\.


--
-- Data for Name: calculation_output_geometry; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.calculation_output_geometry (calculation_id, geometry_id, output_order, role) FROM stdin;
\.


--
-- Data for Name: chem_reaction; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.chem_reaction (id, stoichiometry_hash, reversible, created_at) FROM stdin;
\.


--
-- Data for Name: conformer_assignment_scheme; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.conformer_assignment_scheme (id, name, version, scope, description, parameters_json, code_commit, is_default, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: conformer_group; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.conformer_group (id, species_entry_id, label, note, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: conformer_observation; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.conformer_observation (id, conformer_group_id, calculation_id, assignment_scheme_id, scientific_origin, note, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: conformer_selection; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.conformer_selection (id, conformer_group_id, assignment_scheme_id, selection_kind, note, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: geometry; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.geometry (id, natoms, geom_hash, xyz_text, created_at) FROM stdin;
\.


--
-- Data for Name: geometry_atom; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.geometry_atom (geometry_id, atom_index, element, x, y, z) FROM stdin;
\.


--
-- Data for Name: kinetics; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.kinetics (id, reaction_entry_id, scientific_origin, model_kind, literature_id, workflow_tool_release_id, software_release_id, a, a_units, n, ea_kj_mol, tmin_k, tmax_k, degeneracy, tunneling_model, note, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: kinetics_source_calculation; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.kinetics_source_calculation (kinetics_id, calculation_id, role) FROM stdin;
\.


--
-- Data for Name: level_of_theory; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.level_of_theory (id, method, basis, aux_basis, dispersion, solvent, solvent_model, keywords, lot_hash, created_at) FROM stdin;
\.


--
-- Data for Name: literature; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.literature (id, kind, title, journal, year, volume, issue, pages, doi, isbn, url, publisher, institution, created_at) FROM stdin;
\.


--
-- Data for Name: literature_author; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.literature_author (literature_id, author_id, author_order) FROM stdin;
\.


--
-- Data for Name: network; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.network (id, name, description, literature_id, software_release_id, workflow_tool_release_id, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: network_reaction; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.network_reaction (network_id, reaction_entry_id) FROM stdin;
\.


--
-- Data for Name: network_species; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.network_species (network_id, species_entry_id, role) FROM stdin;
\.


--
-- Data for Name: reaction_entry; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.reaction_entry (id, reaction_id, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: reaction_entry_structure_participant; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.reaction_entry_structure_participant (id, reaction_entry_id, species_entry_id, role, participant_index, note, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: reaction_participant; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.reaction_participant (reaction_id, species_id, role, stoichiometry) FROM stdin;
\.


--
-- Data for Name: software; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.software (id, name, website, description, created_at) FROM stdin;
\.


--
-- Data for Name: software_release; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.software_release (id, software_id, version, revision, build, release_date, notes, created_at) FROM stdin;
\.


--
-- Data for Name: species; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.species (id, kind, smiles, inchi_key, charge, multiplicity, created_at) FROM stdin;
\.


--
-- Data for Name: species_entry; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.species_entry (id, species_id, kind, mol, unmapped_smiles, stereo_kind, stereo_label, electronic_state_kind, electronic_state_label, term_symbol_raw, term_symbol, isotopologue_label, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: species_entry_review; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.species_entry_review (id, species_entry_id, user_id, role, note, created_at) FROM stdin;
\.


--
-- Data for Name: statmech; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.statmech (id, species_entry_id, scientific_origin, literature_id, workflow_tool_release_id, software_release_id, external_symmetry, point_group, is_linear, rigid_rotor_kind, statmech_treatment, freq_scale_factor, uses_projected_frequencies, note, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: statmech_source_calculation; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.statmech_source_calculation (statmech_id, calculation_id, role) FROM stdin;
\.


--
-- Data for Name: statmech_torsion; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.statmech_torsion (id, statmech_id, torsion_index, symmetry_number, treatment_kind, dimension, top_description, invalidated_reason, note, source_scan_calculation_id) FROM stdin;
\.


--
-- Data for Name: statmech_torsion_definition; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.statmech_torsion_definition (torsion_id, coordinate_index, atom1_index, atom2_index, atom3_index, atom4_index) FROM stdin;
\.


--
-- Data for Name: thermo; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.thermo (id, species_entry_id, scientific_origin, literature_id, workflow_tool_release_id, software_release_id, h298_kj_mol, s298_j_mol_k, note, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: thermo_nasa; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.thermo_nasa (thermo_id, t_low, t_mid, t_high, a1, a2, a3, a4, a5, a6, a7, b1, b2, b3, b4, b5, b6, b7) FROM stdin;
\.


--
-- Data for Name: thermo_point; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.thermo_point (thermo_id, temperature_k, cp_j_mol_k, h_kj_mol, s_j_mol_k, g_kj_mol) FROM stdin;
\.


--
-- Data for Name: thermo_source_calculation; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.thermo_source_calculation (thermo_id, calculation_id, role) FROM stdin;
\.


--
-- Data for Name: transition_state; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.transition_state (id, reaction_entry_id, label, note, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: transition_state_entry; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.transition_state_entry (id, transition_state_id, charge, multiplicity, mol, unmapped_smiles, status, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: transition_state_selection; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.transition_state_selection (id, transition_state_id, transition_state_entry_id, selection_kind, note, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: transport; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.transport (id, species_entry_id, scientific_origin, literature_id, software_release_id, workflow_tool_release_id, sigma_angstrom, epsilon_over_k_k, dipole_debye, polarizability_angstrom3, rotational_relaxation, note, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: workflow_tool; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.workflow_tool (id, name, description, created_at) FROM stdin;
\.


--
-- Data for Name: workflow_tool_release; Type: TABLE DATA; Schema: public; Owner: tckdb
--

COPY public.workflow_tool_release (id, workflow_tool_id, version, git_commit, release_date, notes, created_at) FROM stdin;
\.


--
-- Name: app_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.app_user_id_seq', 1, false);


--
-- Name: author_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.author_id_seq', 1, false);


--
-- Name: calculation_artifact_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.calculation_artifact_id_seq', 1, false);


--
-- Name: calculation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.calculation_id_seq', 1, false);


--
-- Name: chem_reaction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.chem_reaction_id_seq', 1, false);


--
-- Name: conformer_assignment_scheme_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.conformer_assignment_scheme_id_seq', 1, false);


--
-- Name: conformer_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.conformer_group_id_seq', 1, false);


--
-- Name: conformer_observation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.conformer_observation_id_seq', 1, false);


--
-- Name: conformer_selection_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.conformer_selection_id_seq', 1, false);


--
-- Name: geometry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.geometry_id_seq', 1, false);


--
-- Name: kinetics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.kinetics_id_seq', 1, false);


--
-- Name: level_of_theory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.level_of_theory_id_seq', 1, false);


--
-- Name: literature_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.literature_id_seq', 1, false);


--
-- Name: network_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.network_id_seq', 1, false);


--
-- Name: reaction_entry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.reaction_entry_id_seq', 1, false);


--
-- Name: reaction_entry_structure_participant_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.reaction_entry_structure_participant_id_seq', 1, false);


--
-- Name: software_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.software_id_seq', 1, false);


--
-- Name: software_release_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.software_release_id_seq', 1, false);


--
-- Name: species_entry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.species_entry_id_seq', 1, false);


--
-- Name: species_entry_review_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.species_entry_review_id_seq', 1, false);


--
-- Name: species_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.species_id_seq', 1, false);


--
-- Name: statmech_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.statmech_id_seq', 1, false);


--
-- Name: statmech_torsion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.statmech_torsion_id_seq', 1, false);


--
-- Name: thermo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.thermo_id_seq', 1, false);


--
-- Name: transition_state_entry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.transition_state_entry_id_seq', 1, false);


--
-- Name: transition_state_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.transition_state_id_seq', 1, false);


--
-- Name: transition_state_selection_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.transition_state_selection_id_seq', 1, false);


--
-- Name: transport_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.transport_id_seq', 1, false);


--
-- Name: workflow_tool_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.workflow_tool_id_seq', 1, false);


--
-- Name: workflow_tool_release_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tckdb
--

SELECT pg_catalog.setval('public.workflow_tool_release_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: app_user app_user_email_uq; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_email_uq UNIQUE (email);


--
-- Name: app_user app_user_orcid_uq; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_orcid_uq UNIQUE (orcid);


--
-- Name: app_user app_user_username_uq; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_username_uq UNIQUE (username);


--
-- Name: author author_orcid_uq; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.author
    ADD CONSTRAINT author_orcid_uq UNIQUE (orcid);


--
-- Name: literature_author literature_author_order_uq; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.literature_author
    ADD CONSTRAINT literature_author_order_uq UNIQUE (literature_id, author_order);


--
-- Name: level_of_theory lot_hash_uq; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.level_of_theory
    ADD CONSTRAINT lot_hash_uq UNIQUE (lot_hash);


--
-- Name: app_user pk_app_user; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT pk_app_user PRIMARY KEY (id);


--
-- Name: author pk_author; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.author
    ADD CONSTRAINT pk_author PRIMARY KEY (id);


--
-- Name: calc_freq_result pk_calc_freq_result; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calc_freq_result
    ADD CONSTRAINT pk_calc_freq_result PRIMARY KEY (calculation_id);


--
-- Name: calc_opt_result pk_calc_opt_result; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calc_opt_result
    ADD CONSTRAINT pk_calc_opt_result PRIMARY KEY (calculation_id);


--
-- Name: calc_sp_result pk_calc_sp_result; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calc_sp_result
    ADD CONSTRAINT pk_calc_sp_result PRIMARY KEY (calculation_id);


--
-- Name: calculation pk_calculation; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation
    ADD CONSTRAINT pk_calculation PRIMARY KEY (id);


--
-- Name: calculation_artifact pk_calculation_artifact; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_artifact
    ADD CONSTRAINT pk_calculation_artifact PRIMARY KEY (id);


--
-- Name: calculation_dependency pk_calculation_dependency; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_dependency
    ADD CONSTRAINT pk_calculation_dependency PRIMARY KEY (parent_calculation_id, child_calculation_id);


--
-- Name: calculation_input_geometry pk_calculation_input_geometry; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_input_geometry
    ADD CONSTRAINT pk_calculation_input_geometry PRIMARY KEY (calculation_id, input_order);


--
-- Name: calculation_output_geometry pk_calculation_output_geometry; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_output_geometry
    ADD CONSTRAINT pk_calculation_output_geometry PRIMARY KEY (calculation_id, output_order);


--
-- Name: chem_reaction pk_chem_reaction; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.chem_reaction
    ADD CONSTRAINT pk_chem_reaction PRIMARY KEY (id);


--
-- Name: conformer_assignment_scheme pk_conformer_assignment_scheme; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_assignment_scheme
    ADD CONSTRAINT pk_conformer_assignment_scheme PRIMARY KEY (id);


--
-- Name: conformer_group pk_conformer_group; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_group
    ADD CONSTRAINT pk_conformer_group PRIMARY KEY (id);


--
-- Name: conformer_observation pk_conformer_observation; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_observation
    ADD CONSTRAINT pk_conformer_observation PRIMARY KEY (id);


--
-- Name: conformer_selection pk_conformer_selection; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_selection
    ADD CONSTRAINT pk_conformer_selection PRIMARY KEY (id);


--
-- Name: geometry pk_geometry; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.geometry
    ADD CONSTRAINT pk_geometry PRIMARY KEY (id);


--
-- Name: geometry_atom pk_geometry_atom; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.geometry_atom
    ADD CONSTRAINT pk_geometry_atom PRIMARY KEY (geometry_id, atom_index);


--
-- Name: kinetics pk_kinetics; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.kinetics
    ADD CONSTRAINT pk_kinetics PRIMARY KEY (id);


--
-- Name: kinetics_source_calculation pk_kinetics_source_calculation; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.kinetics_source_calculation
    ADD CONSTRAINT pk_kinetics_source_calculation PRIMARY KEY (kinetics_id, calculation_id, role);


--
-- Name: level_of_theory pk_level_of_theory; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.level_of_theory
    ADD CONSTRAINT pk_level_of_theory PRIMARY KEY (id);


--
-- Name: literature pk_literature; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.literature
    ADD CONSTRAINT pk_literature PRIMARY KEY (id);


--
-- Name: literature_author pk_literature_author; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.literature_author
    ADD CONSTRAINT pk_literature_author PRIMARY KEY (literature_id, author_id);


--
-- Name: network pk_network; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.network
    ADD CONSTRAINT pk_network PRIMARY KEY (id);


--
-- Name: network_reaction pk_network_reaction; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.network_reaction
    ADD CONSTRAINT pk_network_reaction PRIMARY KEY (network_id, reaction_entry_id);


--
-- Name: network_species pk_network_species; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.network_species
    ADD CONSTRAINT pk_network_species PRIMARY KEY (network_id, species_entry_id, role);


--
-- Name: reaction_entry pk_reaction_entry; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.reaction_entry
    ADD CONSTRAINT pk_reaction_entry PRIMARY KEY (id);


--
-- Name: reaction_entry_structure_participant pk_reaction_entry_structure_participant; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.reaction_entry_structure_participant
    ADD CONSTRAINT pk_reaction_entry_structure_participant PRIMARY KEY (id);


--
-- Name: reaction_participant pk_reaction_participant; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.reaction_participant
    ADD CONSTRAINT pk_reaction_participant PRIMARY KEY (reaction_id, species_id, role);


--
-- Name: software pk_software; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.software
    ADD CONSTRAINT pk_software PRIMARY KEY (id);


--
-- Name: software_release pk_software_release; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.software_release
    ADD CONSTRAINT pk_software_release PRIMARY KEY (id);


--
-- Name: species pk_species; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.species
    ADD CONSTRAINT pk_species PRIMARY KEY (id);


--
-- Name: species_entry pk_species_entry; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.species_entry
    ADD CONSTRAINT pk_species_entry PRIMARY KEY (id);


--
-- Name: species_entry_review pk_species_entry_review; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.species_entry_review
    ADD CONSTRAINT pk_species_entry_review PRIMARY KEY (id);


--
-- Name: statmech pk_statmech; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech
    ADD CONSTRAINT pk_statmech PRIMARY KEY (id);


--
-- Name: statmech_source_calculation pk_statmech_source_calculation; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech_source_calculation
    ADD CONSTRAINT pk_statmech_source_calculation PRIMARY KEY (statmech_id, calculation_id, role);


--
-- Name: statmech_torsion pk_statmech_torsion; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech_torsion
    ADD CONSTRAINT pk_statmech_torsion PRIMARY KEY (id);


--
-- Name: statmech_torsion_definition pk_statmech_torsion_definition; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech_torsion_definition
    ADD CONSTRAINT pk_statmech_torsion_definition PRIMARY KEY (torsion_id, coordinate_index);


--
-- Name: thermo pk_thermo; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo
    ADD CONSTRAINT pk_thermo PRIMARY KEY (id);


--
-- Name: thermo_nasa pk_thermo_nasa; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo_nasa
    ADD CONSTRAINT pk_thermo_nasa PRIMARY KEY (thermo_id);


--
-- Name: thermo_point pk_thermo_point; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo_point
    ADD CONSTRAINT pk_thermo_point PRIMARY KEY (thermo_id, temperature_k);


--
-- Name: thermo_source_calculation pk_thermo_source_calculation; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo_source_calculation
    ADD CONSTRAINT pk_thermo_source_calculation PRIMARY KEY (thermo_id, calculation_id, role);


--
-- Name: transition_state pk_transition_state; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state
    ADD CONSTRAINT pk_transition_state PRIMARY KEY (id);


--
-- Name: transition_state_entry pk_transition_state_entry; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state_entry
    ADD CONSTRAINT pk_transition_state_entry PRIMARY KEY (id);


--
-- Name: transition_state_selection pk_transition_state_selection; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state_selection
    ADD CONSTRAINT pk_transition_state_selection PRIMARY KEY (id);


--
-- Name: transport pk_transport; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transport
    ADD CONSTRAINT pk_transport PRIMARY KEY (id);


--
-- Name: workflow_tool pk_workflow_tool; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.workflow_tool
    ADD CONSTRAINT pk_workflow_tool PRIMARY KEY (id);


--
-- Name: workflow_tool_release pk_workflow_tool_release; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.workflow_tool_release
    ADD CONSTRAINT pk_workflow_tool_release PRIMARY KEY (id);


--
-- Name: reaction_entry_structure_participant reaction_entry_structure_participant_order_uq; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.reaction_entry_structure_participant
    ADD CONSTRAINT reaction_entry_structure_participant_order_uq UNIQUE (reaction_entry_id, role, participant_index);


--
-- Name: software software_name_uq; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.software
    ADD CONSTRAINT software_name_uq UNIQUE (name);


--
-- Name: transition_state_selection transition_state_selection_kind_uq; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state_selection
    ADD CONSTRAINT transition_state_selection_kind_uq UNIQUE (transition_state_id, selection_kind);


--
-- Name: calculation_input_geometry uq_calculation_input_geometry; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_input_geometry
    ADD CONSTRAINT uq_calculation_input_geometry UNIQUE (calculation_id, geometry_id);


--
-- Name: calculation_output_geometry uq_calculation_output_geometry_calculation_geometry; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_output_geometry
    ADD CONSTRAINT uq_calculation_output_geometry_calculation_geometry UNIQUE (calculation_id, geometry_id);


--
-- Name: chem_reaction uq_chem_reaction_stoichiometry_hash; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.chem_reaction
    ADD CONSTRAINT uq_chem_reaction_stoichiometry_hash UNIQUE (stoichiometry_hash);


--
-- Name: geometry uq_geometry_geom_hash; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.geometry
    ADD CONSTRAINT uq_geometry_geom_hash UNIQUE (geom_hash);


--
-- Name: workflow_tool workflow_tool_name_uq; Type: CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.workflow_tool
    ADD CONSTRAINT workflow_tool_name_uq UNIQUE (name);


--
-- Name: calculation_dependency_child_freq_on_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX calculation_dependency_child_freq_on_uq ON public.calculation_dependency USING btree (child_calculation_id) WHERE (dependency_role = 'freq_on'::public.calculation_dependency_role);


--
-- Name: calculation_dependency_child_neb_parent_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX calculation_dependency_child_neb_parent_uq ON public.calculation_dependency USING btree (child_calculation_id) WHERE (dependency_role = 'neb_parent'::public.calculation_dependency_role);


--
-- Name: calculation_dependency_child_optimized_from_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX calculation_dependency_child_optimized_from_uq ON public.calculation_dependency USING btree (child_calculation_id) WHERE (dependency_role = 'optimized_from'::public.calculation_dependency_role);


--
-- Name: calculation_dependency_child_scan_parent_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX calculation_dependency_child_scan_parent_uq ON public.calculation_dependency USING btree (child_calculation_id) WHERE (dependency_role = 'scan_parent'::public.calculation_dependency_role);


--
-- Name: calculation_dependency_child_single_point_on_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX calculation_dependency_child_single_point_on_uq ON public.calculation_dependency USING btree (child_calculation_id) WHERE (dependency_role = 'single_point_on'::public.calculation_dependency_role);


--
-- Name: conformer_assignment_scheme_name_version_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX conformer_assignment_scheme_name_version_uq ON public.conformer_assignment_scheme USING btree (name, version);


--
-- Name: conformer_calculation_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX conformer_calculation_uq ON public.conformer_observation USING btree (calculation_id);


--
-- Name: conformer_group_idx; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE INDEX conformer_group_idx ON public.conformer_observation USING btree (conformer_group_id);


--
-- Name: conformer_group_species_entry_idx; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE INDEX conformer_group_species_entry_idx ON public.conformer_group USING btree (species_entry_id);


--
-- Name: conformer_group_species_entry_label_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX conformer_group_species_entry_label_uq ON public.conformer_group USING btree (species_entry_id, label);


--
-- Name: conformer_selection_kind_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX conformer_selection_kind_uq ON public.conformer_selection USING btree (conformer_group_id, assignment_scheme_id, selection_kind) NULLS NOT DISTINCT;


--
-- Name: software_release_dedupe_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX software_release_dedupe_uq ON public.software_release USING btree (software_id, version, revision, build) NULLS NOT DISTINCT;


--
-- Name: species_entry_identity_idx; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX species_entry_identity_idx ON public.species_entry USING btree (species_id, stereo_kind, stereo_label, electronic_state_kind, electronic_state_label, term_symbol, isotopologue_label) NULLS NOT DISTINCT;


--
-- Name: species_entry_review_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX species_entry_review_uq ON public.species_entry_review USING btree (species_entry_id, user_id, role);


--
-- Name: species_entry_species_idx; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE INDEX species_entry_species_idx ON public.species_entry USING btree (species_id);


--
-- Name: species_inchi_key_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX species_inchi_key_uq ON public.species USING btree (inchi_key);


--
-- Name: statmech_dedupe_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX statmech_dedupe_uq ON public.statmech USING btree (species_entry_id, scientific_origin, workflow_tool_release_id, software_release_id, statmech_treatment) NULLS NOT DISTINCT;


--
-- Name: workflow_tool_release_dedupe_uq; Type: INDEX; Schema: public; Owner: tckdb
--

CREATE UNIQUE INDEX workflow_tool_release_dedupe_uq ON public.workflow_tool_release USING btree (workflow_tool_id, version, git_commit) NULLS NOT DISTINCT;


--
-- Name: calc_freq_result fk_calc_freq_result_calculation_id_calculation; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calc_freq_result
    ADD CONSTRAINT fk_calc_freq_result_calculation_id_calculation FOREIGN KEY (calculation_id) REFERENCES public.calculation(id) DEFERRABLE;


--
-- Name: calc_opt_result fk_calc_opt_result_calculation_id_calculation; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calc_opt_result
    ADD CONSTRAINT fk_calc_opt_result_calculation_id_calculation FOREIGN KEY (calculation_id) REFERENCES public.calculation(id) DEFERRABLE;


--
-- Name: calc_sp_result fk_calc_sp_result_calculation_id_calculation; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calc_sp_result
    ADD CONSTRAINT fk_calc_sp_result_calculation_id_calculation FOREIGN KEY (calculation_id) REFERENCES public.calculation(id) DEFERRABLE;


--
-- Name: calculation_artifact fk_calculation_artifact_calculation_id_calculation; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_artifact
    ADD CONSTRAINT fk_calculation_artifact_calculation_id_calculation FOREIGN KEY (calculation_id) REFERENCES public.calculation(id) DEFERRABLE;


--
-- Name: calculation fk_calculation_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation
    ADD CONSTRAINT fk_calculation_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: calculation_dependency fk_calculation_dependency_child_calculation_id_calculation; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_dependency
    ADD CONSTRAINT fk_calculation_dependency_child_calculation_id_calculation FOREIGN KEY (child_calculation_id) REFERENCES public.calculation(id) DEFERRABLE;


--
-- Name: calculation_dependency fk_calculation_dependency_parent_calculation_id_calculation; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_dependency
    ADD CONSTRAINT fk_calculation_dependency_parent_calculation_id_calculation FOREIGN KEY (parent_calculation_id) REFERENCES public.calculation(id) DEFERRABLE;


--
-- Name: calculation_input_geometry fk_calculation_input_geometry_calculation_id_calculation; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_input_geometry
    ADD CONSTRAINT fk_calculation_input_geometry_calculation_id_calculation FOREIGN KEY (calculation_id) REFERENCES public.calculation(id) DEFERRABLE;


--
-- Name: calculation_input_geometry fk_calculation_input_geometry_geometry_id_geometry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_input_geometry
    ADD CONSTRAINT fk_calculation_input_geometry_geometry_id_geometry FOREIGN KEY (geometry_id) REFERENCES public.geometry(id) DEFERRABLE;


--
-- Name: calculation fk_calculation_literature_id_literature; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation
    ADD CONSTRAINT fk_calculation_literature_id_literature FOREIGN KEY (literature_id) REFERENCES public.literature(id) DEFERRABLE;


--
-- Name: calculation fk_calculation_lot_id_level_of_theory; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation
    ADD CONSTRAINT fk_calculation_lot_id_level_of_theory FOREIGN KEY (lot_id) REFERENCES public.level_of_theory(id) DEFERRABLE;


--
-- Name: calculation_output_geometry fk_calculation_output_geometry_calculation_id_calculation; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_output_geometry
    ADD CONSTRAINT fk_calculation_output_geometry_calculation_id_calculation FOREIGN KEY (calculation_id) REFERENCES public.calculation(id) DEFERRABLE;


--
-- Name: calculation_output_geometry fk_calculation_output_geometry_geometry_id_geometry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation_output_geometry
    ADD CONSTRAINT fk_calculation_output_geometry_geometry_id_geometry FOREIGN KEY (geometry_id) REFERENCES public.geometry(id) DEFERRABLE;


--
-- Name: calculation fk_calculation_software_release_id_software_release; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation
    ADD CONSTRAINT fk_calculation_software_release_id_software_release FOREIGN KEY (software_release_id) REFERENCES public.software_release(id) DEFERRABLE;


--
-- Name: calculation fk_calculation_species_entry_id_species_entry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation
    ADD CONSTRAINT fk_calculation_species_entry_id_species_entry FOREIGN KEY (species_entry_id) REFERENCES public.species_entry(id) DEFERRABLE;


--
-- Name: calculation fk_calculation_transition_state_entry_id_transition_state_entry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation
    ADD CONSTRAINT fk_calculation_transition_state_entry_id_transition_state_entry FOREIGN KEY (transition_state_entry_id) REFERENCES public.transition_state_entry(id) DEFERRABLE;


--
-- Name: calculation fk_calculation_workflow_tool_release_id_workflow_tool_release; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.calculation
    ADD CONSTRAINT fk_calculation_workflow_tool_release_id_workflow_tool_release FOREIGN KEY (workflow_tool_release_id) REFERENCES public.workflow_tool_release(id) DEFERRABLE;


--
-- Name: conformer_assignment_scheme fk_conformer_assignment_scheme_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_assignment_scheme
    ADD CONSTRAINT fk_conformer_assignment_scheme_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: conformer_group fk_conformer_group_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_group
    ADD CONSTRAINT fk_conformer_group_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: conformer_group fk_conformer_group_species_entry_id_species_entry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_group
    ADD CONSTRAINT fk_conformer_group_species_entry_id_species_entry FOREIGN KEY (species_entry_id) REFERENCES public.species_entry(id) DEFERRABLE;


--
-- Name: conformer_observation fk_conformer_observation_assignment_scheme_id_conformer_133b; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_observation
    ADD CONSTRAINT fk_conformer_observation_assignment_scheme_id_conformer_133b FOREIGN KEY (assignment_scheme_id) REFERENCES public.conformer_assignment_scheme(id) DEFERRABLE;


--
-- Name: conformer_observation fk_conformer_observation_calculation_id_calculation; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_observation
    ADD CONSTRAINT fk_conformer_observation_calculation_id_calculation FOREIGN KEY (calculation_id) REFERENCES public.calculation(id) DEFERRABLE;


--
-- Name: conformer_observation fk_conformer_observation_conformer_group_id_conformer_group; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_observation
    ADD CONSTRAINT fk_conformer_observation_conformer_group_id_conformer_group FOREIGN KEY (conformer_group_id) REFERENCES public.conformer_group(id) DEFERRABLE;


--
-- Name: conformer_observation fk_conformer_observation_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_observation
    ADD CONSTRAINT fk_conformer_observation_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: conformer_selection fk_conformer_selection_assignment_scheme_id_conformer_a_a968; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_selection
    ADD CONSTRAINT fk_conformer_selection_assignment_scheme_id_conformer_a_a968 FOREIGN KEY (assignment_scheme_id) REFERENCES public.conformer_assignment_scheme(id) DEFERRABLE;


--
-- Name: conformer_selection fk_conformer_selection_conformer_group_id_conformer_group; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_selection
    ADD CONSTRAINT fk_conformer_selection_conformer_group_id_conformer_group FOREIGN KEY (conformer_group_id) REFERENCES public.conformer_group(id) DEFERRABLE;


--
-- Name: conformer_selection fk_conformer_selection_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.conformer_selection
    ADD CONSTRAINT fk_conformer_selection_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: geometry_atom fk_geometry_atom_geometry_id_geometry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.geometry_atom
    ADD CONSTRAINT fk_geometry_atom_geometry_id_geometry FOREIGN KEY (geometry_id) REFERENCES public.geometry(id);


--
-- Name: kinetics fk_kinetics_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.kinetics
    ADD CONSTRAINT fk_kinetics_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: kinetics fk_kinetics_literature_id_literature; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.kinetics
    ADD CONSTRAINT fk_kinetics_literature_id_literature FOREIGN KEY (literature_id) REFERENCES public.literature(id) DEFERRABLE;


--
-- Name: kinetics fk_kinetics_reaction_entry_id_reaction_entry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.kinetics
    ADD CONSTRAINT fk_kinetics_reaction_entry_id_reaction_entry FOREIGN KEY (reaction_entry_id) REFERENCES public.reaction_entry(id) DEFERRABLE;


--
-- Name: kinetics fk_kinetics_software_release_id_software_release; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.kinetics
    ADD CONSTRAINT fk_kinetics_software_release_id_software_release FOREIGN KEY (software_release_id) REFERENCES public.software_release(id) DEFERRABLE;


--
-- Name: kinetics_source_calculation fk_kinetics_source_calculation_calculation_id_calculation; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.kinetics_source_calculation
    ADD CONSTRAINT fk_kinetics_source_calculation_calculation_id_calculation FOREIGN KEY (calculation_id) REFERENCES public.calculation(id) DEFERRABLE;


--
-- Name: kinetics_source_calculation fk_kinetics_source_calculation_kinetics_id_kinetics; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.kinetics_source_calculation
    ADD CONSTRAINT fk_kinetics_source_calculation_kinetics_id_kinetics FOREIGN KEY (kinetics_id) REFERENCES public.kinetics(id) DEFERRABLE;


--
-- Name: kinetics fk_kinetics_workflow_tool_release_id_workflow_tool_release; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.kinetics
    ADD CONSTRAINT fk_kinetics_workflow_tool_release_id_workflow_tool_release FOREIGN KEY (workflow_tool_release_id) REFERENCES public.workflow_tool_release(id) DEFERRABLE;


--
-- Name: literature_author fk_literature_author_author_id_author; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.literature_author
    ADD CONSTRAINT fk_literature_author_author_id_author FOREIGN KEY (author_id) REFERENCES public.author(id) DEFERRABLE;


--
-- Name: literature_author fk_literature_author_literature_id_literature; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.literature_author
    ADD CONSTRAINT fk_literature_author_literature_id_literature FOREIGN KEY (literature_id) REFERENCES public.literature(id) DEFERRABLE;


--
-- Name: network fk_network_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.network
    ADD CONSTRAINT fk_network_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: network fk_network_literature_id_literature; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.network
    ADD CONSTRAINT fk_network_literature_id_literature FOREIGN KEY (literature_id) REFERENCES public.literature(id) DEFERRABLE;


--
-- Name: network_reaction fk_network_reaction_network_id_network; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.network_reaction
    ADD CONSTRAINT fk_network_reaction_network_id_network FOREIGN KEY (network_id) REFERENCES public.network(id) DEFERRABLE;


--
-- Name: network_reaction fk_network_reaction_reaction_entry_id_reaction_entry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.network_reaction
    ADD CONSTRAINT fk_network_reaction_reaction_entry_id_reaction_entry FOREIGN KEY (reaction_entry_id) REFERENCES public.reaction_entry(id) DEFERRABLE;


--
-- Name: network fk_network_software_release_id_software_release; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.network
    ADD CONSTRAINT fk_network_software_release_id_software_release FOREIGN KEY (software_release_id) REFERENCES public.software_release(id) DEFERRABLE;


--
-- Name: network_species fk_network_species_network_id_network; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.network_species
    ADD CONSTRAINT fk_network_species_network_id_network FOREIGN KEY (network_id) REFERENCES public.network(id) DEFERRABLE;


--
-- Name: network_species fk_network_species_species_entry_id_species_entry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.network_species
    ADD CONSTRAINT fk_network_species_species_entry_id_species_entry FOREIGN KEY (species_entry_id) REFERENCES public.species_entry(id) DEFERRABLE;


--
-- Name: network fk_network_workflow_tool_release_id_workflow_tool_release; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.network
    ADD CONSTRAINT fk_network_workflow_tool_release_id_workflow_tool_release FOREIGN KEY (workflow_tool_release_id) REFERENCES public.workflow_tool_release(id) DEFERRABLE;


--
-- Name: reaction_entry fk_reaction_entry_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.reaction_entry
    ADD CONSTRAINT fk_reaction_entry_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: reaction_entry fk_reaction_entry_reaction_id_chem_reaction; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.reaction_entry
    ADD CONSTRAINT fk_reaction_entry_reaction_id_chem_reaction FOREIGN KEY (reaction_id) REFERENCES public.chem_reaction(id) DEFERRABLE;


--
-- Name: reaction_entry_structure_participant fk_reaction_entry_structure_participant_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.reaction_entry_structure_participant
    ADD CONSTRAINT fk_reaction_entry_structure_participant_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: reaction_entry_structure_participant fk_reaction_entry_structure_participant_reaction_entry__ee77; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.reaction_entry_structure_participant
    ADD CONSTRAINT fk_reaction_entry_structure_participant_reaction_entry__ee77 FOREIGN KEY (reaction_entry_id) REFERENCES public.reaction_entry(id) DEFERRABLE;


--
-- Name: reaction_entry_structure_participant fk_reaction_entry_structure_participant_species_entry_i_f32c; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.reaction_entry_structure_participant
    ADD CONSTRAINT fk_reaction_entry_structure_participant_species_entry_i_f32c FOREIGN KEY (species_entry_id) REFERENCES public.species_entry(id) DEFERRABLE;


--
-- Name: reaction_participant fk_reaction_participant_reaction_id_chem_reaction; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.reaction_participant
    ADD CONSTRAINT fk_reaction_participant_reaction_id_chem_reaction FOREIGN KEY (reaction_id) REFERENCES public.chem_reaction(id) DEFERRABLE;


--
-- Name: reaction_participant fk_reaction_participant_species_id_species; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.reaction_participant
    ADD CONSTRAINT fk_reaction_participant_species_id_species FOREIGN KEY (species_id) REFERENCES public.species(id) DEFERRABLE;


--
-- Name: software_release fk_software_release_software_id_software; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.software_release
    ADD CONSTRAINT fk_software_release_software_id_software FOREIGN KEY (software_id) REFERENCES public.software(id) DEFERRABLE;


--
-- Name: species_entry fk_species_entry_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.species_entry
    ADD CONSTRAINT fk_species_entry_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: species_entry_review fk_species_entry_review_species_entry_id_species_entry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.species_entry_review
    ADD CONSTRAINT fk_species_entry_review_species_entry_id_species_entry FOREIGN KEY (species_entry_id) REFERENCES public.species_entry(id) DEFERRABLE;


--
-- Name: species_entry_review fk_species_entry_review_user_id_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.species_entry_review
    ADD CONSTRAINT fk_species_entry_review_user_id_app_user FOREIGN KEY (user_id) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: species_entry fk_species_entry_species_id_species; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.species_entry
    ADD CONSTRAINT fk_species_entry_species_id_species FOREIGN KEY (species_id) REFERENCES public.species(id) DEFERRABLE;


--
-- Name: statmech fk_statmech_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech
    ADD CONSTRAINT fk_statmech_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: statmech fk_statmech_literature_id_literature; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech
    ADD CONSTRAINT fk_statmech_literature_id_literature FOREIGN KEY (literature_id) REFERENCES public.literature(id) DEFERRABLE;


--
-- Name: statmech fk_statmech_software_release_id_software_release; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech
    ADD CONSTRAINT fk_statmech_software_release_id_software_release FOREIGN KEY (software_release_id) REFERENCES public.software_release(id) DEFERRABLE;


--
-- Name: statmech_source_calculation fk_statmech_source_calculation_calculation_id_calculation; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech_source_calculation
    ADD CONSTRAINT fk_statmech_source_calculation_calculation_id_calculation FOREIGN KEY (calculation_id) REFERENCES public.calculation(id) DEFERRABLE;


--
-- Name: statmech_source_calculation fk_statmech_source_calculation_statmech_id_statmech; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech_source_calculation
    ADD CONSTRAINT fk_statmech_source_calculation_statmech_id_statmech FOREIGN KEY (statmech_id) REFERENCES public.statmech(id) DEFERRABLE;


--
-- Name: statmech fk_statmech_species_entry_id_species_entry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech
    ADD CONSTRAINT fk_statmech_species_entry_id_species_entry FOREIGN KEY (species_entry_id) REFERENCES public.species_entry(id) DEFERRABLE;


--
-- Name: statmech_torsion_definition fk_statmech_torsion_definition_torsion_id_statmech_torsion; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech_torsion_definition
    ADD CONSTRAINT fk_statmech_torsion_definition_torsion_id_statmech_torsion FOREIGN KEY (torsion_id) REFERENCES public.statmech_torsion(id) DEFERRABLE;


--
-- Name: statmech_torsion fk_statmech_torsion_source_scan_calculation_id_calculation; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech_torsion
    ADD CONSTRAINT fk_statmech_torsion_source_scan_calculation_id_calculation FOREIGN KEY (source_scan_calculation_id) REFERENCES public.calculation(id) DEFERRABLE;


--
-- Name: statmech_torsion fk_statmech_torsion_statmech_id_statmech; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech_torsion
    ADD CONSTRAINT fk_statmech_torsion_statmech_id_statmech FOREIGN KEY (statmech_id) REFERENCES public.statmech(id) DEFERRABLE;


--
-- Name: statmech fk_statmech_workflow_tool_release_id_workflow_tool_release; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.statmech
    ADD CONSTRAINT fk_statmech_workflow_tool_release_id_workflow_tool_release FOREIGN KEY (workflow_tool_release_id) REFERENCES public.workflow_tool_release(id) DEFERRABLE;


--
-- Name: thermo fk_thermo_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo
    ADD CONSTRAINT fk_thermo_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: thermo fk_thermo_literature_id_literature; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo
    ADD CONSTRAINT fk_thermo_literature_id_literature FOREIGN KEY (literature_id) REFERENCES public.literature(id) DEFERRABLE;


--
-- Name: thermo_nasa fk_thermo_nasa_thermo_id_thermo; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo_nasa
    ADD CONSTRAINT fk_thermo_nasa_thermo_id_thermo FOREIGN KEY (thermo_id) REFERENCES public.thermo(id) DEFERRABLE;


--
-- Name: thermo_point fk_thermo_point_thermo_id_thermo; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo_point
    ADD CONSTRAINT fk_thermo_point_thermo_id_thermo FOREIGN KEY (thermo_id) REFERENCES public.thermo(id) DEFERRABLE;


--
-- Name: thermo fk_thermo_software_release_id_software_release; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo
    ADD CONSTRAINT fk_thermo_software_release_id_software_release FOREIGN KEY (software_release_id) REFERENCES public.software_release(id) DEFERRABLE;


--
-- Name: thermo_source_calculation fk_thermo_source_calculation_calculation_id_calculation; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo_source_calculation
    ADD CONSTRAINT fk_thermo_source_calculation_calculation_id_calculation FOREIGN KEY (calculation_id) REFERENCES public.calculation(id) DEFERRABLE;


--
-- Name: thermo_source_calculation fk_thermo_source_calculation_thermo_id_thermo; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo_source_calculation
    ADD CONSTRAINT fk_thermo_source_calculation_thermo_id_thermo FOREIGN KEY (thermo_id) REFERENCES public.thermo(id) DEFERRABLE;


--
-- Name: thermo fk_thermo_species_entry_id_species_entry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo
    ADD CONSTRAINT fk_thermo_species_entry_id_species_entry FOREIGN KEY (species_entry_id) REFERENCES public.species_entry(id) DEFERRABLE;


--
-- Name: thermo fk_thermo_workflow_tool_release_id_workflow_tool_release; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.thermo
    ADD CONSTRAINT fk_thermo_workflow_tool_release_id_workflow_tool_release FOREIGN KEY (workflow_tool_release_id) REFERENCES public.workflow_tool_release(id) DEFERRABLE;


--
-- Name: transition_state fk_transition_state_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state
    ADD CONSTRAINT fk_transition_state_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: transition_state_entry fk_transition_state_entry_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state_entry
    ADD CONSTRAINT fk_transition_state_entry_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: transition_state_entry fk_transition_state_entry_transition_state_id_transition_state; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state_entry
    ADD CONSTRAINT fk_transition_state_entry_transition_state_id_transition_state FOREIGN KEY (transition_state_id) REFERENCES public.transition_state(id) DEFERRABLE;


--
-- Name: transition_state fk_transition_state_reaction_entry_id_reaction_entry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state
    ADD CONSTRAINT fk_transition_state_reaction_entry_id_reaction_entry FOREIGN KEY (reaction_entry_id) REFERENCES public.reaction_entry(id) DEFERRABLE;


--
-- Name: transition_state_selection fk_transition_state_selection_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state_selection
    ADD CONSTRAINT fk_transition_state_selection_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: transition_state_selection fk_transition_state_selection_transition_state_entry_id_f48d; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state_selection
    ADD CONSTRAINT fk_transition_state_selection_transition_state_entry_id_f48d FOREIGN KEY (transition_state_entry_id) REFERENCES public.transition_state_entry(id) DEFERRABLE;


--
-- Name: transition_state_selection fk_transition_state_selection_transition_state_id_trans_c45a; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transition_state_selection
    ADD CONSTRAINT fk_transition_state_selection_transition_state_id_trans_c45a FOREIGN KEY (transition_state_id) REFERENCES public.transition_state(id) DEFERRABLE;


--
-- Name: transport fk_transport_created_by_app_user; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transport
    ADD CONSTRAINT fk_transport_created_by_app_user FOREIGN KEY (created_by) REFERENCES public.app_user(id) DEFERRABLE;


--
-- Name: transport fk_transport_literature_id_literature; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transport
    ADD CONSTRAINT fk_transport_literature_id_literature FOREIGN KEY (literature_id) REFERENCES public.literature(id) DEFERRABLE;


--
-- Name: transport fk_transport_software_release_id_software_release; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transport
    ADD CONSTRAINT fk_transport_software_release_id_software_release FOREIGN KEY (software_release_id) REFERENCES public.software_release(id) DEFERRABLE;


--
-- Name: transport fk_transport_species_entry_id_species_entry; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transport
    ADD CONSTRAINT fk_transport_species_entry_id_species_entry FOREIGN KEY (species_entry_id) REFERENCES public.species_entry(id) DEFERRABLE;


--
-- Name: transport fk_transport_workflow_tool_release_id_workflow_tool_release; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.transport
    ADD CONSTRAINT fk_transport_workflow_tool_release_id_workflow_tool_release FOREIGN KEY (workflow_tool_release_id) REFERENCES public.workflow_tool_release(id) DEFERRABLE;


--
-- Name: workflow_tool_release fk_workflow_tool_release_workflow_tool_id_workflow_tool; Type: FK CONSTRAINT; Schema: public; Owner: tckdb
--

ALTER TABLE ONLY public.workflow_tool_release
    ADD CONSTRAINT fk_workflow_tool_release_workflow_tool_id_workflow_tool FOREIGN KEY (workflow_tool_id) REFERENCES public.workflow_tool(id) DEFERRABLE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: tckdb
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- PostgreSQL database dump complete
--

\unrestrict Pjc0PLdNVvrseDo0MsHPJKxwLmS24j9kvh3pjPZ6EztUfSlgwKiBOuPaIp6BuT2


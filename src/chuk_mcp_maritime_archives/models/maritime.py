"""
Pydantic v2 models for maritime domain data structures.

These models represent the core domain objects of the maritime archives
system -- vessels, positions, voyages, cargo, personnel, incidents,
and hull profiles.  They are analogous to models/stac.py in chuk-mcp-stac:
pure domain models with ``extra="allow"`` so that additional fields from
archival sources are preserved when round-tripping through
``model_validate`` / ``model_dump``.

These are NOT response/envelope models (those live elsewhere).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Position & uncertainty
# ---------------------------------------------------------------------------


class PositionUncertainty(BaseModel):
    """Describes the uncertainty envelope around a geographic position."""

    model_config = ConfigDict(extra="allow")

    type: str = Field(
        ...,
        description="Uncertainty geometry type, e.g. 'circle', 'ellipse', 'box'.",
    )
    radius_km: float = Field(
        ...,
        description="Radius of the uncertainty circle in kilometres.",
    )
    confidence: float = Field(
        ...,
        description="Confidence level as a fraction (0.0 - 1.0).",
    )
    source: str = Field(
        ...,
        description="Provenance of the uncertainty estimate, e.g. 'dead_reckoning', 'archival'.",
    )
    notes: str | None = Field(
        None,
        description="Free-text notes on the uncertainty derivation.",
    )


class Position(BaseModel):
    """A geographic position with optional uncertainty metadata."""

    model_config = ConfigDict(extra="allow")

    lat: float = Field(
        ...,
        description="Latitude in decimal degrees (WGS-84).",
    )
    lon: float = Field(
        ...,
        description="Longitude in decimal degrees (WGS-84).",
    )
    uncertainty: PositionUncertainty | None = Field(
        None,
        description="Uncertainty envelope for this position.",
    )


# ---------------------------------------------------------------------------
# Voyage waypoints
# ---------------------------------------------------------------------------


class Waypoint(BaseModel):
    """A single waypoint in a voyage itinerary."""

    model_config = ConfigDict(extra="allow")

    port: str = Field(
        ...,
        description="Port or anchorage name.",
    )
    date: str | None = Field(
        None,
        description="Date of the event at this waypoint (ISO-8601 or partial).",
    )
    event: str = Field(
        ...,
        description="Type of event, e.g. 'departure', 'arrival', 'resupply', 'careening'.",
    )


# ---------------------------------------------------------------------------
# Vessel description
# ---------------------------------------------------------------------------


class VesselDimensions(BaseModel):
    """Physical dimensions of a vessel."""

    model_config = ConfigDict(extra="allow")

    length_m: float | None = Field(
        None,
        description="Overall length in metres.",
    )
    beam_m: float | None = Field(
        None,
        description="Maximum beam (width) in metres.",
    )
    draught_m: float | None = Field(
        None,
        description="Maximum draught (depth below waterline) in metres.",
    )
    source: str | None = Field(
        None,
        description="Source of the dimension data, e.g. 'admiralty_survey', 'estimated'.",
    )


class Vessel(BaseModel):
    """
    Core vessel record.

    Captures identity, construction, and classification data for a single
    ship as it appears in archival sources.
    """

    model_config = ConfigDict(extra="allow")

    name: str = Field(
        ...,
        description="Primary name of the vessel.",
    )
    type: str | None = Field(
        None,
        description="Ship type code, e.g. 'retourschip', 'fluit', 'jacht'.",
    )
    type_description: str | None = Field(
        None,
        description="Human-readable description of the ship type.",
    )
    tonnage: int | None = Field(
        None,
        description="Registered tonnage.",
    )
    tonnage_type: str | None = Field(
        None,
        description="Tonnage measurement system, e.g. 'lasten', 'bm', 'nrt'.",
    )
    built_year: int | None = Field(
        None,
        description="Year the vessel was built.",
    )
    built_shipyard: str | None = Field(
        None,
        description="Name or location of the shipyard where the vessel was built.",
    )
    chamber: str | None = Field(
        None,
        description="VOC chamber (kamer) responsible, e.g. 'Amsterdam', 'Zeeland'.",
    )
    dimensions: VesselDimensions | None = Field(
        None,
        description="Physical dimensions of the vessel.",
    )


# ---------------------------------------------------------------------------
# Personnel
# ---------------------------------------------------------------------------


class PersonnelSummary(BaseModel):
    """Summary of the people aboard for a voyage or incident."""

    model_config = ConfigDict(extra="allow")

    captain: str | None = Field(
        None,
        description="Name of the ship's captain (schipper / kapitein).",
    )
    crew_total: int | None = Field(
        None,
        description="Total number of crew and passengers.",
    )
    soldiers: int | None = Field(
        None,
        description="Number of soldiers aboard.",
    )
    sailors: int | None = Field(
        None,
        description="Number of sailors aboard.",
    )
    craftsmen: int | None = Field(
        None,
        description="Number of craftsmen (ambachtslieden) aboard.",
    )
    officers: int | None = Field(
        None,
        description="Number of officers aboard.",
    )
    source: str | None = Field(
        None,
        description="Provenance of the personnel data.",
    )


# ---------------------------------------------------------------------------
# Cargo
# ---------------------------------------------------------------------------


class CargoSummary(BaseModel):
    """High-level cargo information for a voyage."""

    model_config = ConfigDict(extra="allow")

    summary: str | None = Field(
        None,
        description="Textual summary of the cargo.",
    )
    value_guilders: float | None = Field(
        None,
        description="Estimated cargo value in Dutch guilders.",
    )
    manifest_available: bool = Field(
        False,
        description="Whether a detailed cargo manifest is available.",
    )
    source: str | None = Field(
        None,
        description="Provenance of the cargo data.",
    )


# ---------------------------------------------------------------------------
# Incidents (wrecks, captures, etc.)
# ---------------------------------------------------------------------------


class Incident(BaseModel):
    """
    Describes a significant incident in a vessel's history.

    Covers shipwrecks, captures, groundings, fires, and other calamities
    recorded in archival sources.
    """

    model_config = ConfigDict(extra="allow")

    fate: str = Field(
        ...,
        description="Outcome category, e.g. 'wrecked', 'captured', 'foundered', 'fire'.",
    )
    date: str | None = Field(
        None,
        description="Date of the incident (ISO-8601 or partial).",
    )
    date_precision: str | None = Field(
        None,
        description="Precision of the date, e.g. 'day', 'month', 'year', 'circa'.",
    )
    cause: str | None = Field(
        None,
        description="Primary cause category, e.g. 'storm', 'reef', 'navigation_error'.",
    )
    cause_detail: str | None = Field(
        None,
        description="Narrative detail on the cause.",
    )
    position: Position | None = Field(
        None,
        description="Geographic position of the incident.",
    )
    narrative: str | None = Field(
        None,
        description="Free-text narrative of the incident.",
    )
    lives_lost: int | None = Field(
        None,
        description="Number of lives lost.",
    )
    survivors: int | None = Field(
        None,
        description="Number of survivors.",
    )
    archaeological_status: str | None = Field(
        None,
        description="Current archaeological status, e.g. 'located', 'excavated', 'unlocated'.",
    )
    source_documents: list[str] = Field(
        default_factory=list,
        description="List of archival source document references.",
    )


# ---------------------------------------------------------------------------
# Source references
# ---------------------------------------------------------------------------


class SourceReference(BaseModel):
    """A bibliographic or archival source reference."""

    model_config = ConfigDict(extra="allow")

    reference: str = Field(
        ...,
        description="Citation string or archival call number.",
    )
    url: str | None = Field(
        None,
        description="URL to the source document, if available online.",
    )


# ---------------------------------------------------------------------------
# Hull profiles & hydrodynamics
# ---------------------------------------------------------------------------


class HullHydrodynamics(BaseModel):
    """
    Hydrodynamic parameters for a hull profile.

    Each parameter is stored as a dict with 'min', 'max', and 'typical'
    keys, reflecting the range across known examples of the hull type.
    """

    model_config = ConfigDict(extra="allow")

    displacement_tonnes: dict[str, float] = Field(
        default_factory=dict,
        description="Displacement in metric tonnes as {min, max, typical}.",
    )
    block_coefficient: dict[str, float] = Field(
        default_factory=dict,
        description="Block coefficient (Cb) as {min, max, typical}.",
    )
    waterplane_area_m2: dict[str, float] = Field(
        default_factory=dict,
        description="Waterplane area in square metres as {min, max, typical}.",
    )
    drag_coefficient_broadside: dict[str, float] = Field(
        default_factory=dict,
        description="Broadside hydrodynamic drag coefficient as {min, max, typical}.",
    )
    drag_coefficient_longitudinal: dict[str, float] = Field(
        default_factory=dict,
        description="Longitudinal hydrodynamic drag coefficient as {min, max, typical}.",
    )
    windage_area_m2: dict[str, float] = Field(
        default_factory=dict,
        description="Above-waterline windage area in square metres as {min, max, typical}.",
    )
    windage_coefficient: dict[str, float] = Field(
        default_factory=dict,
        description="Wind drag coefficient as {min, max, typical}.",
    )


class SinkingCharacteristics(BaseModel):
    """
    Modelled sinking behaviour for a hull type.

    Used by drift and dispersal simulations to estimate wreck-site
    deposition patterns.
    """

    model_config = ConfigDict(extra="allow")

    likely_orientation: list[str] = Field(
        default_factory=list,
        description=(
            "Likely orientations during sinking, e.g. ['keel_down', 'beam_ends', 'inverted']."
        ),
    )
    orientation_weights: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Probability weight for each orientation (keys match likely_orientation entries)."
        ),
    )
    terminal_velocity_ms: dict[str, float] = Field(
        default_factory=dict,
        description="Terminal sinking velocity in m/s as {min, max, typical}.",
    )
    notes: str | None = Field(
        None,
        description="Additional notes on sinking behaviour.",
    )


class HullProfile(BaseModel):
    """
    Complete hull profile for a historical ship type.

    Aggregates physical dimensions, hydrodynamic coefficients, sinking
    characteristics, and provenance data.  Used to drive drift models
    and to provide LLM context when reasoning about wreck-site locations.
    """

    model_config = ConfigDict(extra="allow")

    ship_type: str = Field(
        ...,
        description="Canonical ship-type identifier, e.g. 'retourschip', 'fluit'.",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the hull type.",
    )
    subtypes: dict = Field(
        default_factory=dict,
        description="Named subtypes or variants with distinguishing characteristics.",
    )
    dimensions_typical: dict = Field(
        default_factory=dict,
        description="Typical dimension ranges (length, beam, draught) for the type.",
    )
    hydrodynamics: HullHydrodynamics = Field(
        default_factory=HullHydrodynamics,
        description="Hydrodynamic parameters for drift modelling.",
    )
    sinking_characteristics: SinkingCharacteristics = Field(
        default_factory=SinkingCharacteristics,
        description="Modelled sinking behaviour for dispersal estimation.",
    )
    reference_wrecks: list[dict] = Field(
        default_factory=list,
        description=(
            "Known wreck sites used as reference data for this hull type. "
            "Each entry is a dict with at least 'name' and 'location'."
        ),
    )
    sources: list[SourceReference] = Field(
        default_factory=list,
        description="Bibliographic and archival sources for the profile data.",
    )
    llm_guidance: str | None = Field(
        None,
        description=(
            "Free-text guidance for LLM agents reasoning about this hull type, "
            "including caveats and interpretation notes."
        ),
    )

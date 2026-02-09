"""
Pydantic v2 response models for chuk-mcp-maritime-archives.

Every tool returns one of these typed envelopes. Response models use
``extra="forbid"`` to catch stale fields early.  Each model carries a
``to_text()`` method so the ``format_response()`` helper can switch
between JSON and human-readable output.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def format_response(response: BaseModel, output_mode: str = "json") -> str:
    """Format a response model as JSON or text."""
    if output_mode == "text":
        if hasattr(response, "to_text"):
            return response.to_text()
        return response.model_dump_json(indent=2, exclude_none=True)
    return response.model_dump_json(indent=2, exclude_none=True)


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: str
    message: str = ""

    def to_text(self) -> str:
        return f"Error: {self.error}"


# ---------------------------------------------------------------------------
# Archive discovery
# ---------------------------------------------------------------------------


class ArchiveInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    archive_id: str
    name: str
    organisation: str | None = None
    coverage_start: str | None = None
    coverage_end: str | None = None
    record_types: list[str] = Field(default_factory=list)
    total_records: int | None = None
    description: str | None = None


class ArchiveListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    archive_count: int
    archives: list[ArchiveInfo]
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        for a in self.archives:
            lines.append(f"  {a.archive_id}: {a.name}")
            if a.coverage_start:
                lines.append(f"    Period: {a.coverage_start}-{a.coverage_end}")
            if a.description:
                lines.append(f"    {a.description[:80]}...")
        return "\n".join(lines)


class ArchiveDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    archive: ArchiveInfo
    message: str = ""

    def to_text(self) -> str:
        a = self.archive
        lines = [
            f"Archive: {a.name} ({a.archive_id})",
            f"Organisation: {a.organisation or 'Unknown'}",
            f"Period: {a.coverage_start or '?'}-{a.coverage_end or '?'}",
            f"Record types: {', '.join(a.record_types)}",
        ]
        if a.description:
            lines.append(f"Description: {a.description}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Voyage responses
# ---------------------------------------------------------------------------


class VoyageInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voyage_id: str
    ship_name: str
    ship_type: str | None = None
    captain: str | None = None
    departure_port: str | None = None
    departure_date: str | None = None
    destination_port: str | None = None
    fate: str | None = None
    summary: str | None = None


class VoyageSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voyage_count: int
    voyages: list[VoyageInfo]
    archive: str | None = None
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        for v in self.voyages:
            fate_str = f" [{v.fate}]" if v.fate else ""
            lines.append(f"  {v.voyage_id}: {v.ship_name}{fate_str}")
            if v.departure_port and v.departure_date:
                lines.append(
                    f"    {v.departure_port} ({v.departure_date}) -> {v.destination_port or '?'}"
                )
        return "\n".join(lines)


class VoyageDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voyage: dict[str, Any]
    message: str = ""

    def to_text(self) -> str:
        v = self.voyage
        lines = [
            f"Voyage: {v.get('voyage_id', '?')}",
            f"Ship: {v.get('ship_name', '?')} ({v.get('ship_type', '?')})",
            f"Captain: {v.get('captain', 'Unknown')}",
            f"Route: {v.get('departure_port', '?')} -> {v.get('destination_port', '?')}",
            f"Departure: {v.get('departure_date', '?')}",
            f"Fate: {v.get('fate', '?')}",
        ]
        if v.get("summary"):
            lines.append(f"Summary: {v['summary']}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Wreck responses
# ---------------------------------------------------------------------------


class WreckInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wreck_id: str
    ship_name: str
    loss_date: str | None = None
    loss_cause: str | None = None
    region: str | None = None
    status: str | None = None
    position: dict[str, Any] | None = None


class WreckSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wreck_count: int
    wrecks: list[WreckInfo]
    archive: str | None = None
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        for w in self.wrecks:
            status_str = f" [{w.status}]" if w.status else ""
            lines.append(f"  {w.wreck_id}: {w.ship_name}{status_str}")
            if w.loss_date:
                lines.append(f"    Lost: {w.loss_date} ({w.loss_cause or '?'})")
        return "\n".join(lines)


class WreckDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wreck: dict[str, Any]
    message: str = ""

    def to_text(self) -> str:
        w = self.wreck
        lines = [
            f"Wreck: {w.get('wreck_id', '?')}",
            f"Ship: {w.get('ship_name', '?')}",
            f"Lost: {w.get('loss_date', '?')} — Cause: {w.get('loss_cause', '?')}",
            f"Region: {w.get('region', '?')}",
            f"Status: {w.get('status', '?')}",
        ]
        pos = w.get("position")
        if pos:
            lines.append(
                f"Position: {pos.get('lat', '?')}°N, {pos.get('lon', '?')}°E (±{pos.get('uncertainty_km', '?')}km)"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Vessel responses
# ---------------------------------------------------------------------------


class VesselInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vessel_id: str
    name: str
    type: str | None = None
    tonnage: int | None = None
    built_year: int | None = None
    chamber: str | None = None


class VesselSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vessel_count: int
    vessels: list[VesselInfo]
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        for v in self.vessels:
            lines.append(f"  {v.vessel_id}: {v.name} ({v.type or '?'}, {v.tonnage or '?'} lasten)")
        return "\n".join(lines)


class VesselDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vessel: dict[str, Any]
    message: str = ""

    def to_text(self) -> str:
        v = self.vessel
        lines = [
            f"Vessel: {v.get('name', '?')}",
            f"Type: {v.get('type', '?')}",
            f"Tonnage: {v.get('tonnage', '?')} lasten",
            f"Built: {v.get('built_year', '?')} at {v.get('shipyard', '?')}",
            f"Chamber: {v.get('chamber', '?')}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Crew responses
# ---------------------------------------------------------------------------


class CrewInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crew_id: str
    name: str
    rank: str | None = None
    rank_english: str | None = None
    ship_name: str | None = None
    voyage_id: str | None = None


class CrewSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crew_count: int
    crew: list[CrewInfo]
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        for c in self.crew:
            lines.append(f"  {c.crew_id}: {c.name} ({c.rank_english or c.rank or '?'})")
            if c.ship_name:
                lines.append(f"    Ship: {c.ship_name}")
        return "\n".join(lines)


class CrewDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crew_member: dict[str, Any]
    message: str = ""

    def to_text(self) -> str:
        c = self.crew_member
        lines = [
            f"Crew: {c.get('name', '?')}",
            f"Rank: {c.get('rank_english', c.get('rank', '?'))}",
            f"Origin: {c.get('origin', '?')}",
            f"Ship: {c.get('ship_name', '?')}",
            f"Pay: {c.get('monthly_pay_guilders', '?')} guilders/month",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cargo responses
# ---------------------------------------------------------------------------


class CargoInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cargo_id: str
    voyage_id: str | None = None
    ship_name: str | None = None
    commodity: str
    quantity: float | None = None
    unit: str | None = None
    value_guilders: float | None = None


class CargoSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cargo_count: int
    cargo: list[CargoInfo]
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        for c in self.cargo:
            val = f" ({c.value_guilders:,.0f} guilders)" if c.value_guilders else ""
            lines.append(f"  {c.cargo_id}: {c.commodity} — {c.quantity or '?'} {c.unit or ''}{val}")
        return "\n".join(lines)


class CargoDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cargo_entries: list[dict[str, Any]]
    voyage_id: str
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, f"Manifest for voyage {self.voyage_id}:", ""]
        for c in self.cargo_entries:
            lines.append(
                f"  {c.get('commodity', '?')}: {c.get('quantity', '?')} {c.get('unit', '')}"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Location responses
# ---------------------------------------------------------------------------


class LocationInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    lat: float
    lon: float
    region: str
    type: str
    aliases: list[str] = Field(default_factory=list)
    notes: str | None = None


class LocationSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location_count: int
    locations: list[LocationInfo]
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        for loc in self.locations:
            alias_str = f" (aka {', '.join(loc.aliases)})" if loc.aliases else ""
            lines.append(f"  {loc.name}{alias_str}")
            lines.append(f"    {loc.lat:.2f}N, {loc.lon:.2f}E — {loc.region} [{loc.type}]")
            if loc.notes:
                lines.append(f"    {loc.notes}")
        return "\n".join(lines)


class LocationDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: LocationInfo
    message: str = ""

    def to_text(self) -> str:
        loc = self.location
        alias_str = f" (aka {', '.join(loc.aliases)})" if loc.aliases else ""
        lines = [
            f"Location: {loc.name}{alias_str}",
            f"Coordinates: {loc.lat:.4f}N, {loc.lon:.4f}E",
            f"Region: {loc.region}",
            f"Type: {loc.type}",
        ]
        if loc.notes:
            lines.append(f"Notes: {loc.notes}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Hull profile responses
# ---------------------------------------------------------------------------


class HullProfileListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ship_types: list[str]
    count: int
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        for t in self.ship_types:
            lines.append(f"  - {t}")
        return "\n".join(lines)


class HullProfileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: dict[str, Any]
    message: str = ""

    def to_text(self) -> str:
        p = self.profile
        lines = [
            f"Hull Profile: {p.get('ship_type', '?')}",
            f"Description: {p.get('description', '?')}",
        ]
        dims = p.get("dimensions_typical", {})
        if dims:
            lines.append(f"Length: {dims.get('length_m', {}).get('typical', '?')}m")
            lines.append(f"Beam: {dims.get('beam_m', {}).get('typical', '?')}m")
            lines.append(f"Draught: {dims.get('draught_m', {}).get('typical', '?')}m")
        guidance = p.get("llm_guidance")
        if guidance:
            lines.append(f"Guidance: {guidance}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Route responses
# ---------------------------------------------------------------------------


class RouteWaypointInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    lat: float
    lon: float
    region: str
    cumulative_days: int
    stop_days: int = 0
    notes: str | None = None


class RouteInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route_id: str
    name: str
    direction: str
    typical_duration_days: int
    waypoint_count: int


class RouteListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route_count: int
    routes: list[RouteInfo]
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        for r in self.routes:
            lines.append(f"  {r.route_id}: {r.name}")
            lines.append(
                f"    Direction: {r.direction} | ~{r.typical_duration_days} days | {r.waypoint_count} waypoints"
            )
        return "\n".join(lines)


class RouteDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route: dict[str, Any]
    message: str = ""

    def to_text(self) -> str:
        r = self.route
        lines = [
            f"Route: {r.get('name', '?')} ({r.get('route_id', '?')})",
            f"Direction: {r.get('direction', '?')}",
            f"Typical duration: ~{r.get('typical_duration_days', '?')} days",
            "",
        ]
        desc = r.get("description", "")
        if desc:
            lines.append(f"{desc}")
            lines.append("")
        lines.append("Waypoints:")
        for wp in r.get("waypoints", []):
            stop = f" (stop ~{wp['stop_days']}d)" if wp.get("stop_days") else ""
            lines.append(f"  Day {wp['cumulative_days']:>3}: {wp['name']}{stop}")
            if wp.get("notes"):
                lines.append(f"           {wp['notes']}")
        hazards = r.get("hazards", [])
        if hazards:
            lines.append("")
            lines.append("Hazards:")
            for h in hazards:
                lines.append(f"  - {h}")
        season = r.get("season_notes")
        if season:
            lines.append("")
            lines.append(f"Season: {season}")
        return "\n".join(lines)


class PositionEstimateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estimate: dict[str, Any]
    message: str = ""

    def to_text(self) -> str:
        e = self.estimate
        pos = e.get("estimated_position", {})
        seg = e.get("segment", {})
        lines = [
            f"Route: {e.get('route_name', '?')}",
            f"Departed: {e.get('departure_date', '?')} | Target: {e.get('target_date', '?')}",
            f"Elapsed: {e.get('elapsed_days', '?')} days (of ~{e.get('total_route_days', '?')})",
            f"Progress: {e.get('voyage_progress', 0) * 100:.0f}%",
            "",
            f"Estimated position: {pos.get('lat', '?')}N, {pos.get('lon', '?')}E",
            f"Region: {pos.get('region', '?')}",
            f"Segment: {seg.get('from', '?')} -> {seg.get('to', '?')} ({seg.get('progress', 0) * 100:.0f}%)",
            f"Confidence: {e.get('confidence', '?')}",
        ]
        notes = e.get("notes")
        if notes:
            lines.append(f"Notes: {notes}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Position assessment
# ---------------------------------------------------------------------------


class PositionAssessmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assessment: dict[str, Any]
    message: str = ""

    def to_text(self) -> str:
        a = self.assessment.get("assessment", {})
        lines = [
            f"Position Quality: {a.get('quality_label', '?')} (score: {a.get('quality_score', '?')})",
            f"Uncertainty: {a.get('uncertainty_type', '?')} ±{a.get('uncertainty_radius_km', '?')}km",
        ]
        recs = self.assessment.get("recommendations", {})
        if recs.get("for_drift_modelling"):
            lines.append(f"For drift modelling: {recs['for_drift_modelling']}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


class StatisticsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statistics: dict[str, Any]
    message: str = ""

    def to_text(self) -> str:
        s = self.statistics.get("summary", {})
        lines = [
            self.message,
            f"Total voyages: {s.get('total_voyages', '?')}",
            f"Total losses: {s.get('total_losses', '?')}",
            f"Loss rate: {s.get('loss_rate_percent', '?')}%",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# GeoJSON export
# ---------------------------------------------------------------------------


class GeoJSONExportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    geojson: dict[str, Any]
    feature_count: int
    artifact_ref: str | None = None
    message: str = ""

    def to_text(self) -> str:
        lines = [
            self.message,
            f"Features: {self.feature_count}",
        ]
        if self.artifact_ref:
            lines.append(f"Artifact: {self.artifact_ref}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Discovery / capabilities
# ---------------------------------------------------------------------------


class ToolInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category: str
    description: str


class CapabilitiesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    server_name: str
    version: str
    archives: list[ArchiveInfo]
    tools: list[ToolInfo]
    ship_types: list[str]
    regions: dict[str, str]
    message: str = ""

    def to_text(self) -> str:
        lines = [
            f"{self.server_name} v{self.version}",
            "",
            f"Archives ({len(self.archives)}):",
        ]
        for a in self.archives:
            lines.append(f"  {a.archive_id}: {a.name}")
        lines.append(f"\nTools ({len(self.tools)}):")
        for t in self.tools:
            lines.append(f"  {t.name} [{t.category}]: {t.description}")
        return "\n".join(lines)

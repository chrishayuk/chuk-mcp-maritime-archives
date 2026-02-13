"""
Pydantic v2 response models for chuk-mcp-maritime-archives.

Every tool returns one of these typed envelopes. Response models use
``extra="forbid"`` to catch stale fields early.  Each model carries a
``to_text()`` method so the ``format_response()`` helper can switch
between JSON and human-readable output.
"""

from __future__ import annotations

import base64
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Cursor utilities
# ---------------------------------------------------------------------------


def encode_cursor(offset: int) -> str:
    """Encode an integer offset as an opaque cursor string."""
    return base64.urlsafe_b64encode(json.dumps({"o": offset}).encode()).decode().rstrip("=")


def decode_cursor(cursor: str | None) -> int:
    """Decode an opaque cursor string to an integer offset. Returns 0 for None/empty."""
    if not cursor:
        return 0
    padded = cursor + "=" * (-len(cursor) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded))
    return int(payload["o"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _pagination_footer(count: int, total: int | None, has_more: bool, cursor: str | None) -> str:
    """Build a pagination footer for to_text() output."""
    if total is not None and has_more and cursor:
        return f'\n  Showing {count} of {total} total matches. Use cursor="{cursor}" for next page.'
    if total is not None and total > count:
        return f"\n  Showing {count} of {total} total matches."
    return ""


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
    archive: str | None = None


class VoyageSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voyage_count: int
    voyages: list[VoyageInfo]
    archive: str | None = None
    message: str = ""
    total_count: int | None = None
    next_cursor: str | None = None
    has_more: bool = False

    def to_text(self) -> str:
        lines = [self.message, ""]
        for v in self.voyages:
            fate_str = f" [{v.fate}]" if v.fate else ""
            archive_str = f" ({v.archive})" if v.archive else ""
            lines.append(f"  {v.voyage_id}: {v.ship_name}{fate_str}{archive_str}")
            if v.departure_port and v.departure_date:
                lines.append(
                    f"    {v.departure_port} ({v.departure_date}) -> {v.destination_port or '?'}"
                )
        footer = _pagination_footer(
            len(self.voyages), self.total_count, self.has_more, self.next_cursor
        )
        if footer:
            lines.append(footer)
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
# Cross-archive linking responses
# ---------------------------------------------------------------------------


class VoyageFullResponse(BaseModel):
    """Unified view of a voyage with all linked records."""

    model_config = ConfigDict(extra="forbid")

    voyage: dict[str, Any]
    wreck: dict[str, Any] | None = None
    vessel: dict[str, Any] | None = None
    hull_profile: dict[str, Any] | None = None
    cliwoc_track: dict[str, Any] | None = None
    links_found: list[str]
    message: str = ""

    def to_text(self) -> str:
        v = self.voyage
        lines = [
            self.message,
            "",
            f"Voyage: {v.get('voyage_id', '?')}",
            f"Ship: {v.get('ship_name', '?')} ({v.get('ship_type', '?')})",
            f"Captain: {v.get('captain', 'Unknown')}",
            f"Route: {v.get('departure_port', '?')} -> {v.get('destination_port', '?')}",
            f"Departure: {v.get('departure_date', '?')}",
            f"Arrival: {v.get('arrival_date', '?')}",
            f"Fate: {v.get('fate', '?')}",
        ]

        if self.wreck:
            w = self.wreck
            lines.extend(
                [
                    "",
                    "--- Wreck Record ---",
                    f"Wreck ID: {w.get('wreck_id', '?')}",
                    f"Lost: {w.get('loss_date', '?')}",
                    f"Cause: {w.get('loss_cause', '?')}",
                    f"Location: {w.get('loss_location', '?')}",
                    f"Region: {w.get('region', '?')}",
                    f"Status: {w.get('status', '?')}",
                ]
            )

        if self.vessel:
            vs = self.vessel
            lines.extend(
                [
                    "",
                    "--- Vessel ---",
                    f"Vessel ID: {vs.get('vessel_id', '?')}",
                    f"Name: {vs.get('name', '?')}",
                    f"Type: {vs.get('type', '?')}",
                    f"Tonnage: {vs.get('tonnage', '?')} lasten",
                    f"Built: {vs.get('built_year', '?')}",
                    f"Voyages: {len(vs.get('voyage_ids', []))}",
                ]
            )

        if self.hull_profile:
            hp = self.hull_profile
            lines.extend(
                [
                    "",
                    "--- Hull Profile ---",
                    f"Ship type: {hp.get('ship_type', '?')}",
                    f"Description: {hp.get('description', '?')}",
                ]
            )

        if self.cliwoc_track:
            ct = self.cliwoc_track
            lines.extend(
                [
                    "",
                    "--- CLIWOC Track ---",
                    f"CLIWOC voyage: {ct.get('voyage_id', '?')}",
                    f"Nationality: {ct.get('nationality', '?')}",
                    f"Period: {ct.get('start_date', '?')} to {ct.get('end_date', '?')}",
                    f"Positions: {ct.get('position_count', '?')}",
                ]
            )

        lines.extend(["", f"Links found: {', '.join(self.links_found) or 'none'}"])
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
    archive: str | None = None
    flag: str | None = None
    vessel_type: str | None = None
    depth_estimate_m: float | None = None


class WreckSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wreck_count: int
    wrecks: list[WreckInfo]
    archive: str | None = None
    message: str = ""
    total_count: int | None = None
    next_cursor: str | None = None
    has_more: bool = False

    def to_text(self) -> str:
        lines = [self.message, ""]
        for w in self.wrecks:
            status_str = f" [{w.status}]" if w.status else ""
            lines.append(f"  {w.wreck_id}: {w.ship_name}{status_str}")
            if w.loss_date:
                lines.append(f"    Lost: {w.loss_date} ({w.loss_cause or '?'})")
        footer = _pagination_footer(
            len(self.wrecks), self.total_count, self.has_more, self.next_cursor
        )
        if footer:
            lines.append(footer)
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
# Narrative search responses
# ---------------------------------------------------------------------------


class NarrativeHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str
    record_type: str
    archive: str
    ship_name: str
    date: str | None = None
    field: str
    snippet: str
    match_count: int = 1


class NarrativeSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_count: int
    results: list[NarrativeHit]
    query: str
    record_type: str | None = None
    archive: str | None = None
    total_count: int | None = None
    next_cursor: str | None = None
    has_more: bool = False
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        for r in self.results:
            type_tag = f"[{r.record_type}]"
            lines.append(f"  {r.record_id} {type_tag} {r.ship_name}")
            if r.date:
                lines.append(f"    Date: {r.date}  Archive: {r.archive}  Field: {r.field}")
            else:
                lines.append(f"    Archive: {r.archive}  Field: {r.field}")
            lines.append(f"    ...{r.snippet}...")
        footer = _pagination_footer(
            len(self.results), self.total_count, self.has_more, self.next_cursor
        )
        if footer:
            lines.append(footer)
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
    total_count: int | None = None
    next_cursor: str | None = None
    has_more: bool = False

    def to_text(self) -> str:
        lines = [self.message, ""]
        for v in self.vessels:
            lines.append(f"  {v.vessel_id}: {v.name} ({v.type or '?'}, {v.tonnage or '?'} lasten)")
        footer = _pagination_footer(
            len(self.vessels), self.total_count, self.has_more, self.next_cursor
        )
        if footer:
            lines.append(footer)
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
    total_count: int | None = None
    next_cursor: str | None = None
    has_more: bool = False

    def to_text(self) -> str:
        lines = [self.message, ""]
        for c in self.crew:
            lines.append(f"  {c.crew_id}: {c.name} ({c.rank_english or c.rank or '?'})")
            if c.ship_name:
                lines.append(f"    Ship: {c.ship_name}")
        footer = _pagination_footer(
            len(self.crew), self.total_count, self.has_more, self.next_cursor
        )
        if footer:
            lines.append(footer)
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
    quantity: str | float | None = None
    unit: str | None = None
    value_guilders: float | None = None


class CargoSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cargo_count: int
    cargo: list[CargoInfo]
    message: str = ""
    total_count: int | None = None
    next_cursor: str | None = None
    has_more: bool = False

    def to_text(self) -> str:
        lines = [self.message, ""]
        for c in self.cargo:
            val = f" ({c.value_guilders:,.0f} guilders)" if c.value_guilders else ""
            lines.append(f"  {c.cargo_id}: {c.commodity} — {c.quantity or '?'} {c.unit or ''}{val}")
        footer = _pagination_footer(
            len(self.cargo), self.total_count, self.has_more, self.next_cursor
        )
        if footer:
            lines.append(footer)
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


class SegmentSpeedInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment_from: str
    segment_to: str
    departure_month: int | None = None
    sample_count: int
    mean_km_day: float
    median_km_day: float
    std_dev_km_day: float
    min_km_day: float | None = None
    max_km_day: float | None = None
    p25_km_day: float | None = None
    p75_km_day: float | None = None


class SpeedProfileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route_id: str
    departure_month: int | None = None
    segment_count: int
    segments: list[SegmentSpeedInfo]
    notes: str | None = None
    message: str = ""

    def to_text(self) -> str:
        lines = [
            self.message,
            f"Route: {self.route_id}",
            f"Segments: {self.segment_count}",
            "",
        ]
        if self.departure_month:
            lines.append(f"Departure month: {self.departure_month}")
        for s in self.segments:
            lines.append(
                f"  {s.segment_from} -> {s.segment_to}: "
                f"{s.mean_km_day:.0f} km/day (median {s.median_km_day:.0f}, "
                f"std {s.std_dev_km_day:.0f}, n={s.sample_count})"
            )
        if self.notes:
            lines.append(f"\nNotes: {self.notes}")
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
# Track responses (CLIWOC ship tracks)
# ---------------------------------------------------------------------------


class TrackInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voyage_id: int
    nationality: str | None = None
    ship_name: str | None = None
    company: str | None = None
    voyage_from: str | None = None
    voyage_to: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration_days: int | None = None
    year_start: int | None = None
    year_end: int | None = None
    position_count: int = 0


class TrackSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    track_count: int
    tracks: list[TrackInfo]
    message: str = ""
    total_count: int | None = None
    next_cursor: str | None = None
    has_more: bool = False

    def to_text(self) -> str:
        lines = [self.message, ""]
        for t in self.tracks:
            nat = f" [{t.nationality}]" if t.nationality else ""
            ship = f" {t.ship_name}" if t.ship_name else ""
            lines.append(f"  Voyage {t.voyage_id}{nat}{ship}: {t.start_date} to {t.end_date}")
            lines.append(f"    {t.position_count} positions, ~{t.duration_days or '?'} days")
        footer = _pagination_footer(
            len(self.tracks), self.total_count, self.has_more, self.next_cursor
        )
        if footer:
            lines.append(footer)
        return "\n".join(lines)


class TrackDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    track: dict[str, Any]
    message: str = ""

    def to_text(self) -> str:
        t = self.track
        lines = [
            f"CLIWOC Voyage {t.get('voyage_id', '?')}",
        ]
        if t.get("ship_name"):
            lines.append(f"Ship: {t['ship_name']}")
        if t.get("company"):
            lines.append(f"Company: {t['company']}")
        lines.append(f"Nationality: {t.get('nationality', '?')}")
        if t.get("voyage_from") or t.get("voyage_to"):
            lines.append(f"Route: {t.get('voyage_from', '?')} -> {t.get('voyage_to', '?')}")
        lines.extend(
            [
                f"Period: {t.get('start_date', '?')} to {t.get('end_date', '?')}",
                f"Duration: ~{t.get('duration_days', '?')} days",
                f"Positions: {t.get('position_count', 0)}",
            ]
        )
        positions = t.get("positions", [])
        if positions:
            lines.append("")
            lines.append("Track:")
            for p in positions[:20]:
                lines.append(
                    f"  {p.get('date', '?'):12s}  {p.get('lat', '?'):7}N  {p.get('lon', '?'):7}E"
                )
            if len(positions) > 20:
                lines.append(f"  ... and {len(positions) - 20} more positions")
        return "\n".join(lines)


class NearbyTrackInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voyage_id: int
    nationality: str | None = None
    ship_name: str | None = None
    company: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration_days: int | None = None
    position_count: int = 0
    distance_km: float
    matching_position: dict[str, Any]


class NearbyTracksResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search_point: dict[str, Any]
    search_date: str
    radius_km: float
    track_count: int
    tracks: list[NearbyTrackInfo]
    message: str = ""

    def to_text(self) -> str:
        lines = [
            self.message,
            f"Search: {self.search_point.get('lat')}N, {self.search_point.get('lon')}E",
            f"Date: {self.search_date}  Radius: {self.radius_km}km",
            "",
        ]
        for t in self.tracks:
            nat = f" [{t.nationality}]" if t.nationality else ""
            pos = t.matching_position
            lines.append(
                f"  Voyage {t.voyage_id}{nat}: "
                f"{pos.get('lat')}N, {pos.get('lon')}E "
                f"({t.distance_km}km away)"
            )
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
# Timeline responses
# ---------------------------------------------------------------------------


class TimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str
    type: str
    title: str
    details: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, Any] | None = None
    source: str


class TimelineResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voyage_id: str
    ship_name: str | None = None
    event_count: int
    events: list[TimelineEvent]
    geojson: dict[str, Any] | None = None
    artifact_ref: str | None = None
    data_sources: list[str] = Field(default_factory=list)
    message: str = ""

    def to_text(self) -> str:
        lines = [
            self.message,
            f"Voyage: {self.voyage_id}",
        ]
        if self.ship_name:
            lines.append(f"Ship: {self.ship_name}")
        lines.append(f"Events: {self.event_count}")
        if self.artifact_ref:
            lines.append(f"Artifact: {self.artifact_ref}")
        lines.append("")
        for e in self.events:
            pos_str = ""
            if e.position:
                pos_str = f" [{e.position.get('lat', '?')}N, {e.position.get('lon', '?')}E]"
            lines.append(f"  {e.date}  [{e.type}] {e.title}{pos_str}")
        if self.data_sources:
            lines.append(f"\nSources: {', '.join(self.data_sources)}")
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

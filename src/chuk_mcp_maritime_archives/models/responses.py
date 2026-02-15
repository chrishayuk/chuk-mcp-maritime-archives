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


def format_response(
    response: BaseModel,
    output_mode: str = "json",
    fields: list[str] | None = None,
) -> str:
    """Format a response model as JSON, text, or CSV.

    Args:
        response: Pydantic response model
        output_mode: "json" (default), "text", or "csv"
        fields: For CSV/JSON — limit output to these field names
    """
    if output_mode == "csv":
        if hasattr(response, "to_csv"):
            return response.to_csv(fields=fields)
        return response.model_dump_json(indent=2, exclude_none=True)
    if output_mode == "text":
        if hasattr(response, "to_text"):
            return response.to_text()
        return response.model_dump_json(indent=2, exclude_none=True)
    if fields and hasattr(response, "to_json_with_fields"):
        return response.to_json_with_fields(fields=fields)
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
    crew: list[dict[str, Any]] | None = None
    links_found: list[str]
    link_confidence: dict[str, float] = Field(default_factory=dict)
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

        if self.crew:
            lines.extend(["", f"--- Crew ({len(self.crew)} records) ---"])
            for c in self.crew[:10]:
                lines.append(
                    f"  {c.get('name', '?')} - {c.get('rank_english', c.get('rank', '?'))}"
                )
            if len(self.crew) > 10:
                lines.append(f"  ... and {len(self.crew) - 10} more")

        if self.link_confidence:
            conf_parts = [f"{k}: {v:.0%}" for k, v in self.link_confidence.items()]
            lines.extend(["", f"Link confidence: {', '.join(conf_parts)}"])

        lines.extend(["", f"Links found: {', '.join(self.links_found) or 'none'}"])
        return "\n".join(lines)


class LinkAuditResponse(BaseModel):
    """Results of cross-archive link quality audit."""

    model_config = ConfigDict(extra="forbid")

    wreck_links: dict[str, Any]
    cliwoc_links: dict[str, Any]
    crew_links: dict[str, Any]
    total_links_evaluated: int
    confidence_distribution: dict[str, int] = Field(default_factory=dict)
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]

        wl = self.wreck_links
        lines.extend(
            [
                "--- Wreck Links ---",
                f"  Ground truth: {wl.get('ground_truth_count', 0)} wrecks with voyage_id",
                f"  Matched: {wl.get('matched_count', 0)}",
                f"  Precision: {wl.get('precision', 0):.1%}",
                f"  Recall: {wl.get('recall', 0):.1%}",
            ]
        )

        cl = self.cliwoc_links
        lines.extend(
            [
                "",
                "--- CLIWOC Track Links ---",
                f"  DAS-number direct links: {cl.get('direct_links', 0)}",
                f"  Fuzzy matches found: {cl.get('fuzzy_matches', 0)}",
                f"  Mean confidence: {cl.get('mean_confidence', 0):.2f}",
                f"  Matches >= 0.7: {cl.get('high_confidence_count', 0)}",
                f"  Matches >= 0.5: {cl.get('moderate_confidence_count', 0)}",
            ]
        )

        crl = self.crew_links
        lines.extend(
            [
                "",
                "--- Crew Links ---",
                f"  Exact voyage_id matches: {crl.get('exact_matches', 0)}",
                f"  Fuzzy ship+date matches: {crl.get('fuzzy_matches', 0)}",
            ]
        )

        if self.confidence_distribution:
            lines.extend(["", "--- Confidence Distribution ---"])
            for bucket, count in sorted(self.confidence_distribution.items(), reverse=True):
                lines.append(f"  {bucket}: {count}")

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
# Muster responses (DSS — GZMVOC ship-level crew composition)
# ---------------------------------------------------------------------------


class MusterInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    muster_id: str
    ship_name: str
    captain: str | None = None
    muster_date: str | None = None
    muster_location: str | None = None
    total_crew: int | None = None
    das_voyage_id: str | None = None
    archive: str | None = None


class MusterSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    muster_count: int
    musters: list[MusterInfo]
    message: str = ""
    total_count: int | None = None
    next_cursor: str | None = None
    has_more: bool = False

    def to_text(self) -> str:
        lines = [self.message, ""]
        for m in self.musters:
            lines.append(
                f"  {m.muster_id}: {m.ship_name}"
                f" ({m.muster_location or '?'}, {m.muster_date or '?'})"
            )
            if m.total_crew:
                lines.append(f"    Crew: {m.total_crew}")
            if m.das_voyage_id:
                lines.append(f"    DAS voyage: {m.das_voyage_id}")
        footer = _pagination_footer(
            len(self.musters), self.total_count, self.has_more, self.next_cursor
        )
        if footer:
            lines.append(footer)
        return "\n".join(lines)


class MusterDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    muster: dict[str, Any]
    message: str = ""

    def to_text(self) -> str:
        m = self.muster
        lines = [
            f"Muster: {m.get('ship_name', '?')}",
            f"Captain: {m.get('captain', '?')}",
            f"Date: {m.get('muster_date', '?')}",
            f"Location: {m.get('muster_location', '?')}",
            f"European crew: {m.get('total_european', '?')}",
            f"Asian crew: {m.get('total_asian', '?')}",
            f"Total crew: {m.get('total_crew', '?')}",
            f"Mean wage: {m.get('mean_wage_guilders', '?')} guilders/month",
        ]
        if m.get("das_voyage_id"):
            lines.append(f"DAS voyage: {m['das_voyage_id']}")
        return "\n".join(lines)


class WageComparisonResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group1_label: str
    group1_n: int
    group1_mean_wage: float
    group1_median_wage: float
    group2_label: str
    group2_n: int
    group2_mean_wage: float
    group2_median_wage: float
    difference_pct: float
    message: str = ""

    def to_text(self) -> str:
        lines = [
            self.message,
            "",
            f"  {self.group1_label}: n={self.group1_n}, "
            f"mean={self.group1_mean_wage:.1f}, "
            f"median={self.group1_median_wage:.1f} guilders/month",
            f"  {self.group2_label}: n={self.group2_n}, "
            f"mean={self.group2_mean_wage:.1f}, "
            f"median={self.group2_median_wage:.1f} guilders/month",
            f"  Difference: {self.difference_pct:+.1f}%",
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
# Track analytics responses
# ---------------------------------------------------------------------------


class DailySpeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str
    lat: float
    lon: float
    km_day: float


class TrackSpeedsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voyage_id: int
    ship_name: str | None = None
    nationality: str | None = None
    observation_count: int
    mean_km_day: float
    speeds: list[DailySpeed]
    message: str = ""

    def to_text(self) -> str:
        lines = [
            self.message,
            f"Voyage {self.voyage_id}: {self.observation_count} observations, "
            f"mean {self.mean_km_day:.1f} km/day",
            "",
        ]
        for s in self.speeds[:20]:
            lines.append(f"  {s.date}  {s.lat:7.2f}N  {s.lon:7.2f}E  {s.km_day:.1f} km/day")
        if len(self.speeds) > 20:
            lines.append(f"  ... and {len(self.speeds) - 20} more observations")
        return "\n".join(lines)


class SpeedAggregationGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_key: str
    n: int
    mean_km_day: float
    median_km_day: float
    std_km_day: float
    ci_lower: float
    ci_upper: float
    p25_km_day: float | None = None
    p75_km_day: float | None = None


class TrackSpeedAggregationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_observations: int
    total_voyages: int
    group_by: str
    aggregate_by: str = "observation"
    groups: list[SpeedAggregationGroup]
    latitude_band: list[float] | None = None
    longitude_band: list[float] | None = None
    direction_filter: str | None = None
    nationality_filter: str | None = None
    month_start_filter: int | None = None
    month_end_filter: int | None = None
    wind_force_min_filter: int | None = None
    wind_force_max_filter: int | None = None
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, f"Grouped by: {self.group_by}"]
        if self.aggregate_by != "observation":
            lines.append(f"Aggregated by: {self.aggregate_by}")
        if self.month_start_filter is not None or self.month_end_filter is not None:
            lines.append(
                f"Season filter: months {self.month_start_filter or 1}"
                f"-{self.month_end_filter or 12}"
            )
        if self.wind_force_min_filter is not None or self.wind_force_max_filter is not None:
            lines.append(
                f"Wind force filter: Beaufort {self.wind_force_min_filter or 0}"
                f"-{self.wind_force_max_filter or 12}"
            )
        lines.append("")
        for g in self.groups:
            lines.append(
                f"  {g.group_key:>12s}: {g.mean_km_day:6.1f} km/day "
                f"(median {g.median_km_day:.1f}, std {g.std_km_day:.1f}, n={g.n})"
            )
        unit = "voyage means" if self.aggregate_by == "voyage" else "observations"
        lines.append(f"\nTotal: {self.total_observations} {unit}, {self.total_voyages} voyages")
        return "\n".join(lines)


class SpeedComparisonResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period1_label: str
    period1_n: int
    period1_mean: float
    period1_std: float
    period2_label: str
    period2_n: int
    period2_mean: float
    period2_std: float
    mann_whitney_u: float
    z_score: float
    p_value: float
    significant: bool
    effect_size: float
    aggregate_by: str = "observation"
    period1_samples: list[float] | None = None
    period2_samples: list[float] | None = None
    month_start_filter: int | None = None
    month_end_filter: int | None = None
    wind_force_min_filter: int | None = None
    wind_force_max_filter: int | None = None
    message: str = ""

    def to_text(self) -> str:
        sig = "SIGNIFICANT" if self.significant else "not significant"
        unit = "voyage means" if self.aggregate_by == "voyage" else "observations"
        lines = [self.message]
        if self.aggregate_by != "observation":
            lines.append(f"Aggregated by: {self.aggregate_by}")
        if self.month_start_filter is not None or self.month_end_filter is not None:
            lines.append(
                f"Season filter: months {self.month_start_filter or 1}"
                f"-{self.month_end_filter or 12}"
            )
        if self.wind_force_min_filter is not None or self.wind_force_max_filter is not None:
            lines.append(
                f"Wind force filter: Beaufort {self.wind_force_min_filter or 0}"
                f"-{self.wind_force_max_filter or 12}"
            )
        lines.extend(
            [
                f"Period 1 ({self.period1_label}): n={self.period1_n} {unit}, "
                f"mean={self.period1_mean:.1f} km/day, std={self.period1_std:.1f}",
                f"Period 2 ({self.period2_label}): n={self.period2_n} {unit}, "
                f"mean={self.period2_mean:.1f} km/day, std={self.period2_std:.1f}",
                "",
                f"Mann-Whitney U = {self.mann_whitney_u:.1f}",
                f"z = {self.z_score:.4f}",
                f"p = {self.p_value:.6f} ({sig} at p<0.05)",
                f"Cohen's d = {self.effect_size:.3f}",
            ]
        )
        return "\n".join(lines)


class DiDSpeedTestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period1_label: str
    period2_label: str
    aggregate_by: str
    n_bootstrap: int
    period1_eastbound_n: int
    period1_eastbound_mean: float
    period1_westbound_n: int
    period1_westbound_mean: float
    period2_eastbound_n: int
    period2_eastbound_mean: float
    period2_westbound_n: int
    period2_westbound_mean: float
    eastbound_diff: float
    westbound_diff: float
    did_estimate: float
    did_ci_lower: float
    did_ci_upper: float
    did_p_value: float
    significant: bool
    latitude_band: list[float] | None = None
    longitude_band: list[float] | None = None
    nationality_filter: str | None = None
    month_start_filter: int | None = None
    month_end_filter: int | None = None
    wind_force_min_filter: int | None = None
    wind_force_max_filter: int | None = None
    message: str = ""

    def to_text(self) -> str:
        sig = "SIGNIFICANT" if self.significant else "not significant"
        unit = "voyage means" if self.aggregate_by == "voyage" else "observations"
        lines = [
            self.message,
            f"Aggregated by: {self.aggregate_by}",
        ]
        if self.wind_force_min_filter is not None or self.wind_force_max_filter is not None:
            lines.append(
                f"Wind force filter: Beaufort {self.wind_force_min_filter or 0}"
                f"-{self.wind_force_max_filter or 12}"
            )
        lines.extend(
            [
                "",
                "2x2 Cell Summary:",
                f"  Period 1 ({self.period1_label}):",
                f"    Eastbound: n={self.period1_eastbound_n} {unit}, "
                f"mean={self.period1_eastbound_mean:.1f} km/day",
                f"    Westbound: n={self.period1_westbound_n} {unit}, "
                f"mean={self.period1_westbound_mean:.1f} km/day",
                f"  Period 2 ({self.period2_label}):",
                f"    Eastbound: n={self.period2_eastbound_n} {unit}, "
                f"mean={self.period2_eastbound_mean:.1f} km/day",
                f"    Westbound: n={self.period2_westbound_n} {unit}, "
                f"mean={self.period2_westbound_mean:.1f} km/day",
                "",
                f"Eastbound diff: {self.eastbound_diff:+.1f} km/day",
                f"Westbound diff: {self.westbound_diff:+.1f} km/day",
                "",
                f"DiD estimate: {self.did_estimate:+.1f} km/day",
                f"95% CI: [{self.did_ci_lower:.1f}, {self.did_ci_upper:.1f}]",
                f"p = {self.did_p_value:.6f} ({sig} at p<0.05)",
                f"Bootstrap iterations: {self.n_bootstrap}",
            ]
        )
        if self.month_start_filter is not None or self.month_end_filter is not None:
            lines.append(
                f"Season filter: months {self.month_start_filter or 1}"
                f"-{self.month_end_filter or 12}"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tortuosity
# ---------------------------------------------------------------------------


class TrackTortuosityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voyage_id: int
    ship_name: str | None = None
    nationality: str | None = None
    path_km: float
    net_km: float
    tortuosity_r: float
    inferred_direction: str
    n_in_box: int
    message: str = ""

    def to_text(self) -> str:
        lines = [
            self.message,
            f"Voyage {self.voyage_id}",
            f"  Path distance: {self.path_km:.1f} km",
            f"  Net distance:  {self.net_km:.1f} km",
            f"  Tortuosity:    {self.tortuosity_r:.4f} (1.0 = perfectly direct)",
            f"  Direction:     {self.inferred_direction}",
            f"  Positions:     {self.n_in_box}",
        ]
        return "\n".join(lines)


class TortuosityAggregationGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_key: str
    n: int
    mean_tortuosity: float
    median_tortuosity: float
    std_tortuosity: float
    ci_lower: float
    ci_upper: float
    p25_tortuosity: float | None = None
    p75_tortuosity: float | None = None


class TortuosityComparisonResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period1_label: str
    period1_n: int
    period1_mean: float
    period2_label: str
    period2_n: int
    period2_mean: float
    diff: float
    ci_lower: float
    ci_upper: float
    p_value: float
    significant: bool


class TortuosityAggregationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_voyages: int
    min_positions_required: int
    group_by: str
    groups: list[TortuosityAggregationGroup]
    comparison: TortuosityComparisonResult | None = None
    latitude_band: list[float] | None = None
    longitude_band: list[float] | None = None
    direction_filter: str | None = None
    nationality_filter: str | None = None
    month_start_filter: int | None = None
    month_end_filter: int | None = None
    r_min_filter: float | None = None
    r_max_filter: float | None = None
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, f"Grouped by: {self.group_by}"]
        if self.r_min_filter is not None or self.r_max_filter is not None:
            r_lo = self.r_min_filter if self.r_min_filter is not None else "—"
            r_hi = self.r_max_filter if self.r_max_filter is not None else "—"
            lines.append(f"Tortuosity filter: R in [{r_lo}, {r_hi}]")
        lines.append("")
        for g in self.groups:
            lines.append(
                f"  {g.group_key:>12s}: {g.mean_tortuosity:.4f} "
                f"(median {g.median_tortuosity:.4f}, std {g.std_tortuosity:.4f}, n={g.n})"
            )
        lines.append(
            f"\nTotal: {self.total_voyages} voyages "
            f"(min {self.min_positions_required} positions required)"
        )
        if self.comparison:
            c = self.comparison
            sig = "SIGNIFICANT" if c.significant else "not significant"
            lines.extend(
                [
                    "",
                    "Period comparison:",
                    f"  {c.period1_label}: n={c.period1_n}, mean={c.period1_mean:.4f}",
                    f"  {c.period2_label}: n={c.period2_n}, mean={c.period2_mean:.4f}",
                    f"  Diff: {c.diff:+.4f}",
                    f"  95% CI: [{c.ci_lower:.4f}, {c.ci_upper:.4f}]",
                    f"  p = {c.p_value:.6f} ({sig})",
                ]
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Speed export
# ---------------------------------------------------------------------------


class SpeedSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voyage_id: int
    date: str | None = None
    year: int
    month: int | None = None
    day: int | None = None
    direction: str | None = None
    speed_km_day: float
    nationality: str | None = None
    ship_name: str | None = None
    lat: float | None = None
    lon: float | None = None
    wind_force: int | None = None
    wind_direction: int | None = None
    n_observations: int | None = None


class SpeedExportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_matching: int
    returned: int
    offset: int = 0
    has_more: bool = False
    next_offset: int | None = None
    aggregate_by: str
    samples: list[SpeedSample]
    latitude_band: list[float] | None = None
    longitude_band: list[float] | None = None
    direction_filter: str | None = None
    nationality_filter: str | None = None
    year_start_filter: int | None = None
    year_end_filter: int | None = None
    month_start_filter: int | None = None
    month_end_filter: int | None = None
    wind_force_min_filter: int | None = None
    wind_force_max_filter: int | None = None
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        lines.append(f"Total matching: {self.total_matching:,}")
        lines.append(f"Returned: {self.returned:,} (offset {self.offset})")
        if self.has_more:
            lines.append(f"(more available — use offset={self.next_offset} for next page)")
        lines.append(f"Aggregate by: {self.aggregate_by}")
        lines.append("")
        if self.aggregate_by == "voyage":
            header = (
                f"{'VoyID':>6} {'Year':>5} {'Mon':>3} {'Dir':>10} {'km/day':>8} {'Nat':>3} {'N':>3}"
            )
            lines.append(header)
            lines.append("-" * len(header))
            for s in self.samples[:50]:
                lines.append(
                    f"{s.voyage_id:>6} {s.year:>5} {s.month or 0:>3} "
                    f"{(s.direction or '?'):>10} {s.speed_km_day:>8.1f} "
                    f"{(s.nationality or '?'):>3} {s.n_observations or 0:>3}"
                )
        else:
            header = f"{'VoyID':>6} {'Date':>12} {'Dir':>10} {'km/day':>8} {'Nat':>3} {'BF':>3}"
            lines.append(header)
            lines.append("-" * len(header))
            for s in self.samples[:50]:
                bf = str(s.wind_force) if s.wind_force is not None else ""
                date_str = s.date or f"{s.year}-{s.month or 0:02d}"
                lines.append(
                    f"{s.voyage_id:>6} {date_str:>12} "
                    f"{(s.direction or '?'):>10} {s.speed_km_day:>8.1f} "
                    f"{(s.nationality or '?'):>3} {bf:>3}"
                )
        if len(self.samples) > 50:
            lines.append(f"... and {len(self.samples) - 50} more")
        return "\n".join(lines)

    _OBS_FIELDS = [
        "voyage_id",
        "date",
        "year",
        "month",
        "day",
        "direction",
        "speed_km_day",
        "nationality",
        "ship_name",
        "lat",
        "lon",
        "wind_force",
        "wind_direction",
    ]
    _VOY_FIELDS = [
        "voyage_id",
        "year",
        "month",
        "direction",
        "speed_km_day",
        "nationality",
        "ship_name",
        "n_observations",
    ]

    def _resolve_fields(self, fields: list[str] | None) -> list[str]:
        """Return the field list to use, validating against available columns."""
        available = self._VOY_FIELDS if self.aggregate_by == "voyage" else self._OBS_FIELDS
        if not fields:
            return available
        return [f for f in fields if f in available]

    def to_csv(self, fields: list[str] | None = None) -> str:
        """Compact CSV format — all records, not truncated.

        Returns a metadata header (lines starting with #) followed by
        standard CSV. Token-efficient: ~3-4x smaller than JSON.
        """
        cols = self._resolve_fields(fields)
        lines = [
            f"# total_matching={self.total_matching} returned={self.returned}"
            f" offset={self.offset} has_more={self.has_more}"
            + (f" next_offset={self.next_offset}" if self.next_offset else ""),
            ",".join(cols),
        ]
        for s in self.samples:
            d = s.model_dump(include=set(cols))
            lines.append(",".join(str(d.get(c, "")) if d.get(c) is not None else "" for c in cols))
        return "\n".join(lines)

    def to_json_with_fields(self, fields: list[str] | None = None) -> str:
        """JSON output with only selected fields per sample."""
        cols = self._resolve_fields(fields)
        col_set = set(cols)
        data = self.model_dump(exclude_none=True)
        data["samples"] = [
            {k: v for k, v in s.items() if k in col_set}
            for s in (sample.model_dump(include=col_set) for sample in self.samples)
        ]
        return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Wind Rose
# ---------------------------------------------------------------------------


class BeaufortCount(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force: int
    count: int
    percent: float
    mean_speed_km_day: float | None = None


class WindDirectionCount(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sector: str
    count: int
    percent: float
    mean_speed_km_day: float | None = None


class DistanceCalibration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    n_pairs: int
    mean_logged_km_day: float
    mean_haversine_km_day: float
    logged_over_haversine: float | None = None


class WindRoseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_with_wind: int
    total_without_wind: int
    total_with_direction: int = 0
    total_without_direction: int = 0
    total_voyages: int
    has_wind_data: bool
    has_direction_data: bool = False
    beaufort_counts: list[BeaufortCount]
    direction_counts: list[WindDirectionCount] | None = None
    distance_calibration: DistanceCalibration | None = None
    period1_label: str | None = None
    period1_counts: list[BeaufortCount] | None = None
    period2_label: str | None = None
    period2_counts: list[BeaufortCount] | None = None
    period1_direction_counts: list[WindDirectionCount] | None = None
    period2_direction_counts: list[WindDirectionCount] | None = None
    latitude_band: list[float] | None = None
    longitude_band: list[float] | None = None
    direction_filter: str | None = None
    nationality_filter: str | None = None
    month_start_filter: int | None = None
    month_end_filter: int | None = None
    message: str = ""

    def to_text(self) -> str:
        if not self.has_wind_data and not self.has_direction_data:
            return self.message
        lines = [self.message, ""]

        # Beaufort distribution
        if self.has_wind_data:
            lines.append("Beaufort Force Distribution:")
            for bc in self.beaufort_counts:
                if bc.count > 0:
                    bar = "#" * max(1, int(bc.percent / 2))
                    spd = f"{bc.mean_speed_km_day:.1f} km/day" if bc.mean_speed_km_day else ""
                    lines.append(
                        f"  Beaufort {bc.force:>2d}: {bc.count:>6,} "
                        f"({bc.percent:5.1f}%)  {spd:>12s}  {bar}"
                    )
            lines.append(f"\nWith Beaufort data: {self.total_with_wind:,}")
            lines.append(f"Without Beaufort data: {self.total_without_wind:,}")

        # Wind direction distribution
        if self.has_direction_data and self.direction_counts:
            lines.append("\nWind Direction Distribution:")
            for dc in self.direction_counts:
                if dc.count > 0:
                    bar = "#" * max(1, int(dc.percent / 2))
                    spd = f"{dc.mean_speed_km_day:.1f} km/day" if dc.mean_speed_km_day else ""
                    lines.append(
                        f"  {dc.sector:>2s}: {dc.count:>6,} ({dc.percent:5.1f}%)  {spd:>12s}  {bar}"
                    )
            lines.append(f"\nWith direction data: {self.total_with_direction:,}")

        # Distance calibration
        if self.distance_calibration:
            cal = self.distance_calibration
            lines.append(f"\nDistance Calibration ({cal.n_pairs:,} pairs):")
            lines.append(f"  Mean logged: {cal.mean_logged_km_day:.1f} km/day")
            lines.append(f"  Mean haversine: {cal.mean_haversine_km_day:.1f} km/day")
            if cal.logged_over_haversine:
                lines.append(f"  Ratio (logged/haversine): {cal.logged_over_haversine:.3f}")

        # Period comparisons
        if self.period1_label and self.period1_counts:
            p1_n = sum(c.count for c in self.period1_counts)
            p2_n = sum(c.count for c in (self.period2_counts or []))
            lines.append(f"\nPeriod 1 ({self.period1_label}): {p1_n:,} Beaufort obs")
            lines.append(f"Period 2 ({self.period2_label}): {p2_n:,} Beaufort obs")
        if self.period1_direction_counts:
            p1_dir_n = sum(c.count for c in self.period1_direction_counts)
            p2_dir_n = sum(c.count for c in (self.period2_direction_counts or []))
            lines.append(f"Period 1 direction obs: {p1_dir_n:,}")
            lines.append(f"Period 2 direction obs: {p2_dir_n:,}")

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
# Crew demographics / career / survival responses
# ---------------------------------------------------------------------------


class DemographicsGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_key: str
    count: int
    percentage: float
    fate_distribution: dict[str, int] = Field(default_factory=dict)


class CrewDemographicsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_records: int
    total_filtered: int
    group_by: str
    group_count: int
    groups: list[DemographicsGroup]
    other_count: int = 0
    filters_applied: dict[str, str] = Field(default_factory=dict)
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, f"Grouped by: {self.group_by}", ""]
        for g in self.groups:
            lines.append(f"  {g.group_key:>20s}: {g.count:>6d}  ({g.percentage:.1f}%)")
        if self.other_count:
            lines.append(f"  {'(other)':>20s}: {self.other_count:>6d}")
        lines.append(f"\nTotal filtered: {self.total_filtered} of {self.total_records}")
        return "\n".join(lines)


class CareerVoyage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crew_id: str
    ship_name: str | None = None
    voyage_id: str | None = None
    rank: str | None = None
    embarkation_date: str | None = None
    service_end_reason: str | None = None


class CareerRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    origin: str | None = None
    voyage_count: int
    first_date: str | None = None
    last_date: str | None = None
    career_span_years: float | None = None
    distinct_ships: list[str] = Field(default_factory=list)
    ranks_held: list[str] = Field(default_factory=list)
    final_fate: str | None = None
    voyages: list[CareerVoyage] = Field(default_factory=list)


class CrewCareerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_name: str
    query_origin: str | None = None
    individual_count: int
    total_matches: int
    individuals: list[CareerRecord]
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        for ind in self.individuals:
            lines.append(f"  {ind.name} (origin: {ind.origin or '?'})")
            lines.append(
                f"    {ind.voyage_count} voyages, {ind.first_date or '?'} to {ind.last_date or '?'}"
            )
            if ind.ranks_held:
                lines.append(f"    Ranks: {' -> '.join(ind.ranks_held)}")
            if ind.distinct_ships:
                lines.append(f"    Ships: {', '.join(ind.distinct_ships)}")
            if ind.final_fate:
                lines.append(f"    Final fate: {ind.final_fate}")
        return "\n".join(lines)


class SurvivalGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_key: str
    total: int
    survived: int = 0
    died_voyage: int = 0
    died_asia: int = 0
    deserted: int = 0
    discharged: int = 0
    survival_rate: float = 0.0
    mortality_rate: float = 0.0
    desertion_rate: float = 0.0


class CrewSurvivalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_records: int
    total_with_known_fate: int
    group_by: str
    group_count: int
    groups: list[SurvivalGroup]
    filters_applied: dict[str, str] = Field(default_factory=dict)
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, f"Grouped by: {self.group_by}", ""]
        for g in self.groups:
            lines.append(
                f"  {g.group_key:>20s}: n={g.total:>5d}  "
                f"survived={g.survival_rate:.1f}%  "
                f"mortality={g.mortality_rate:.1f}%  "
                f"desertion={g.desertion_rate:.1f}%"
            )
        lines.append(
            f"\nTotal with known fate: {self.total_with_known_fate} of {self.total_records}"
        )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Discovery / capabilities
# ---------------------------------------------------------------------------


class ToolInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category: str
    description: str


# ---------------------------------------------------------------------------
# Galleon Transit Times
# ---------------------------------------------------------------------------


class GalleonTransitSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    n: int
    mean: float
    median: float
    std: float
    min: int
    max: int


class GalleonTransitRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voyage_id: str
    ship_name: str | None = None
    captain: str | None = None
    tonnage: int | None = None
    departure_date: str | None = None
    departure_port: str | None = None
    arrival_date: str | None = None
    destination_port: str | None = None
    trade_direction: str | None = None
    fate: str | None = None
    transit_days: int
    year: int


class GalleonTransitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_matching: int
    returned: int
    truncated: bool
    skipped_no_dates: int
    records: list[GalleonTransitRecord]
    summary: GalleonTransitSummary | None = None
    eastbound_summary: GalleonTransitSummary | None = None
    westbound_summary: GalleonTransitSummary | None = None
    trade_direction_filter: str | None = None
    year_start_filter: int | None = None
    year_end_filter: int | None = None
    fate_filter: str | None = None
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        lines.append(f"Total matching: {self.total_matching:,}")
        lines.append(f"Returned: {self.returned:,}")
        if self.truncated:
            lines.append("(truncated — increase max_results for more)")
        lines.append(f"Skipped (no dates): {self.skipped_no_dates}")
        lines.append("")
        if self.summary:
            lines.append(
                f"Overall: mean={self.summary.mean:.1f} days, "
                f"median={self.summary.median:.1f}, "
                f"std={self.summary.std:.1f}, "
                f"range={self.summary.min}-{self.summary.max}"
            )
        if self.eastbound_summary:
            s = self.eastbound_summary
            lines.append(
                f"Eastbound (Acapulco→Manila): n={s.n}, mean={s.mean:.1f} days, std={s.std:.1f}"
            )
        if self.westbound_summary:
            s = self.westbound_summary
            lines.append(
                f"Westbound (Manila→Acapulco): n={s.n}, mean={s.mean:.1f} days, std={s.std:.1f}"
            )
        lines.append("")
        header = f"{'VoyID':>14} {'Year':>5} {'Dir':>10} {'Days':>5} {'Ship':>20} {'Fate':>10}"
        lines.append(header)
        lines.append("-" * len(header))
        for r in self.records[:50]:
            lines.append(
                f"{r.voyage_id:>14} {r.year:>5} "
                f"{(r.trade_direction or '?'):>10} {r.transit_days:>5} "
                f"{(r.ship_name or '?'):>20} {(r.fate or '?'):>10}"
            )
        if len(self.records) > 50:
            lines.append(f"... and {len(self.records) - 50} more")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Wind Direction by Year
# ---------------------------------------------------------------------------


class WindDirectionYearSector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sector: str
    count: int
    percent: float
    mean_speed_km_day: float | None = None


class WindDirectionYearGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int
    total_observations: int
    sectors: list[WindDirectionYearSector]


class WindDirectionByYearResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_observations: int
    total_with_direction: int
    total_years: int
    years: list[WindDirectionYearGroup]
    latitude_band: list[float] | None = None
    longitude_band: list[float] | None = None
    direction_filter: str | None = None
    nationality_filter: str | None = None
    month_start_filter: int | None = None
    month_end_filter: int | None = None
    message: str = ""

    def to_text(self) -> str:
        lines = [self.message, ""]
        lines.append(f"Total observations: {self.total_observations:,}")
        lines.append(f"With direction: {self.total_with_direction:,}")
        lines.append(f"Years covered: {self.total_years}")
        lines.append("")
        header = (
            f"{'Year':>5} {'N':>6}  "
            f"{'N':>4} {'NE':>4} {'E':>4} {'SE':>4} "
            f"{'S':>4} {'SW':>4} {'W':>4} {'NW':>4}"
        )
        lines.append(header)
        lines.append("-" * len(header))
        for yg in self.years[:50]:
            pcts = {s.sector: f"{s.percent:.0f}" for s in yg.sectors}
            lines.append(
                f"{yg.year:>5} {yg.total_observations:>6}  "
                f"{pcts.get('N', '0'):>4} {pcts.get('NE', '0'):>4} "
                f"{pcts.get('E', '0'):>4} {pcts.get('SE', '0'):>4} "
                f"{pcts.get('S', '0'):>4} {pcts.get('SW', '0'):>4} "
                f"{pcts.get('W', '0'):>4} {pcts.get('NW', '0'):>4}"
            )
        if len(self.years) > 50:
            lines.append(f"... and {len(self.years) - 50} more")
        return "\n".join(lines)


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

"""
Pure-Python entity resolution for historical maritime ship names.

Provides fuzzy matching, phonetic encoding, and confidence scoring
for linking records across archives where ship names vary in spelling,
casing, and use of articles (e.g. "De Batavia" vs "BATAVIA").

No external dependencies -- consistent with the project's local-first
pattern of implementing algorithms from scratch (cf. Mann-Whitney U
in cliwoc_tracks.py).
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Ship name normalization
# ---------------------------------------------------------------------------

# Leading articles and prefixes stripped during normalization.
# San/Santa/Sao are NOT stripped -- they are integral to ship names
# like "San Pablo", "Santa Ana", "Sao Gabriel".
_STRIP_PREFIXES = frozenset(
    {
        "de",
        "het",
        "'t",
        "den",
        "der",
        "a",
        "o",
        "la",
        "el",
        "los",
        "las",
        "le",
        "les",
        "hms",
        "voc",
        "ss",
        "uss",
        "css",
        "rms",
        "s",
        "t",
    }
)

_SPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^A-Z0-9 ]")


def normalize_ship_name(name: str) -> str:
    """
    Normalize a ship name for matching.

    Pipeline:
    1. Uppercase
    2. Strip non-alphanumeric (except spaces)
    3. Collapse multiple spaces
    4. Strip leading article/prefix words

    Examples:
        "De Batavia"           -> "BATAVIA"
        "'T Wapen van Hoorn"   -> "WAPEN VAN HOORN"
        "HMS Victory"          -> "VICTORY"
        "BATAVIA"              -> "BATAVIA"
        ""                     -> ""
    """
    if not name:
        return ""

    result = name.upper().strip()
    # Collapse spaces first (before punctuation removal)
    result = _SPACE_RE.sub(" ", result).strip()

    # Strip leading prefix words (before punctuation removal so 'T works)
    words = result.split()
    while len(words) > 1 and words[0].strip("'").lower() in _STRIP_PREFIXES:
        words.pop(0)
    result = " ".join(words)

    # Remove non-alphanumeric (except spaces) and collapse again
    result = _NON_ALNUM_RE.sub("", result)
    result = _SPACE_RE.sub(" ", result).strip()

    return result


# ---------------------------------------------------------------------------
# Levenshtein distance (two-row DP)
# ---------------------------------------------------------------------------


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Compute Levenshtein edit distance between two strings.

    Uses standard dynamic programming with O(min(m,n)) space.
    Ship names are typically 5-25 characters, so this is fast.
    """
    if s1 == s2:
        return 0

    len1, len2 = len(s1), len(s2)

    # Ensure s1 is the shorter string for space optimization
    if len1 > len2:
        s1, s2 = s2, s1
        len1, len2 = len2, len1

    if len1 == 0:
        return len2

    prev_row = list(range(len1 + 1))
    for j in range(1, len2 + 1):
        curr_row = [j] + [0] * len1
        for i in range(1, len1 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            curr_row[i] = min(
                curr_row[i - 1] + 1,  # insertion
                prev_row[i] + 1,  # deletion
                prev_row[i - 1] + cost,  # substitution
            )
        prev_row = curr_row

    return prev_row[len1]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Normalized Levenshtein similarity in [0.0, 1.0].

    1.0 means exact match, 0.0 means completely different.
    """
    if not s1 and not s2:
        return 1.0
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    return 1.0 - levenshtein_distance(s1, s2) / max_len


# ---------------------------------------------------------------------------
# Soundex (American Soundex)
# ---------------------------------------------------------------------------

_SOUNDEX_MAP = {
    "B": "1",
    "F": "1",
    "P": "1",
    "V": "1",
    "C": "2",
    "G": "2",
    "J": "2",
    "K": "2",
    "Q": "2",
    "S": "2",
    "X": "2",
    "Z": "2",
    "D": "3",
    "T": "3",
    "L": "4",
    "M": "5",
    "N": "5",
    "R": "6",
}


def soundex(name: str) -> str:
    """
    Compute American Soundex code for a name.

    Returns a 4-character code (letter + 3 digits).
    Returns empty string for empty input.

    Examples:
        "BATAVIA"     -> "B310"
        "HOLLANDIA"   -> "H453"
        "AMSTERDAM"   -> "A523"
    """
    if not name:
        return ""

    # Keep only letters
    letters = "".join(c for c in name.upper() if c.isalpha())
    if not letters:
        return ""

    # First letter is kept
    code = [letters[0]]
    prev_digit = _SOUNDEX_MAP.get(letters[0], "0")

    for ch in letters[1:]:
        digit = _SOUNDEX_MAP.get(ch, "0")
        if digit != "0" and digit != prev_digit:
            code.append(digit)
            if len(code) == 4:
                break
        prev_digit = digit

    # Pad with zeros
    while len(code) < 4:
        code.append("0")

    return "".join(code[:4])


# ---------------------------------------------------------------------------
# Date proximity scoring
# ---------------------------------------------------------------------------


def _extract_year(date_str: str | None) -> int | None:
    """Extract a 4-digit year from a date string, or None."""
    if not date_str or len(date_str) < 4:
        return None
    try:
        return int(date_str[:4])
    except ValueError:
        return None


def date_proximity_score(
    query_date: str | None,
    candidate_start: str | None,
    candidate_end: str | None = None,
) -> float:
    """
    Score date proximity in [0.0, 1.0].

    Decay function based on year distance:
        0 years: 1.0
        1 year:  0.8
        2 years: 0.5
        3 years: 0.2
        4+ years: 0.0

    If candidate has both start and end dates, uses the closer one.
    Returns 0.5 if either date is missing (neutral).
    """
    q_year = _extract_year(query_date)
    if q_year is None:
        return 0.5

    c_start = _extract_year(candidate_start)
    c_end = _extract_year(candidate_end)

    if c_start is None and c_end is None:
        return 0.5

    # Compute minimum year distance to query
    distances = []
    if c_start is not None:
        distances.append(abs(q_year - c_start))
    if c_end is not None:
        distances.append(abs(q_year - c_end))

    min_dist = min(distances)

    # Decay function
    if min_dist == 0:
        return 1.0
    if min_dist == 1:
        return 0.8
    if min_dist == 2:
        return 0.5
    if min_dist == 3:
        return 0.2
    return 0.0


# ---------------------------------------------------------------------------
# Composite match scoring
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MatchResult:
    """Result of entity matching between two records."""

    candidate_id: str
    confidence: float  # 0.0 - 1.0
    match_type: str  # "exact", "normalized_exact", "fuzzy", "phonetic"
    name_similarity: float
    date_proximity: float
    nationality_match: bool
    details: str  # human-readable explanation


# Scoring weights
_W_NAME = 0.50
_W_DATE = 0.30
_W_NATIONALITY = 0.10
_W_PHONETIC = 0.10


def score_ship_match(
    query_name: str,
    query_date: str | None,
    query_nationality: str | None,
    candidate_name: str,
    candidate_id: str,
    candidate_date_start: str | None = None,
    candidate_date_end: str | None = None,
    candidate_nationality: str | None = None,
) -> MatchResult:
    """
    Score a candidate record against a query.

    Weights:
        Name similarity:   0.50 (Levenshtein on normalized names)
        Date proximity:     0.30 (year-based decay)
        Nationality match:  0.10 (binary)
        Phonetic match:     0.10 (Soundex agreement)
    """
    q_norm = normalize_ship_name(query_name)
    c_norm = normalize_ship_name(candidate_name)

    # Name similarity (Levenshtein on normalized)
    name_sim = levenshtein_similarity(q_norm, c_norm)

    # Date proximity
    date_score = date_proximity_score(query_date, candidate_date_start, candidate_date_end)

    # Nationality
    nat_match = False
    if query_nationality and candidate_nationality:
        nat_match = query_nationality.upper() == candidate_nationality.upper()
    elif not query_nationality and not candidate_nationality:
        nat_match = True  # both unknown, neutral
    nat_score = 1.0 if nat_match else 0.0

    # Phonetic match (Soundex)
    q_soundex = soundex(q_norm)
    c_soundex = soundex(c_norm)
    phonetic_score = 1.0 if (q_soundex and c_soundex and q_soundex == c_soundex) else 0.0

    # Composite confidence
    confidence = (
        _W_NAME * name_sim
        + _W_DATE * date_score
        + _W_NATIONALITY * nat_score
        + _W_PHONETIC * phonetic_score
    )

    # Determine match type
    if q_norm == c_norm:
        match_type = "normalized_exact" if query_name.upper() != candidate_name.upper() else "exact"
    elif phonetic_score > 0 and name_sim >= 0.7:
        match_type = "phonetic"
    else:
        match_type = "fuzzy"

    details = (
        f"name={name_sim:.2f} date={date_score:.2f} "
        f"nat={'Y' if nat_match else 'N'} phon={'Y' if phonetic_score > 0 else 'N'}"
    )

    return MatchResult(
        candidate_id=candidate_id,
        confidence=round(confidence, 4),
        match_type=match_type,
        name_similarity=round(name_sim, 4),
        date_proximity=round(date_score, 4),
        nationality_match=nat_match,
        details=details,
    )


# ---------------------------------------------------------------------------
# Pre-built fuzzy index
# ---------------------------------------------------------------------------


class ShipNameIndex:
    """
    Pre-built index for fuzzy ship name matching.

    Stores three index levels for fast lookup:
    1. Exact normalized name -> records
    2. Soundex code -> records
    3. All normalized entries (Levenshtein fallback)

    Lookup short-circuits: exact match first, then Soundex,
    then Levenshtein scan (limited to candidates with similar length).
    """

    def __init__(
        self,
        records: list[dict[str, Any]],
        name_field: str = "ship_name",
        id_field: str = "voyage_id",
    ) -> None:
        self._name_field = name_field
        self._id_field = id_field

        # Index levels
        self._exact: dict[str, list[dict]] = defaultdict(list)
        self._soundex: dict[str, list[dict]] = defaultdict(list)
        self._all_normalized: list[tuple[str, dict]] = []

        for rec in records:
            name = rec.get(name_field, "")
            if not name:
                continue
            norm = normalize_ship_name(name)
            if not norm:
                continue

            self._exact[norm].append(rec)
            sx = soundex(norm)
            if sx:
                self._soundex[sx].append(rec)
            self._all_normalized.append((norm, rec))

    @property
    def size(self) -> int:
        """Number of indexed records."""
        return len(self._all_normalized)

    def find_matches(
        self,
        query_name: str,
        query_date: str | None = None,
        query_nationality: str | None = None,
        min_confidence: float = 0.50,
        max_results: int = 5,
        date_field_start: str = "start_date",
        date_field_end: str = "end_date",
        nationality_field: str = "nationality",
    ) -> list[MatchResult]:
        """
        Find matching records, sorted by confidence descending.

        Returns at most max_results matches above min_confidence.
        """
        q_norm = normalize_ship_name(query_name)
        if not q_norm:
            return []

        # Collect candidates (deduplicated by record identity)
        seen_ids: set[str] = set()
        candidates: list[dict] = []

        # Level 1: exact normalized match
        for rec in self._exact.get(q_norm, []):
            rid = rec.get(self._id_field, "")
            if rid not in seen_ids:
                seen_ids.add(rid)
                candidates.append(rec)

        # Level 2: Soundex match (extends candidates)
        q_soundex = soundex(q_norm)
        if q_soundex:
            for rec in self._soundex.get(q_soundex, []):
                rid = rec.get(self._id_field, "")
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    candidates.append(rec)

        # Level 3: Levenshtein fallback (only if few candidates so far)
        if len(candidates) < max_results:
            q_len = len(q_norm)
            for norm, rec in self._all_normalized:
                rid = rec.get(self._id_field, "")
                if rid in seen_ids:
                    continue
                # Early rejection: length difference > 3 means low similarity
                if abs(len(norm) - q_len) > 3:
                    continue
                seen_ids.add(rid)
                candidates.append(rec)

        # Score all candidates
        results: list[MatchResult] = []
        for rec in candidates:
            result = score_ship_match(
                query_name=query_name,
                query_date=query_date,
                query_nationality=query_nationality,
                candidate_name=rec.get(self._name_field, ""),
                candidate_id=rec.get(self._id_field, ""),
                candidate_date_start=rec.get(date_field_start),
                candidate_date_end=rec.get(date_field_end),
                candidate_nationality=rec.get(nationality_field),
            )
            if result.confidence >= min_confidence:
                results.append(result)

        # Sort by confidence descending
        results.sort(key=lambda r: r.confidence, reverse=True)
        return results[:max_results]

"""Tests for entity resolution — fuzzy ship name matching and confidence scoring."""

import pytest

from chuk_mcp_maritime_archives.core.entity_resolution import (
    ShipNameIndex,
    date_proximity_score,
    levenshtein_distance,
    levenshtein_similarity,
    normalize_ship_name,
    score_ship_match,
    soundex,
)


# ---------------------------------------------------------------------------
# normalize_ship_name
# ---------------------------------------------------------------------------


class TestNormalizeShipName:
    def test_basic(self):
        assert normalize_ship_name("BATAVIA") == "BATAVIA"

    def test_lowercase(self):
        assert normalize_ship_name("batavia") == "BATAVIA"

    def test_strip_de(self):
        assert normalize_ship_name("De Batavia") == "BATAVIA"

    def test_strip_het(self):
        assert normalize_ship_name("Het Wapen") == "WAPEN"

    def test_strip_t(self):
        assert normalize_ship_name("'T Wapen van Hoorn") == "WAPEN VAN HOORN"

    def test_strip_hms(self):
        assert normalize_ship_name("HMS Victory") == "VICTORY"

    def test_strip_voc(self):
        assert normalize_ship_name("VOC Amsterdam") == "AMSTERDAM"

    def test_no_strip_san(self):
        """San/Santa/Sao are integral to ship names, not stripped."""
        assert normalize_ship_name("San Pablo") == "SAN PABLO"

    def test_no_strip_santa(self):
        assert normalize_ship_name("Santa Ana") == "SANTA ANA"

    def test_no_strip_sao(self):
        assert normalize_ship_name("Sao Gabriel") == "SAO GABRIEL"

    def test_collapse_spaces(self):
        assert normalize_ship_name("De   Batavia") == "BATAVIA"

    def test_empty_string(self):
        assert normalize_ship_name("") == ""

    def test_only_article(self):
        """If name is just an article, keep it."""
        assert normalize_ship_name("De") == "DE"

    def test_multiple_articles(self):
        """Strip multiple leading articles."""
        assert normalize_ship_name("De La Rosa") == "ROSA"

    def test_mixed_case(self):
        assert normalize_ship_name("Red Dragon") == "RED DRAGON"

    def test_strip_punctuation(self):
        assert normalize_ship_name("'s Lands Welvaren") == "LANDS WELVAREN"


# ---------------------------------------------------------------------------
# levenshtein_distance
# ---------------------------------------------------------------------------


class TestLevenshteinDistance:
    def test_identical(self):
        assert levenshtein_distance("BATAVIA", "BATAVIA") == 0

    def test_one_substitution(self):
        assert levenshtein_distance("BATAVIA", "BATAVIB") == 1

    def test_one_deletion(self):
        assert levenshtein_distance("BATAVIA", "BATAVI") == 1

    def test_one_insertion(self):
        assert levenshtein_distance("BATAVIA", "BATAVAIA") == 1

    def test_empty_vs_nonempty(self):
        assert levenshtein_distance("", "ABC") == 3

    def test_both_empty(self):
        assert levenshtein_distance("", "") == 0

    def test_real_case_hollandia(self):
        """Historical spelling variant: single vs double L."""
        assert levenshtein_distance("HOLLANDIA", "HOLANDIA") == 1

    def test_completely_different(self):
        assert levenshtein_distance("ABC", "XYZ") == 3


class TestLevenshteinSimilarity:
    def test_exact(self):
        assert levenshtein_similarity("BATAVIA", "BATAVIA") == 1.0

    def test_one_off(self):
        sim = levenshtein_similarity("BATAVIA", "BATAVIB")
        assert 0.8 < sim < 0.95  # 1 - 1/7 ≈ 0.857

    def test_both_empty(self):
        assert levenshtein_similarity("", "") == 1.0

    def test_completely_different(self):
        sim = levenshtein_similarity("A", "Z")
        assert sim == 0.0


# ---------------------------------------------------------------------------
# soundex
# ---------------------------------------------------------------------------


class TestSoundex:
    def test_batavia(self):
        assert soundex("BATAVIA") == "B310"

    def test_hollandia(self):
        assert soundex("HOLLANDIA") == "H453"

    def test_amsterdam(self):
        assert soundex("AMSTERDAM") == "A523"

    def test_identical_names_same_code(self):
        assert soundex("BATAVIA") == soundex("BATAVIA")

    def test_similar_names_same_code(self):
        """Historical spelling variants should produce same code."""
        assert soundex("RIDDERSCHAP") == soundex("RIDERSCHAP")

    def test_empty(self):
        assert soundex("") == ""

    def test_single_letter(self):
        assert soundex("A") == "A000"


# ---------------------------------------------------------------------------
# date_proximity_score
# ---------------------------------------------------------------------------


class TestDateProximityScore:
    def test_same_year(self):
        assert date_proximity_score("1720-03-15", "1720-01-01") == 1.0

    def test_one_year_apart(self):
        assert date_proximity_score("1720-03-15", "1721-01-01") == 0.8

    def test_two_years_apart(self):
        assert date_proximity_score("1720-03-15", "1722-01-01") == 0.5

    def test_three_years_apart(self):
        assert date_proximity_score("1720-03-15", "1723-01-01") == 0.2

    def test_four_years_apart(self):
        assert date_proximity_score("1720-03-15", "1724-01-01") == 0.0

    def test_missing_query(self):
        assert date_proximity_score(None, "1720-01-01") == 0.5

    def test_missing_candidate(self):
        assert date_proximity_score("1720-03-15", None) == 0.5

    def test_both_missing(self):
        assert date_proximity_score(None, None) == 0.5

    def test_start_and_end_dates(self):
        """Uses the closer of start/end to query."""
        score = date_proximity_score("1720-03-15", "1718-01-01", "1720-12-01")
        assert score == 1.0  # end date is in same year


# ---------------------------------------------------------------------------
# score_ship_match
# ---------------------------------------------------------------------------


class TestScoreShipMatch:
    def test_exact_match(self):
        result = score_ship_match(
            query_name="BATAVIA",
            query_date="1720-03-15",
            query_nationality="NL",
            candidate_name="BATAVIA",
            candidate_id="cliwoc:42",
            candidate_date_start="1720-01-01",
            candidate_nationality="NL",
        )
        assert result.confidence >= 0.90
        assert result.match_type == "exact"
        assert result.name_similarity == 1.0
        assert result.nationality_match is True

    def test_normalized_exact(self):
        """De Batavia vs BATAVIA should be normalized_exact."""
        result = score_ship_match(
            query_name="De Batavia",
            query_date=None,
            query_nationality=None,
            candidate_name="BATAVIA",
            candidate_id="test:1",
        )
        assert result.match_type == "normalized_exact"
        assert result.name_similarity == 1.0

    def test_fuzzy_match(self):
        result = score_ship_match(
            query_name="HOLLANDIA",
            query_date="1720-03-15",
            query_nationality="NL",
            candidate_name="HOLANDIA",
            candidate_id="test:1",
            candidate_date_start="1720-01-01",
            candidate_nationality="NL",
        )
        assert 0.7 <= result.confidence <= 1.0
        assert result.name_similarity > 0.8

    def test_date_penalty(self):
        """3-year gap should reduce confidence."""
        close = score_ship_match(
            query_name="BATAVIA",
            query_date="1720-03-15",
            query_nationality="NL",
            candidate_name="BATAVIA",
            candidate_id="test:1",
            candidate_date_start="1720-01-01",
            candidate_nationality="NL",
        )
        far = score_ship_match(
            query_name="BATAVIA",
            query_date="1720-03-15",
            query_nationality="NL",
            candidate_name="BATAVIA",
            candidate_id="test:2",
            candidate_date_start="1723-01-01",
            candidate_nationality="NL",
        )
        assert close.confidence > far.confidence

    def test_nationality_penalty(self):
        """Different nationality should reduce confidence."""
        same_nat = score_ship_match(
            query_name="BATAVIA",
            query_date=None,
            query_nationality="NL",
            candidate_name="BATAVIA",
            candidate_id="test:1",
            candidate_nationality="NL",
        )
        diff_nat = score_ship_match(
            query_name="BATAVIA",
            query_date=None,
            query_nationality="NL",
            candidate_name="BATAVIA",
            candidate_id="test:2",
            candidate_nationality="UK",
        )
        assert same_nat.confidence > diff_nat.confidence


# ---------------------------------------------------------------------------
# ShipNameIndex
# ---------------------------------------------------------------------------


class TestShipNameIndex:
    @pytest.fixture
    def sample_records(self):
        return [
            {
                "ship_name": "BATAVIA",
                "voyage_id": "1",
                "start_date": "1720-01-01",
                "end_date": "1720-12-01",
                "nationality": "NL",
            },
            {
                "ship_name": "HOLLANDIA",
                "voyage_id": "2",
                "start_date": "1720-03-01",
                "end_date": "1720-11-01",
                "nationality": "NL",
            },
            {
                "ship_name": "AMSTERDAM",
                "voyage_id": "3",
                "start_date": "1725-01-01",
                "end_date": "1725-12-01",
                "nationality": "NL",
            },
            {
                "ship_name": "Red Dragon",
                "voyage_id": "4",
                "start_date": "1601-02-13",
                "end_date": "1603-09-11",
                "nationality": "UK",
            },
        ]

    @pytest.fixture
    def index(self, sample_records):
        return ShipNameIndex(sample_records)

    def test_size(self, index):
        assert index.size == 4

    def test_exact_match(self, index):
        matches = index.find_matches("BATAVIA", query_date="1720-06-01", query_nationality="NL")
        assert len(matches) >= 1
        assert matches[0].candidate_id == "1"
        assert matches[0].confidence >= 0.90

    def test_fuzzy_match(self, index):
        """HOLANDIA should fuzzy-match HOLLANDIA."""
        matches = index.find_matches("HOLANDIA", query_date="1720-06-01", query_nationality="NL")
        assert len(matches) >= 1
        found_ids = [m.candidate_id for m in matches]
        assert "2" in found_ids  # HOLLANDIA

    def test_normalized_match(self, index):
        """'De Batavia' should match 'BATAVIA' after normalization."""
        matches = index.find_matches("De Batavia", query_date="1720-06-01")
        assert len(matches) >= 1
        assert matches[0].candidate_id == "1"

    def test_no_match(self, index):
        matches = index.find_matches("ZZZZZZZ", min_confidence=0.90)
        assert len(matches) == 0

    def test_sorted_by_confidence(self, index):
        matches = index.find_matches("BATAVIA", min_confidence=0.0, max_results=10)
        for i in range(len(matches) - 1):
            assert matches[i].confidence >= matches[i + 1].confidence

    def test_cross_archive_match(self, index):
        """EIC ship with different casing should still be found."""
        matches = index.find_matches("RED DRAGON", query_nationality="UK", min_confidence=0.50)
        assert len(matches) >= 1
        assert matches[0].candidate_id == "4"

    def test_empty_query(self, index):
        assert index.find_matches("") == []

    def test_max_results(self, index):
        matches = index.find_matches("BATAVIA", min_confidence=0.0, max_results=2)
        assert len(matches) <= 2

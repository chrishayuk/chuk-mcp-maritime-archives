"""
Hull hydrodynamic profiles for VOC ship types.

Reference data for drift modelling. Values derived from archaeological
measurements of recovered VOC wrecks and construction specifications.
"""


HULL_PROFILES: dict[str, dict] = {
    "retourschip": {
        "ship_type": "retourschip",
        "description": "Large VOC ship for Asia route (600-1200 lasten)",
        "subtypes": {
            "large": {"tonnage_range": [1000, 1200], "typical": 1100},
            "medium": {"tonnage_range": [600, 800], "typical": 700},
            "small": {"tonnage_range": [400, 600], "typical": 500},
        },
        "dimensions_typical": {
            "length_m": {"min": 40, "max": 52, "typical": 45},
            "beam_m": {"min": 10, "max": 13, "typical": 11.5},
            "draught_m": {"min": 4.5, "max": 6.5, "typical": 5.5},
        },
        "hydrodynamics": {
            "displacement_tonnes": {"min": 800, "max": 1800, "typical": 1200},
            "block_coefficient": {"min": 0.55, "max": 0.65, "typical": 0.60},
            "waterplane_area_m2": {"min": 320, "max": 550, "typical": 420},
            "drag_coefficient_broadside": {"min": 0.90, "max": 1.10, "typical": 1.00},
            "drag_coefficient_longitudinal": {"min": 0.35, "max": 0.45, "typical": 0.40},
            "windage_area_m2": {"min": 200, "max": 400, "typical": 300},
            "windage_coefficient": {"min": 0.02, "max": 0.06, "typical": 0.03},
        },
        "sinking_characteristics": {
            "likely_orientation": ["keel_down", "broadside"],
            "orientation_weights": {
                "keel_down": 0.6,
                "broadside": 0.25,
                "bow_first": 0.1,
                "inverted": 0.05,
            },
            "terminal_velocity_ms": {"min": 2.0, "max": 5.0, "typical": 3.5},
            "notes": (
                "Large retourschips typically sink keel-down due to ballast. "
                "Storm damage may cause broadside sinking if hull breached "
                "asymmetrically."
            ),
        },
        "reference_wrecks": [
            {"name": "Batavia", "found": 1963, "measurements": "Hull sections measured"},
            {"name": "Amsterdam", "found": 1969, "measurements": "Near-complete hull"},
            {"name": "Hollandia", "found": 1971, "measurements": "Lower hull preserved"},
        ],
        "sources": [
            {"reference": "Adams, J. Ships of the VOC. Archaeological evidence."},
            {"reference": "Amsterdam Admiralty construction specifications"},
        ],
        "llm_guidance": (
            "Use typical values for Monte Carlo central estimate. Sample from "
            "min-max range for uncertainty propagation. Orientation weights "
            "should be adjusted based on loss cause — storm losses more likely "
            "broadside, reef strikes more likely bow_first."
        ),
    },
    "fluit": {
        "ship_type": "fluit",
        "description": "Cargo vessel, economical crew (200-600 lasten)",
        "subtypes": {
            "large": {"tonnage_range": [400, 600], "typical": 500},
            "standard": {"tonnage_range": [200, 400], "typical": 300},
        },
        "dimensions_typical": {
            "length_m": {"min": 25, "max": 40, "typical": 32},
            "beam_m": {"min": 6, "max": 9, "typical": 7.5},
            "draught_m": {"min": 3.0, "max": 4.5, "typical": 3.8},
        },
        "hydrodynamics": {
            "displacement_tonnes": {"min": 250, "max": 700, "typical": 450},
            "block_coefficient": {"min": 0.60, "max": 0.70, "typical": 0.65},
            "waterplane_area_m2": {"min": 120, "max": 280, "typical": 190},
            "drag_coefficient_broadside": {"min": 0.85, "max": 1.05, "typical": 0.95},
            "drag_coefficient_longitudinal": {"min": 0.30, "max": 0.40, "typical": 0.35},
            "windage_area_m2": {"min": 80, "max": 180, "typical": 130},
            "windage_coefficient": {"min": 0.02, "max": 0.05, "typical": 0.03},
        },
        "sinking_characteristics": {
            "likely_orientation": ["keel_down", "broadside"],
            "orientation_weights": {
                "keel_down": 0.55,
                "broadside": 0.30,
                "bow_first": 0.10,
                "inverted": 0.05,
            },
            "terminal_velocity_ms": {"min": 1.5, "max": 4.0, "typical": 2.8},
            "notes": (
                "Fluits have rounded hull form and shallow draught. "
                "Broad beam relative to length makes broadside sinking more "
                "likely than for retourschips."
            ),
        },
        "reference_wrecks": [
            {"name": "Vergulde Draeck", "found": 1963, "measurements": "Partial hull"},
        ],
        "sources": [
            {"reference": "Hoving, A.J. Nicolaes Witsens Scheeps-Bouw-Konst Open Gestelt."},
        ],
        "llm_guidance": (
            "Fluits are smaller and lighter than retourschips. Use for VOC "
            "intra-Asian trade routes and smaller European-Asia voyages."
        ),
    },
    "jacht": {
        "ship_type": "jacht",
        "description": "Fast, light vessel for patrol and messenger duties (50-200 lasten)",
        "subtypes": {
            "standard": {"tonnage_range": [50, 200], "typical": 120},
        },
        "dimensions_typical": {
            "length_m": {"min": 18, "max": 30, "typical": 24},
            "beam_m": {"min": 5, "max": 7, "typical": 6.0},
            "draught_m": {"min": 2.0, "max": 3.5, "typical": 2.8},
        },
        "hydrodynamics": {
            "displacement_tonnes": {"min": 60, "max": 250, "typical": 150},
            "block_coefficient": {"min": 0.45, "max": 0.55, "typical": 0.50},
            "waterplane_area_m2": {"min": 70, "max": 160, "typical": 110},
            "drag_coefficient_broadside": {"min": 0.80, "max": 1.00, "typical": 0.90},
            "drag_coefficient_longitudinal": {"min": 0.25, "max": 0.35, "typical": 0.30},
            "windage_area_m2": {"min": 40, "max": 100, "typical": 70},
            "windage_coefficient": {"min": 0.03, "max": 0.07, "typical": 0.04},
        },
        "sinking_characteristics": {
            "likely_orientation": ["keel_down", "bow_first", "broadside"],
            "orientation_weights": {
                "keel_down": 0.45,
                "broadside": 0.25,
                "bow_first": 0.20,
                "inverted": 0.10,
            },
            "terminal_velocity_ms": {"min": 1.0, "max": 3.0, "typical": 2.0},
            "notes": (
                "Light vessels with less ballast. More prone to capsizing "
                "and inverted sinking than heavier types."
            ),
        },
        "reference_wrecks": [],
        "sources": [
            {"reference": "VOC construction records, Nationaal Archief"},
        ],
        "llm_guidance": (
            "Small, fast vessels. Higher windage coefficient relative to "
            "displacement means more wind-driven drift. Use for messenger "
            "vessels and small patrol craft."
        ),
    },
    "hooker": {
        "ship_type": "hooker",
        "description": "Small coastal trading vessel (30-150 lasten)",
        "subtypes": {
            "standard": {"tonnage_range": [30, 150], "typical": 80},
        },
        "dimensions_typical": {
            "length_m": {"min": 15, "max": 25, "typical": 20},
            "beam_m": {"min": 4, "max": 6, "typical": 5.0},
            "draught_m": {"min": 1.5, "max": 3.0, "typical": 2.2},
        },
        "hydrodynamics": {
            "displacement_tonnes": {"min": 35, "max": 180, "typical": 100},
            "block_coefficient": {"min": 0.50, "max": 0.60, "typical": 0.55},
            "waterplane_area_m2": {"min": 50, "max": 120, "typical": 80},
            "drag_coefficient_broadside": {"min": 0.85, "max": 1.05, "typical": 0.95},
            "drag_coefficient_longitudinal": {"min": 0.30, "max": 0.40, "typical": 0.35},
            "windage_area_m2": {"min": 25, "max": 60, "typical": 40},
            "windage_coefficient": {"min": 0.03, "max": 0.08, "typical": 0.05},
        },
        "sinking_characteristics": {
            "likely_orientation": ["keel_down", "broadside"],
            "orientation_weights": {
                "keel_down": 0.50,
                "broadside": 0.30,
                "bow_first": 0.10,
                "inverted": 0.10,
            },
            "terminal_velocity_ms": {"min": 0.8, "max": 2.5, "typical": 1.5},
            "notes": "Small coastal vessels. Shallow draught, limited ballast.",
        },
        "reference_wrecks": [],
        "sources": [
            {"reference": "Dutch maritime construction traditions, 17th century"},
        ],
        "llm_guidance": (
            "Smallest VOC vessel type. Primarily for coastal and inter-island "
            "trade in Asian waters. Rarely used on Europe-Asia routes."
        ),
    },
    "pinas": {
        "ship_type": "pinas",
        "description": "Medium ship, versatile for trade and war (200-500 lasten)",
        "subtypes": {
            "large": {"tonnage_range": [350, 500], "typical": 420},
            "standard": {"tonnage_range": [200, 350], "typical": 280},
        },
        "dimensions_typical": {
            "length_m": {"min": 28, "max": 40, "typical": 34},
            "beam_m": {"min": 7, "max": 10, "typical": 8.5},
            "draught_m": {"min": 3.5, "max": 5.0, "typical": 4.2},
        },
        "hydrodynamics": {
            "displacement_tonnes": {"min": 250, "max": 600, "typical": 400},
            "block_coefficient": {"min": 0.50, "max": 0.60, "typical": 0.55},
            "waterplane_area_m2": {"min": 150, "max": 320, "typical": 230},
            "drag_coefficient_broadside": {"min": 0.85, "max": 1.05, "typical": 0.95},
            "drag_coefficient_longitudinal": {"min": 0.30, "max": 0.40, "typical": 0.35},
            "windage_area_m2": {"min": 100, "max": 220, "typical": 160},
            "windage_coefficient": {"min": 0.02, "max": 0.06, "typical": 0.04},
        },
        "sinking_characteristics": {
            "likely_orientation": ["keel_down", "broadside"],
            "orientation_weights": {
                "keel_down": 0.55,
                "broadside": 0.25,
                "bow_first": 0.15,
                "inverted": 0.05,
            },
            "terminal_velocity_ms": {"min": 1.5, "max": 4.0, "typical": 2.5},
            "notes": (
                "Versatile warship/trader. Finer hull form than fluit "
                "but broader than jacht."
            ),
        },
        "reference_wrecks": [],
        "sources": [
            {"reference": "VOC ship classification records"},
        ],
        "llm_guidance": (
            "Medium-sized warship/trader. Used for both Europe-Asia routes "
            "and intra-Asian operations. More manoeuvrable than retourschip."
        ),
    },
    "fregat": {
        "ship_type": "fregat",
        "description": "Fast warship, smaller than retourschip (300-600 lasten)",
        "subtypes": {
            "large": {"tonnage_range": [450, 600], "typical": 520},
            "standard": {"tonnage_range": [300, 450], "typical": 380},
        },
        "dimensions_typical": {
            "length_m": {"min": 30, "max": 42, "typical": 36},
            "beam_m": {"min": 8, "max": 11, "typical": 9.5},
            "draught_m": {"min": 3.5, "max": 5.0, "typical": 4.5},
        },
        "hydrodynamics": {
            "displacement_tonnes": {"min": 350, "max": 750, "typical": 550},
            "block_coefficient": {"min": 0.48, "max": 0.58, "typical": 0.53},
            "waterplane_area_m2": {"min": 180, "max": 360, "typical": 270},
            "drag_coefficient_broadside": {"min": 0.85, "max": 1.05, "typical": 0.95},
            "drag_coefficient_longitudinal": {"min": 0.28, "max": 0.38, "typical": 0.33},
            "windage_area_m2": {"min": 120, "max": 260, "typical": 190},
            "windage_coefficient": {"min": 0.02, "max": 0.06, "typical": 0.04},
        },
        "sinking_characteristics": {
            "likely_orientation": ["keel_down", "broadside", "bow_first"],
            "orientation_weights": {
                "keel_down": 0.50,
                "broadside": 0.25,
                "bow_first": 0.15,
                "inverted": 0.10,
            },
            "terminal_velocity_ms": {"min": 1.5, "max": 4.0, "typical": 2.8},
            "notes": (
                "Fast warship hull form. Finer lines than retourschip "
                "or fluit. More likely to sink bow-first due to cannon weight "
                "forward."
            ),
        },
        "reference_wrecks": [],
        "sources": [
            {"reference": "VOC military vessel specifications"},
        ],
        "llm_guidance": (
            "Fast warship. Finer hull lines mean lower drag coefficients "
            "than retourschip. Higher speed capability but less cargo capacity."
        ),
    },
}

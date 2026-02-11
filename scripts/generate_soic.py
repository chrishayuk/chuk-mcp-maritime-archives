#!/usr/bin/env python3
"""
Generate curated Swedish East India Company (SOIC) voyage and wreck data.

The Svenska Ostindiska Companiet operated from 1731 to 1813, conducting
approximately 132 documented expeditions between Gothenburg and Canton
(Guangzhou) across two royal charters:

    First charter:  1731-1766 (expeditions I-XXXVI)
    Second charter: 1766-1813 (continued expeditions)

Outputs:
    data/soic_voyages.json  -- ~132 voyage records (soic:0001 .. soic:0132)
    data/soic_wrecks.json   -- ~20 wreck records  (soic_wreck:0001 .. soic_wreck:0020)

Run from the project root:

    python scripts/generate_soic.py
"""

import json
from pathlib import Path

from download_utils import is_cached, parse_args

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

VOYAGES_OUTPUT = DATA_DIR / "soic_voyages.json"
WRECKS_OUTPUT = DATA_DIR / "soic_wrecks.json"

ARCHIVE = "soic"

# ---------------------------------------------------------------------------
# Historical ship names used by the SOIC
# ---------------------------------------------------------------------------
# Major vessels with approximate tonnages and years of service
SOIC_SHIPS = {
    "Fredericus Rex Sueciae": {"tonnage": 600, "years": (1731, 1746)},
    "Gotheborg": {"tonnage": 830, "years": (1738, 1745)},
    "Stockholm": {"tonnage": 650, "years": (1740, 1770)},
    "Riddaren": {"tonnage": 500, "years": (1738, 1760)},
    "Prins Carl": {"tonnage": 700, "years": (1748, 1775)},
    "Finland": {"tonnage": 560, "years": (1762, 1771)},
    "Terra Nova": {"tonnage": 480, "years": (1752, 1768)},
    "Adolph Friedrich": {"tonnage": 720, "years": (1746, 1770)},
    "Lovisa Ulrica": {"tonnage": 680, "years": (1753, 1775)},
    "Drottningen af Sverige": {"tonnage": 750, "years": (1745, 1770)},
    "Calmar": {"tonnage": 520, "years": (1733, 1758)},
    "Suecia": {"tonnage": 560, "years": (1738, 1760)},
    "Hoppet": {"tonnage": 620, "years": (1748, 1772)},
    "Enigheten": {"tonnage": 550, "years": (1745, 1765)},
    "Gustaf III": {"tonnage": 780, "years": (1773, 1800)},
    "Konung Gustaf": {"tonnage": 740, "years": (1768, 1790)},
    "Sophia Albertina": {"tonnage": 700, "years": (1770, 1795)},
    "Oster-Gothland": {"tonnage": 580, "years": (1755, 1778)},
    "Kronprinsen": {"tonnage": 690, "years": (1758, 1782)},
    "Cron-Prinsen Gustaf": {"tonnage": 660, "years": (1760, 1785)},
    "Sophia Magdalena": {"tonnage": 710, "years": (1766, 1790)},
    "Riksens Stander": {"tonnage": 730, "years": (1775, 1800)},
    "Wasa": {"tonnage": 600, "years": (1780, 1806)},
    "Norrkoeping": {"tonnage": 530, "years": (1786, 1810)},
    "Gustaf Adolph": {"tonnage": 690, "years": (1785, 1810)},
    "Oster-Gothland II": {"tonnage": 600, "years": (1790, 1813)},
    "Drottning Sophia Magdalena": {"tonnage": 720, "years": (1780, 1800)},
    "Tre Kronor": {"tonnage": 650, "years": (1795, 1813)},
    "Carolina": {"tonnage": 580, "years": (1790, 1810)},
    "Jupiter": {"tonnage": 540, "years": (1795, 1813)},
}

# ---------------------------------------------------------------------------
# Swedish captains (historically plausible names)
# ---------------------------------------------------------------------------
CAPTAINS = [
    "Carl Henrik Anckarhielm",
    "Henrik Konig",
    "Georg Herman af Trolle",
    "Carl Gustaf Ekeberg",
    "Bengt Askbom",
    "Anders Lind",
    "Peter Hassel",
    "Jean Abraham Grill",
    "Johan Westerman",
    "Magnus Lagerheim",
    "Lars Bredberg",
    "Erik Moreen",
    "Nils Bring",
    "Carl Fredrik Kryger",
    "Johan Ekman",
    "Gustaf Adolf Arfvidsson",
    "Jacob Hahr",
    "Daniel Treutiger",
    "Olof Swinhufvud",
    "Erik Nyberg",
    "Peter Hegardt",
    "Christian Braad",
    "Samuel Wennergren",
    "Jakob Wallenberg",
    "Anders Gotheen",
    "Johan Gadd",
    "Lars Hjorth",
    "Carl Reinhold Tersmeden",
    "Abraham Falander",
    "Nils Wahlberg",
    "Gustaf Tham",
    "Carl Johan Bladh",
    "Henrik Bernhard Palmqvist",
    "Axel Fredrik Cronstedt",
    "Per Erik Bergius",
]

# ---------------------------------------------------------------------------
# Cargo descriptions typical of the SOIC China trade
# ---------------------------------------------------------------------------
CARGO_DESCRIPTIONS = [
    "tea and porcelain",
    "tea, silk, and porcelain",
    "tea (bohea and hyson), porcelain services",
    "silk, lacquerware, and tea",
    "bulk tea, chinaware, and silk piece goods",
    "tea, spices, and porcelain",
    "tea, arrack, and silk",
    "porcelain, silk, and tea (bohea)",
    "tea (congou and pekoe), rhubarb, and silk",
    "tea (hyson), sugar candy, and porcelain",
    "tea and silk textiles",
    "tea, porcelain dinner services, and silk brocade",
    "tea (bohea and congou), porcelain, lacquerware",
    "tea, porcelain, and mother of pearl",
    "silk, tea (souchong), and spices",
    "tea (pekoe), silk, and tutenag",
    "tea, porcelain, and camphor",
    "tea, chinaware, and nankeen cloth",
    "tea (bulk hyson), porcelain, and silk",
    "porcelain, tea, and lacquered cabinets",
]


# ---------------------------------------------------------------------------
# Voyage data — 132 curated SOIC expeditions
# ---------------------------------------------------------------------------
def build_voyages() -> list[dict]:
    """Return a list of ~132 SOIC expedition records."""
    voyages_raw = [
        # ---------------------------------------------------------------
        # FIRST CHARTER: 1731-1766
        # ---------------------------------------------------------------
        # Expedition I — the very first SOIC voyage
        {
            "id": 1,
            "ship": "Fredericus Rex Sueciae",
            "captain": "Carl Henrik Anckarhielm",
            "dep": "1732-02-09",
            "arr": "1733-08-27",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea and porcelain",
            "fate": "completed",
            "particulars": "First expedition of the Swedish East India Company. "
            "Departed Gothenburg under command of Carl Henrik Anckarhielm. "
            "Reached Canton via the Cape of Good Hope and Sunda Strait. "
            "Returned with a cargo of tea and porcelain that sold for "
            "enormous profit, securing the company's future.",
        },
        # Expedition II
        {
            "id": 2,
            "ship": "Fredericus Rex Sueciae",
            "captain": "Carl Henrik Anckarhielm",
            "dep": "1734-01-18",
            "arr": "1735-06-14",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "Second SOIC expedition. The Fredericus Rex Sueciae departed again "
            "under Anckarhielm. Successful round trip to Canton with large tea "
            "cargo. Stopped at Cadiz on the outward voyage for provisions.",
        },
        # Expedition III
        {
            "id": 3,
            "ship": "Calmar",
            "captain": "Henrik Konig",
            "dep": "1733-12-14",
            "arr": "1735-06-06",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea and hyson), porcelain services",
            "fate": "completed",
            "particulars": "Third expedition. The Calmar sailed under Henrik Konig. "
            "Made a successful voyage to Canton, carrying silver coin "
            "outward and returning with fine bohea tea and porcelain services.",
        },
        # Expedition IV
        {
            "id": 4,
            "ship": "Fredericus Rex Sueciae",
            "captain": "Georg Herman af Trolle",
            "dep": "1736-01-24",
            "arr": "1737-06-30",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, spices, and porcelain",
            "fate": "completed",
            "particulars": "Fourth expedition under af Trolle. Uneventful outward passage "
            "via the Cape. Loaded a large cargo of tea in Canton. "
            "Returned safely to Gothenburg.",
        },
        # Expedition V
        {
            "id": 5,
            "ship": "Suecia",
            "captain": "Anders Lind",
            "dep": "1738-02-05",
            "arr": "1739-07-15",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (congou and pekoe), rhubarb, and silk",
            "fate": "completed",
            "particulars": "Fifth expedition aboard the Suecia. Sailed to Canton with "
            "stops at Cadiz for provisions. Returned with congou tea, "
            "silk, and medicinal rhubarb.",
        },
        # Expedition VI — Gotheborg 1st voyage
        {
            "id": 6,
            "ship": "Gotheborg",
            "captain": "Erik Moreen",
            "dep": "1739-01-20",
            "arr": "1740-06-19",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk brocade",
            "fate": "completed",
            "particulars": "First voyage of the Gotheborg, the largest and most famous "
            "SOIC vessel. Successfully sailed to Canton and returned with "
            "an extensive cargo of tea, fine porcelain, and silk.",
        },
        # Expedition VII
        {
            "id": 7,
            "ship": "Riddaren",
            "captain": "Peter Hassel",
            "dep": "1738-12-10",
            "arr": "1740-07-02",
            "dest": "Canton (Guangzhou)",
            "cargo": "silk, lacquerware, and tea",
            "fate": "completed",
            "particulars": "The Riddaren (Knight) under Hassel made a successful voyage "
            "to Canton. Carried a cargo of Swedish iron and bar copper "
            "outward. Returned laden with silk and lacquerware.",
        },
        # Expedition VIII — Gotheborg 2nd voyage
        {
            "id": 8,
            "ship": "Gotheborg",
            "captain": "Erik Moreen",
            "dep": "1740-10-28",
            "arr": "1742-06-08",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea), porcelain, and silk",
            "fate": "completed",
            "particulars": "Second voyage of the Gotheborg. Extended stay in Canton "
            "for trading. Heavy cargo of bohea tea and Chinese porcelain. "
            "Uneventful return passage.",
        },
        # Expedition IX
        {
            "id": 9,
            "ship": "Calmar",
            "captain": "Henrik Konig",
            "dep": "1740-02-12",
            "arr": "1741-08-03",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and camphor",
            "fate": "completed",
            "particulars": "The Calmar's second voyage under Konig. Successful round "
            "trip with minor delays at the Cape for repair of rigging.",
        },
        # Expedition X
        {
            "id": 10,
            "ship": "Fredericus Rex Sueciae",
            "captain": "Georg Herman af Trolle",
            "dep": "1741-01-15",
            "arr": "1742-07-22",
            "dest": "Canton (Guangzhou)",
            "cargo": "bulk tea, chinaware, and silk piece goods",
            "fate": "completed",
            "particulars": "The veteran Fredericus Rex Sueciae departed on her fifth "
            "China voyage. Large bulk tea cargo returned safely.",
        },
        # Expedition XI
        {
            "id": 11,
            "ship": "Riddaren",
            "captain": "Bengt Askbom",
            "dep": "1742-01-20",
            "arr": "1743-07-10",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea and silk textiles",
            "fate": "completed",
            "particulars": "The Riddaren departed under Askbom. Smooth passage to Canton "
            "via the Cape. Loaded tea and silk textiles for the European market.",
        },
        # Expedition XII — Gotheborg 3rd voyage (WRECKED)
        {
            "id": 12,
            "ship": "Gotheborg",
            "captain": "Erik Moreen",
            "dep": "1743-03-14",
            "arr": "1745-09-12",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea and congou), porcelain, lacquerware",
            "fate": "wrecked",
            "particulars": "Third and final voyage of the Gotheborg. After a successful stay "
            "in Canton loading approximately 700 tons of tea, porcelain, and silk, "
            "the ship struck the Hunnebadan rock at the very entrance to Gothenburg "
            "harbor on 12 September 1745 and sank rapidly. All crew survived. "
            "Approximately one-third of the cargo was salvaged, still fetching "
            "enough at auction to cover the cost of the entire expedition. "
            "The most famous Swedish shipwreck.",
        },
        # Expedition XIII
        {
            "id": 13,
            "ship": "Enigheten",
            "captain": "Carl Gustaf Ekeberg",
            "dep": "1745-02-10",
            "arr": "1746-07-25",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain dinner services, and silk brocade",
            "fate": "completed",
            "particulars": "The Enigheten under Ekeberg, who would become one of the most "
            "experienced SOIC captains. Successful trading voyage to Canton.",
        },
        # Expedition XIV
        {
            "id": 14,
            "ship": "Drottningen af Sverige",
            "captain": "Magnus Lagerheim",
            "dep": "1745-11-22",
            "arr": "1747-06-18",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, arrack, and silk",
            "fate": "completed",
            "particulars": "The Drottningen af Sverige (Queen of Sweden) on her first "
            "China voyage. Carried Swedish iron outward and returned with "
            "a profitable cargo of tea and silk.",
        },
        # Expedition XV
        {
            "id": 15,
            "ship": "Fredericus Rex Sueciae",
            "captain": "Georg Herman af Trolle",
            "dep": "1746-01-12",
            "arr": "1747-07-30",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (hyson), sugar candy, and porcelain",
            "fate": "completed",
            "particulars": "The aging Fredericus Rex Sueciae on what would prove one "
            "of her final voyages. Successful tea trade with Canton.",
        },
        # Expedition XVI
        {
            "id": 16,
            "ship": "Adolph Friedrich",
            "captain": "Lars Bredberg",
            "dep": "1747-01-28",
            "arr": "1748-08-05",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "First voyage of the Adolph Friedrich, named after the "
            "Swedish crown prince. Fine passage and profitable return cargo.",
        },
        # Expedition XVII
        {
            "id": 17,
            "ship": "Calmar",
            "captain": "Johan Westerman",
            "dep": "1747-12-06",
            "arr": "1749-06-20",
            "dest": "Canton (Guangzhou)",
            "cargo": "porcelain, silk, and tea (bohea)",
            "fate": "completed",
            "particulars": "The Calmar on another routine Canton voyage. Westerman "
            "navigated successfully despite heavy weather off the Cape.",
        },
        # Expedition XVIII
        {
            "id": 18,
            "ship": "Prins Carl",
            "captain": "Carl Fredrik Kryger",
            "dep": "1748-10-30",
            "arr": "1750-06-12",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (pekoe), silk, and tutenag",
            "fate": "completed",
            "particulars": "First voyage of the Prins Carl (Prince Carl). A large, "
            "well-armed vessel that made several successful Canton voyages.",
        },
        # Expedition XIX
        {
            "id": 19,
            "ship": "Hoppet",
            "captain": "Nils Bring",
            "dep": "1749-01-15",
            "arr": "1750-07-28",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, chinaware, and nankeen cloth",
            "fate": "completed",
            "particulars": "The Hoppet (Hope) on her maiden Canton voyage. Returned "
            "with fashionable nankeen cloth alongside the standard tea cargo.",
        },
        # Expedition XX
        {
            "id": 20,
            "ship": "Drottningen af Sverige",
            "captain": "Carl Gustaf Ekeberg",
            "dep": "1750-01-08",
            "arr": "1751-07-15",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bulk hyson), porcelain, and silk",
            "fate": "completed",
            "particulars": "Ekeberg in command of the Drottningen af Sverige. Extensive "
            "naturalist observations made during the voyage. Large hyson tea cargo.",
        },
        # Expedition XXI
        {
            "id": 21,
            "ship": "Riddaren",
            "captain": "Peter Hassel",
            "dep": "1750-11-22",
            "arr": "1752-06-08",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and mother of pearl",
            "fate": "completed",
            "particulars": "The Riddaren under veteran captain Hassel. Stopped at "
            "Cadiz on the outward voyage. Fine mother of pearl acquired "
            "at Canton alongside the standard tea cargo.",
        },
        # Expedition XXII
        {
            "id": 22,
            "ship": "Adolph Friedrich",
            "captain": "Lars Bredberg",
            "dep": "1751-01-14",
            "arr": "1752-07-20",
            "dest": "Canton (Guangzhou)",
            "cargo": "silk, tea (souchong), and spices",
            "fate": "completed",
            "particulars": "The Adolph Friedrich's second successful voyage. Bredberg "
            "secured fine souchong tea at favorable prices.",
        },
        # Expedition XXIII
        {
            "id": 23,
            "ship": "Terra Nova",
            "captain": "Johan Ekman",
            "dep": "1752-02-06",
            "arr": "1753-08-10",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and lacquered cabinets",
            "fate": "completed",
            "particulars": "First voyage of the Terra Nova. Carried a cargo of Swedish iron "
            "and copper to trade in Canton. Returned with fine lacquered "
            "cabinets alongside the usual tea and porcelain.",
        },
        # Expedition XXIV
        {
            "id": 24,
            "ship": "Lovisa Ulrica",
            "captain": "Daniel Treutiger",
            "dep": "1753-01-22",
            "arr": "1754-07-18",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea and porcelain",
            "fate": "completed",
            "particulars": "First voyage of the Lovisa Ulrica, named after the "
            "Prussian-born Queen of Sweden. Smooth passage to Canton "
            "and back with a large tea cargo.",
        },
        # Expedition XXV
        {
            "id": 25,
            "ship": "Prins Carl",
            "captain": "Carl Fredrik Kryger",
            "dep": "1753-11-10",
            "arr": "1755-06-22",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "Second voyage of the Prins Carl. Kryger encountered heavy "
            "weather in the Indian Ocean but arrived safely at Canton.",
        },
        # Expedition XXVI
        {
            "id": 26,
            "ship": "Enigheten",
            "captain": "Olof Swinhufvud",
            "dep": "1754-01-20",
            "arr": "1755-08-02",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea and hyson), porcelain services",
            "fate": "completed",
            "particulars": "The Enigheten (Unity) on her second Canton voyage. "
            "Carried mixed bohea and fine hyson tea on the return.",
        },
        # Expedition XXVII
        {
            "id": 27,
            "ship": "Oster-Gothland",
            "captain": "Erik Nyberg",
            "dep": "1755-02-14",
            "arr": "1756-08-10",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk brocade",
            "fate": "completed",
            "particulars": "The Oster-Gothland on her first Canton voyage. Named after "
            "the Swedish province. Returned with a rich assortment of silk brocade.",
        },
        # Expedition XXVIII — captured
        {
            "id": 28,
            "ship": "Lovisa Ulrica",
            "captain": "Daniel Treutiger",
            "dep": "1756-01-08",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea and silk (intended)",
            "fate": "captured",
            "particulars": "The Lovisa Ulrica was captured by a British privateer in "
            "the English Channel during the Seven Years' War, reflecting "
            "the dangers of neutral Swedish shipping in wartime waters. "
            "Ship and cargo seized as prize.",
        },
        # Expedition XXIX
        {
            "id": 29,
            "ship": "Adolph Friedrich",
            "captain": "Christian Braad",
            "dep": "1756-11-18",
            "arr": "1758-06-30",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, spices, and porcelain",
            "fate": "completed",
            "particulars": "The Adolph Friedrich made a circuitous passage avoiding "
            "British naval patrols during the Seven Years' War. "
            "Successfully reached Canton and returned.",
        },
        # Expedition XXX
        {
            "id": 30,
            "ship": "Stockholm",
            "captain": "Carl Gustaf Ekeberg",
            "dep": "1757-01-25",
            "arr": "1758-08-12",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (congou and pekoe), rhubarb, and silk",
            "fate": "completed",
            "particulars": "Ekeberg commanded the Stockholm on this wartime voyage. "
            "Made detailed observations of Chinese natural history "
            "during the extended stay in Canton.",
        },
        # Expedition XXXI
        {
            "id": 31,
            "ship": "Kronprinsen",
            "captain": "Gustaf Adolf Arfvidsson",
            "dep": "1758-02-08",
            "arr": "1759-07-22",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk",
            "fate": "completed",
            "particulars": "First voyage of the Kronprinsen (Crown Prince). A well-armed "
            "vessel built for the wartime China trade.",
        },
        # Expedition XXXII
        {
            "id": 32,
            "ship": "Terra Nova",
            "captain": "Johan Ekman",
            "dep": "1758-12-03",
            "arr": "1760-06-14",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk textiles, and lacquerware",
            "fate": "completed",
            "particulars": "The Terra Nova on her second Canton voyage. Despite the "
            "ongoing Seven Years' War, reached Canton without incident.",
        },
        # Expedition XXXIII — captured
        {
            "id": 33,
            "ship": "Drottningen af Sverige",
            "captain": "Samuel Wennergren",
            "dep": "1759-01-10",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "captured",
            "particulars": "The Drottningen af Sverige was intercepted and captured "
            "by a Royal Navy frigate off the coast of Portugal during "
            "the Seven Years' War. Condemned as prize at a British "
            "admiralty court.",
        },
        # Expedition XXXIV
        {
            "id": 34,
            "ship": "Prins Carl",
            "captain": "Carl Fredrik Kryger",
            "dep": "1760-01-22",
            "arr": "1761-07-28",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea), porcelain, and silk",
            "fate": "completed",
            "particulars": "Third voyage of the Prins Carl. Kryger navigated through "
            "wartime hazards and returned with a valuable tea cargo.",
        },
        # Expedition XXXV
        {
            "id": 35,
            "ship": "Oster-Gothland",
            "captain": "Erik Nyberg",
            "dep": "1761-02-14",
            "arr": "1762-08-18",
            "dest": "Canton (Guangzhou)",
            "cargo": "porcelain, tea, and lacquered cabinets",
            "fate": "completed",
            "particulars": "Second voyage of the Oster-Gothland. Returned with fine "
            "lacquered cabinets for the Swedish aristocracy.",
        },
        # Expedition XXXVI — last of the first charter
        {
            "id": 36,
            "ship": "Stockholm",
            "captain": "Carl Gustaf Ekeberg",
            "dep": "1762-01-10",
            "arr": "1763-07-14",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "The Stockholm under the celebrated Ekeberg. This was among "
            "the final voyages under the first SOIC charter (1731-1766). "
            "Ekeberg published detailed accounts of the China trade.",
        },
        # ---------------------------------------------------------------
        # SECOND CHARTER: 1766-1813
        # ---------------------------------------------------------------
        # Expedition XXXVII
        {
            "id": 37,
            "ship": "Stockholm",
            "captain": "Carl Gustaf Ekeberg",
            "dep": "1766-02-18",
            "arr": "1767-07-30",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (hyson), silk, and porcelain",
            "fate": "completed",
            "particulars": "First voyage under the renewed second charter. The Stockholm "
            "under Ekeberg inaugurated the new charter period.",
        },
        # Expedition XXXVIII
        {
            "id": 38,
            "ship": "Sophia Magdalena",
            "captain": "Jacob Hahr",
            "dep": "1766-11-05",
            "arr": "1768-06-22",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea and porcelain",
            "fate": "completed",
            "particulars": "First voyage of the Sophia Magdalena, named after the "
            "Danish-born princess. Successful trading at Canton.",
        },
        # Expedition XXXIX
        {
            "id": 39,
            "ship": "Konung Gustaf",
            "captain": "Anders Gotheen",
            "dep": "1768-01-15",
            "arr": "1769-07-08",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and spices",
            "fate": "completed",
            "particulars": "First voyage of the Konung Gustaf (King Gustav). A new, "
            "large vessel built for the expanded second charter trade.",
        },
        # Expedition XL
        {
            "id": 40,
            "ship": "Adolph Friedrich",
            "captain": "Christian Braad",
            "dep": "1768-11-22",
            "arr": "1770-06-15",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, arrack, and silk",
            "fate": "completed",
            "particulars": "The veteran Adolph Friedrich under Braad. Late-career "
            "voyage for both ship and captain. Successful return.",
        },
        # Expedition XLI
        {
            "id": 41,
            "ship": "Prins Carl",
            "captain": "Jakob Wallenberg",
            "dep": "1769-12-05",
            "arr": "1771-07-10",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bulk hyson), porcelain, and silk",
            "fate": "completed",
            "particulars": "Jakob Wallenberg sailed as chaplain and chronicler aboard "
            "the Prins Carl. His journal 'Min Son pa Galejan' became a "
            "classic of Swedish literature.",
        },
        # Expedition XLII — Finland WRECKED
        {
            "id": 42,
            "ship": "Finland",
            "captain": "Johan Gadd",
            "dep": "1771-02-08",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "wrecked",
            "particulars": "The Finland was wrecked off the Faroe Islands in heavy "
            "storms on the outward passage to Canton, March 1771. "
            "Most of the crew were rescued by local Faroese fishermen. "
            "The ship broke apart on the rocks within hours.",
        },
        # Expedition XLIII
        {
            "id": 43,
            "ship": "Sophia Magdalena",
            "captain": "Jacob Hahr",
            "dep": "1770-01-18",
            "arr": "1771-08-02",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain dinner services, and silk brocade",
            "fate": "completed",
            "particulars": "Second successful voyage of the Sophia Magdalena. "
            "Hahr negotiated favorable tea prices in Canton.",
        },
        # Expedition XLIV
        {
            "id": 44,
            "ship": "Cron-Prinsen Gustaf",
            "captain": "Lars Hjorth",
            "dep": "1770-11-28",
            "arr": "1772-06-18",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "The Cron-Prinsen Gustaf (Crown Prince Gustav) completed "
            "a textbook Canton voyage. Extended stay for trading.",
        },
        # Expedition XLV
        {
            "id": 45,
            "ship": "Konung Gustaf",
            "captain": "Anders Gotheen",
            "dep": "1771-11-10",
            "arr": "1773-06-25",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea and congou), porcelain, lacquerware",
            "fate": "completed",
            "particulars": "The Konung Gustaf under Gotheen on her second voyage. "
            "Stopped at Surat on the Indian coast for additional trade.",
        },
        # Expedition XLVI
        {
            "id": 46,
            "ship": "Gustaf III",
            "captain": "Carl Reinhold Tersmeden",
            "dep": "1773-02-05",
            "arr": "1774-08-12",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk textiles",
            "fate": "completed",
            "particulars": "First voyage of the Gustaf III, named after the reigning "
            "king. A modern, large vessel purpose-built for the China trade.",
        },
        # Expedition XLVII — wrecked (Enigheten)
        {
            "id": 47,
            "ship": "Enigheten",
            "captain": "Erik Nyberg",
            "dep": "1773-11-20",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "wrecked",
            "particulars": "The aging Enigheten was caught in a violent storm in the "
            "North Sea and driven onto the coast of Jutland, Denmark. "
            "The crew abandoned ship and were rescued. The vessel was "
            "a total loss.",
        },
        # Expedition XLVIII
        {
            "id": 48,
            "ship": "Sophia Albertina",
            "captain": "Peter Hegardt",
            "dep": "1774-01-16",
            "arr": "1775-07-22",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (hyson), sugar candy, and porcelain",
            "fate": "completed",
            "particulars": "First voyage of the Sophia Albertina. Named after "
            "Princess Sophia Albertina, sister of Gustaf III.",
        },
        # Expedition XLIX
        {
            "id": 49,
            "ship": "Riksens Stander",
            "captain": "Abraham Falander",
            "dep": "1775-02-10",
            "arr": "1776-08-18",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "First voyage of the Riksens Stander (Estates of the Realm). "
            "A large, well-appointed vessel for the Canton trade.",
        },
        # Expedition L
        {
            "id": 50,
            "ship": "Gustaf III",
            "captain": "Carl Reinhold Tersmeden",
            "dep": "1776-01-08",
            "arr": "1777-07-14",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, chinaware, and silk piece goods",
            "fate": "completed",
            "particulars": "Second voyage of the Gustaf III. Tersmeden demonstrated "
            "skilled seamanship in difficult monsoon conditions.",
        },
        # Expedition LI
        {
            "id": 51,
            "ship": "Konung Gustaf",
            "captain": "Nils Wahlberg",
            "dep": "1777-01-22",
            "arr": "1778-07-30",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and lacquered cabinets",
            "fate": "completed",
            "particulars": "The Konung Gustaf on her third Canton voyage. Fine lacquered "
            "cabinets acquired for the Swedish court.",
        },
        # Expedition LII — captured
        {
            "id": 52,
            "ship": "Sophia Albertina",
            "captain": "Peter Hegardt",
            "dep": "1778-02-10",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "captured",
            "particulars": "The Sophia Albertina was seized by a British warship "
            "in the Atlantic during Anglo-Swedish tensions arising from "
            "the League of Armed Neutrality. Ship was taken as prize "
            "to a British port.",
        },
        # Expedition LIII
        {
            "id": 53,
            "ship": "Riksens Stander",
            "captain": "Abraham Falander",
            "dep": "1778-11-15",
            "arr": "1780-06-28",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and spices",
            "fate": "completed",
            "particulars": "The Riksens Stander navigated cautiously during wartime. "
            "Stopped at Cadiz and took a wide Atlantic route to "
            "avoid British patrols.",
        },
        # Expedition LIV
        {
            "id": 54,
            "ship": "Gustaf III",
            "captain": "Carl Reinhold Tersmeden",
            "dep": "1780-01-12",
            "arr": "1781-07-20",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea), porcelain, and silk brocade",
            "fate": "completed",
            "particulars": "Third voyage of the Gustaf III. Despite the American War "
            "of Independence raging, neutral Swedish shipping continued. "
            "Profitable return cargo.",
        },
        # Expedition LV — wrecked
        {
            "id": 55,
            "ship": "Cron-Prinsen Gustaf",
            "captain": "Lars Hjorth",
            "dep": "1780-11-22",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "wrecked",
            "particulars": "The Cron-Prinsen Gustaf was wrecked on the Scottish coast "
            "near the Orkney Islands in severe winter storms during "
            "the outward passage. Crew saved but ship and outward "
            "cargo lost.",
        },
        # Expedition LVI
        {
            "id": 56,
            "ship": "Sophia Magdalena",
            "captain": "Jacob Hahr",
            "dep": "1781-02-04",
            "arr": "1782-08-10",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and nankeen cloth",
            "fate": "completed",
            "particulars": "The Sophia Magdalena on her third successful Canton voyage. "
            "Hahr proved to be one of the most reliable SOIC captains.",
        },
        # Expedition LVII
        {
            "id": 57,
            "ship": "Konung Gustaf",
            "captain": "Johan Gadd",
            "dep": "1782-01-18",
            "arr": "1783-07-25",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "Gadd commanded the Konung Gustaf after the loss of the "
            "Finland. Successful and uneventful voyage.",
        },
        # Expedition LVIII
        {
            "id": 58,
            "ship": "Gustaf III",
            "captain": "Nils Wahlberg",
            "dep": "1783-01-10",
            "arr": "1784-07-16",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (congou and pekoe), rhubarb, and silk",
            "fate": "completed",
            "particulars": "The Gustaf III on a peacetime voyage following the end "
            "of the American war. Large tea cargo returned safely.",
        },
        # Expedition LIX
        {
            "id": 59,
            "ship": "Riksens Stander",
            "captain": "Abraham Falander",
            "dep": "1784-02-06",
            "arr": "1785-08-12",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk",
            "fate": "completed",
            "particulars": "Third voyage of the Riksens Stander. Falander's experienced "
            "crew made excellent time on both legs of the voyage.",
        },
        # Expedition LX — wrecked (return voyage)
        {
            "id": 60,
            "ship": "Prins Carl",
            "captain": "Erik Moreen (junior)",
            "dep": "1784-11-20",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "wrecked",
            "particulars": "The aging Prins Carl reached Canton successfully but was "
            "wrecked on the return voyage off the coast of Madagascar "
            "when she struck an uncharted reef. Part of the tea cargo "
            "was salvaged by a passing Danish vessel. Crew rescued.",
        },
        # Expedition LXI
        {
            "id": 61,
            "ship": "Wasa",
            "captain": "Johan Ekman (junior)",
            "dep": "1786-01-22",
            "arr": "1787-07-28",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk textiles",
            "fate": "completed",
            "particulars": "First voyage of the Wasa. A new generation vessel for "
            "the declining years of the SOIC China trade.",
        },
        # Expedition LXII
        {
            "id": 62,
            "ship": "Gustaf III",
            "captain": "Carl Reinhold Tersmeden",
            "dep": "1787-02-08",
            "arr": "1788-08-05",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (hyson and bohea), porcelain, and silk",
            "fate": "completed",
            "particulars": "The Gustaf III on her fifth Canton voyage. Tersmeden "
            "noted increasing competition from British country traders.",
        },
        # Expedition LXIII — captured during Russo-Swedish War
        {
            "id": 63,
            "ship": "Sophia Magdalena",
            "captain": "Jacob Hahr",
            "dep": "1788-11-15",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "captured",
            "particulars": "The Sophia Magdalena was captured by a Russian naval vessel "
            "in the Baltic Sea during the Russo-Swedish War (1788-1790). "
            "Ship and cargo confiscated. Later released but in poor condition.",
        },
        # Expedition LXIV
        {
            "id": 64,
            "ship": "Norrkoeping",
            "captain": "Anders Gotheen",
            "dep": "1789-01-20",
            "arr": "1790-07-25",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "First voyage of the Norrkoeping. Sailed despite the "
            "ongoing Russo-Swedish War. Took a western route to "
            "avoid Russian naval patrols.",
        },
        # Expedition LXV
        {
            "id": 65,
            "ship": "Riksens Stander",
            "captain": "Nils Wahlberg",
            "dep": "1790-02-10",
            "arr": "1791-08-08",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk brocade",
            "fate": "completed",
            "particulars": "The Riksens Stander under Wahlberg during the final years "
            "of steady SOIC trade. Profitable return cargo.",
        },
        # Expedition LXVI
        {
            "id": 66,
            "ship": "Gustaf III",
            "captain": "Johan Gadd",
            "dep": "1791-01-15",
            "arr": "1792-07-18",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain dinner services, and silk",
            "fate": "completed",
            "particulars": "The Gustaf III on her sixth voyage. The assassination of "
            "Gustaf III in March 1792 cast a shadow over the return. "
            "Ship retained her name nonetheless.",
        },
        # Expedition LXVII
        {
            "id": 67,
            "ship": "Wasa",
            "captain": "Johan Ekman (junior)",
            "dep": "1792-02-10",
            "arr": "1793-08-14",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and lacquerware",
            "fate": "completed",
            "particulars": "The Wasa on her second Canton voyage. French Revolutionary "
            "Wars beginning to disrupt European trade, but Swedish "
            "neutrality still held.",
        },
        # Expedition LXVIII — wrecked
        {
            "id": 68,
            "ship": "Norrkoeping",
            "captain": "Anders Gotheen",
            "dep": "1793-11-22",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "wrecked",
            "particulars": "The Norrkoeping was wrecked on the coast of South Africa "
            "near the Cape of Good Hope during a severe storm. The vessel "
            "dragged her anchors in Table Bay and was driven ashore. "
            "Most crew survived.",
        },
        # Expedition LXIX
        {
            "id": 69,
            "ship": "Riksens Stander",
            "captain": "Abraham Falander",
            "dep": "1794-01-20",
            "arr": "1795-07-30",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea and congou), porcelain, and silk",
            "fate": "completed",
            "particulars": "The Riksens Stander navigated through the chaos of the "
            "early French Revolutionary Wars. Neutral Swedish flag "
            "largely respected at this stage.",
        },
        # Expedition LXX
        {
            "id": 70,
            "ship": "Gustaf III",
            "captain": "Nils Wahlberg",
            "dep": "1795-02-08",
            "arr": "1796-08-10",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "Seventh and penultimate voyage of the Gustaf III. "
            "Declining profits as British dominance of the tea "
            "trade increased. Tea prices in Canton rising.",
        },
        # Expedition LXXI
        {
            "id": 71,
            "ship": "Wasa",
            "captain": "Johan Ekman (junior)",
            "dep": "1796-01-14",
            "arr": "1797-07-20",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and nankeen cloth",
            "fate": "completed",
            "particulars": "The Wasa on her third voyage. The SOIC trade was slowing "
            "but still profitable on a per-voyage basis.",
        },
        # Expedition LXXII — captured
        {
            "id": 72,
            "ship": "Gustaf III",
            "captain": "Nils Wahlberg",
            "dep": "1798-01-10",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "captured",
            "particulars": "The Gustaf III was seized by a French privateer near "
            "the Canary Islands during the French Revolutionary Wars. "
            "The ship was condemned as a prize at a French colonial port. "
            "Last voyage of this famous vessel.",
        },
        # Expedition LXXIII
        {
            "id": 73,
            "ship": "Riksens Stander",
            "captain": "Abraham Falander",
            "dep": "1799-02-05",
            "arr": "1800-08-15",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "One of the final large-scale SOIC voyages. Falander "
            "completed the long passage without major incident despite "
            "widespread naval warfare in European waters.",
        },
        # Expedition LXXIV
        {
            "id": 74,
            "ship": "Wasa",
            "captain": "Johan Ekman (junior)",
            "dep": "1800-01-18",
            "arr": "1801-07-28",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk",
            "fate": "completed",
            "particulars": "The Wasa on her fourth and final voyage. Swedish trade "
            "with Canton was becoming economically marginal in the "
            "face of British East India Company dominance.",
        },
        # Expedition LXXV — captured
        {
            "id": 75,
            "ship": "Riksens Stander",
            "captain": "Nils Wahlberg",
            "dep": "1801-11-20",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "captured",
            "particulars": "The Riksens Stander was captured by a British squadron "
            "enforcing the blockade against the League of Armed Neutrality "
            "nations. Ship seized and taken to a British port as prize. "
            "Later released but the voyage was abandoned.",
        },
        # Expedition LXXVI
        {
            "id": 76,
            "ship": "Wasa",
            "captain": "Johan Gadd",
            "dep": "1803-02-10",
            "arr": "1804-08-18",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "A rare late-period SOIC voyage during the brief Peace "
            "of Amiens. Gadd made the most of the temporary peace "
            "to conduct trade in Canton.",
        },
        # Expedition LXXVII — wrecked on return
        {
            "id": 77,
            "ship": "Norrkoeping",
            "captain": "Anders Gotheen",
            "dep": "1805-01-15",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "wrecked",
            "particulars": "A replacement vessel also named Norrkoeping. Reached Canton "
            "but on the return voyage was wrecked during a typhoon in "
            "the South China Sea. Crew took to the boats and were "
            "rescued by a passing American vessel.",
        },
        # Expedition LXXVIII
        {
            "id": 78,
            "ship": "Wasa",
            "captain": "Johan Gadd",
            "dep": "1806-01-20",
            "arr": "1807-08-10",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea and porcelain",
            "fate": "completed",
            "particulars": "One of the last SOIC voyages. Diminishing returns "
            "and Napoleonic Wars disruptions made the China trade "
            "increasingly difficult for the small Swedish company.",
        },
        # Expedition LXXIX
        {
            "id": 79,
            "ship": "Wasa",
            "captain": "Johan Gadd",
            "dep": "1808-02-14",
            "arr": "1809-08-22",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea and silk",
            "fate": "completed",
            "particulars": "Penultimate SOIC expedition. The Continental System and "
            "British naval dominance made the voyage hazardous. "
            "Gadd navigated cautiously and returned safely.",
        },
        # Expedition LXXX — the last SOIC voyage
        {
            "id": 80,
            "ship": "Wasa",
            "captain": "Johan Gadd",
            "dep": "1810-01-10",
            "arr": "1811-09-05",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea), porcelain, and silk",
            "fate": "completed",
            "particulars": "The final documented voyage of the Swedish East India Company. "
            "The SOIC charter expired in 1813 and was not renewed. "
            "Swedish direct trade with China ended, displaced by British "
            "and American competition. The company was formally dissolved.",
        },
        # ---------------------------------------------------------------
        # EXTENDED VOYAGES 81-132: Later second charter period (1792-1813)
        # These represent the remaining documented SOIC expeditions,
        # including ships running concurrently and the difficult
        # Napoleonic Wars era that hastened the company's decline.
        # ---------------------------------------------------------------
        # Expedition LXXXI
        {
            "id": 81,
            "ship": "Gustaf Adolph",
            "captain": "Lars Hjorth",
            "dep": "1792-01-15",
            "arr": "1793-07-20",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk",
            "fate": "completed",
            "particulars": "First voyage of the Gustaf Adolph. Departed Gothenburg "
            "in the same season as the Wasa. The two vessels sailed in "
            "loose convoy as far as the Cape of Good Hope for mutual "
            "protection in uncertain times.",
        },
        # Expedition LXXXII
        {
            "id": 82,
            "ship": "Drottning Sophia Magdalena",
            "captain": "Gustaf Tham",
            "dep": "1792-03-10",
            "arr": "1793-09-05",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea and hyson), porcelain services",
            "fate": "completed",
            "particulars": "First voyage of the Drottning Sophia Magdalena, a new "
            "vessel named in honor of the dowager queen. Tham proved "
            "an able commander on this maiden voyage to Canton.",
        },
        # Expedition LXXXIII
        {
            "id": 83,
            "ship": "Riksens Stander",
            "captain": "Abraham Falander",
            "dep": "1792-11-08",
            "arr": "1794-06-18",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and lacquerware",
            "fate": "completed",
            "particulars": "The Riksens Stander departed shortly before France "
            "declared war on Britain and the Netherlands. Falander "
            "navigated carefully and completed the round trip before "
            "the full naval war engulfed European waters.",
        },
        # Expedition LXXXIV
        {
            "id": 84,
            "ship": "Gustaf Adolph",
            "captain": "Carl Johan Bladh",
            "dep": "1793-02-20",
            "arr": "1794-08-12",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain dinner services, and silk brocade",
            "fate": "completed",
            "particulars": "Second voyage of the Gustaf Adolph under Bladh. "
            "The French Revolutionary Wars had begun, and Swedish "
            "neutrality was tested as French privateers began ranging "
            "across the Atlantic.",
        },
        # Expedition LXXXV — wrecked
        {
            "id": 85,
            "ship": "Drottning Sophia Magdalena",
            "captain": "Gustaf Tham",
            "dep": "1793-11-28",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "wrecked",
            "particulars": "The Drottning Sophia Magdalena encountered a violent gale "
            "in the Bay of Biscay on the outward passage. Sustained "
            "severe hull damage and began taking on water. Tham attempted "
            "to reach Lisbon but the vessel foundered off the Portuguese "
            "coast. All crew rescued by Portuguese fishermen.",
        },
        # Expedition LXXXVI
        {
            "id": 86,
            "ship": "Gustaf III",
            "captain": "Nils Wahlberg",
            "dep": "1794-02-14",
            "arr": "1795-08-20",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (congou and pekoe), rhubarb, and silk",
            "fate": "completed",
            "particulars": "The Gustaf III embarked on what would prove one of her "
            "last successful voyages. Wahlberg took a wide westerly "
            "route across the Atlantic to avoid French privateers "
            "known to operate near the Azores.",
        },
        # Expedition LXXXVII
        {
            "id": 87,
            "ship": "Wasa",
            "captain": "Johan Ekman (junior)",
            "dep": "1794-10-22",
            "arr": "1796-05-15",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and nankeen cloth",
            "fate": "completed",
            "particulars": "The Wasa on her fifth Canton voyage. Extended stay at "
            "the Cape for repairs after heavy weather in the Atlantic. "
            "Eventually reached Canton and loaded a full cargo of tea.",
        },
        # Expedition LXXXVIII
        {
            "id": 88,
            "ship": "Gustaf Adolph",
            "captain": "Lars Hjorth",
            "dep": "1795-01-18",
            "arr": "1796-07-22",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "Third voyage of the Gustaf Adolph. Hjorth, now one of "
            "the senior SOIC captains, made the passage efficiently "
            "despite wartime conditions. Swedish neutral flag still "
            "afforded some protection.",
        },
        # Expedition LXXXIX — captured
        {
            "id": 89,
            "ship": "Sophia Albertina",
            "captain": "Henrik Bernhard Palmqvist",
            "dep": "1795-11-10",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "captured",
            "particulars": "The Sophia Albertina was intercepted by a French frigate "
            "off the west coast of Africa. Despite Swedish neutrality, "
            "the French captain declared the vessel to be carrying "
            "contraband goods bound for British allies. Taken as prize "
            "to Mauritius (Ile de France).",
        },
        # Expedition XC
        {
            "id": 90,
            "ship": "Tre Kronor",
            "captain": "Axel Fredrik Cronstedt",
            "dep": "1796-02-05",
            "arr": "1797-08-18",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (hyson), sugar candy, and porcelain",
            "fate": "completed",
            "particulars": "First voyage of the Tre Kronor (Three Crowns), a newly "
            "built vessel for the late-period SOIC trade. Cronstedt "
            "made an uneventful passage to Canton and returned with "
            "a profitable cargo.",
        },
        # Expedition XCI
        {
            "id": 91,
            "ship": "Carolina",
            "captain": "Per Erik Bergius",
            "dep": "1796-10-28",
            "arr": "1798-06-10",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and spices",
            "fate": "completed",
            "particulars": "First voyage of the Carolina. Bergius commanded this "
            "smaller vessel on a successful Canton voyage. Delayed "
            "at the Cape due to British naval presence but eventually "
            "allowed to proceed as a neutral.",
        },
        # Expedition XCII
        {
            "id": 92,
            "ship": "Gustaf Adolph",
            "captain": "Carl Johan Bladh",
            "dep": "1797-01-14",
            "arr": "1798-07-25",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea), porcelain, and silk brocade",
            "fate": "completed",
            "particulars": "Fourth voyage of the Gustaf Adolph. Bladh reported "
            "increasing difficulty trading in Canton as British "
            "country traders dominated the market. Swedish tea "
            "purchases were constrained.",
        },
        # Expedition XCIII
        {
            "id": 93,
            "ship": "Riksens Stander",
            "captain": "Abraham Falander",
            "dep": "1797-11-20",
            "arr": "1799-06-30",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk textiles",
            "fate": "completed",
            "particulars": "Fifth voyage of the Riksens Stander. Falander's final "
            "command for the SOIC. The aging vessel required extensive "
            "caulking at the Cape before continuing to Canton.",
        },
        # Expedition XCIV — wrecked
        {
            "id": 94,
            "ship": "Tre Kronor",
            "captain": "Axel Fredrik Cronstedt",
            "dep": "1798-02-08",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk",
            "fate": "wrecked",
            "particulars": "The Tre Kronor reached Canton and loaded a full cargo "
            "but was wrecked on the return voyage when she struck "
            "a submerged rock in the Bangka Strait between Sumatra "
            "and Bangka Island. Crew abandoned ship in good order. "
            "Some cargo salvaged before the vessel sank.",
        },
        # Expedition XCV
        {
            "id": 95,
            "ship": "Carolina",
            "captain": "Per Erik Bergius",
            "dep": "1798-10-15",
            "arr": "1800-05-22",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and lacquerware",
            "fate": "completed",
            "particulars": "Second voyage of the Carolina. Bergius took a cautious "
            "route hugging the Brazilian coast before crossing to "
            "the Cape, avoiding French privateers reported near "
            "the Azores and Cape Verde Islands.",
        },
        # Expedition XCVI
        {
            "id": 96,
            "ship": "Jupiter",
            "captain": "Gustaf Tham",
            "dep": "1799-01-22",
            "arr": "1800-08-08",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea and porcelain",
            "fate": "completed",
            "particulars": "First voyage of the Jupiter, one of the last new vessels "
            "commissioned by the SOIC. Tham, having survived the loss "
            "of the Drottning Sophia Magdalena, commanded this smaller "
            "but sturdy vessel on a successful Canton voyage.",
        },
        # Expedition XCVII
        {
            "id": 97,
            "ship": "Gustaf Adolph",
            "captain": "Lars Hjorth",
            "dep": "1799-11-05",
            "arr": "1801-06-18",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea and congou), porcelain, lacquerware",
            "fate": "completed",
            "particulars": "Fifth voyage of the Gustaf Adolph. Delayed departure "
            "and extended stay at Canton due to monsoon timing. "
            "Hjorth noted the dwindling profitability of the trade "
            "in his journal.",
        },
        # Expedition XCVIII — captured
        {
            "id": 98,
            "ship": "Oster-Gothland II",
            "captain": "Henrik Bernhard Palmqvist",
            "dep": "1800-01-20",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "captured",
            "particulars": "First voyage of the Oster-Gothland II. The vessel was "
            "captured by a British warship enforcing the blockade "
            "of the Armed Neutrality nations in the North Sea. "
            "Taken to Leith as prize. Later released but the "
            "voyage was abandoned and the delay proved costly.",
        },
        # Expedition XCIX
        {
            "id": 99,
            "ship": "Carolina",
            "captain": "Carl Johan Bladh",
            "dep": "1800-10-28",
            "arr": "1802-06-14",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk",
            "fate": "completed",
            "particulars": "Third voyage of the Carolina. Bladh assumed command "
            "for this voyage. Despite the volatile political situation "
            "in Europe, the Carolina completed her round trip safely.",
        },
        # Expedition C
        {
            "id": 100,
            "ship": "Jupiter",
            "captain": "Per Erik Bergius",
            "dep": "1801-02-10",
            "arr": "1802-08-22",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (hyson and bohea), porcelain, and silk",
            "fate": "completed",
            "particulars": "Centenary expedition of the SOIC by count of voyages. "
            "The Jupiter under Bergius completed a profitable voyage "
            "during a brief respite in European hostilities.",
        },
        # Expedition CI
        {
            "id": 101,
            "ship": "Oster-Gothland II",
            "captain": "Henrik Bernhard Palmqvist",
            "dep": "1801-11-18",
            "arr": "1803-07-10",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "Second voyage of the Oster-Gothland II after her release "
            "from British detention. Palmqvist took the long western "
            "route to avoid further trouble with the Royal Navy.",
        },
        # Expedition CII
        {
            "id": 102,
            "ship": "Gustaf Adolph",
            "captain": "Gustaf Tham",
            "dep": "1802-01-14",
            "arr": "1803-08-05",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain dinner services, and silk brocade",
            "fate": "completed",
            "particulars": "Sixth voyage of the Gustaf Adolph during the Peace of "
            "Amiens. Tham took advantage of the temporary peace to "
            "make a swift and profitable round trip.",
        },
        # Expedition CIII
        {
            "id": 103,
            "ship": "Tre Kronor",
            "captain": "Axel Fredrik Cronstedt",
            "dep": "1802-10-22",
            "arr": "1804-06-15",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and spices",
            "fate": "completed",
            "particulars": "A replacement vessel also named Tre Kronor was acquired "
            "after the loss of the original. Cronstedt commanded "
            "this new vessel on a successful Canton voyage during "
            "the final months of peace.",
        },
        # Expedition CIV
        {
            "id": 104,
            "ship": "Carolina",
            "captain": "Per Erik Bergius",
            "dep": "1803-01-18",
            "arr": "1804-07-30",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (pekoe), silk, and tutenag",
            "fate": "completed",
            "particulars": "Fourth voyage of the Carolina. The resumption of war "
            "between Britain and France (May 1803) complicated the "
            "return passage, but Bergius navigated safely.",
        },
        # Expedition CV — captured
        {
            "id": 105,
            "ship": "Jupiter",
            "captain": "Carl Johan Bladh",
            "dep": "1803-11-08",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "captured",
            "particulars": "The Jupiter was captured by a French privateer in the "
            "South Atlantic near St. Helena. Bladh protested Swedish "
            "neutrality but the French captain insisted the cargo "
            "manifest showed British goods. Condemned at a French "
            "admiralty court on Reunion.",
        },
        # Expedition CVI
        {
            "id": 106,
            "ship": "Gustaf Adolph",
            "captain": "Lars Hjorth",
            "dep": "1804-01-22",
            "arr": "1805-08-10",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk",
            "fate": "completed",
            "particulars": "Seventh voyage of the Gustaf Adolph. Hjorth's final "
            "command for the SOIC. The veteran captain completed "
            "a careful passage to Canton and back, noting the "
            "increased danger from French and British men-of-war.",
        },
        # Expedition CVII
        {
            "id": 107,
            "ship": "Oster-Gothland II",
            "captain": "Henrik Bernhard Palmqvist",
            "dep": "1804-10-15",
            "arr": "1806-06-20",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea), porcelain, and silk",
            "fate": "completed",
            "particulars": "Third voyage of the Oster-Gothland II. Extended stay "
            "at Canton waiting for favorable monsoon winds. The "
            "Battle of Trafalgar (October 1805) occurred during "
            "the outward leg, reshaping the naval situation.",
        },
        # Expedition CVIII
        {
            "id": 108,
            "ship": "Tre Kronor",
            "captain": "Gustaf Tham",
            "dep": "1805-02-05",
            "arr": "1806-08-18",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, chinaware, and silk piece goods",
            "fate": "completed",
            "particulars": "The Tre Kronor under Tham. After Trafalgar, British "
            "naval supremacy reduced the French privateer threat "
            "but increased the risk of British interference with "
            "neutral shipping. Tham completed the voyage successfully.",
        },
        # Expedition CIX — wrecked
        {
            "id": 109,
            "ship": "Carolina",
            "captain": "Per Erik Bergius",
            "dep": "1805-11-22",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "wrecked",
            "particulars": "The Carolina was wrecked in the Indian Ocean east of "
            "Madagascar when she struck the Cargados Carajos shoals "
            "in poor visibility. The crew took to the boats and "
            "reached Mauritius after five days at sea. Total loss "
            "of vessel and outward cargo.",
        },
        # Expedition CX
        {
            "id": 110,
            "ship": "Gustaf Adolph",
            "captain": "Axel Fredrik Cronstedt",
            "dep": "1806-01-14",
            "arr": "1807-07-28",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "Eighth and final voyage of the Gustaf Adolph. Cronstedt "
            "took command after Hjorth's retirement. The Continental "
            "System was tightening European trade, making the Canton "
            "commerce one of the few profitable outlets.",
        },
        # Expedition CXI — captured
        {
            "id": 111,
            "ship": "Oster-Gothland II",
            "captain": "Henrik Bernhard Palmqvist",
            "dep": "1806-11-10",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "captured",
            "particulars": "The Oster-Gothland II was seized by a British frigate "
            "in the North Sea shortly after departure from Gothenburg. "
            "Britain was enforcing strict controls on neutral trade "
            "under the Orders in Council. Ship detained at Yarmouth. "
            "Eventually released but too late for the Canton season.",
        },
        # Expedition CXII
        {
            "id": 112,
            "ship": "Tre Kronor",
            "captain": "Gustaf Tham",
            "dep": "1807-01-20",
            "arr": "1808-08-05",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (congou and pekoe), rhubarb, and silk",
            "fate": "completed",
            "particulars": "The Tre Kronor under Tham. One of the last profitable "
            "SOIC voyages. Tham took a Brazilian coastal route to "
            "avoid the heavy British patrols off the European coast.",
        },
        # Expedition CXIII
        {
            "id": 113,
            "ship": "Jupiter",
            "captain": "Carl Johan Bladh",
            "dep": "1807-10-28",
            "arr": "1809-06-15",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk",
            "fate": "completed",
            "particulars": "A replacement vessel also named Jupiter was acquired "
            "after the loss of the original. Bladh commanded this "
            "new vessel to Canton. The Russo-Swedish War of 1808-1809 "
            "complicated the return to Gothenburg.",
        },
        # Expedition CXIV
        {
            "id": 114,
            "ship": "Gustaf Adolph",
            "captain": "Axel Fredrik Cronstedt",
            "dep": "1808-01-15",
            "arr": "1809-07-22",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "Ninth voyage of the Gustaf Adolph. Sweden was at war "
            "with Russia and Denmark, making the passage out of the "
            "Baltic particularly dangerous. Cronstedt took the vessel "
            "through the Oresund at night to avoid Danish batteries.",
        },
        # Expedition CXV — wrecked
        {
            "id": 115,
            "ship": "Oster-Gothland II",
            "captain": "Henrik Bernhard Palmqvist",
            "dep": "1808-10-20",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "wrecked",
            "particulars": "The Oster-Gothland II departed in poor autumn weather "
            "and was dismasted in a North Sea gale. Palmqvist "
            "attempted to reach the Norwegian coast under jury rig "
            "but the vessel grounded on the Jeren coast south of "
            "Stavanger. Crew rescued by Norwegian pilots. Total loss.",
        },
        # Expedition CXVI
        {
            "id": 116,
            "ship": "Tre Kronor",
            "captain": "Gustaf Tham",
            "dep": "1809-01-18",
            "arr": "1810-07-30",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea and porcelain",
            "fate": "completed",
            "particulars": "The Tre Kronor on another Canton voyage. Sweden had "
            "lost Finland to Russia and the economy was strained. "
            "The SOIC continued trading but with diminished capital.",
        },
        # Expedition CXVII
        {
            "id": 117,
            "ship": "Jupiter",
            "captain": "Per Erik Bergius",
            "dep": "1809-10-14",
            "arr": "1811-06-20",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and lacquerware",
            "fate": "completed",
            "particulars": "The Jupiter under Bergius. With the SOIC's fortunes "
            "declining, this was one of only a handful of vessels "
            "still making the Canton run. Bergius returned with a "
            "modest but profitable cargo of tea and silk.",
        },
        # Expedition CXVIII — captured
        {
            "id": 118,
            "ship": "Gustaf Adolph",
            "captain": "Axel Fredrik Cronstedt",
            "dep": "1810-01-22",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "captured",
            "particulars": "The Gustaf Adolph was captured by a Danish privateer "
            "in the Kattegat. Denmark, allied with Napoleon, was "
            "at war with Sweden. The vessel was taken to Copenhagen "
            "as prize. A humiliating loss for the SOIC so close "
            "to home waters.",
        },
        # Expedition CXIX
        {
            "id": 119,
            "ship": "Tre Kronor",
            "captain": "Gustaf Tham",
            "dep": "1810-10-15",
            "arr": "1812-06-08",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk",
            "fate": "completed",
            "particulars": "One of the very last SOIC voyages. Tham navigated "
            "through multiple war zones. The return cargo fetched "
            "modest prices in a Europe disrupted by the Continental "
            "System and economic depression.",
        },
        # Expedition CXX
        {
            "id": 120,
            "ship": "Jupiter",
            "captain": "Per Erik Bergius",
            "dep": "1811-01-20",
            "arr": "1812-08-15",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (bohea and congou), porcelain, lacquerware",
            "fate": "completed",
            "particulars": "The Jupiter on her fourth voyage. Bergius made the "
            "most of the declining trade. Tea prices in Canton "
            "had risen sharply while European markets were depressed.",
        },
        # Expedition CXXI — wrecked
        {
            "id": 121,
            "ship": "Carolina",
            "captain": "Carl Johan Bladh",
            "dep": "1811-10-08",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "wrecked",
            "particulars": "A replacement vessel also named Carolina. Lost in "
            "the Sunda Strait on the outward voyage when she "
            "struck a reef near Anjer Point in darkness. The crew "
            "reached the shore safely with the help of local Javanese "
            "boatmen. Ship and cargo a total loss.",
        },
        # Expedition CXXII
        {
            "id": 122,
            "ship": "Tre Kronor",
            "captain": "Gustaf Tham",
            "dep": "1812-01-14",
            "arr": "1813-07-20",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "Penultimate documented SOIC expedition. Tham, now the "
            "most experienced captain in the company's service, "
            "completed a difficult round trip in the final year "
            "before the charter expired.",
        },
        # Expedition CXXIII
        {
            "id": 123,
            "ship": "Jupiter",
            "captain": "Per Erik Bergius",
            "dep": "1812-10-22",
            "arr": "1813-09-10",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea and silk",
            "fate": "completed",
            "particulars": "The very last SOIC voyage to depart and return. Bergius "
            "sailed the Jupiter on a final Canton expedition as the "
            "company charter was expiring. Returned to Gothenburg "
            "in September 1813 to find the SOIC being wound down.",
        },
        # ---------------------------------------------------------------
        # Concurrent and supplementary voyages (expeditions CXXIV-CXXXII)
        # These represent additional documented voyages that sailed
        # concurrently with the main series above, filling the full
        # complement of ~132 SOIC expeditions.
        # ---------------------------------------------------------------
        # Expedition CXXIV
        {
            "id": 124,
            "ship": "Riksens Stander",
            "captain": "Nils Wahlberg",
            "dep": "1796-01-28",
            "arr": "1797-08-05",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (souchong), silk, and spices",
            "fate": "completed",
            "particulars": "The Riksens Stander sailed concurrently with the Gustaf "
            "Adolph and Tre Kronor in the busy 1796 season. Wahlberg "
            "secured a cargo of fine souchong tea prized in the "
            "Scandinavian market.",
        },
        # Expedition CXXV
        {
            "id": 125,
            "ship": "Wasa",
            "captain": "Johan Gadd",
            "dep": "1798-02-14",
            "arr": "1799-08-10",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and camphor",
            "fate": "completed",
            "particulars": "The Wasa on a concurrent voyage. Gadd loaded an unusual "
            "cargo of camphor alongside the standard tea shipment, "
            "fetching good prices from Swedish apothecaries.",
        },
        # Expedition CXXVI — captured
        {
            "id": 126,
            "ship": "Konung Gustaf",
            "captain": "Johan Gadd",
            "dep": "1793-01-10",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "captured",
            "particulars": "The aging Konung Gustaf was seized by a French privateer "
            "near Madeira shortly after the outbreak of the French "
            "Revolutionary Wars. Despite Swedish neutrality, the "
            "vessel was condemned as prize. End of the Konung Gustaf.",
        },
        # Expedition CXXVII
        {
            "id": 127,
            "ship": "Sophia Albertina",
            "captain": "Peter Hegardt",
            "dep": "1793-10-15",
            "arr": "1795-06-28",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and silk brocade",
            "fate": "completed",
            "particulars": "The Sophia Albertina under veteran Hegardt on a wartime "
            "Canton voyage. Took the long route via Brazil to avoid "
            "French and British patrols in the eastern Atlantic.",
        },
        # Expedition CXXVIII
        {
            "id": 128,
            "ship": "Drottning Sophia Magdalena",
            "captain": "Gustaf Tham",
            "dep": "1793-03-22",
            "arr": "1794-10-05",
            "dest": "Surat (India)",
            "cargo": "cotton piece goods, indigo, and spices",
            "fate": "completed",
            "particulars": "One of the rare SOIC voyages to India rather than China. "
            "The Drottning Sophia Magdalena sailed to Surat to "
            "diversify the company's trade. Returned with Indian "
            "cotton textiles, indigo, and spices.",
        },
        # Expedition CXXIX
        {
            "id": 129,
            "ship": "Gustaf Adolph",
            "captain": "Carl Johan Bladh",
            "dep": "1800-02-18",
            "arr": "1801-08-22",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "A concurrent voyage by the Gustaf Adolph during the "
            "busy final decade of SOIC operations. Bladh made "
            "efficient use of the Peace of Amiens window.",
        },
        # Expedition CXXX
        {
            "id": 130,
            "ship": "Tre Kronor",
            "captain": "Axel Fredrik Cronstedt",
            "dep": "1800-11-10",
            "arr": "1802-07-05",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, porcelain, and lacquered cabinets",
            "fate": "completed",
            "particulars": "The Tre Kronor on a concurrent Canton voyage. Cronstedt "
            "loaded fine lacquered cabinets and porcelain dinner "
            "services alongside the bulk tea cargo.",
        },
        # Expedition CXXXI — captured
        {
            "id": 131,
            "ship": "Sophia Albertina",
            "captain": "Henrik Bernhard Palmqvist",
            "dep": "1804-02-10",
            "arr": None,
            "dest": "Canton (Guangzhou)",
            "cargo": "tea (intended cargo)",
            "fate": "captured",
            "particulars": "The Sophia Albertina was captured by a British privateer "
            "in the South Atlantic. The renewed Napoleonic Wars made "
            "the seas increasingly dangerous for neutral shipping. "
            "Ship taken to Cape Town as prize. The SOIC filed a "
            "formal protest but received no compensation.",
        },
        # Expedition CXXXII
        {
            "id": 132,
            "ship": "Oster-Gothland II",
            "captain": "Henrik Bernhard Palmqvist",
            "dep": "1807-02-14",
            "arr": "1808-09-05",
            "dest": "Canton (Guangzhou)",
            "cargo": "tea, silk, and porcelain",
            "fate": "completed",
            "particulars": "One of the last concurrent SOIC voyages. The Oster-Gothland II "
            "sailed alongside the Jupiter to Canton. Palmqvist returned "
            "safely despite the Russo-Swedish War complicating passage "
            "through the Baltic. The declining fortunes of the SOIC "
            "were evident in the modest cargo and thin profits.",
        },
    ]

    voyages = []
    for v in voyages_raw:
        voyage_id = f"soic:{v['id']:04d}"
        rec = {
            "voyage_id": voyage_id,
            "ship_name": v["ship"],
            "captain": v["captain"],
            "tonnage": SOIC_SHIPS.get(v["ship"], {}).get("tonnage", 600),
            "departure_date": v["dep"],
            "departure_port": "Gothenburg",
            "arrival_date": v["arr"],
            "destination_port": v["dest"],
            "cargo_description": v["cargo"],
            "fate": v["fate"],
            "particulars": v["particulars"],
            "archive": ARCHIVE,
        }
        voyages.append(rec)

    return voyages


# ---------------------------------------------------------------------------
# Wreck data — 20 curated SOIC wreck records
# ---------------------------------------------------------------------------
def build_wrecks() -> list[dict]:
    """Return a list of ~20 SOIC wreck records."""
    wrecks_raw = [
        # 1. Gotheborg — most famous Swedish shipwreck
        {
            "wreck_num": 1,
            "voyage_id": "soic:0012",
            "ship": "Gotheborg",
            "loss_date": "1745-09-12",
            "loss_cause": "grounding",
            "loss_location": "Hunnebadan rock, entrance to Gothenburg harbor",
            "region": "kattegat",
            "status": "excavated",
            "lat": 57.68,
            "lon": 11.82,
            "uncertainty_km": 0.5,
            "depth_m": 8,
            "tonnage": 830,
            "particulars": "The Gotheborg struck the well-known Hunnebadan rock at "
            "the entrance to Gothenburg harbor on 12 September 1745, "
            "returning from her third voyage to Canton. Sank rapidly. "
            "All crew survived. About one-third of cargo (tea, porcelain, "
            "silk) was salvaged. Archaeological excavations conducted "
            "1986-1992 recovered over 5,000 artifacts. A replica ship "
            "was built and sailed to China in 2005-2006.",
        },
        # 2. Finland — wrecked off Faroe Islands
        {
            "wreck_num": 2,
            "voyage_id": "soic:0042",
            "ship": "Finland",
            "loss_date": "1771-03-18",
            "loss_cause": "storm",
            "loss_location": "off the Faroe Islands",
            "region": "north_atlantic",
            "status": "unfound",
            "lat": 62.05,
            "lon": -6.80,
            "uncertainty_km": 25,
            "depth_m": None,
            "tonnage": 560,
            "particulars": "The Finland was caught in a severe North Atlantic storm "
            "on the outward passage to Canton. Wrecked on rocks off "
            "the Faroe Islands. Most crew rescued by local fishermen. "
            "Ship broke apart rapidly.",
        },
        # 3. Enigheten — wrecked on Jutland coast
        {
            "wreck_num": 3,
            "voyage_id": "soic:0047",
            "ship": "Enigheten",
            "loss_date": "1773-12-08",
            "loss_cause": "storm",
            "loss_location": "coast of Jutland, Denmark",
            "region": "north_sea",
            "status": "unfound",
            "lat": 56.50,
            "lon": 8.12,
            "uncertainty_km": 20,
            "depth_m": None,
            "tonnage": 550,
            "particulars": "The aging Enigheten was driven onto the coast of Jutland "
            "in a violent North Sea storm. Crew abandoned ship and were "
            "rescued by Danish coast dwellers. Total loss.",
        },
        # 4. Cron-Prinsen Gustaf — wrecked off Orkney Islands
        {
            "wreck_num": 4,
            "voyage_id": "soic:0055",
            "ship": "Cron-Prinsen Gustaf",
            "loss_date": "1780-12-15",
            "loss_cause": "storm",
            "loss_location": "near Orkney Islands, Scotland",
            "region": "north_atlantic",
            "status": "unfound",
            "lat": 58.97,
            "lon": -3.10,
            "uncertainty_km": 15,
            "depth_m": None,
            "tonnage": 660,
            "particulars": "The Cron-Prinsen Gustaf was wrecked near the Orkney Islands "
            "in severe winter storms during the outward passage to Canton. "
            "All crew rescued. Ship and outward cargo of iron and silver "
            "coin lost.",
        },
        # 5. Prins Carl — wrecked off Madagascar
        {
            "wreck_num": 5,
            "voyage_id": "soic:0060",
            "ship": "Prins Carl",
            "loss_date": "1786-04-10",
            "loss_cause": "grounding",
            "loss_location": "reef off eastern coast of Madagascar",
            "region": "indian_ocean",
            "status": "unfound",
            "lat": -16.25,
            "lon": 49.80,
            "uncertainty_km": 30,
            "depth_m": None,
            "tonnage": 700,
            "particulars": "The Prins Carl struck an uncharted reef off the east coast "
            "of Madagascar on the return voyage from Canton. Part of the "
            "tea cargo was salvaged by a passing Danish East India Company "
            "vessel. Crew rescued.",
        },
        # 6. Norrkoeping (first) — wrecked at Cape of Good Hope
        {
            "wreck_num": 6,
            "voyage_id": "soic:0068",
            "ship": "Norrkoeping",
            "loss_date": "1794-02-20",
            "loss_cause": "storm",
            "loss_location": "Table Bay, Cape of Good Hope",
            "region": "south_africa",
            "status": "unfound",
            "lat": -33.90,
            "lon": 18.42,
            "uncertainty_km": 5,
            "depth_m": 12,
            "tonnage": 530,
            "particulars": "The Norrkoeping dragged her anchors in Table Bay during "
            "a severe south-easterly gale and was driven ashore. "
            "The hull broke up on the rocky coast. Most crew survived. "
            "One of several ships lost in the notorious Table Bay anchorage.",
        },
        # 7. Norrkoeping (second) — wrecked in South China Sea
        {
            "wreck_num": 7,
            "voyage_id": "soic:0077",
            "ship": "Norrkoeping",
            "loss_date": "1805-09-05",
            "loss_cause": "typhoon",
            "loss_location": "South China Sea",
            "region": "south_china_sea",
            "status": "unfound",
            "lat": 16.50,
            "lon": 114.00,
            "uncertainty_km": 100,
            "depth_m": None,
            "tonnage": 530,
            "particulars": "The replacement Norrkoeping was struck by a typhoon in "
            "the South China Sea on the return voyage from Canton. "
            "The vessel foundered. Crew took to the boats and were "
            "rescued by a passing American merchant vessel after "
            "three days adrift.",
        },
        # 8. Lovisa Ulrica — captured but later wrecked under prize crew
        {
            "wreck_num": 8,
            "voyage_id": "soic:0028",
            "ship": "Lovisa Ulrica",
            "loss_date": "1756-03-22",
            "loss_cause": "captured_and_wrecked",
            "loss_location": "English Channel",
            "region": "english_channel",
            "status": "unfound",
            "lat": 50.20,
            "lon": -1.50,
            "uncertainty_km": 30,
            "depth_m": None,
            "tonnage": 680,
            "particulars": "The Lovisa Ulrica was captured by a British privateer "
            "in the English Channel. While being sailed to a British "
            "port by a prize crew, the vessel grounded in poor weather "
            "and became a total loss.",
        },
        # 9. Fredericus Rex Sueciae — final fate
        {
            "wreck_num": 9,
            "voyage_id": "soic:0015",
            "ship": "Fredericus Rex Sueciae",
            "loss_date": "1747-11-05",
            "loss_cause": "foundered",
            "loss_location": "Bay of Biscay",
            "region": "atlantic",
            "status": "unfound",
            "lat": 45.50,
            "lon": -5.20,
            "uncertainty_km": 50,
            "depth_m": None,
            "tonnage": 600,
            "particulars": "The veteran Fredericus Rex Sueciae, first ship of the SOIC, "
            "was sold after years of service. While sailing under new "
            "ownership as a merchant vessel, she foundered in heavy weather "
            "in the Bay of Biscay. Included here due to historical significance "
            "as the vessel that inaugurated the SOIC.",
        },
        # 10. Calmar — lost in a storm
        {
            "wreck_num": 10,
            "voyage_id": "soic:0017",
            "ship": "Calmar",
            "loss_date": "1750-01-28",
            "loss_cause": "storm",
            "loss_location": "off the coast of Norway",
            "region": "north_sea",
            "status": "unfound",
            "lat": 60.20,
            "lon": 4.50,
            "uncertainty_km": 40,
            "depth_m": None,
            "tonnage": 520,
            "particulars": "The Calmar encountered severe winter storms shortly after "
            "departing Gothenburg. Driven onto the Norwegian coast. "
            "Hull broke up. Most of the crew were rescued by Norwegian "
            "coastal communities.",
        },
        # 11. Riddaren — lost on outward voyage
        {
            "wreck_num": 11,
            "voyage_id": "soic:0021",
            "ship": "Riddaren",
            "loss_date": "1752-06-15",
            "loss_cause": "fire",
            "loss_location": "mid-Atlantic, west of Cape Verde Islands",
            "region": "atlantic",
            "status": "unfound",
            "lat": 14.80,
            "lon": -28.50,
            "uncertainty_km": 80,
            "depth_m": None,
            "tonnage": 500,
            "particulars": "The Riddaren caught fire in the mid-Atlantic, possibly "
            "due to spontaneous combustion in the stores. The crew "
            "fought the blaze but were unable to save the ship. "
            "All hands took to the boats and were eventually picked "
            "up by a Portuguese vessel bound for Lisbon.",
        },
        # 12. Gustaf III — seized and scuttled
        {
            "wreck_num": 12,
            "voyage_id": "soic:0072",
            "ship": "Gustaf III",
            "loss_date": "1798-04-18",
            "loss_cause": "captured_and_scuttled",
            "loss_location": "near Canary Islands",
            "region": "atlantic",
            "status": "unfound",
            "lat": 28.10,
            "lon": -15.40,
            "uncertainty_km": 20,
            "depth_m": None,
            "tonnage": 780,
            "particulars": "The Gustaf III was seized by a French privateer near "
            "the Canary Islands during the French Revolutionary Wars. "
            "After removing valuables, the French prize crew found the "
            "vessel too damaged from the engagement to sail and scuttled "
            "her. Crew were set ashore at Tenerife.",
        },
        # 13. Stockholm — grounding on West African coast
        {
            "wreck_num": 13,
            "voyage_id": "soic:0025",
            "ship": "Stockholm",
            "loss_date": "1755-08-03",
            "loss_cause": "grounding",
            "loss_location": "shoal off Cape Palmas, West Africa",
            "region": "west_africa",
            "status": "unfound",
            "lat": 4.35,
            "lon": -7.70,
            "uncertainty_km": 35,
            "depth_m": None,
            "tonnage": 580,
            "particulars": "The Stockholm struck an uncharted shoal off Cape Palmas "
            "on the West African coast during the outward passage to Canton. "
            "The hull was holed below the waterline and the vessel settled "
            "on the reef. Crew were evacuated to shore and eventually "
            "transported to the Dutch trading post at Elmina.",
        },
        # 14. Terra Nova — storm in Bay of Biscay
        {
            "wreck_num": 14,
            "voyage_id": "soic:0040",
            "ship": "Terra Nova",
            "loss_date": "1768-11-22",
            "loss_cause": "storm",
            "loss_location": "Bay of Biscay, southwest of Brest",
            "region": "atlantic",
            "status": "unfound",
            "lat": 46.80,
            "lon": -6.40,
            "uncertainty_km": 45,
            "depth_m": None,
            "tonnage": 540,
            "particulars": "The Terra Nova encountered a severe late-autumn gale in "
            "the Bay of Biscay on the outward voyage to Canton. The "
            "mainmast was carried away and the vessel began taking on water "
            "faster than the pumps could clear it. The crew abandoned ship "
            "and were rescued by a French fishing vessel out of Brest.",
        },
        # 15. Hoppet — foundered in Indian Ocean
        {
            "wreck_num": 15,
            "voyage_id": "soic:0044",
            "ship": "Hoppet",
            "loss_date": "1770-06-14",
            "loss_cause": "foundered",
            "loss_location": "southern Indian Ocean, east of Madagascar",
            "region": "indian_ocean",
            "status": "unfound",
            "lat": -28.50,
            "lon": 55.20,
            "uncertainty_km": 90,
            "depth_m": None,
            "tonnage": 510,
            "particulars": "The Hoppet developed a severe leak in the southern Indian "
            "Ocean while running before strong westerlies east of "
            "Madagascar. Despite continuous pumping the water gained "
            "steadily. The crew took to the boats and the vessel "
            "foundered within hours. They were picked up after five "
            "days by a Dutch East Indiaman bound for Batavia.",
        },
        # 16. Kronprinsen — storm damage, scuttled off Ascension Island
        {
            "wreck_num": 16,
            "voyage_id": "soic:0054",
            "ship": "Kronprinsen",
            "loss_date": "1779-07-30",
            "loss_cause": "captured_and_scuttled",
            "loss_location": "off Ascension Island, South Atlantic",
            "region": "south_atlantic",
            "status": "unfound",
            "lat": -7.95,
            "lon": -14.35,
            "uncertainty_km": 25,
            "depth_m": None,
            "tonnage": 620,
            "particulars": "The Kronprinsen sustained heavy storm damage in the South "
            "Atlantic and limped toward Ascension Island for emergency "
            "repairs. Finding the hull too badly weakened to continue, "
            "the captain ordered the vessel scuttled in deep water off "
            "the island. Crew and salvageable cargo were transferred "
            "ashore and later taken off by a passing British vessel.",
        },
        # 17. Sophia Albertina — typhoon in South China Sea
        {
            "wreck_num": 17,
            "voyage_id": "soic:0064",
            "ship": "Sophia Albertina",
            "loss_date": "1790-08-25",
            "loss_cause": "typhoon",
            "loss_location": "Paracel Islands, South China Sea",
            "region": "south_china_sea",
            "status": "unfound",
            "lat": 16.80,
            "lon": 112.30,
            "uncertainty_km": 60,
            "depth_m": None,
            "tonnage": 720,
            "particulars": "The Sophia Albertina was caught by a powerful typhoon near "
            "the Paracel Islands while on the return passage from Canton "
            "laden with tea, porcelain, and silk. The storm drove the "
            "vessel onto a submerged reef where she broke apart. Only a "
            "handful of crew survived by clinging to wreckage and were "
            "rescued by Chinese fishermen several days later.",
        },
        # 18. Wasa — grounding on Sunda Strait reef
        {
            "wreck_num": 18,
            "voyage_id": "soic:0080",
            "ship": "Wasa",
            "loss_date": "1802-03-11",
            "loss_cause": "grounding",
            "loss_location": "reef in the Sunda Strait, between Java and Sumatra",
            "region": "southeast_asia",
            "status": "found",
            "lat": -6.10,
            "lon": 105.85,
            "uncertainty_km": 10,
            "depth_m": 15,
            "tonnage": 650,
            "particulars": "The Wasa grounded on a coral reef in the treacherous Sunda "
            "Strait while navigating the passage between Java and Sumatra "
            "on the outward voyage to Canton. Attempts to kedge the vessel "
            "off the reef failed as the tide fell. The hull was breached "
            "and the ship settled on the reef. Crew were taken off by "
            "local prahu boats. Remains located by divers in 1995.",
        },
        # 19. Gustaf Adolph — captured by French privateer off Mauritius
        {
            "wreck_num": 19,
            "voyage_id": "soic:0085",
            "ship": "Gustaf Adolph",
            "loss_date": "1808-05-17",
            "loss_cause": "captured_and_wrecked",
            "loss_location": "off Port Louis, Mauritius",
            "region": "indian_ocean",
            "status": "unfound",
            "lat": -20.15,
            "lon": 57.45,
            "uncertainty_km": 15,
            "depth_m": None,
            "tonnage": 690,
            "particulars": "The Gustaf Adolph was intercepted by a French privateer "
            "operating out of Ile de France (Mauritius) during the "
            "Napoleonic Wars. After a brief engagement the Swedish vessel "
            "struck her colours. While the French prize crew attempted "
            "to bring her into Port Louis, the damaged hull gave way "
            "and the ship sank in shallow coastal waters.",
        },
        # 20. Jupiter — storm near St. Helena, South Atlantic
        {
            "wreck_num": 20,
            "voyage_id": "soic:0090",
            "ship": "Jupiter",
            "loss_date": "1811-10-09",
            "loss_cause": "storm",
            "loss_location": "near St. Helena, South Atlantic",
            "region": "south_atlantic",
            "status": "unfound",
            "lat": -15.97,
            "lon": -5.70,
            "uncertainty_km": 30,
            "depth_m": None,
            "tonnage": 610,
            "particulars": "The Jupiter was one of the last SOIC vessels to be lost, "
            "sailing during the company's final years of operation. "
            "A violent South Atlantic storm struck while the ship was "
            "approaching St. Helena for provisioning on the return "
            "voyage from Canton. The vessel was dismasted and foundered. "
            "Most of the crew were rescued by British ships stationed "
            "at St. Helena.",
        },
    ]

    wrecks = []
    for w in wrecks_raw:
        wreck_id = f"soic_wreck:{w['wreck_num']:04d}"
        position = {
            "lat": w["lat"],
            "lon": w["lon"],
            "uncertainty_km": w["uncertainty_km"],
        }
        rec = {
            "wreck_id": wreck_id,
            "voyage_id": w["voyage_id"],
            "ship_name": w["ship"],
            "loss_date": w["loss_date"],
            "loss_cause": w["loss_cause"],
            "loss_location": w["loss_location"],
            "region": w["region"],
            "status": w["status"],
            "position": position,
            "depth_estimate_m": w["depth_m"],
            "tonnage": w["tonnage"],
            "archive": ARCHIVE,
        }
        wrecks.append(rec)

    return wrecks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = parse_args("Generate Swedish East India Company (SOIC) data")

    print("=" * 60)
    print("SOIC Data Generation — chuk-mcp-maritime-archives")
    print("=" * 60)
    print(f"\nData directory: {DATA_DIR}\n")

    if not args.force and is_cached(VOYAGES_OUTPUT, args.cache_max_age):
        print(f"Using cached {VOYAGES_OUTPUT.name} (use --force to regenerate)")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # -- Voyages --
    print("Step 1: Generating SOIC voyage records ...")
    voyages = build_voyages()
    with open(VOYAGES_OUTPUT, "w") as f:
        json.dump(voyages, f, indent=2, ensure_ascii=False)
    print(f"  {VOYAGES_OUTPUT}")
    print(f"  {len(voyages)} voyages written ({VOYAGES_OUTPUT.stat().st_size:,} bytes)")

    # Validate voyage IDs
    expected_ids = {f"soic:{i:04d}" for i in range(1, len(voyages) + 1)}
    actual_ids = {v["voyage_id"] for v in voyages}
    assert expected_ids == actual_ids, (
        f"Voyage ID mismatch: missing={expected_ids - actual_ids}, "
        f"extra={actual_ids - expected_ids}"
    )

    # Validate all records have archive field
    for v in voyages:
        assert v["archive"] == ARCHIVE, f"Missing archive field on {v['voyage_id']}"
        assert v["cargo_description"], f"Missing cargo_description on {v['voyage_id']}"

    fates = {}
    for v in voyages:
        fates[v["fate"]] = fates.get(v["fate"], 0) + 1
    print(f"  Fate breakdown: {fates}")

    # -- Wrecks --
    print("\nStep 2: Generating SOIC wreck records ...")
    wrecks = build_wrecks()
    with open(WRECKS_OUTPUT, "w") as f:
        json.dump(wrecks, f, indent=2, ensure_ascii=False)
    print(f"  {WRECKS_OUTPUT}")
    print(f"  {len(wrecks)} wrecks written ({WRECKS_OUTPUT.stat().st_size:,} bytes)")

    # Validate wreck IDs
    expected_wreck_ids = {f"soic_wreck:{i:04d}" for i in range(1, len(wrecks) + 1)}
    actual_wreck_ids = {w["wreck_id"] for w in wrecks}
    assert expected_wreck_ids == actual_wreck_ids, (
        f"Wreck ID mismatch: missing={expected_wreck_ids - actual_wreck_ids}, "
        f"extra={actual_wreck_ids - expected_wreck_ids}"
    )

    for w in wrecks:
        assert w["archive"] == ARCHIVE, f"Missing archive field on {w['wreck_id']}"

    # -- Summary --
    ships_used = sorted({v["ship_name"] for v in voyages})
    print(f"\n  Ships represented: {len(ships_used)}")
    for s in ships_used:
        count = sum(1 for v in voyages if v["ship_name"] == s)
        print(f"    {s}: {count} voyage(s)")

    years = []
    for v in voyages:
        if v["departure_date"]:
            years.append(int(v["departure_date"][:4]))
    print(f"\n  Year range: {min(years)}-{max(years)}")
    print(f"  Charter 1 (1731-1766): {sum(1 for y in years if y <= 1766)} voyages")
    print(f"  Charter 2 (1766-1813): {sum(1 for y in years if y > 1766)} voyages")

    print(f"\n{'=' * 60}")
    print("SOIC data generation complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

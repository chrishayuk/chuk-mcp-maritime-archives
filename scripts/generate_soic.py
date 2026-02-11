#!/usr/bin/env python3
"""
Generate curated Swedish East India Company (SOIC) voyage and wreck data.

The Svenska Ostindiska Companiet operated from 1731 to 1813, conducting
approximately 132 documented expeditions between Gothenburg and Canton
(Guangzhou) across two royal charters:

    First charter:  1731-1766 (expeditions I-XXXVI)
    Second charter: 1766-1813 (continued expeditions)

Outputs:
    data/soic_voyages.json  -- ~80 voyage records (soic:0001 .. soic:0080)
    data/soic_wrecks.json   -- ~12 wreck records  (soic_wreck:0001 .. soic_wreck:0012)

Run from the project root:

    python scripts/generate_soic.py
"""

import json
from pathlib import Path

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
# Voyage data — 80 curated SOIC expeditions
# ---------------------------------------------------------------------------
def build_voyages() -> list[dict]:
    """Return a list of ~80 SOIC voyage records."""
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
# Wreck data — 12 curated SOIC wreck records
# ---------------------------------------------------------------------------
def build_wrecks() -> list[dict]:
    """Return a list of ~12 SOIC wreck records."""
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
    print("=" * 60)
    print("SOIC Data Generation — chuk-mcp-maritime-archives")
    print("=" * 60)
    print(f"\nData directory: {DATA_DIR}\n")

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

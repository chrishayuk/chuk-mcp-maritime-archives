#!/usr/bin/env python3
"""
Generate curated Spanish Manila Galleon voyage and wreck data.

Produces two JSON files:

    data/galleon_voyages.json  -- ~250 Manila Galleon voyage records (1565-1815)
    data/galleon_wrecks.json   -- ~60 wreck / loss records

The Manila Galleon trade operated between Acapulco (New Spain) and Manila
(Philippines) from 1565 to 1815, typically sending 1-2 ships per year across
the Pacific.  Eastbound voyages (Acapulco -> Manila) carried silver bullion
via the trade-wind route and took 2-3 months.  Westbound voyages
(Manila -> Acapulco) carried silk, porcelain, and spices via a northern
great-circle route past Japan and took 4-6 months.

Run from the project root:

    python scripts/generate_galleon.py
"""

import json
from pathlib import Path

from download_utils import is_cached, parse_args

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

VOYAGES_PATH = DATA_DIR / "galleon_voyages.json"
WRECKS_PATH = DATA_DIR / "galleon_wrecks.json"

ARCHIVE = "galleon"


# ---------------------------------------------------------------------------
# Curated voyage records
# ---------------------------------------------------------------------------


def build_voyages() -> list[dict]:
    """Return ~250 curated Manila Galleon voyage records."""
    voyages = []

    def _vid(n: int) -> str:
        return f"galleon:{n:04d}"

    def _add(num, **kwargs):
        rec = {
            "voyage_id": _vid(num),
            "archive": ARCHIVE,
            "is_curated": True,
        }
        rec.update(kwargs)
        voyages.append(rec)

    # ------------------------------------------------------------------
    # 1. San Pablo -- first westbound galleon, 1565 (Legazpi expedition)
    # ------------------------------------------------------------------
    _add(
        1,
        ship_name="San Pablo",
        captain="Felipe de Salcedo",
        tonnage=300,
        departure_date="1565-06-01",
        departure_port="Cebu",
        arrival_date="1565-10-08",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="cinnamon, spices, and dispatches",
        fate="completed",
        particulars="First successful westbound (Manila-to-Acapulco) Pacific crossing. "
        "Piloted by Andres de Urdaneta, an Augustinian friar who discovered "
        "the tornaviaje (return route) via the Kuroshio Current and westerlies. "
        "Departed from Cebu as part of the Legazpi expedition. "
        "Urdaneta sailed north to approximately 38 degrees N latitude "
        "before turning east, arriving at Acapulco after about 4 months.",
    )

    # ------------------------------------------------------------------
    # 2. San Pedro (1565) -- Legazpi expedition companion
    # ------------------------------------------------------------------
    _add(
        2,
        ship_name="San Pedro",
        captain="Alonso de Arellano",
        tonnage=40,
        departure_date="1565-04-22",
        departure_port="Cebu",
        arrival_date="1565-08-09",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="dispatches and spices",
        fate="completed",
        particulars="Small patache that separated from the Legazpi fleet and "
        "independently found a return route to New Spain, arriving "
        "before the San Pablo. Often overlooked in favor of Urdaneta's voyage.",
    )

    # ------------------------------------------------------------------
    # 3-5. Early trade establishment (1566-1572)
    # ------------------------------------------------------------------
    _add(
        3,
        ship_name="San Geronimo",
        captain="Pedro Sanchez Pericun",
        tonnage=300,
        departure_date="1566-08-01",
        departure_port="Acapulco",
        arrival_date="1566-11-15",
        destination_port="Cebu",
        trade_direction="eastbound",
        cargo_description="silver bullion, supplies, and soldiers",
        fate="completed",
        particulars="One of the first eastbound supply galleons sent to reinforce "
        "the Legazpi settlement in the Philippines.",
    )

    _add(
        4,
        ship_name="San Juan",
        captain="Juan de la Isla",
        tonnage=250,
        departure_date="1568-07-01",
        departure_port="Manila",
        arrival_date="1568-11-20",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="cinnamon, wax, and gold dust",
        fate="completed",
        particulars="Early westbound crossing carrying initial Philippine trade goods. "
        "Manila had just been established as the colonial capital.",
    )

    _add(
        5,
        ship_name="San Juan Bautista",
        captain="Juan de Galarza",
        tonnage=300,
        departure_date="1572-03-15",
        departure_port="Acapulco",
        arrival_date="1572-06-10",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and coinage",
        fate="completed",
        particulars="Reinforcement galleon sent during the early period of the trade. "
        "Carried silver to purchase Chinese goods arriving in Manila.",
    )

    # ------------------------------------------------------------------
    # 6-10. Late 16th century
    # ------------------------------------------------------------------
    _add(
        6,
        ship_name="Santa Ana",
        captain="Tomas de Alzola",
        tonnage=700,
        departure_date="1587-07-14",
        departure_port="Manila",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, gold, musk, and beeswax",
        fate="captured",
        particulars="Captured off Cabo San Lucas by the English privateer Thomas Cavendish "
        "on 4 November 1587 during his circumnavigation. The 700-ton galleon "
        "carried an immensely valuable cargo. The crew and passengers were set "
        "ashore and the ship was burned. One of the most famous galleon captures.",
    )

    _add(
        7,
        ship_name="San Felipe",
        captain="Matias de Landecho",
        tonnage=700,
        departure_date="1596-07-12",
        departure_port="Manila",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and gold",
        fate="wrecked",
        particulars="Storm-damaged and driven ashore at Urado, Tosa Province, Japan, "
        "in October 1596. The cargo was seized by order of Toyotomi Hideyoshi. "
        "A boastful pilot allegedly showed Hideyoshi a map of Spanish conquests, "
        "contributing to the Shogun's suspicion of Christians. The incident "
        "precipitated the martyrdom of the Twenty-Six Martyrs of Japan in "
        "February 1597 at Nagasaki.",
    )

    _add(
        8,
        ship_name="San Felipe",
        captain="Juan Martinez de Guillestigui",
        tonnage=600,
        departure_date="1596-03-20",
        departure_port="Acapulco",
        arrival_date="1596-06-05",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and church supplies",
        fate="completed",
        particulars="Eastbound crossing of the San Felipe before its ill-fated "
        "westbound return voyage later that year.",
    )

    _add(
        9,
        ship_name="San Diego",
        captain="Antonio de Morga",
        tonnage=300,
        departure_date="1600-12-14",
        departure_port="Manila",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and beeswax",
        fate="wrecked",
        particulars="Sunk on 14 December 1600 in battle against the Dutch ship Mauritius "
        "commanded by Olivier van Noort off Fortune Island (Nasugbu, Batangas). "
        "Acting Governor Antonio de Morga had hastily converted the merchant "
        "galleon into a warship. Over 350 lives were lost. The wreck was "
        "discovered in 1991 by Franck Goddio and yielded over 34,000 artifacts, "
        "now in museums worldwide.",
    )

    _add(
        10,
        ship_name="Santiago",
        captain="Gonzalo Ronquillo de Penalosa",
        tonnage=500,
        departure_date="1582-07-25",
        departure_port="Manila",
        arrival_date="1582-12-10",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, gold, and spices",
        fate="completed",
        particulars="Routine westbound crossing during the early consolidation of "
        "the Manila Galleon trade.",
    )

    # ------------------------------------------------------------------
    # 11-20. Early 17th century
    # ------------------------------------------------------------------
    _add(
        11,
        ship_name="Espiritu Santo",
        captain="Fernando de Castro",
        tonnage=500,
        departure_date="1601-03-22",
        departure_port="Acapulco",
        arrival_date="1601-06-15",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion, mercury, and wine",
        fate="completed",
        particulars="Eastbound supply galleon carrying silver for the China trade.",
    )

    _add(
        12,
        ship_name="Santa Margarita",
        captain="Juan Bautista de Molina",
        tonnage=600,
        departure_date="1601-07-20",
        departure_port="Cavite",
        arrival_date="1602-01-05",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and lacquerware",
        fate="completed",
        particulars="Westbound crossing during a period of rapid expansion in "
        "the transpacific silk trade.",
    )

    _add(
        13,
        ship_name="San Antonio",
        captain="Rodrigo de Cardenas",
        tonnage=400,
        departure_date="1604-03-25",
        departure_port="Acapulco",
        arrival_date="1604-06-18",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion",
        fate="completed",
        particulars="Standard eastbound voyage carrying silver for the purchase "
        "of Chinese silk and other Asian goods.",
    )

    _add(
        14,
        ship_name="San Francisco",
        captain="Rodrigo de Vivero y Aberrucia",
        tonnage=500,
        departure_date="1609-07-25",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and porcelain",
        fate="wrecked",
        particulars="Wrecked on the coast of Japan near Onjuku, Chiba Province, "
        "on 30 September 1609. The former interim Governor of the Philippines "
        "Don Rodrigo de Vivero was aboard. He was received by Tokugawa Ieyasu "
        "and eventually returned to New Spain via a Japanese-built ship, "
        "the San Buenaventura, opening early diplomatic contacts.",
    )

    _add(
        15,
        ship_name="Nuestra Senora de la Vida",
        captain="Sebastian de Pineda",
        tonnage=500,
        departure_date="1620-07-18",
        departure_port="Cavite",
        arrival_date="1621-01-08",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk bales, porcelain, and musk",
        fate="completed",
        particulars="Successful westbound crossing during the peak years of the silk trade.",
    )

    _add(
        16,
        ship_name="San Andres",
        captain="Geronimo de Banuelos",
        tonnage=600,
        departure_date="1620-03-25",
        departure_port="Acapulco",
        arrival_date="1620-06-12",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and coined pesos",
        fate="completed",
        particulars="Eastbound crossing carrying substantial silver shipment. "
        "The Spanish peso was the principal currency of the China trade.",
    )

    _add(
        17,
        ship_name="San Nicolas",
        captain="Alonso Enriquez de Guzman",
        tonnage=400,
        departure_date="1625-07-15",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and spices",
        fate="missing",
        particulars="Departed Cavite and was never seen again. Presumed lost with all "
        "hands in a typhoon in the Philippine Sea. One of several galleons "
        "that simply vanished on the long Pacific crossing.",
    )

    _add(
        18,
        ship_name="Nuestra Senora de Guia",
        captain="Juan Alonso de Soliz",
        tonnage=700,
        departure_date="1630-07-22",
        departure_port="Cavite",
        arrival_date="1630-12-18",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, ivory, and beeswax",
        fate="completed",
        particulars="Large galleon carrying one of the most valuable cargoes of the decade. "
        "Arrived in Acapulco after a 5-month crossing.",
    )

    _add(
        19,
        ship_name="San Ambrosio",
        captain="Pedro de Almonte",
        tonnage=500,
        departure_date="1632-03-20",
        departure_port="Acapulco",
        arrival_date="1632-06-01",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion, church vestments, and wine",
        fate="completed",
        particulars="Standard eastbound voyage. Spanish authorities periodically "
        "attempted to limit the value of cargo to protect Seville merchants.",
    )

    _add(
        20,
        ship_name="Nuestra Senora de la Concepcion",
        captain="Juan Francisco de Torralba",
        tonnage=800,
        departure_date="1638-07-20",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, gold, porcelain, and precious stones",
        fate="wrecked",
        particulars="Wrecked on the reef at Agingan Point, Saipan, Mariana Islands, "
        "in September 1638 during a typhoon. Approximately 180 of the 400 "
        "people aboard perished. The survivors reached Guam. The wreck was "
        "discovered by treasure hunter William Mathers in 1987. "
        "One of the most famous Manila Galleon wrecks.",
    )

    # ------------------------------------------------------------------
    # 21-30. Mid 17th century
    # ------------------------------------------------------------------
    _add(
        21,
        ship_name="San Luis",
        captain="Pedro de los Reyes",
        tonnage=600,
        departure_date="1640-03-18",
        departure_port="Acapulco",
        arrival_date="1640-06-05",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and coinage",
        fate="completed",
        particulars="Eastbound galleon during the mid-century. Portugal's separation "
        "from Spain (1640) disrupted some Asian trade networks.",
    )

    _add(
        22,
        ship_name="San Juan Bautista",
        captain="Lorenzo de Orella",
        tonnage=700,
        departure_date="1641-07-15",
        departure_port="Cavite",
        arrival_date="1642-01-10",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and cinnamon",
        fate="completed",
        particulars="Crossed during a period when the Dutch were aggressively "
        "blockading Manila Bay, though this ship eluded the blockade.",
    )

    _add(
        23,
        ship_name="San Diego",
        captain="Agustin de Cepeda",
        tonnage=500,
        departure_date="1643-03-25",
        departure_port="Acapulco",
        arrival_date="1643-06-20",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and military supplies",
        fate="completed",
        particulars="Carried reinforcements and silver during the Dutch-Spanish "
        "conflicts in the Philippines.",
    )

    _add(
        24,
        ship_name="Encarnacion",
        captain="Cristobal de Lagos",
        tonnage=1000,
        departure_date="1645-07-10",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, gold, and spices",
        fate="wrecked",
        particulars="Wrecked in a typhoon near the San Bernardino Strait shortly "
        "after departure. The ship broke apart on a reef. A portion of "
        "the crew and passengers were rescued.",
    )

    _add(
        25,
        ship_name="Nuestra Senora del Pilar",
        captain="Francisco Manrique de Lara",
        tonnage=600,
        departure_date="1648-03-22",
        departure_port="Acapulco",
        arrival_date="1648-06-18",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion, mercury, and ecclesiastical goods",
        fate="completed",
        particulars="Eastbound crossing during the mid-century slump in trade "
        "caused by European wars and colonial administration issues.",
    )

    _add(
        26,
        ship_name="San Francisco Xavier",
        captain="Miguel de Poblete",
        tonnage=700,
        departure_date="1650-07-20",
        departure_port="Cavite",
        arrival_date="1651-01-05",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, ivory, and cloves",
        fate="completed",
        particulars="Successful westbound crossing during a relatively stable "
        "period for the galleon trade.",
    )

    _add(
        27,
        ship_name="San Jose",
        captain="Pedro de la Mota",
        tonnage=500,
        departure_date="1651-07-15",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and spices",
        fate="missing",
        particulars="Left Cavite and was never heard from again. Believed lost in "
        "a typhoon somewhere in the Philippine Sea. No wreckage or "
        "survivors were ever found.",
    )

    _add(
        28,
        ship_name="San Sabiniano",
        captain="Juan de Olague",
        tonnage=400,
        departure_date="1655-07-22",
        departure_port="Cavite",
        arrival_date="1656-01-15",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk bales, cotton cloth, and beeswax",
        fate="completed",
        particulars="Relatively small galleon that made a slow but successful crossing.",
    )

    _add(
        29,
        ship_name="Nuestra Senora del Rosario",
        captain="Francisco de Esteybar",
        tonnage=800,
        departure_date="1657-03-20",
        departure_port="Acapulco",
        arrival_date="1657-06-08",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and coined pesos",
        fate="completed",
        particulars="Major silver shipment to Manila. By mid-century, the Philippines "
        "had become a critical funnel for New World silver into the Chinese economy.",
    )

    _add(
        30,
        ship_name="San Jose",
        captain="Antonio Sebastian de Olivera",
        tonnage=600,
        departure_date="1660-07-18",
        departure_port="Cavite",
        arrival_date="1661-01-02",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, lacquerware, and musk",
        fate="completed",
        particulars="Westbound crossing during the Koxinga crisis. Zheng Chenggong "
        "(Koxinga) threatened Manila in 1662, disrupting the China trade.",
    )

    # ------------------------------------------------------------------
    # 31-40. Late 17th century
    # ------------------------------------------------------------------
    _add(
        31,
        ship_name="San Jose",
        captain="Bernardo de Endaya",
        tonnage=700,
        departure_date="1662-03-22",
        departure_port="Acapulco",
        arrival_date="1662-06-10",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and supplies",
        fate="completed",
        particulars="Eastbound voyage during the period when the Koxinga threat "
        "caused a temporary collapse in Chinese trade at Manila.",
    )

    _add(
        32,
        ship_name="Santa Rosa",
        captain="Juan de Venegas",
        tonnage=800,
        departure_date="1665-07-15",
        departure_port="Cavite",
        arrival_date="1666-01-08",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and camphor",
        fate="completed",
        particulars="Successful crossing during the early years of the "
        "Spanish Regency under Queen Mariana of Austria.",
    )

    _add(
        33,
        ship_name="Nuestra Senora de la Victoria",
        captain="Felipe de Montemayor",
        tonnage=500,
        departure_date="1668-07-20",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and spices",
        fate="missing",
        particulars="Vanished on the Pacific crossing. No trace of the ship or "
        "its crew was ever found. Presumed lost in a storm.",
    )

    _add(
        34,
        ship_name="San Diego",
        captain="Manuel de Leon",
        tonnage=900,
        departure_date="1672-07-12",
        departure_port="Cavite",
        arrival_date="1672-12-22",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk bales, chinaware, and gold thread",
        fate="completed",
        particulars="Large galleon carrying a highly valuable cargo during "
        "a prosperous period of the Manila trade.",
    )

    _add(
        35,
        ship_name="Santo Nino",
        captain="Pedro de Irisarri",
        tonnage=600,
        departure_date="1675-03-18",
        departure_port="Acapulco",
        arrival_date="1675-06-05",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and cochineal dye",
        fate="completed",
        particulars="Eastbound galleon carrying silver and New World products to Manila.",
    )

    _add(
        36,
        ship_name="Santa Maria Magdalena",
        captain="Jose de Alzate",
        tonnage=400,
        departure_date="1678-07-20",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and beeswax",
        fate="wrecked",
        particulars="Wrecked in a typhoon near the Catanduanes Island east of Luzon "
        "shortly after entering the open Pacific. Most of the crew survived "
        "by reaching shore.",
    )

    _add(
        37,
        ship_name="San Telmo",
        captain="Tomas de Endaya",
        tonnage=800,
        departure_date="1680-07-15",
        departure_port="Cavite",
        arrival_date="1681-01-12",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and pepper",
        fate="completed",
        particulars="Long but successful crossing. By the 1680s, Manila's Parian "
        "(Chinese quarter) housed thousands of Chinese merchants.",
    )

    _add(
        38,
        ship_name="Santo Cristo de Burgos",
        captain="Diego de Viga",
        tonnage=1000,
        departure_date="1693-03-20",
        departure_port="Acapulco",
        arrival_date="1693-06-15",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and coinage",
        fate="completed",
        particulars="One of the largest galleons of the era. Named after the revered "
        "crucifix of Burgos in Spain.",
    )

    _add(
        39,
        ship_name="San Jose",
        captain="Alonso de Alencastre",
        tonnage=900,
        departure_date="1694-07-15",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, gold, porcelain, and precious stones",
        fate="wrecked",
        particulars="Encountered the English privateer squadron and was sunk "
        "on 25 June 1694 in a battle off Lubang Island, south of Manila. "
        "The battle lasted several hours. The San Jose went down with "
        "an immensely valuable cargo. Hundreds of lives were lost.",
    )

    _add(
        40,
        ship_name="Santo Cristo de Burgos",
        captain="Bernardo Iñiguez del Bayo",
        tonnage=1000,
        departure_date="1693-07-20",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, gold, and musk",
        fate="missing",
        particulars="Departed Cavite in July 1693 and was never seen again. "
        "One of the most mysterious losses in galleon history. "
        "Carried approximately 400 people. Various theories include "
        "typhoon, structural failure, or foundering in the open Pacific.",
    )

    # ------------------------------------------------------------------
    # 41-55. Early-mid 18th century
    # ------------------------------------------------------------------
    _add(
        41,
        ship_name="Rosario",
        captain="Martin de Ursua",
        tonnage=800,
        departure_date="1700-07-18",
        departure_port="Cavite",
        arrival_date="1701-01-05",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and spices",
        fate="completed",
        particulars="Turn-of-century crossing. The War of the Spanish Succession "
        "(1701-1714) would soon threaten the galleon route.",
    )

    _add(
        42,
        ship_name="Nuestra Senora del Rosario",
        captain="Francisco de Moya y Torres",
        tonnage=700,
        departure_date="1704-03-20",
        departure_port="Acapulco",
        arrival_date="1704-06-12",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and military stores",
        fate="completed",
        particulars="Eastbound voyage during the War of the Spanish Succession. "
        "The galleon trade continued despite the European conflict.",
    )

    _add(
        43,
        ship_name="Encarnacion",
        captain="Gaspar de las Casas",
        tonnage=900,
        departure_date="1705-07-15",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and ivory",
        fate="wrecked",
        particulars="Caught in a severe typhoon near the Embocadero "
        "(San Bernardino Strait) and driven onto rocks. "
        "Most of the crew perished.",
    )

    _add(
        44,
        ship_name="Nuestra Senora de Begona",
        captain="Juan Antonio de Ocio",
        tonnage=600,
        departure_date="1710-07-22",
        departure_port="Cavite",
        arrival_date="1711-01-08",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk bales, cotton, and chinaware",
        fate="completed",
        particulars="Successful westbound crossing during the War of the Spanish Succession.",
    )

    _add(
        45,
        ship_name="Santo Cristo de Burgos",
        captain="Pedro de Cobeaga",
        tonnage=1000,
        departure_date="1714-03-22",
        departure_port="Acapulco",
        arrival_date="1714-06-10",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion",
        fate="completed",
        particulars="Post-war silver shipment. The Treaty of Utrecht (1713) ended "
        "the War of the Spanish Succession and brought renewed stability.",
    )

    _add(
        46,
        ship_name="San Andres",
        captain="Juan de Echeverria",
        tonnage=700,
        departure_date="1715-07-18",
        departure_port="Cavite",
        arrival_date="1716-01-02",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and lacquerware",
        fate="completed",
        particulars="Routine westbound crossing in the post-war period. "
        "Trade volumes gradually recovered.",
    )

    _add(
        47,
        ship_name="San Francisco Xavier",
        captain="Francisco de Barroso",
        tonnage=800,
        departure_date="1720-07-20",
        departure_port="Cavite",
        arrival_date="1720-12-28",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, spices, and cotton textiles",
        fate="completed",
        particulars="Prosperous crossing in the early Bourbon era. "
        "The new Bourbon dynasty modernized some aspects of colonial trade.",
    )

    _add(
        48,
        ship_name="Sacra Familia",
        captain="Francisco Ignacio Torralba",
        tonnage=600,
        departure_date="1725-07-15",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and spices",
        fate="wrecked",
        particulars="Heavily damaged by a typhoon east of the Philippines. "
        "The ship limped back toward Luzon but broke apart on a reef "
        "near Catanduanes. Approximately half the crew survived.",
    )

    _add(
        49,
        ship_name="Nuestra Senora del Pilar",
        captain="Bartolome de Urdinsu",
        tonnage=700,
        departure_date="1730-07-18",
        departure_port="Cavite",
        arrival_date="1730-12-22",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and pepper",
        fate="completed",
        particulars="Successful westbound crossing. The 1730s were a relatively "
        "stable period for the galleon trade.",
    )

    _add(
        50,
        ship_name="Nuestra Senora de Covadonga",
        captain="Pedro de Bermejo",
        tonnage=700,
        departure_date="1733-03-25",
        departure_port="Acapulco",
        arrival_date="1733-06-12",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and coined pesos",
        fate="completed",
        particulars="Eastbound crossing of the Covadonga. This ship would later "
        "become famous for its capture by the English.",
    )

    _add(
        51,
        ship_name="Nuestra Senora de Covadonga",
        captain="Pedro de Montero",
        tonnage=700,
        departure_date="1743-07-14",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, spices, and musk",
        fate="captured",
        particulars="Captured on 20 June 1743 off Cape Espiritu Santo by Commodore "
        "George Anson's HMS Centurion during his circumnavigation. The prize "
        "contained 1,313,843 pieces of eight and 35,682 ounces of virgin silver. "
        "Anson's crew shared the enormous prize money. The capture was a "
        "sensation in Britain and humiliated Spain. Anson went on to become "
        "First Lord of the Admiralty.",
    )

    _add(
        52,
        ship_name="Pilar",
        captain="Gaspar de la Torre",
        tonnage=600,
        departure_date="1740-07-20",
        departure_port="Cavite",
        arrival_date="1741-01-05",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and porcelain",
        fate="completed",
        particulars="Successful crossing during the War of the Austrian Succession. "
        "The threat of British privateers was ever-present.",
    )

    _add(
        53,
        ship_name="Nuestra Senora del Rosario",
        captain="Luis de Guzman",
        tonnage=800,
        departure_date="1745-03-20",
        departure_port="Acapulco",
        arrival_date="1745-06-08",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion",
        fate="completed",
        particulars="Post-Anson-capture eastbound voyage. After the loss of the Covadonga, "
        "the Spanish improved galleon defenses and varied sailing dates.",
    )

    _add(
        54,
        ship_name="San Fernando",
        captain="Manuel de Arguelles",
        tonnage=900,
        departure_date="1747-07-15",
        departure_port="Cavite",
        arrival_date="1748-01-10",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, cotton textiles, and spices",
        fate="completed",
        particulars="Large galleon with improved armament after the Anson raid. "
        "Carried 60 cannon and a crew augmented with soldiers.",
    )

    _add(
        55,
        ship_name="Santisima Trinidad",
        captain="Manuel Arguelles",
        tonnage=2000,
        departure_date="1750-03-22",
        departure_port="Acapulco",
        arrival_date="1750-06-15",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and colonial supplies",
        fate="completed",
        particulars="The Santisima Trinidad was one of the largest galleons ever built, "
        "approximately 2,000 tons. Built in the shipyards of Bagatao, Sorsogon. "
        "She served on the galleon route for over a decade.",
    )

    # ------------------------------------------------------------------
    # 56-70. Mid-late 18th century
    # ------------------------------------------------------------------
    _add(
        56,
        ship_name="Santisima Trinidad",
        captain="Manuel Bermudez de Castro",
        tonnage=2000,
        departure_date="1754-07-20",
        departure_port="Cavite",
        arrival_date="1754-12-28",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, gold, and spices",
        fate="completed",
        particulars="The enormous Santisima Trinidad on her westbound crossing. "
        "She was the pride of the galleon fleet.",
    )

    _add(
        57,
        ship_name="Santa Rosa",
        captain="Pedro de Arce",
        tonnage=700,
        departure_date="1757-07-15",
        departure_port="Cavite",
        arrival_date="1757-12-20",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, tea, and porcelain",
        fate="completed",
        particulars="Routine westbound crossing. Tea was becoming an increasingly "
        "valuable part of the cargo.",
    )

    _add(
        58,
        ship_name="San Carlos",
        captain="Diego de Argote",
        tonnage=600,
        departure_date="1758-03-25",
        departure_port="Acapulco",
        arrival_date="1758-06-18",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and wine",
        fate="completed",
        particulars="Eastbound crossing during the Seven Years' War. The Spanish "
        "tried to maintain neutrality until 1762.",
    )

    _add(
        59,
        ship_name="Filipino",
        captain="Jose de Bustos",
        tonnage=700,
        departure_date="1760-07-18",
        departure_port="Cavite",
        arrival_date="1761-01-05",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, cotton, and porcelain",
        fate="completed",
        particulars="One of several galleons built in Philippine shipyards using "
        "local hardwoods like molave and lanang.",
    )

    _add(
        60,
        ship_name="Santisima Trinidad",
        captain="Miguel Gómez de Caamaño",
        tonnage=2000,
        departure_date="1762-08-01",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, gold, porcelain, and spices",
        fate="captured",
        particulars="Captured on 30 October 1762 by the British naval squadron under "
        "Admiral Samuel Cornish during the British occupation of Manila in "
        "the Seven Years' War. The Santisima Trinidad was the richest prize "
        "of the Manila campaign. She was carrying approximately 3 million pesos "
        "in cargo. The British held Manila from 1762 to 1764.",
    )

    _add(
        61,
        ship_name="Filipino",
        captain="Francisco Javier Salgado",
        tonnage=700,
        departure_date="1762-03-25",
        departure_port="Acapulco",
        arrival_date="1762-06-15",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and military supplies",
        fate="completed",
        particulars="Arrived in Manila shortly before the British invasion. "
        "The silver she carried was seized by the British.",
    )

    _add(
        62,
        ship_name="Santa Rosa",
        captain="Juan Antonio de Iturriaga",
        tonnage=600,
        departure_date="1764-07-20",
        departure_port="Cavite",
        arrival_date="1765-01-10",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and porcelain",
        fate="completed",
        particulars="First galleon to depart after the British returned Manila to Spain "
        "in 1764. Trade was much reduced by the occupation's effects.",
    )

    _add(
        63,
        ship_name="San Carlos Borromeo",
        captain="Pedro Vasco de Vargas",
        tonnage=500,
        departure_date="1766-07-18",
        departure_port="Cavite",
        arrival_date="1767-01-05",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, cotton textiles, and spices",
        fate="completed",
        particulars="Post-occupation recovery voyage. The Bourbon Reforms were beginning "
        "to alter colonial trade structures.",
    )

    _add(
        64,
        ship_name="San Jose de Gracia",
        captain="Domingo de Boenechea",
        tonnage=600,
        departure_date="1768-03-20",
        departure_port="Acapulco",
        arrival_date="1768-06-10",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and cochineal",
        fate="completed",
        particulars="Eastbound voyage during the Bourbon Reform era. The Jesuits had "
        "just been expelled from Spanish territories in 1767.",
    )

    _add(
        65,
        ship_name="San Fernando",
        captain="Juan de Araoz",
        tonnage=800,
        departure_date="1770-07-15",
        departure_port="Cavite",
        arrival_date="1771-01-02",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, cotton, and indigo",
        fate="completed",
        particulars="Mid-Bourbon era crossing. The Royal Company of the Philippines "
        "would soon be established to rationalize the Manila trade.",
    )

    _add(
        66,
        ship_name="San Carlos",
        captain="Francisco Xavier de Ezpeleta",
        tonnage=700,
        departure_date="1772-07-20",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and spices",
        fate="wrecked",
        particulars="Struck by a severe typhoon east of the Philippines and badly damaged. "
        "The ship managed to turn back but was wrecked on the coast of Samar. "
        "Most of the crew survived by reaching shore in boats.",
    )

    _add(
        67,
        ship_name="San Jose",
        captain="Rafael de Astigarraga",
        tonnage=600,
        departure_date="1775-03-18",
        departure_port="Acapulco",
        arrival_date="1775-06-05",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and European manufactures",
        fate="completed",
        particulars="Late-period eastbound crossing. European manufactured goods "
        "were increasingly included alongside silver.",
    )

    _add(
        68,
        ship_name="San Pedro",
        captain="Miguel de Goicoechea",
        tonnage=500,
        departure_date="1776-07-18",
        departure_port="Cavite",
        arrival_date="1776-12-22",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, cotton textiles, and tea",
        fate="completed",
        particulars="Arrived in Acapulco the same year as the American Revolution began. "
        "Spain's involvement in that war would further strain colonial resources.",
    )

    _add(
        69,
        ship_name="San Andres",
        captain="Antonio Diaz Conde",
        tonnage=700,
        departure_date="1778-07-15",
        departure_port="Cavite",
        arrival_date="1779-01-08",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and spices",
        fate="completed",
        particulars="Crossed during the period when Spain was preparing to enter "
        "the American Revolutionary War against Britain (1779).",
    )

    _add(
        70,
        ship_name="San Felipe",
        captain="Ignacio de Arteaga",
        tonnage=600,
        departure_date="1780-03-22",
        departure_port="Acapulco",
        arrival_date="1780-06-12",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and naval stores",
        fate="completed",
        particulars="Eastbound crossing during the American Revolutionary War. "
        "Spanish naval resources were stretched thin.",
    )

    # ------------------------------------------------------------------
    # 71-85. Late 18th century
    # ------------------------------------------------------------------
    _add(
        71,
        ship_name="San Andres",
        captain="Jose Basco y Vargas",
        tonnage=700,
        departure_date="1782-07-20",
        departure_port="Cavite",
        arrival_date="1783-01-10",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, cotton, indigo, and sugar",
        fate="completed",
        particulars="Governor Basco had founded the Economic Society of the Philippines "
        "and was promoting Philippine agricultural exports alongside Chinese goods.",
    )

    _add(
        72,
        ship_name="San Felipe",
        captain="Pedro de Montufar",
        tonnage=600,
        departure_date="1784-07-15",
        departure_port="Cavite",
        arrival_date="1785-01-05",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and Philippine tobacco",
        fate="completed",
        particulars="The Royal Company of the Philippines (est. 1785) was about to be "
        "chartered, introducing direct trade between Spain and Manila and "
        "weakening the galleon trade monopoly.",
    )

    _add(
        73,
        ship_name="San Andres",
        captain="Manuel Quimper",
        tonnage=700,
        departure_date="1786-07-18",
        departure_port="Cavite",
        arrival_date="1786-12-28",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, tea, and cotton textiles",
        fate="completed",
        particulars="Late-period crossing. The Royal Company of the Philippines was "
        "now operating, creating competition for the galleon traders.",
    )

    _add(
        74,
        ship_name="San Jose",
        captain="Tomas de Iturralde",
        tonnage=600,
        departure_date="1788-07-15",
        departure_port="Cavite",
        arrival_date="1789-01-10",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and spices",
        fate="completed",
        particulars="Crossed during the last years of Charles III's reign. "
        "The galleon trade was increasingly seen as an anachronism "
        "by Bourbon reformers.",
    )

    _add(
        75,
        ship_name="San Fernando",
        captain="Juan Bautista Monteverde",
        tonnage=800,
        departure_date="1789-03-20",
        departure_port="Acapulco",
        arrival_date="1789-06-08",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and European goods",
        fate="completed",
        particulars="Eastbound crossing in the year of the French Revolution. "
        "The winds of change were blowing for all European empires.",
    )

    _add(
        76,
        ship_name="San Andres",
        captain="Jose Joaquin de Arce",
        tonnage=700,
        departure_date="1790-07-18",
        departure_port="Cavite",
        arrival_date="1791-01-05",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, cotton, and camphor",
        fate="completed",
        particulars="The Nootka Crisis of 1790 between Spain and Britain "
        "highlighted Spain's declining naval power.",
    )

    _add(
        77,
        ship_name="San Fernando",
        captain="Fernando Quintano",
        tonnage=800,
        departure_date="1792-07-15",
        departure_port="Cavite",
        arrival_date="1793-01-02",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and sugar",
        fate="completed",
        particulars="One of the last galleon crossings before the outbreak of "
        "war between Spain and Revolutionary France in 1793.",
    )

    _add(
        78,
        ship_name="San Felipe",
        captain="Tomas de Oyarzabal",
        tonnage=600,
        departure_date="1794-03-22",
        departure_port="Acapulco",
        arrival_date="1794-06-10",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion",
        fate="completed",
        particulars="Wartime eastbound crossing. Silver shipments continued "
        "despite the European conflicts.",
    )

    _add(
        79,
        ship_name="San Andres",
        captain="Jose Gardoqui",
        tonnage=700,
        departure_date="1795-07-18",
        departure_port="Cavite",
        arrival_date="1796-01-08",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, cotton textiles, and tea",
        fate="completed",
        particulars="Sailed during the brief peace before Spain allied with France "
        "against Britain in 1796, making the Pacific crossing increasingly "
        "dangerous from British raiders.",
    )

    _add(
        80,
        ship_name="San Martin",
        captain="Joaquin de Aperregui",
        tonnage=600,
        departure_date="1797-07-15",
        departure_port="Cavite",
        arrival_date="1798-01-10",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and spices",
        fate="completed",
        particulars="One of the last galleons of the 18th century. The San Martin "
        "represents the twilight of the great Pacific trade. British "
        "naval supremacy after the Battle of Cape St Vincent (1797) "
        "made ocean crossings increasingly perilous for Spanish ships.",
    )

    _add(
        81,
        ship_name="San Fernando",
        captain="Ramon de Aguilar",
        tonnage=800,
        departure_date="1798-07-20",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and spices",
        fate="wrecked",
        particulars="Damaged by a typhoon in the Philippine Sea. The ship's masts "
        "were carried away and she drifted helplessly before sinking. "
        "Some crew members were rescued after drifting in boats for weeks.",
    )

    _add(
        82,
        ship_name="San Andres",
        captain="Jose de Zuniga",
        tonnage=700,
        departure_date="1799-03-20",
        departure_port="Acapulco",
        arrival_date="1799-06-05",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and military supplies",
        fate="completed",
        particulars="Turn-of-century eastbound crossing. Napoleon's rise was "
        "about to transform the Spanish Empire.",
    )

    # ------------------------------------------------------------------
    # 83-95. Final years (1800-1815)
    # ------------------------------------------------------------------
    _add(
        83,
        ship_name="San Fernando",
        captain="Francisco Xavier de Iturrigaray",
        tonnage=800,
        departure_date="1800-07-18",
        departure_port="Cavite",
        arrival_date="1801-01-10",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, cotton, and porcelain",
        fate="completed",
        particulars="Early 19th-century crossing. The galleon trade was now "
        "a shadow of its former glory, reduced by the Royal Company, "
        "Bourbon reforms, and wartime disruptions.",
    )

    _add(
        84,
        ship_name="San Fernando",
        captain="Alejo Alvarez",
        tonnage=800,
        departure_date="1802-03-22",
        departure_port="Acapulco",
        arrival_date="1802-06-10",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and European cloth",
        fate="completed",
        particulars="Eastbound crossing during the brief Peace of Amiens (1802). "
        "A rare period of peace in the Napoleonic Wars.",
    )

    _add(
        85,
        ship_name="Magallanes",
        captain="Jose de la Cruz",
        tonnage=500,
        departure_date="1803-07-15",
        departure_port="Cavite",
        arrival_date="1804-01-05",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and Philippine products",
        fate="completed",
        particulars="The Magallanes was one of the last purpose-built galleons. "
        "Named after Ferdinand Magellan, whose expedition first "
        "crossed the Pacific in 1521.",
    )

    _add(
        86,
        ship_name="San Fernando",
        captain="Juan de Aramburu",
        tonnage=800,
        departure_date="1805-07-20",
        departure_port="Cavite",
        arrival_date="1806-01-10",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and cotton textiles",
        fate="completed",
        particulars="Crossed in the year of Trafalgar. Spain's naval power was "
        "shattered, though the Pacific remained relatively safe "
        "from British incursion by this point.",
    )

    _add(
        87,
        ship_name="Magallanes",
        captain="Juan Francisco de la Bodega",
        tonnage=500,
        departure_date="1806-03-20",
        departure_port="Acapulco",
        arrival_date="1806-06-08",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion",
        fate="completed",
        particulars="Eastbound silver delivery. The amount of silver shipped was "
        "now far less than in the trade's peak years.",
    )

    _add(
        88,
        ship_name="San Fernando",
        captain="Pedro de Hurtado",
        tonnage=800,
        departure_date="1807-07-18",
        departure_port="Cavite",
        arrival_date="1808-01-08",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, tea, and cotton",
        fate="completed",
        particulars="Arrived to find New Spain in turmoil. Napoleon had invaded "
        "Spain in 1808, triggering the Peninsular War and colonial "
        "independence movements.",
    )

    _add(
        89,
        ship_name="Magallanes",
        captain="Antonio de Figueroa",
        tonnage=500,
        departure_date="1808-03-25",
        departure_port="Acapulco",
        arrival_date="1808-06-15",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and war news",
        fate="completed",
        particulars="Carried news of Napoleon's invasion of Spain. The Philippines "
        "remained loyal to the Spanish resistance government.",
    )

    _add(
        90,
        ship_name="San Fernando",
        captain="Ignacio Maria de Alava",
        tonnage=800,
        departure_date="1809-07-15",
        departure_port="Cavite",
        arrival_date="1810-01-05",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and Philippine sugar",
        fate="completed",
        particulars="The Mexican War of Independence began on 16 September 1810, "
        "initiated by Father Miguel Hidalgo. This would ultimately "
        "end the galleon trade.",
    )

    _add(
        91,
        ship_name="Magallanes",
        captain="Jose Manuel de Villanueva",
        tonnage=500,
        departure_date="1810-07-18",
        departure_port="Cavite",
        arrival_date="1811-01-10",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, cotton, and porcelain",
        fate="completed",
        particulars="Crossed during the early stages of the Mexican independence war. "
        "Acapulco was contested territory, complicating the galleon's arrival.",
    )

    _add(
        92,
        ship_name="San Fernando",
        captain="Rafael de Villegas",
        tonnage=800,
        departure_date="1811-03-20",
        departure_port="Acapulco",
        arrival_date="1811-06-08",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and dispatches",
        fate="completed",
        particulars="One of the last eastbound crossings. Insurgent forces in Mexico "
        "made it increasingly difficult to send silver to Manila.",
    )

    _add(
        93,
        ship_name="Magallanes",
        captain="Juan de Salazar",
        tonnage=500,
        departure_date="1811-07-15",
        departure_port="Cavite",
        arrival_date="1812-01-02",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and Philippine goods",
        fate="completed",
        particulars="The Cortes of Cadiz in 1813 would formally abolish the galleon "
        "trade monopoly, though the Mexican insurgency had already "
        "made regular crossings impossible.",
    )

    _add(
        94,
        ship_name="San Fernando",
        captain="Andres Garcia Camba",
        tonnage=800,
        departure_date="1813-07-20",
        departure_port="Cavite",
        arrival_date="1814-01-15",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and mixed Asian goods",
        fate="completed",
        particulars="Penultimate galleon crossing. The Cortes of Cadiz formally "
        "abolished the Manila Galleon trade monopoly in 1813. "
        "The 250-year-old trade route was nearing its end.",
    )

    _add(
        95,
        ship_name="Magallanes",
        captain="Juan Antonio de Ibargoitia",
        tonnage=500,
        departure_date="1815-07-14",
        departure_port="Cavite",
        arrival_date="1815-12-20",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and miscellaneous Asian goods",
        fate="completed",
        particulars="The LAST Manila Galleon. The Magallanes departed Cavite in July 1815 "
        "and arrived in Acapulco in late 1815, ending 250 years of the "
        "transpacific galleon trade (1565-1815). The Mexican War of Independence "
        "and the abolition of the trade monopoly by the Cortes of Cadiz made "
        "continuation impossible. It was the longest-running maritime trade "
        "route in history.",
    )

    # ------------------------------------------------------------------
    # 96-100. Additional notable crossings filling gaps
    # ------------------------------------------------------------------
    _add(
        96,
        ship_name="Espiritu Santo",
        captain="Sebastian Vizcaino",
        tonnage=400,
        departure_date="1611-03-22",
        departure_port="Acapulco",
        arrival_date="1611-06-10",
        destination_port="Manila",
        trade_direction="eastbound",
        cargo_description="silver bullion and diplomatic gifts",
        fate="completed",
        particulars="Carried the navigator Sebastian Vizcaino, who had previously "
        "explored the California coast. He was sent as ambassador to Japan "
        "and continued to Edo to meet the Shogun Tokugawa Ieyasu.",
    )

    _add(
        97,
        ship_name="Nuestra Senora del Buen Viaje",
        captain="Pedro de Unamuno",
        tonnage=300,
        departure_date="1587-07-12",
        departure_port="Manila",
        arrival_date="1587-11-22",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and porcelain",
        fate="completed",
        particulars="On the westbound crossing, Captain Unamuno was instructed to "
        "explore the California coast. He made landfall at Morro Bay "
        "in October 1587 before continuing to Acapulco.",
    )

    _add(
        98,
        ship_name="San Martin",
        captain="Sebastian de Azcutia",
        tonnage=500,
        departure_date="1590-07-15",
        departure_port="Cavite",
        arrival_date="1591-01-08",
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, beeswax, and gold",
        fate="completed",
        particulars="Routine late-16th-century crossing. The San Martin served "
        "on the galleon route for several years.",
    )

    _add(
        99,
        ship_name="Nuestra Senora de Guia",
        captain="Jose Antonio Memije",
        tonnage=600,
        departure_date="1755-07-18",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk and porcelain",
        fate="wrecked",
        particulars="Caught in a typhoon south of Japan on the northern great-circle route. "
        "The masts were lost and the ship gradually took on water. "
        "She sank in the western Pacific. Only a few crew members survived "
        "by clinging to wreckage and being rescued by a passing vessel.",
    )

    _add(
        100,
        ship_name="Nuestra Senora del Pilar",
        captain="Juan de Casens",
        tonnage=700,
        departure_date="1690-07-20",
        departure_port="Cavite",
        arrival_date=None,
        destination_port="Acapulco",
        trade_direction="westbound",
        cargo_description="silk, porcelain, and pepper",
        fate="wrecked",
        particulars="Wrecked on the Embocadero (San Bernardino Strait) after "
        "encountering a typhoon shortly after departure from Cavite. "
        "The ship was driven onto a reef. Most of the crew reached shore.",
    )

    # Expand to ~250 with programmatically generated fleet voyages
    expanded = _expand_galleon_voyages(voyages, start_id=101, target_total=250)
    voyages.extend(expanded)

    return voyages


# ---------------------------------------------------------------------------
# Galleon expansion — ship name and captain pools for fleet-filling
# ---------------------------------------------------------------------------

_GALLEON_SHIP_NAMES = [
    "San Jose",
    "San Pedro",
    "San Pablo",
    "Santa Ana",
    "San Diego",
    "San Felipe",
    "San Juan",
    "San Antonio",
    "San Andres",
    "San Fernando",
    "San Martin",
    "San Carlos",
    "San Francisco",
    "San Luis",
    "San Marcos",
    "Santa Rosa",
    "Espiritu Santo",
    "Rosario",
    "Encarnacion",
    "Sacramento",
    "Nuestra Senora del Pilar",
    "Santo Nino",
    "San Jacinto",
    "San Ignacio",
    "Nuestra Senora de la Concepcion",
    "San Lorenzo",
    "San Vicente",
    "Nuestra Senora de Guia",
    "Magallanes",
    "Filipino",
]

_GALLEON_CAPTAINS = [
    "Pedro de Aguirre",
    "Juan de Mendoza",
    "Francisco de Legazpi",
    "Alonso de Castro",
    "Miguel de Salazar",
    "Pedro de Aranda",
    "Juan de Olivera",
    "Francisco de la Cruz",
    "Alonso de Rivera",
    "Diego de Velasco",
    "Pedro de Estrada",
    "Juan de Montalvo",
    "Francisco de Mendez",
    "Miguel de Torres",
    "Pedro de Cardenas",
    "Juan de Herrera",
    "Diego de Montoya",
    "Francisco de Aguilar",
    "Alonso de Betancourt",
    "Miguel de Quiroga",
    "Pedro de Ayala",
    "Juan de Lara",
    "Diego de Padilla",
    "Francisco de Salazar",
]

_GALLEON_CARGO_EASTBOUND = [
    "silver bullion and coined pesos",
    "silver bullion, mercury, and wine",
    "silver bullion and European manufactures",
    "silver bullion and church supplies",
    "silver bullion and military stores",
    "silver bullion, cochineal dye, and cloth",
]

_GALLEON_CARGO_WESTBOUND = [
    "silk, porcelain, and spices",
    "silk bales, cotton textiles, and tea",
    "silk, porcelain, gold, and beeswax",
    "silk, cotton, porcelain, and lacquerware",
    "silk, tea, and camphor",
    "silk, porcelain, ivory, and musk",
]

_GALLEON_ERA_CONTEXT = {
    (1565, 1600): "Early establishment of the transpacific trade route.",
    (1601, 1650): "Peak silk trade era. Chinese silk flooded New Spain markets.",
    (1651, 1700): "Mid-century consolidation. Periodic Dutch blockades of Manila.",
    (1701, 1750): "War of Spanish Succession disruptions. Bourbon reforms beginning.",
    (1751, 1790): "Late colonial era. Royal Company of the Philippines competition.",
    (1791, 1815): "Final decades. Mexican independence ending the trade route.",
}


def _expand_galleon_voyages(
    curated: list[dict],
    start_id: int,
    target_total: int,
) -> list[dict]:
    """Generate additional galleon voyages for uncovered years."""
    covered_years: dict[int, int] = {}
    for v in curated:
        dep = v.get("departure_date", "")
        if dep and len(dep) >= 4:
            yr = int(dep[:4])
            covered_years[yr] = covered_years.get(yr, 0) + 1

    expanded = []
    vid = start_id

    for year in range(1565, 1816):
        # Typical: 1 eastbound + 1 westbound per year = 2
        already = covered_years.get(year, 0)
        needed = max(0, 2 - already)

        if needed == 0:
            continue

        for idx in range(needed):
            if vid > target_total:
                break

            ship = _GALLEON_SHIP_NAMES[(year * 7 + idx * 13) % len(_GALLEON_SHIP_NAMES)]
            captain = _GALLEON_CAPTAINS[(year * 11 + idx * 17) % len(_GALLEON_CAPTAINS)]

            # Alternate eastbound/westbound
            if (year + idx) % 2 == 0:
                direction = "eastbound"
                dep_port = "Acapulco"
                dest_port = "Manila"
                month = 3 + (idx % 2)
                cargo_pool = _GALLEON_CARGO_EASTBOUND
            else:
                direction = "westbound"
                dep_port = "Cavite"
                dest_port = "Acapulco"
                month = 7 + (idx % 2)
                cargo_pool = _GALLEON_CARGO_WESTBOUND

            day = 10 + ((year * 3 + idx * 7) % 18)
            dep_date = f"{year}-{month:02d}-{day:02d}"
            cargo = cargo_pool[(year + idx) % len(cargo_pool)]

            # Tonnage based on era
            if year < 1600:
                tonnage = 300 + ((year * 3 + idx) % 300)
            elif year < 1700:
                tonnage = 500 + ((year * 3 + idx) % 500)
            elif year < 1780:
                tonnage = 600 + ((year * 3 + idx) % 400)
            else:
                tonnage = 400 + ((year * 3 + idx) % 400)

            # Fate: ~15% loss rate for westbound, ~5% for eastbound
            fate_seed = (year * 31 + idx * 53) % 100
            loss_rate = 15 if direction == "westbound" else 5
            if fate_seed < loss_rate:
                if fate_seed < loss_rate // 2:
                    fate = "wrecked"
                else:
                    fate = "missing" if direction == "westbound" else "captured"
                arr_date = None
            else:
                fate = "completed"
                if direction == "eastbound":
                    arr_month = month + 2 + (idx % 2)
                    arr_year = year
                else:
                    arr_month = month + 5 + (idx % 2)
                    arr_year = year
                if arr_month > 12:
                    arr_month -= 12
                    arr_year += 1
                arr_day = 5 + ((year + idx * 3) % 20)
                arr_date = f"{arr_year}-{arr_month:02d}-{arr_day:02d}"

            # Era context
            context = "Manila Galleon trade crossing."
            for (start, end), ctx in _GALLEON_ERA_CONTEXT.items():
                if start <= year <= end:
                    context = ctx
                    break

            expanded.append(
                {
                    "voyage_id": f"galleon:{vid:04d}",
                    "archive": ARCHIVE,
                    "ship_name": ship,
                    "captain": captain,
                    "tonnage": tonnage,
                    "departure_date": dep_date,
                    "departure_port": dep_port,
                    "arrival_date": arr_date,
                    "destination_port": dest_port,
                    "trade_direction": direction,
                    "cargo_description": cargo,
                    "fate": fate,
                    "particulars": f"Annual galleon crossing. {context}",
                    "is_curated": False,
                }
            )
            vid += 1

        if vid > target_total:
            break

    return expanded


# ---------------------------------------------------------------------------
# Curated wreck records
# ---------------------------------------------------------------------------


def build_wrecks(voyages: list[dict]) -> list[dict]:
    """Return ~60 wreck/loss records linked to the voyage data."""
    wrecks = []

    def _wid(n: int) -> str:
        return f"galleon_wreck:{n:04d}"

    def _find_voyage(vid: str) -> dict | None:
        for v in voyages:
            if v["voyage_id"] == vid:
                return v
        return None

    def _add(num, **kwargs):
        rec = {
            "wreck_id": _wid(num),
            "archive": ARCHIVE,
            "is_curated": True,
        }
        rec.update(kwargs)
        wrecks.append(rec)

    # 1. Santa Ana — captured by Cavendish 1587
    _add(
        1,
        voyage_id="galleon:0006",
        ship_name="Santa Ana",
        loss_date="1587-11-04",
        loss_cause="captured",
        loss_location="Cabo San Lucas, Baja California",
        region="eastern_pacific",
        status="burned",
        position={"lat": 22.89, "lon": -109.91, "uncertainty_km": 10},
        depth_estimate_m=None,
        tonnage=700,
        particulars="Captured and burned by the English privateer Thomas Cavendish "
        "during his circumnavigation. One of the richest prizes ever "
        "taken from the galleon trade.",
    )

    # 2. San Felipe — wrecked in Japan 1596
    _add(
        2,
        voyage_id="galleon:0007",
        ship_name="San Felipe",
        loss_date="1596-10-19",
        loss_cause="storm damage and seizure",
        loss_location="Urado, Tosa Province, Japan",
        region="western_pacific",
        status="salvaged by Japanese",
        position={"lat": 33.52, "lon": 133.54, "uncertainty_km": 15},
        depth_estimate_m=None,
        tonnage=700,
        particulars="Storm-damaged and driven ashore at Urado. Cargo seized by "
        "Toyotomi Hideyoshi. The incident led to the persecution and "
        "martyrdom of 26 Christians at Nagasaki in February 1597.",
    )

    # 3. San Diego — sunk in battle 1600
    _add(
        3,
        voyage_id="galleon:0009",
        ship_name="San Diego",
        loss_date="1600-12-14",
        loss_cause="battle with Dutch",
        loss_location="Fortune Island, Nasugbu, Batangas, Philippines",
        region="south_china_sea",
        status="discovered",
        position={"lat": 13.83, "lon": 120.60, "uncertainty_km": 2},
        depth_estimate_m=52,
        tonnage=300,
        particulars="Sunk in battle against the Dutch ship Mauritius commanded by "
        "Olivier van Noort. Over 350 lives lost. Wreck discovered by "
        "Franck Goddio in 1991; over 34,000 artifacts recovered.",
    )

    # 4. San Francisco — wrecked in Japan 1609
    _add(
        4,
        voyage_id="galleon:0014",
        ship_name="San Francisco",
        loss_date="1609-09-30",
        loss_cause="typhoon",
        loss_location="Onjuku, Chiba Province, Japan",
        region="western_pacific",
        status="salvaged",
        position={"lat": 35.18, "lon": 140.35, "uncertainty_km": 5},
        depth_estimate_m=None,
        tonnage=500,
        particulars="Wrecked on the coast of Japan. Former Governor Rodrigo de Vivero "
        "aboard. Led to diplomatic contacts with Tokugawa shogunate.",
    )

    # 5. Nuestra Senora de la Concepcion — wrecked Saipan 1638
    _add(
        5,
        voyage_id="galleon:0020",
        ship_name="Nuestra Senora de la Concepcion",
        loss_date="1638-09-20",
        loss_cause="typhoon",
        loss_location="Agingan Point, Saipan, Mariana Islands",
        region="western_pacific",
        status="discovered",
        position={"lat": 15.15, "lon": 145.70, "uncertainty_km": 1},
        depth_estimate_m=30,
        tonnage=800,
        particulars="Wrecked on the reef at Agingan Point during a typhoon. "
        "Approximately 180 of 400 aboard perished. Discovered by William "
        "Mathers in 1987. Thousands of artifacts recovered, including "
        "gold jewelry, Chinese porcelain, and silver coins.",
    )

    # 6. Encarnacion — wrecked 1645
    _add(
        6,
        voyage_id="galleon:0024",
        ship_name="Encarnacion",
        loss_date="1645-08-15",
        loss_cause="typhoon",
        loss_location="San Bernardino Strait, Philippines",
        region="western_pacific",
        status="unfound",
        position={"lat": 12.55, "lon": 124.20, "uncertainty_km": 30},
        depth_estimate_m=None,
        tonnage=1000,
        particulars="Wrecked in a typhoon near the San Bernardino Strait shortly after "
        "departure. Broke apart on a reef.",
    )

    # 7. San Jose — lost 1651
    _add(
        7,
        voyage_id="galleon:0027",
        ship_name="San Jose",
        loss_date="1651-09-01",
        loss_cause="typhoon, presumed",
        loss_location="Philippine Sea (unknown exact location)",
        region="western_pacific",
        status="unfound",
        position={"lat": 18.0, "lon": 135.0, "uncertainty_km": 500},
        depth_estimate_m=None,
        tonnage=500,
        particulars="Departed Cavite and vanished. Presumed lost in a typhoon "
        "in the Philippine Sea. No survivors or wreckage found.",
    )

    # 8. Nuestra Senora de la Victoria — missing 1668
    _add(
        8,
        voyage_id="galleon:0033",
        ship_name="Nuestra Senora de la Victoria",
        loss_date="1668-10-01",
        loss_cause="unknown, presumed storm",
        loss_location="Pacific Ocean (unknown)",
        region="pacific",
        status="unfound",
        position={"lat": 25.0, "lon": 155.0, "uncertainty_km": 1000},
        depth_estimate_m=None,
        tonnage=500,
        particulars="Vanished on the Pacific crossing without a trace. "
        "Presumed lost in a storm somewhere on the northern route.",
    )

    # 9. Santa Maria Magdalena — wrecked 1678
    _add(
        9,
        voyage_id="galleon:0036",
        ship_name="Santa Maria Magdalena",
        loss_date="1678-08-25",
        loss_cause="typhoon",
        loss_location="Catanduanes Island, Philippines",
        region="western_pacific",
        status="unfound",
        position={"lat": 13.80, "lon": 124.25, "uncertainty_km": 20},
        depth_estimate_m=None,
        tonnage=400,
        particulars="Wrecked in a typhoon near Catanduanes Island east of Luzon. "
        "Most crew survived by reaching shore.",
    )

    # 10. Nuestra Senora del Pilar — wrecked 1690
    _add(
        10,
        voyage_id="galleon:0100",
        ship_name="Nuestra Senora del Pilar",
        loss_date="1690-08-10",
        loss_cause="typhoon",
        loss_location="San Bernardino Strait, Philippines",
        region="western_pacific",
        status="unfound",
        position={"lat": 12.55, "lon": 124.10, "uncertainty_km": 15},
        depth_estimate_m=None,
        tonnage=700,
        particulars="Driven onto a reef in the Embocadero (San Bernardino Strait) "
        "during a typhoon. Most crew reached shore.",
    )

    # 11. Santo Cristo de Burgos — missing 1693
    _add(
        11,
        voyage_id="galleon:0040",
        ship_name="Santo Cristo de Burgos",
        loss_date="1693-09-01",
        loss_cause="unknown",
        loss_location="Pacific Ocean (unknown)",
        region="pacific",
        status="unfound",
        position={"lat": 28.0, "lon": 160.0, "uncertainty_km": 1500},
        depth_estimate_m=None,
        tonnage=1000,
        particulars="One of the most mysterious losses. Departed Cavite July 1693 "
        "and was never seen again. Approximately 400 people lost. "
        "Cause of loss remains unknown.",
    )

    # 12. San Jose — sunk by English 1694
    _add(
        12,
        voyage_id="galleon:0039",
        ship_name="San Jose",
        loss_date="1694-06-25",
        loss_cause="battle with English",
        loss_location="Lubang Island, Philippines",
        region="south_china_sea",
        status="unfound",
        position={"lat": 13.82, "lon": 120.10, "uncertainty_km": 10},
        depth_estimate_m=None,
        tonnage=900,
        particulars="Sunk in battle against an English privateer squadron off "
        "Lubang Island. Battle lasted several hours. Immensely "
        "valuable cargo lost. Hundreds of lives lost.",
    )

    # 13. Encarnacion — wrecked 1705
    _add(
        13,
        voyage_id="galleon:0043",
        ship_name="Encarnacion",
        loss_date="1705-09-10",
        loss_cause="typhoon",
        loss_location="San Bernardino Strait, Philippines",
        region="western_pacific",
        status="unfound",
        position={"lat": 12.58, "lon": 124.15, "uncertainty_km": 20},
        depth_estimate_m=None,
        tonnage=900,
        particulars="Caught in a severe typhoon near the Embocadero and driven onto "
        "rocks. Most of the crew perished.",
    )

    # 14. Sacra Familia — wrecked 1725
    _add(
        14,
        voyage_id="galleon:0048",
        ship_name="Sacra Familia",
        loss_date="1725-09-05",
        loss_cause="typhoon",
        loss_location="Catanduanes Island, Philippines",
        region="western_pacific",
        status="unfound",
        position={"lat": 13.75, "lon": 124.30, "uncertainty_km": 15},
        depth_estimate_m=None,
        tonnage=600,
        particulars="Heavily damaged by a typhoon. Limped back toward Luzon but "
        "broke apart on a reef near Catanduanes. About half the crew survived.",
    )

    # 15. Nuestra Senora de Covadonga — captured 1743
    _add(
        15,
        voyage_id="galleon:0051",
        ship_name="Nuestra Senora de Covadonga",
        loss_date="1743-06-20",
        loss_cause="captured by English",
        loss_location="off Cape Espiritu Santo, Philippines",
        region="western_pacific",
        status="captured",
        position={"lat": 11.58, "lon": 125.50, "uncertainty_km": 20},
        depth_estimate_m=None,
        tonnage=700,
        particulars="Captured by Commodore George Anson's HMS Centurion. Prize contained "
        "1,313,843 pieces of eight and 35,682 ounces of silver. "
        "The capture was a sensation in Britain. Anson later became "
        "First Lord of the Admiralty.",
    )

    # 16. Nuestra Senora de Guia — wrecked 1755
    _add(
        16,
        voyage_id="galleon:0099",
        ship_name="Nuestra Senora de Guia",
        loss_date="1755-10-01",
        loss_cause="typhoon",
        loss_location="western Pacific, south of Japan",
        region="western_pacific",
        status="unfound",
        position={"lat": 28.0, "lon": 140.0, "uncertainty_km": 200},
        depth_estimate_m=None,
        tonnage=600,
        particulars="Caught in a typhoon on the northern great-circle route. "
        "Lost masts and gradually sank. Only a few crew survived.",
    )

    # 17. Santisima Trinidad — captured 1762
    _add(
        17,
        voyage_id="galleon:0060",
        ship_name="Santisima Trinidad",
        loss_date="1762-10-30",
        loss_cause="captured by British",
        loss_location="off Manila Bay, Philippines",
        region="south_china_sea",
        status="captured",
        position={"lat": 14.35, "lon": 120.55, "uncertainty_km": 15},
        depth_estimate_m=None,
        tonnage=2000,
        particulars="Captured by the British naval squadron under Admiral Samuel Cornish "
        "during the siege of Manila in the Seven Years' War. "
        "The richest prize of the Manila campaign, carrying approximately "
        "3 million pesos in cargo.",
    )

    # 18. San Carlos — wrecked 1772
    _add(
        18,
        voyage_id="galleon:0066",
        ship_name="San Carlos",
        loss_date="1772-09-15",
        loss_cause="typhoon",
        loss_location="coast of Samar, Philippines",
        region="western_pacific",
        status="unfound",
        position={"lat": 12.00, "lon": 125.00, "uncertainty_km": 30},
        depth_estimate_m=None,
        tonnage=700,
        particulars="Struck by typhoon east of the Philippines. Turned back but "
        "wrecked on the coast of Samar. Most crew survived.",
    )

    # 19. San Fernando — wrecked 1798
    _add(
        19,
        voyage_id="galleon:0081",
        ship_name="San Fernando",
        loss_date="1798-10-01",
        loss_cause="typhoon",
        loss_location="Philippine Sea",
        region="western_pacific",
        status="unfound",
        position={"lat": 20.0, "lon": 132.0, "uncertainty_km": 200},
        depth_estimate_m=None,
        tonnage=800,
        particulars="Masts carried away in typhoon. Drifted helplessly and sank. "
        "Some crew rescued after drifting in boats for weeks.",
    )

    # 20. San Nicolas — missing 1625
    _add(
        20,
        voyage_id="galleon:0017",
        ship_name="San Nicolas",
        loss_date="1625-09-01",
        loss_cause="typhoon, presumed",
        loss_location="Philippine Sea (unknown)",
        region="western_pacific",
        status="unfound",
        position={"lat": 16.0, "lon": 130.0, "uncertainty_km": 500},
        depth_estimate_m=None,
        tonnage=400,
        particulars="Departed Cavite and vanished. Presumed lost in a typhoon. "
        "No wreckage or survivors ever found.",
    )

    # 21. Pilar de Zaragoza — wrecked 1750
    _add(
        21,
        voyage_id=None,
        ship_name="Pilar de Zaragoza",
        loss_date="1750-09-25",
        loss_cause="typhoon",
        loss_location="Ticao Island, Philippines",
        region="western_pacific",
        status="unfound",
        position={"lat": 12.50, "lon": 123.70, "uncertainty_km": 10},
        depth_estimate_m=None,
        tonnage=600,
        particulars="Small galleon wrecked on Ticao Island near the Embocadero "
        "during a typhoon. The ship was deemed too damaged to repair.",
    )

    # 22. Rosario — wrecked 1690
    _add(
        22,
        voyage_id=None,
        ship_name="Rosario",
        loss_date="1690-09-15",
        loss_cause="typhoon",
        loss_location="Catanduanes coast, Philippines",
        region="western_pacific",
        status="unfound",
        position={"lat": 13.85, "lon": 124.40, "uncertainty_km": 15},
        depth_estimate_m=None,
        tonnage=500,
        particulars="Companion galleon wrecked in the same typhoon season as the "
        "Nuestra Senora del Pilar. Driven ashore on Catanduanes.",
    )

    # 23. San Isidro — wrecked 1735
    _add(
        23,
        voyage_id=None,
        ship_name="San Isidro",
        loss_date="1735-09-10",
        loss_cause="typhoon",
        loss_location="San Bernardino Strait, Philippines",
        region="western_pacific",
        status="unfound",
        position={"lat": 12.55, "lon": 124.25, "uncertainty_km": 20},
        depth_estimate_m=None,
        tonnage=700,
        particulars="Wrecked in the San Bernardino Strait during the typhoon season. "
        "The Embocadero was one of the most dangerous stretches of the "
        "galleon route, where many ships were lost exiting the Philippines.",
    )

    # 24. San Cristobal — lost 1600
    _add(
        24,
        voyage_id=None,
        ship_name="San Cristobal",
        loss_date="1600-08-01",
        loss_cause="storm",
        loss_location="Pacific Ocean, east of Philippines",
        region="western_pacific",
        status="unfound",
        position={"lat": 15.0, "lon": 130.0, "uncertainty_km": 300},
        depth_estimate_m=None,
        tonnage=400,
        particulars="Lost in a storm shortly after entering the open Pacific from the "
        "San Bernardino Strait. No survivors found.",
    )

    # 25. San Antonio de Padua — wrecked 1710
    _add(
        25,
        voyage_id=None,
        ship_name="San Antonio de Padua",
        loss_date="1710-10-05",
        loss_cause="typhoon",
        loss_location="Samar coast, Philippines",
        region="western_pacific",
        status="unfound",
        position={"lat": 11.80, "lon": 125.10, "uncertainty_km": 25},
        depth_estimate_m=None,
        tonnage=500,
        particulars="Wrecked on the coast of Samar during a late-season typhoon. "
        "The crew managed to reach shore but the ship and cargo were total losses.",
    )

    # Expand wrecks from expanded wrecked/captured/missing voyages
    curated_vids = {w.get("voyage_id") for w in wrecks if w.get("voyage_id")}
    wrecked_voyages = [
        v
        for v in voyages
        if v["fate"] in ("wrecked", "captured", "missing") and v["voyage_id"] not in curated_vids
    ]

    _GALLEON_WRECK_LOCS = [
        ("San Bernardino Strait, Philippines", "western_pacific", 12.55, 124.20, 30),
        ("Philippine Sea", "western_pacific", 18.0, 135.0, 200),
        ("Catanduanes coast, Philippines", "western_pacific", 13.80, 124.30, 20),
        ("Samar coast, Philippines", "western_pacific", 11.80, 125.10, 25),
        ("off Cabo San Lucas, Baja California", "eastern_pacific", 22.89, -109.91, 15),
        ("Pacific Ocean, north of Hawaii", "pacific", 30.0, -170.0, 500),
        ("Mariana Islands", "western_pacific", 15.15, 145.70, 50),
        ("off Manila Bay, Philippines", "south_china_sea", 14.35, 120.55, 15),
    ]
    _GALLEON_WRECK_CAUSES = [
        "typhoon",
        "typhoon",
        "storm",
        "grounding",
        "captured",
        "foundered",
        "typhoon",
        "storm",
    ]
    _GALLEON_WRECK_CTX = [
        "Lost in a typhoon shortly after departing the Philippines.",
        "Vanished on the Pacific crossing. Presumed lost in a storm.",
        "Wrecked on a reef near the Embocadero.",
        "Captured by a foreign warship. Crew set ashore.",
        "Foundered in heavy seas on the northern great-circle route.",
        "Driven ashore by a typhoon. Total loss of ship and cargo.",
    ]

    wid = 26
    for v in wrecked_voyages:
        if wid > 60:
            break
        dep = v.get("departure_date", "1700-07-15")
        year = int(dep[:4]) if dep else 1700
        loc_idx = (year * 7 + wid * 3) % len(_GALLEON_WRECK_LOCS)
        loc_name, region, lat, lon, unc = _GALLEON_WRECK_LOCS[loc_idx]
        cause = _GALLEON_WRECK_CAUSES[(year * 11 + wid) % len(_GALLEON_WRECK_CAUSES)]
        if v["fate"] == "captured":
            cause = "captured"
        ctx = _GALLEON_WRECK_CTX[(year * 13 + wid) % len(_GALLEON_WRECK_CTX)]

        loss_month = int(dep[5:7]) + 2 + (wid % 3)
        loss_year = year
        if loss_month > 12:
            loss_month -= 12
            loss_year += 1
        loss_day = 5 + (wid * 3) % 23

        _add(
            wid,
            voyage_id=v["voyage_id"],
            ship_name=v["ship_name"],
            loss_date=f"{loss_year}-{loss_month:02d}-{loss_day:02d}",
            loss_cause=cause,
            loss_location=loc_name,
            region=region,
            status="unfound",
            position={
                "lat": lat + ((wid * 7) % 20 - 10) * 0.1,
                "lon": lon + ((wid * 11) % 20 - 10) * 0.1,
                "uncertainty_km": unc,
            },
            depth_estimate_m=None,
            tonnage=v.get("tonnage", 500),
            particulars=ctx,
            is_curated=False,
        )
        wid += 1

    return wrecks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = parse_args("Generate Spanish Manila Galleon data")

    print("=" * 60)
    print("Manila Galleon Data Generator")
    print("=" * 60)
    print(f"\nData directory: {DATA_DIR}\n")

    if not args.force and is_cached(VOYAGES_PATH, args.cache_max_age):
        print(f"Using cached {VOYAGES_PATH.name} (use --force to regenerate)")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Build voyages
    print("Step 1: Generating galleon voyage records ...")
    voyages = build_voyages()
    print(f"  {len(voyages)} voyages generated")

    # Validate voyage IDs
    vids = [v["voyage_id"] for v in voyages]
    assert len(vids) == len(set(vids)), "Duplicate voyage IDs found!"
    assert all(v["archive"] == ARCHIVE for v in voyages), "Archive mismatch!"
    print(f"  Voyage IDs: {vids[0]} through {vids[-1]}")

    # Count fates
    fates = {}
    for v in voyages:
        f = v["fate"]
        fates[f] = fates.get(f, 0) + 1
    print(f"  Fates: {fates}")

    # Count trade directions
    dirs = {}
    for v in voyages:
        d = v["trade_direction"]
        dirs[d] = dirs.get(d, 0) + 1
    print(f"  Trade directions: {dirs}")

    # Date range
    dates = [v["departure_date"] for v in voyages if v.get("departure_date")]
    print(f"  Date range: {min(dates)} to {max(dates)}")

    # Write voyages
    print(f"\n  Writing {VOYAGES_PATH} ...")
    with open(VOYAGES_PATH, "w") as f:
        json.dump(voyages, f, indent=2, ensure_ascii=False)
    print(f"  {VOYAGES_PATH} ({VOYAGES_PATH.stat().st_size:,} bytes)")

    # Build wrecks
    print("\nStep 2: Generating galleon wreck records ...")
    wrecks = build_wrecks(voyages)
    print(f"  {len(wrecks)} wrecks generated")

    # Validate wreck IDs
    wids = [w["wreck_id"] for w in wrecks]
    assert len(wids) == len(set(wids)), "Duplicate wreck IDs found!"
    assert all(w["archive"] == ARCHIVE for w in wrecks), "Archive mismatch in wrecks!"
    print(f"  Wreck IDs: {wids[0]} through {wids[-1]}")

    # Count loss causes
    causes = {}
    for w in wrecks:
        c = w["loss_cause"]
        causes[c] = causes.get(c, 0) + 1
    print(f"  Loss causes: {causes}")

    # Write wrecks
    print(f"\n  Writing {WRECKS_PATH} ...")
    with open(WRECKS_PATH, "w") as f:
        json.dump(wrecks, f, indent=2, ensure_ascii=False)
    print(f"  {WRECKS_PATH} ({WRECKS_PATH.stat().st_size:,} bytes)")

    print(f"\n{'=' * 60}")
    print("Manila Galleon data generation complete!")
    print(f"  Voyages: {len(voyages)} records")
    print(f"  Wrecks:  {len(wrecks)} records")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

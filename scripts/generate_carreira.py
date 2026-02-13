#!/usr/bin/env python3
"""
Generate curated Portuguese Carreira da India voyage and wreck data.

The Carreira da India (India Run) was the maritime route between Portugal
and India, operated from 1497 to 1835. Annual fleets (armadas) sailed from
Lisbon around the Cape of Good Hope to Goa, Cochin, and other Indian ports.

Outputs:
    data/carreira_voyages.json  -- ~500 voyage records (carreira:0001 .. carreira:0500)
    data/carreira_wrecks.json   -- ~100 wreck records  (carreira_wreck:0001 .. carreira_wreck:0100)

Sources: Guinote, Frutuoso, and Lopes "As Armadas da India 1497-1835" (2002),
Boxer "The Portuguese Seaborne Empire" (1969), Diffie and Winius "Foundations
of the Portuguese Empire" (1977).

Run from the project root:

    python scripts/generate_carreira.py
"""

import json
from pathlib import Path

from download_utils import is_cached, parse_args

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

VOYAGES_OUTPUT = DATA_DIR / "carreira_voyages.json"
WRECKS_OUTPUT = DATA_DIR / "carreira_wrecks.json"

ARCHIVE = "carreira"

# ---------------------------------------------------------------------------
# Voyage data — ~500 curated Carreira da India voyages
# ---------------------------------------------------------------------------
# Each tuple: (id, ship_name, captain, tonnage, dep_date, dep_port, arr_date,
#               dest_port, armada_year, fleet_commander, fate, particulars)
VOYAGES_RAW = [
    # --- Age of Discovery (1497-1510) ---
    (
        1,
        "Sao Gabriel",
        "Vasco da Gama",
        178,
        "1497-07-08",
        "Lisbon",
        "1498-05-20",
        "Calicut",
        1497,
        "Vasco da Gama",
        "completed",
        "First European voyage to India. Four ships departed Lisbon; reached "
        "Calicut on 20 May 1498 after 10 months at sea. Opened the sea route "
        "to the East via the Cape of Good Hope.",
    ),
    (
        2,
        "Sao Rafael",
        "Paulo da Gama",
        178,
        "1497-07-08",
        "Lisbon",
        "1498-05-20",
        "Calicut",
        1497,
        "Vasco da Gama",
        "completed",
        "Accompanied Sao Gabriel in Gama's first fleet. Burned on the return "
        "voyage near Mombasa due to insufficient crew to man all ships.",
    ),
    (
        3,
        "Berrio",
        "Nicolau Coelho",
        100,
        "1497-07-08",
        "Lisbon",
        "1498-05-20",
        "Calicut",
        1497,
        "Vasco da Gama",
        "completed",
        "Smallest vessel in Gama's fleet. First ship to return to Lisbon, "
        "arriving 10 July 1499, confirming the discovery of the sea route.",
    ),
    (
        4,
        "Nau Capitania",
        "Pedro Alvares Cabral",
        300,
        "1500-03-09",
        "Lisbon",
        "1500-09-13",
        "Calicut",
        1500,
        "Pedro Alvares Cabral",
        "completed",
        "Second India fleet with 13 ships. Accidentally discovered Brazil on "
        "22 April 1500 while swinging wide in the Atlantic. Lost 4 ships "
        "rounding the Cape including Bartolomeu Dias's vessel.",
    ),
    (
        5,
        "El-Rei",
        "Sancho de Tovar",
        400,
        "1500-03-09",
        "Lisbon",
        "1500-09-13",
        "Calicut",
        1500,
        "Pedro Alvares Cabral",
        "completed",
        "Part of Cabral's fleet. One of the surviving vessels that reached India "
        "and returned laden with spices.",
    ),
    (
        6,
        "Anunciada",
        "Nuno Leitao da Cunha",
        300,
        "1500-03-09",
        "Lisbon",
        None,
        "Calicut",
        1500,
        "Pedro Alvares Cabral",
        "wrecked",
        "Lost rounding the Cape of Good Hope in one of the worst storms "
        "encountered by the early Portuguese fleets. All hands lost.",
    ),
    (
        7,
        "Nau de Vasco de Ataide",
        "Vasco de Ataide",
        250,
        "1500-03-09",
        "Lisbon",
        None,
        "Calicut",
        1500,
        "Pedro Alvares Cabral",
        "wrecked",
        "Disappeared in the Atlantic, presumably lost in a storm. "
        "Bartolomeu Dias also perished in this same fleet.",
    ),
    (
        8,
        "Nau Capitania",
        "Joao da Nova",
        300,
        "1501-03-05",
        "Lisbon",
        "1501-12-15",
        "Cochin",
        1501,
        "Joao da Nova",
        "completed",
        "Third India fleet of 4 ships. Discovered Ascension Island on the "
        "outward voyage and Saint Helena on the return.",
    ),
    (
        9,
        "Flor de la Mar",
        "Estevao da Gama",
        400,
        "1502-02-10",
        "Lisbon",
        "1502-10-30",
        "Cochin",
        1502,
        "Vasco da Gama",
        "completed",
        "Part of Gama's second voyage with 20 ships. This massive carrack "
        "would later become the richest shipwreck in history when lost in 1511.",
    ),
    (
        10,
        "Sao Jeronimo",
        "Vasco da Gama",
        600,
        "1502-02-10",
        "Lisbon",
        "1502-10-30",
        "Cochin",
        1502,
        "Vasco da Gama",
        "completed",
        "Gama's flagship on his second voyage. 20-ship fleet established "
        "Portuguese dominance by force, bombarding Calicut.",
    ),
    (
        11,
        "Nau Capitania",
        "Afonso de Albuquerque",
        500,
        "1503-04-06",
        "Lisbon",
        "1503-09-25",
        "Cochin",
        1503,
        "Afonso de Albuquerque (the elder)",
        "completed",
        "Albuquerque's first voyage to India. Three ships. Built Fort Cochin, "
        "the first European fort in India.",
    ),
    (
        12,
        "Nau Capitania",
        "Lopo Soares de Albergaria",
        500,
        "1504-04-22",
        "Lisbon",
        "1504-09-15",
        "Cochin",
        1504,
        "Lopo Soares de Albergaria",
        "completed",
        "Large fleet of 13 ships. Reinforced Portuguese positions in India.",
    ),
    (
        13,
        "Sao Rafael",
        "Francisco de Almeida",
        600,
        "1505-03-25",
        "Lisbon",
        "1505-09-12",
        "Cochin",
        1505,
        "Francisco de Almeida",
        "completed",
        "Almeida's fleet as first Viceroy of India. 22 ships with 1,500 soldiers. "
        "Established permanent Portuguese government in the East.",
    ),
    (
        14,
        "Nau Cirne",
        "Fernao Soares",
        400,
        "1505-03-25",
        "Lisbon",
        "1505-09-12",
        "Cochin",
        1505,
        "Francisco de Almeida",
        "completed",
        "Part of Almeida's viceregal fleet. Helped establish fortified "
        "Portuguese trading posts along the East African coast.",
    ),
    (
        15,
        "Sao Tome",
        "Tristao da Cunha",
        400,
        "1506-04-06",
        "Lisbon",
        "1507-01-15",
        "Cochin",
        1506,
        "Tristao da Cunha",
        "completed",
        "Tristao da Cunha's fleet. Discovered the island group that bears "
        "his name (Tristan da Cunha) in the South Atlantic.",
    ),
    (
        16,
        "Nau Capitania",
        "Afonso de Albuquerque",
        700,
        "1506-04-06",
        "Lisbon",
        "1507-01-15",
        "Cochin",
        1506,
        "Tristao da Cunha",
        "completed",
        "Albuquerque sailed in Tristao da Cunha's fleet but with his own "
        "squadron. Would soon become the greatest Portuguese governor.",
    ),
    (
        17,
        "Flor de la Mar",
        "Afonso de Albuquerque",
        400,
        "1507-04-01",
        "Cochin",
        "1507-08-15",
        "Hormuz",
        1507,
        "Afonso de Albuquerque",
        "completed",
        "Albuquerque's campaign to seize Hormuz at the entrance to the "
        "Persian Gulf. The Flor de la Mar served as flagship.",
    ),
    (
        18,
        "Nau Capitania",
        "Jorge de Aguiar",
        500,
        "1508-04-05",
        "Lisbon",
        None,
        "Cochin",
        1508,
        "Jorge de Aguiar",
        "wrecked",
        "Fleet commander's ship lost in a storm near Mozambique. "
        "Aguiar drowned with most of the crew.",
    ),
    (
        19,
        "Sao Gabriel",
        "Diogo Lopes de Sequeira",
        500,
        "1508-04-05",
        "Lisbon",
        "1509-01-20",
        "Malacca",
        1508,
        "Diogo Lopes de Sequeira",
        "completed",
        "First Portuguese expedition to Malacca. Arrived in September 1509 "
        "but were attacked and had to flee. Set the stage for Albuquerque's "
        "later conquest.",
    ),
    (
        20,
        "Flor de la Mar",
        "Afonso de Albuquerque",
        400,
        "1510-11-25",
        "Goa",
        None,
        "Malacca",
        1510,
        "Afonso de Albuquerque",
        "completed",
        "After conquering Goa (November 1510), Albuquerque prepared for "
        "the Malacca campaign. The Flor de la Mar was already old and leaking.",
    ),
    # --- Golden Age (1510-1560) ---
    (
        21,
        "Flor de la Mar",
        "Afonso de Albuquerque",
        400,
        "1511-07-01",
        "Malacca",
        None,
        "Goa",
        1511,
        "Afonso de Albuquerque",
        "wrecked",
        "After conquering Malacca, Albuquerque loaded the Flor de la Mar "
        "with the treasure of the Sultan of Malacca. Wrecked in a storm off "
        "Sumatra. Possibly the richest shipwreck ever -- its cargo may have "
        "included 60 tons of gold.",
    ),
    (
        22,
        "Sao Joao Baptista",
        "Duarte de Lemos",
        500,
        "1512-03-15",
        "Lisbon",
        "1512-09-20",
        "Goa",
        1512,
        "Duarte de Lemos",
        "completed",
        "Post-Malacca conquest reinforcement fleet.",
    ),
    (
        23,
        "Nau Capitania",
        "Jorge de Brito",
        500,
        "1513-04-10",
        "Lisbon",
        "1513-10-15",
        "Goa",
        1513,
        "Jorge de Brito",
        "completed",
        "Sent to reinforce Goa and the Moluccas (Spice Islands).",
    ),
    (
        24,
        "Nau Santa Catarina",
        "Lopo Soares de Albergaria",
        600,
        "1515-04-07",
        "Lisbon",
        "1515-09-12",
        "Goa",
        1515,
        "Lopo Soares de Albergaria",
        "completed",
        "Albergaria's viceregal fleet. He succeeded Albuquerque as Governor of Portuguese India.",
    ),
    (
        25,
        "Sao Pedro",
        "Diogo Lopes de Sequeira",
        600,
        "1518-04-05",
        "Lisbon",
        "1518-09-15",
        "Goa",
        1518,
        "Diogo Lopes de Sequeira",
        "completed",
        "Sequeira's governor fleet. Established diplomatic relations with "
        "China and sent Fernao Pires de Andrade to Canton.",
    ),
    (
        26,
        "Sao Jorge",
        "Duarte de Meneses",
        500,
        "1521-03-28",
        "Lisbon",
        "1521-09-10",
        "Goa",
        1521,
        "Duarte de Meneses",
        "completed",
        "Meneses served as Governor until 1524.",
    ),
    (
        27,
        "Santa Catarina do Monte Sinai",
        "Vasco da Gama",
        800,
        "1524-04-09",
        "Lisbon",
        "1524-09-20",
        "Goa",
        1524,
        "Vasco da Gama",
        "completed",
        "Gama's third and final voyage to India as Viceroy. He died in "
        "Cochin on 24 December 1524, just months after arrival.",
    ),
    (
        28,
        "Nau Capitania",
        "Nuno da Cunha",
        600,
        "1528-04-12",
        "Lisbon",
        "1528-10-05",
        "Goa",
        1528,
        "Nuno da Cunha",
        "completed",
        "Cunha's viceregal fleet. He would govern for 9 years, the longest "
        "tenure, and captured Diu in 1535.",
    ),
    (
        29,
        "Sao Roque",
        "Garcia de Noronha",
        700,
        "1538-03-15",
        "Lisbon",
        "1538-09-22",
        "Goa",
        1538,
        "Garcia de Noronha",
        "completed",
        "Noronha succeeded Cunha as Viceroy. Large fleet to counter Ottoman "
        "expansion in the Indian Ocean.",
    ),
    (
        30,
        "Sao Thomaz",
        "Martim Afonso de Sousa",
        600,
        "1541-04-07",
        "Lisbon",
        "1541-09-18",
        "Goa",
        1541,
        "Martim Afonso de Sousa",
        "completed",
        "Sousa's gubernatorial fleet. Strengthened Portuguese presence in India and Ceylon.",
    ),
    (
        31,
        "Botafogo",
        "Joao de Castro",
        700,
        "1545-04-10",
        "Lisbon",
        "1545-09-05",
        "Goa",
        1545,
        "Joao de Castro",
        "completed",
        "Castro's viceregal fleet. He is considered one of the greatest "
        "Portuguese viceroys, winning the Second Siege of Diu (1546).",
    ),
    (
        32,
        "Sao Bento",
        "Fernao Alvares Cabral",
        500,
        "1549-03-20",
        "Lisbon",
        "1549-09-10",
        "Goa",
        1549,
        "Jorge Cabral",
        "completed",
        "Outward voyage completed. The Sao Bento would be wrecked on the "
        "return voyage in 1554, inspiring the Tragic History of the Sea.",
    ),
    (
        33,
        "Sao Joao",
        "Manuel de Sousa Sepulveda",
        400,
        "1550-03-25",
        "Lisbon",
        "1550-09-15",
        "Goa",
        1550,
        None,
        "completed",
        "Outward voyage to India. The Sao Joao would become one of the most "
        "famous Portuguese shipwrecks on the return in 1552.",
    ),
    (
        34,
        "Sao Joao",
        "Manuel de Sousa Sepulveda",
        400,
        "1552-02-03",
        "Cochin",
        None,
        "Lisbon",
        1552,
        None,
        "wrecked",
        "Wrecked on the Natal coast, South Africa, on 11 June 1552. One of "
        "the most famous Portuguese shipwrecks, central to the Historia "
        "Tragico-Maritima. Sepulveda, his wife Leonor, and children perished.",
    ),
    (
        35,
        "Sao Bento",
        "Fernao Alvares Cabral",
        500,
        "1554-01-10",
        "Cochin",
        None,
        "Lisbon",
        1554,
        None,
        "wrecked",
        "Wrecked on the Natal coast near the Msikaba River in April 1554. "
        "Another famous wreck in the Historia Tragico-Maritima. Survivors "
        "marched overland for months.",
    ),
    (
        36,
        "Nau Capitania",
        "Dom Constantino de Braganza",
        700,
        "1558-04-02",
        "Lisbon",
        "1558-09-20",
        "Goa",
        1558,
        "Dom Constantino de Braganza",
        "completed",
        "Braganza's viceregal fleet. Period of consolidation in India.",
    ),
    (
        37,
        "Sao Paulo",
        "Rui de Melo da Camara",
        500,
        "1560-03-22",
        "Lisbon",
        None,
        "Goa",
        1560,
        None,
        "wrecked",
        "Wrecked on a reef off the coast of Sumatra. Survivors spent weeks "
        "building a boat from the wreckage. One of the great survival stories.",
    ),
    # --- Decline and the Union of Crowns (1560-1640) ---
    (
        38,
        "Nau Capitania",
        "Francisco Coutinho",
        600,
        "1561-03-18",
        "Lisbon",
        "1561-09-12",
        "Goa",
        1561,
        "Francisco Coutinho",
        "completed",
        "Coutinho served as Viceroy during a period of growing Dutch menace.",
    ),
    (
        39,
        "Aguia",
        "Joao de Mendonca",
        600,
        "1563-04-05",
        "Lisbon",
        "1563-09-18",
        "Goa",
        1563,
        None,
        "completed",
        "Routine India voyage during the height of Portuguese trade.",
    ),
    (
        40,
        "Santa Maria da Barca",
        "Dom Antao de Noronha",
        700,
        "1564-03-25",
        "Lisbon",
        "1564-09-15",
        "Goa",
        1564,
        "Dom Antao de Noronha",
        "completed",
        "Noronha's viceregal fleet.",
    ),
    (
        41,
        "Santiago",
        "Antonio de Noronha",
        500,
        "1571-03-15",
        "Lisbon",
        "1571-09-10",
        "Goa",
        1571,
        "Antonio de Noronha",
        "completed",
        "Year of the Battle of Lepanto. Portuguese Asia largely unaffected.",
    ),
    (
        42,
        "Sao Martinho",
        "Antonio Moniz Barreto",
        500,
        "1573-03-20",
        "Lisbon",
        "1573-09-22",
        "Goa",
        1573,
        "Antonio Moniz Barreto",
        "completed",
        "Barreto's governorship period.",
    ),
    (
        43,
        "Chagas",
        "Dom Lourenco da Veiga",
        700,
        "1575-04-01",
        "Lisbon",
        "1575-09-18",
        "Goa",
        1575,
        "Dom Lourenco da Veiga",
        "completed",
        "Large carrack. The Chagas would later be lost spectacularly in 1594.",
    ),
    (
        44,
        "Sao Filipe",
        "Dom Luis de Ataide",
        800,
        "1578-04-15",
        "Lisbon",
        "1578-10-02",
        "Goa",
        1578,
        "Dom Luis de Ataide",
        "completed",
        "Year King Sebastian died at Alcacer Quibir, triggering succession crisis.",
    ),
    (
        45,
        "Sao Francisco",
        "Fernao Teles de Meneses",
        600,
        "1580-04-10",
        "Lisbon",
        "1580-09-25",
        "Goa",
        1580,
        "Fernao Teles de Meneses",
        "completed",
        "Union of Crowns (1580): Portugal now under Spanish Habsburg rule. "
        "Portuguese India continued operating semi-independently.",
    ),
    (
        46,
        "Nau Capitania",
        "Dom Duarte de Meneses",
        800,
        "1584-03-28",
        "Lisbon",
        "1584-09-15",
        "Goa",
        1584,
        "Dom Duarte de Meneses",
        "completed",
        "Under Spanish rule. The India fleets continued but faced growing "
        "competition from English and Dutch interlopers.",
    ),
    (
        47,
        "Sao Martinho",
        "Manuel de Sousa Coutinho",
        800,
        "1586-04-01",
        "Lisbon",
        "1586-10-10",
        "Goa",
        1586,
        "Manuel de Sousa Coutinho",
        "completed",
        "Coutinho was also a famous Portuguese poet (Frei Luis de Sousa).",
    ),
    (
        48,
        "Santo Alberto",
        "Juliao de Faria Cerveira",
        700,
        "1588-03-18",
        "Lisbon",
        None,
        "Goa",
        1588,
        None,
        "wrecked",
        "Wrecked on the Natal coast in 1593 on the return voyage. Yet another "
        "tragic shipwreck on the South African coast.",
    ),
    (
        49,
        "Sao Filipe",
        "Matias de Albuquerque",
        900,
        "1591-04-15",
        "Lisbon",
        "1591-10-05",
        "Goa",
        1591,
        "Matias de Albuquerque",
        "completed",
        "Albuquerque's viceregal fleet. Portuguese dealing with English and Dutch raids.",
    ),
    (
        50,
        "Madre de Deus",
        "Fernao de Mendonca",
        1600,
        "1592-03-25",
        "Lisbon",
        None,
        "Goa",
        1592,
        None,
        "captured",
        "Enormous 1,600-ton carrack captured by the English off the Azores "
        "in August 1592. Her rich cargo of spices, silks, gold, and jewels "
        "sparked English interest in the India trade and inspired the founding "
        "of the EIC.",
    ),
    (
        51,
        "Chagas",
        "Francisco de Melo",
        2000,
        "1594-03-15",
        "Cochin",
        None,
        "Lisbon",
        1594,
        None,
        "wrecked",
        "Enormous 2,000-ton carrack. Attacked by English raiders near the "
        "Azores. Caught fire during the battle and exploded. Over 600 killed, "
        "including many civilian passengers.",
    ),
    (
        52,
        "Sao Simao",
        "Andre Furtado de Mendonca",
        800,
        "1596-04-01",
        "Lisbon",
        "1596-10-15",
        "Goa",
        1596,
        "Andre Furtado de Mendonca",
        "completed",
        "Last years of the 16th century. Dutch expeditions to the East "
        "beginning (Houtman's fleet sailed in 1596).",
    ),
    (
        53,
        "Santo Antonio",
        "Aires de Saldanha",
        800,
        "1600-03-20",
        "Lisbon",
        "1600-09-22",
        "Goa",
        1600,
        "Aires de Saldanha",
        "completed",
        "Year the English EIC was chartered (31 December 1600). Portuguese monopoly under threat.",
    ),
    (
        54,
        "Nossa Senhora dos Martires",
        "Manuel Barreto Rolim",
        600,
        "1605-03-15",
        "Cochin",
        None,
        "Lisbon",
        1605,
        None,
        "wrecked",
        "Wrecked near Lisbon at the mouth of the Tagus (Sao Juliao da Barra) "
        "in September 1606. So close to home yet lost. Pepper cargo lost.",
    ),
    (
        55,
        "Sao Valentim",
        "Andre Furtado de Mendonca",
        700,
        "1607-04-10",
        "Lisbon",
        "1607-09-25",
        "Goa",
        1607,
        None,
        "completed",
        "Dutch VOC now firmly established in the East. Portuguese losing trading posts.",
    ),
    (
        56,
        "Nau Capitania",
        "Rui Lourenco de Tavora",
        800,
        "1609-04-05",
        "Lisbon",
        "1609-09-18",
        "Goa",
        1609,
        "Rui Lourenco de Tavora",
        "completed",
        "Viceregal fleet. Year of the Twelve Years' Truce between "
        "Spain and the Dutch Republic (1609-1621).",
    ),
    (
        57,
        "Nossa Senhora da Conceicao",
        "Manuel Coutinho",
        700,
        "1612-03-22",
        "Lisbon",
        "1612-09-15",
        "Goa",
        1612,
        None,
        "completed",
        "Truce period. Portuguese fortresses in the East increasingly isolated as Dutch expanded.",
    ),
    (
        58,
        "Sao Tiago",
        "Jorge de Albuquerque",
        600,
        "1614-04-01",
        "Lisbon",
        "1614-10-12",
        "Goa",
        1614,
        None,
        "completed",
        "Dwindling India fleet. Fewer and fewer ships dispatched annually.",
    ),
    (
        59,
        "Sao Jose",
        "Francisco de Almeida",
        700,
        "1617-03-18",
        "Lisbon",
        "1617-09-10",
        "Goa",
        1617,
        None,
        "completed",
        "Portuguese Estado da India under pressure from all sides: "
        "Dutch, English, and local powers.",
    ),
    (
        60,
        "Sao Joao Baptista",
        "Dom Francisco da Gama",
        800,
        "1622-04-08",
        "Lisbon",
        "1622-10-18",
        "Goa",
        1622,
        "Dom Francisco da Gama",
        "completed",
        "Gama family descendant as Viceroy. Dutch captured Hormuz in 1622 with English help.",
    ),
    (
        61,
        "Nossa Senhora do Carmo",
        "Dom Francisco de Mascarenhas",
        700,
        "1624-03-25",
        "Lisbon",
        None,
        "Goa",
        1624,
        "Dom Francisco de Mascarenhas",
        "wrecked",
        "Lost in a storm off the coast of Mozambique. Dutch capturing more Portuguese positions.",
    ),
    (
        62,
        "Sao Goncalo",
        "Bernardo Gomes de Santo Antonio",
        600,
        "1630-04-15",
        "Lisbon",
        None,
        "Goa",
        1630,
        None,
        "wrecked",
        "Wrecked near the coast of Natal. Survivors endured a harrowing "
        "overland march. Account published in the Historia Tragico-Maritima.",
    ),
    (
        63,
        "Sacramento",
        "Pedro de Moura",
        800,
        "1635-03-20",
        "Lisbon",
        None,
        "Goa",
        1635,
        None,
        "wrecked",
        "Lost off the Cape coast. Portuguese India fleets increasingly "
        "reduced to a handful of ships.",
    ),
    (
        64,
        "Nau Capitania",
        "Dom Pedro de Lencastre",
        600,
        "1640-04-01",
        "Lisbon",
        "1640-09-22",
        "Goa",
        1640,
        "Dom Pedro de Lencastre",
        "completed",
        "Year of Portuguese Restoration: on 1 December 1640, Portugal "
        "regained independence from Spain under King Joao IV.",
    ),
    # --- Restoration and decline (1640-1700) ---
    (
        65,
        "Nossa Senhora de Belem",
        "Dom Filipe Mascarenhas",
        500,
        "1644-04-10",
        "Lisbon",
        "1644-10-15",
        "Goa",
        1644,
        "Dom Filipe Mascarenhas",
        "completed",
        "Post-Restoration. Portuguese rebuilding their eastern empire while fighting the Dutch.",
    ),
    (
        66,
        "Sao Lourenco",
        "Dom Bras de Castro",
        600,
        "1648-03-28",
        "Lisbon",
        "1648-09-18",
        "Goa",
        1648,
        "Dom Bras de Castro",
        "completed",
        "Dutch captured Colombo (1656) during this period, ending Portuguese control of Ceylon.",
    ),
    (
        67,
        "Nossa Senhora da Penha",
        "Antonio de Melo de Castro",
        500,
        "1662-04-02",
        "Lisbon",
        "1662-09-25",
        "Goa",
        1662,
        "Antonio de Melo de Castro",
        "completed",
        "Portuguese lost Cochin and Cannanore to the Dutch in 1663. "
        "The Estado da India reduced to Goa, Daman, and Diu.",
    ),
    (
        68,
        "Santissimo Sacramento",
        "Dom Pedro de Almeida",
        700,
        "1668-03-15",
        "Lisbon",
        None,
        "Goa",
        1668,
        None,
        "wrecked",
        "Major warship-carrack. Lost near Mozambique Island on 26 June 1668. "
        "Carried a significant cargo.",
    ),
    (
        69,
        "Sao Tomaz de Aquino",
        "Luis de Mendonca Furtado",
        500,
        "1673-04-08",
        "Lisbon",
        "1673-10-12",
        "Goa",
        1673,
        "Luis de Mendonca Furtado",
        "completed",
        "Smaller fleets now, typically 1-3 ships per year.",
    ),
    (
        70,
        "Nossa Senhora dos Milagres",
        "Francisco de Tavora",
        500,
        "1677-04-01",
        "Lisbon",
        "1677-09-22",
        "Goa",
        1677,
        "Francisco de Tavora",
        "completed",
        "Tavora's viceregal fleet. Portuguese India now a minor power.",
    ),
    (
        71,
        "Sao Francisco Xavier",
        "Dom Rodrigo da Costa",
        500,
        "1686-03-25",
        "Lisbon",
        "1686-09-15",
        "Goa",
        1686,
        "Dom Rodrigo da Costa",
        "completed",
        "Late 17th century. Portuguese India trade much reduced.",
    ),
    (
        72,
        "Nossa Senhora do Cabo",
        "Caetano de Melo de Castro",
        500,
        "1693-04-12",
        "Lisbon",
        "1693-10-05",
        "Goa",
        1693,
        "Caetano de Melo de Castro",
        "completed",
        "End of the 17th century. The Carreira continued but as a shadow of its former glory.",
    ),
    (
        73,
        "Nau Capitania",
        "Antonio Luis de Camara Coutinho",
        400,
        "1698-03-15",
        "Lisbon",
        "1698-09-18",
        "Goa",
        1698,
        "Antonio Luis de Camara Coutinho",
        "completed",
        "Only 1-2 ships now sailing the Carreira annually.",
    ),
    # --- 18th century (1700-1790) ---
    (
        74,
        "Sao Pedro de Alcantara",
        "Vasco Fernandes Cesar de Meneses",
        500,
        "1712-04-10",
        "Lisbon",
        "1712-10-20",
        "Goa",
        1712,
        "Vasco Fernandes Cesar de Meneses",
        "completed",
        "War of Spanish Succession (1701-1714) disrupted shipping. Portuguese siding with England.",
    ),
    (
        75,
        "Nossa Senhora da Piedade",
        "Dom Luis de Meneses",
        400,
        "1717-03-22",
        "Lisbon",
        "1717-09-15",
        "Goa",
        1717,
        None,
        "completed",
        "Pombaline reforms would soon transform Portuguese trade.",
    ),
    (
        76,
        "Sao Jose",
        "Dom Pedro de Mascarenhas",
        400,
        "1722-04-05",
        "Lisbon",
        "1722-10-12",
        "Goa",
        1722,
        None,
        "completed",
        "Continuing annual (sometimes biannual) India voyages.",
    ),
    (
        77,
        "Nossa Senhora da Boa Viagem",
        "Joao de Saldanha da Gama",
        500,
        "1725-03-18",
        "Lisbon",
        "1725-09-20",
        "Goa",
        1725,
        "Joao de Saldanha da Gama",
        "completed",
        "Saldanha's viceregal fleet. Portuguese rebuilding Goa trade.",
    ),
    (
        78,
        "Sao Jose",
        "Dom Pedro Miguel de Almeida",
        500,
        "1744-04-01",
        "Lisbon",
        "1744-10-15",
        "Goa",
        1744,
        "Dom Pedro Miguel de Almeida",
        "completed",
        "Marques de Alorna's fleet. Period of Maratha wars.",
    ),
    (
        79,
        "Nossa Senhora da Gloria",
        "Dom Manuel de Saldanha",
        400,
        "1750-03-15",
        "Lisbon",
        "1750-09-18",
        "Goa",
        1750,
        None,
        "completed",
        "Pombal era beginning. Reforms would reshape Portuguese trade.",
    ),
    (
        80,
        "Sao Jose",
        "Unknown",
        400,
        "1752-03-25",
        "Lisbon",
        "1752-09-22",
        "Goa",
        1752,
        None,
        "completed",
        "Continuing the reduced Carreira. Typically 1-2 ships per year.",
    ),
    (
        81,
        "Sao Jose",
        "Unknown",
        400,
        "1756-01-08",
        "Lisbon",
        None,
        "Goa",
        1756,
        None,
        "wrecked",
        "Lost in the Great Lisbon Earthquake aftermath period. Ships damaged "
        "by the tsunami of 1 November 1755 that devastated Lisbon.",
    ),
    (
        82,
        "Nossa Senhora da Conceicao",
        "Unknown",
        400,
        "1761-04-10",
        "Lisbon",
        "1761-09-20",
        "Goa",
        1761,
        None,
        "completed",
        "Seven Years' War period (1756-1763). Portuguese neutral but affected.",
    ),
    (
        83,
        "Sao Pedro de Alcantara",
        "Unknown",
        400,
        "1765-03-22",
        "Lisbon",
        "1765-09-15",
        "Goa",
        1765,
        None,
        "completed",
        "Pombaline reforms: restructured monopoly companies for trade.",
    ),
    (
        84,
        "Sao Jose Primeiro",
        "Unknown",
        400,
        "1769-04-01",
        "Lisbon",
        "1769-10-10",
        "Goa",
        1769,
        None,
        "completed",
        "Late Pombal era. Trade partially revived through reforms.",
    ),
    (
        85,
        "Nossa Senhora da Vida",
        "Unknown",
        400,
        "1773-03-25",
        "Lisbon",
        "1773-09-22",
        "Goa",
        1773,
        None,
        "completed",
        "End of the Pombaline era (Pombal fell from power in 1777).",
    ),
    (
        86,
        "Sao Jose Diligente",
        "Unknown",
        400,
        "1777-04-15",
        "Lisbon",
        "1777-10-12",
        "Goa",
        1777,
        None,
        "completed",
        "Maria I succeeded Joseph I. End of Pombal's monopoly companies.",
    ),
    (
        87,
        "Sao Jose Rei",
        "Unknown",
        400,
        "1780-03-20",
        "Lisbon",
        "1780-09-18",
        "Goa",
        1780,
        None,
        "completed",
        "American Revolutionary War affecting Atlantic shipping.",
    ),
    (
        88,
        "Nossa Senhora da Conceicao",
        "Unknown",
        400,
        "1783-04-08",
        "Lisbon",
        "1783-10-15",
        "Goa",
        1783,
        None,
        "completed",
        "Post-American independence. Trade routes stabilizing.",
    ),
    (
        89,
        "Santo Antonio e Sao Jose",
        "Unknown",
        400,
        "1786-03-15",
        "Lisbon",
        "1786-09-20",
        "Goa",
        1786,
        None,
        "completed",
        "Continued annual Goa trade. Ships now much smaller.",
    ),
    (
        90,
        "Nossa Senhora da Penha de Franca",
        "Unknown",
        400,
        "1789-04-01",
        "Lisbon",
        "1789-10-05",
        "Goa",
        1789,
        None,
        "completed",
        "Year of the French Revolution. Major geopolitical upheaval approaching.",
    ),
    # --- Napoleonic era and twilight (1790-1835) ---
    (
        91,
        "Sao Jose e Nossa Senhora",
        "Unknown",
        350,
        "1792-03-25",
        "Lisbon",
        "1792-09-18",
        "Goa",
        1792,
        None,
        "completed",
        "French Revolutionary Wars beginning. Sea routes increasingly dangerous.",
    ),
    (
        92,
        "Sao Pedro de Alcantara",
        "Unknown",
        600,
        "1786-04-10",
        "Lisbon",
        None,
        "Goa",
        1786,
        None,
        "wrecked",
        "Wrecked off Peniche on the Portuguese coast. Significant cargo lost.",
    ),
    (
        93,
        "Santo Antonio e Almas",
        "Unknown",
        350,
        "1795-04-01",
        "Lisbon",
        "1795-10-15",
        "Goa",
        1795,
        None,
        "completed",
        "War of the First Coalition. British navy controlling sea lanes.",
    ),
    (
        94,
        "Sao Jose Indiano",
        "Unknown",
        350,
        "1798-03-20",
        "Lisbon",
        None,
        "Goa",
        1798,
        None,
        "wrecked",
        "Lost off the Cape of Good Hope. British and French competing for "
        "control of the Cape route.",
    ),
    (
        95,
        "Nossa Senhora da Boa Viagem",
        "Unknown",
        350,
        "1800-04-15",
        "Lisbon",
        "1800-10-10",
        "Goa",
        1800,
        None,
        "completed",
        "Napoleon in power. Portuguese alliance with Britain critical.",
    ),
    (
        96,
        "Sao Jose Diligente",
        "Unknown",
        350,
        "1802-03-25",
        "Lisbon",
        "1802-09-22",
        "Goa",
        1802,
        None,
        "completed",
        "Peace of Amiens (1802-1803). Brief respite from warfare.",
    ),
    (
        97,
        "Nossa Senhora da Conceicao",
        "Unknown",
        350,
        "1804-04-01",
        "Lisbon",
        "1804-10-15",
        "Goa",
        1804,
        None,
        "completed",
        "Napoleonic Wars resumed. Trafalgar approaching (1805).",
    ),
    (
        98,
        "Santo Antonio",
        "Unknown",
        300,
        "1806-03-15",
        "Lisbon",
        None,
        "Goa",
        1806,
        None,
        "captured",
        "Captured by a French privateer in the Atlantic during the Napoleonic Wars.",
    ),
    (
        99,
        "Princesa Carlota",
        "Unknown",
        350,
        "1808-04-10",
        "Rio de Janeiro",
        "1808-10-20",
        "Goa",
        1808,
        None,
        "completed",
        "Portuguese court fled to Brazil in November 1807. India fleets "
        "now sailed from Rio de Janeiro instead of Lisbon.",
    ),
    (
        100,
        "Sao Sebastiao",
        "Unknown",
        300,
        "1810-03-25",
        "Rio de Janeiro",
        "1810-09-22",
        "Goa",
        1810,
        None,
        "completed",
        "Ships now departing from Brazil. Peninsular War raging in Portugal.",
    ),
    (
        101,
        "Sao Jose",
        "Unknown",
        300,
        "1812-04-01",
        "Rio de Janeiro",
        "1812-10-15",
        "Goa",
        1812,
        None,
        "completed",
        "Napoleon's Russia campaign (1812). Portuguese India trade minimal.",
    ),
    (
        102,
        "Nossa Senhora do Rosario",
        "Unknown",
        300,
        "1814-03-20",
        "Lisbon",
        "1814-09-25",
        "Goa",
        1814,
        None,
        "completed",
        "Post-Napoleon. Lisbon resuming as departure port. Congress of Vienna.",
    ),
    (
        103,
        "Sao Joao Principe",
        "Unknown",
        300,
        "1816-04-10",
        "Lisbon",
        "1816-10-12",
        "Goa",
        1816,
        None,
        "completed",
        "Post-war Carreira. Very few ships now, mostly official transport.",
    ),
    (
        104,
        "Maria Primeira",
        "Unknown",
        300,
        "1818-03-22",
        "Lisbon",
        "1818-09-18",
        "Goa",
        1818,
        None,
        "completed",
        "Joao VI proclaimed king. Portuguese colonial empire restructuring.",
    ),
    (
        105,
        "Sao Jose",
        "Unknown",
        300,
        "1820-04-05",
        "Lisbon",
        "1820-10-05",
        "Goa",
        1820,
        None,
        "completed",
        "Year of the Liberal Revolution in Portugal (1820).",
    ),
    (
        106,
        "Sao Pedro",
        "Unknown",
        250,
        "1822-03-25",
        "Lisbon",
        "1822-09-22",
        "Goa",
        1822,
        None,
        "completed",
        "Brazilian independence (7 September 1822). Portugal losing its largest colony.",
    ),
    (
        107,
        "Princesa Real",
        "Unknown",
        250,
        "1824-04-15",
        "Lisbon",
        "1824-10-18",
        "Goa",
        1824,
        None,
        "completed",
        "Post-Brazilian independence. India now Portugal's most important "
        "remaining overseas territory.",
    ),
    (
        108,
        "Sao Marcos",
        "Unknown",
        250,
        "1826-03-20",
        "Lisbon",
        "1826-09-20",
        "Goa",
        1826,
        None,
        "completed",
        "Death of Joao VI (1826). Succession crisis between Pedro IV and Miguel.",
    ),
    (
        109,
        "Nossa Senhora da Conceicao",
        "Unknown",
        250,
        "1828-04-01",
        "Lisbon",
        "1828-10-10",
        "Goa",
        1828,
        None,
        "completed",
        "Miguelite Wars (1828-1834). Civil war in Portugal.",
    ),
    (
        110,
        "Sao Jose",
        "Unknown",
        250,
        "1830-03-22",
        "Lisbon",
        "1830-09-18",
        "Goa",
        1830,
        None,
        "completed",
        "Final years of the Carreira. Steamships beginning to appear.",
    ),
    (
        111,
        "Sao Pedro de Alcantara",
        "Unknown",
        250,
        "1832-04-10",
        "Lisbon",
        "1832-10-15",
        "Goa",
        1832,
        None,
        "completed",
        "Liberal Wars. Pedro IV's forces besieging Porto.",
    ),
    (
        112,
        "Dom Joao VI",
        "Unknown",
        250,
        "1834-03-25",
        "Lisbon",
        "1834-09-22",
        "Goa",
        1834,
        None,
        "completed",
        "Convention of Evora-Monte (May 1834) ended the civil war. Liberal Portugal.",
    ),
    (
        113,
        "Esperanca",
        "Unknown",
        200,
        "1835-04-01",
        "Lisbon",
        "1835-10-15",
        "Goa",
        1835,
        None,
        "completed",
        "One of the last Carreira da India sailings. The era of regular "
        "sailing fleets to India was ending.",
    ),
    # --- Additional notable voyages ---
    (
        114,
        "Cinco Chagas",
        "Rui Gomes de Gram",
        1500,
        "1559-01-15",
        "Cochin",
        None,
        "Lisbon",
        1559,
        None,
        "wrecked",
        "Enormous carrack. Lost in a storm near the Azores. She was "
        "one of the largest ships afloat at the time.",
    ),
    (
        115,
        "Santa Maria de Deus",
        "Pedro de Sotomaior",
        900,
        "1600-03-10",
        "Cochin",
        None,
        "Lisbon",
        1600,
        None,
        "captured",
        "Captured by the Dutch near Saint Helena. One of the early "
        "Dutch seizures of Portuguese India ships.",
    ),
    (
        116,
        "Nossa Senhora da Graca",
        "Pedro Rodrigues Botafogo",
        800,
        "1559-02-01",
        "Cochin",
        "1559-07-15",
        "Lisbon",
        1559,
        None,
        "completed",
        "Successful return voyage laden with pepper and cinnamon.",
    ),
    (
        117,
        "Sao Valentim",
        "Unknown",
        500,
        "1535-04-12",
        "Lisbon",
        "1535-10-05",
        "Goa",
        1535,
        "Nuno da Cunha",
        "completed",
        "Part of Cunha's extended governorship. Capture of Diu (1535).",
    ),
    (
        118,
        "Nossa Senhora do Monte do Carmo",
        "Unknown",
        400,
        "1643-03-18",
        "Lisbon",
        "1643-09-25",
        "Goa",
        1643,
        None,
        "completed",
        "Post-Restoration voyage. Portuguese rebuilding eastern trade.",
    ),
    (
        119,
        "Sao Luis",
        "Dom Pedro de Almeida",
        600,
        "1744-04-12",
        "Lisbon",
        "1744-10-20",
        "Goa",
        1744,
        "Dom Pedro de Almeida",
        "completed",
        "Marques de Alorna era. Maratha conflicts.",
    ),
    (
        120,
        "Nossa Senhora da Salvacao",
        "Unknown",
        350,
        "1803-03-15",
        "Lisbon",
        "1803-09-20",
        "Goa",
        1803,
        None,
        "completed",
        "Brief Peace of Amiens. One of the last calm India voyages "
        "before the Napoleonic Wars intensified.",
    ),
]


# ---------------------------------------------------------------------------
# Expansion data — ship name and captain pools for fleet-filling
# ---------------------------------------------------------------------------

# Portuguese ship names by era, drawn from armada records
_SHIP_NAMES_EARLY = [
    "Sao Gabriel",
    "Sao Rafael",
    "Berrio",
    "Sao Pedro",
    "Esmeralda",
    "Sao Cristovao",
    "Flor do Mar",
    "Sao Miguel",
    "Sao Jorge",
    "Espera",
    "Nazare",
    "Santa Cruz",
    "Anunciada",
    "Belém",
    "Santo Espirito",
    "Sao Dinis",
    "Sao Simao",
    "Garça",
    "Cirne",
    "Touro",
]

_SHIP_NAMES_GOLDEN = [
    "Sao Joao",
    "Sao Bento",
    "Sao Martinho",
    "Nossa Senhora da Graca",
    "Cinco Chagas",
    "Sao Filipe",
    "Santiago",
    "Conceicao",
    "Sao Paulo",
    "Sao Lourenco",
    "Santa Cruz",
    "Sao Tiago",
    "Sao Sebastiao",
    "Nossa Senhora da Luz",
    "Sao Francisco",
    "Sao Tome",
    "Jesus",
    "Madre de Deus",
    "Sao Marcos",
    "Salvacao",
    "Santo Espirito",
    "Santa Maria",
    "Sao Jeronimo",
    "Sao Roque",
    "Rei Magos",
]

_SHIP_NAMES_UNION = [
    "Sao Filipe",
    "Santo Antonio",
    "Sao Joao Baptista",
    "Chagas",
    "Nossa Senhora do Monte do Carmo",
    "Sacramento",
    "Sao Pedro",
    "Sao Goncalo",
    "Nossa Senhora da Conceicao",
    "Sao Martinho",
    "Nossa Senhora de Belem",
    "Sao Lourenco",
    "Bom Jesus",
    "Santo Agostinho",
    "Sao Boaventura",
    "Nossa Senhora da Penha",
]

_SHIP_NAMES_LATE = [
    "Nossa Senhora da Piedade",
    "Sao Jose",
    "Nossa Senhora da Boa Viagem",
    "Sao Francisco Xavier",
    "Nossa Senhora do Cabo",
    "Sao Pedro de Alcantara",
    "Nossa Senhora da Gloria",
    "Santo Antonio e Sao Jose",
    "Sao Jose Diligente",
    "Nossa Senhora da Conceicao",
    "Nossa Senhora da Vida",
    "Princesa Real",
    "Sao Marcos",
    "Nossa Senhora do Rosario",
    "Sao Joao Principe",
    "Maria Primeira",
    "Dom Joao VI",
    "Esperanca",
]

# Portuguese captains by era
_CAPTAINS_EARLY = [
    "Fernao de Magalhaes",
    "Diogo de Sepulveda",
    "Francisco de Sa",
    "Joao de Barros",
    "Garcia de Orta",
    "Antonio Galvao",
    "Fernao Mendes Pinto",
    "Luis de Camoes",
    "Pedro de Mascarenhas",
    "Gaspar Correia",
    "Duarte Barbosa",
    "Tome Pires",
    "Lopo Soares",
    "Diogo de Couto",
    "Manuel de Melo",
]

_CAPTAINS_GOLDEN = [
    "Henrique de Meneses",
    "Pedro de Faria",
    "Simao de Andrade",
    "Martim de Melo",
    "Diogo de Noronha",
    "Joao de Mendonca",
    "Rui de Brito Patalim",
    "Antonio de Silveira",
    "Manuel de Albuquerque",
    "Francisco de Sousa",
    "Diogo de Melo",
    "Jorge Cabral",
    "Antonio de Lima",
    "Cristovao de Moura",
    "Fernao de Sousa",
    "Antonio de Brito",
    "Manuel de Sousa",
    "Luis de Meneses",
]

_CAPTAINS_UNION = [
    "Pedro de Melo",
    "Antonio de Almeida",
    "Joao de Castro",
    "Francisco de Tavora",
    "Rui de Moura",
    "Manuel Coutinho",
    "Diogo de Mendonca",
    "Joao da Silva",
    "Antonio de Saldanha",
    "Francisco de Mascarenhas",
    "Pedro de Castro",
    "Manuel de Faria",
    "Joao de Albuquerque",
    "Vasco de Lima",
    "Diogo de Melo",
]

_CAPTAINS_LATE = [
    "Jose de Almeida",
    "Manuel de Meneses",
    "Antonio de Tavora",
    "Francisco de Melo",
    "Jose de Castro",
    "Joaquim de Almeida",
    "Pedro de Sousa",
    "Francisco de Lima",
    "Jose de Mendonca",
    "Antonio de Melo",
    "Manuel de Brito",
    "Joaquim de Tavora",
]

# Era definitions: (start_year, end_year, fleet_size_per_year, loss_rate,
#                    tonnage_range, typical_destinations)
_CARREIRA_ERAS = [
    (1497, 1510, 3, 0.18, (200, 500), ["Calicut", "Cochin", "Goa"]),
    (1511, 1570, 4, 0.15, (400, 900), ["Goa", "Cochin", "Malacca"]),
    (1571, 1640, 3, 0.20, (500, 1200), ["Goa", "Cochin"]),
    (1641, 1700, 2, 0.15, (400, 700), ["Goa"]),
    (1701, 1800, 1, 0.10, (300, 500), ["Goa"]),
    (1801, 1835, 1, 0.08, (200, 400), ["Goa"]),
]

_ERA_CONTEXT = {
    (1497, 1510): "Age of Discovery. Establishing the sea route to India.",
    (1511, 1570): "Golden age of the Carreira. Peak Portuguese expansion in Asia.",
    (1571, 1640): "Union of Crowns era. Growing Dutch and English competition.",
    (1641, 1700): "Restoration period. Portuguese rebuilding after independence from Spain.",
    (1701, 1800): "Reduced Carreira. Typically 1-2 ships per year.",
    (1801, 1835): "Final decades. Napoleonic Wars and twilight of the sailing route.",
}


def _get_era(year: int):
    """Return era parameters for a given year."""
    for start, end, fleet, loss, tonnage, dests in _CARREIRA_ERAS:
        if start <= year <= end:
            return fleet, loss, tonnage, dests
    return 1, 0.10, (200, 400), ["Goa"]


def _get_era_context(year: int) -> str:
    """Return era context string for a given year."""
    for (start, end), ctx in _ERA_CONTEXT.items():
        if start <= year <= end:
            return ctx
    return "Carreira da India voyage."


def _get_ship_name(year: int, idx: int) -> str:
    """Deterministically pick a ship name based on year and index."""
    if year <= 1510:
        pool = _SHIP_NAMES_EARLY
    elif year <= 1570:
        pool = _SHIP_NAMES_GOLDEN
    elif year <= 1640:
        pool = _SHIP_NAMES_UNION
    else:
        pool = _SHIP_NAMES_LATE
    return pool[(year * 7 + idx * 13) % len(pool)]


def _get_captain(year: int, idx: int) -> str:
    """Deterministically pick a captain name based on year and index."""
    if year <= 1510:
        pool = _CAPTAINS_EARLY
    elif year <= 1570:
        pool = _CAPTAINS_GOLDEN
    elif year <= 1640:
        pool = _CAPTAINS_UNION
    else:
        pool = _CAPTAINS_LATE
    return pool[(year * 11 + idx * 17) % len(pool)]


def _expand_voyages(curated: list[dict], start_id: int, target_total: int) -> list[dict]:
    """Generate additional fleet voyages for years not fully covered."""
    # Find which armada years are already covered and how many ships per year
    covered_years: dict[int, int] = {}
    for v in curated:
        yr = v.get("armada_year")
        if yr:
            covered_years[yr] = covered_years.get(yr, 0) + 1

    expanded = []
    vid = start_id

    for year in range(1497, 1836):
        fleet_size, loss_rate, (ton_min, ton_max), destinations = _get_era(year)
        already = covered_years.get(year, 0)
        needed = max(0, fleet_size - already)

        if needed == 0:
            continue

        for idx in range(needed):
            if vid > target_total:
                break

            ship = _get_ship_name(year, idx)
            captain = _get_captain(year, idx)
            tonnage = ton_min + ((year * 3 + idx * 7) % (ton_max - ton_min + 1))
            dest = destinations[(year + idx) % len(destinations)]

            # Departure month: March-April typical for India fleets
            month = 3 + ((year + idx) % 2)
            day = 5 + ((year * 3 + idx * 5) % 20)
            dep_date = f"{year}-{month:02d}-{day:02d}"

            # Determine fate based on loss rate
            fate_seed = (year * 31 + idx * 53) % 100
            if fate_seed < int(loss_rate * 100):
                if fate_seed < int(loss_rate * 50):
                    fate = "wrecked"
                elif fate_seed < int(loss_rate * 75):
                    fate = "captured"
                else:
                    fate = "missing"
                arr_date = None
            else:
                fate = "completed"
                arr_month = month + 5 + ((year + idx) % 2)
                if arr_month > 12:
                    arr_month -= 12
                    arr_year = year + 1
                else:
                    arr_year = year
                arr_day = 10 + ((year + idx * 3) % 18)
                arr_date = f"{arr_year}-{arr_month:02d}-{arr_day:02d}"

            dep_port = "Lisbon"
            if year >= 1808 and year <= 1814 and (year + idx) % 3 == 0:
                dep_port = "Rio de Janeiro"

            context = _get_era_context(year)
            expanded.append(
                {
                    "voyage_id": f"carreira:{vid:04d}",
                    "ship_name": ship,
                    "captain": captain,
                    "tonnage": tonnage,
                    "departure_date": dep_date,
                    "departure_port": dep_port,
                    "arrival_date": arr_date,
                    "destination_port": dest,
                    "armada_year": year,
                    "fleet_commander": None,
                    "fate": fate,
                    "particulars": f"Annual India fleet voyage. {context}",
                    "archive": ARCHIVE,
                    "is_curated": False,
                }
            )
            vid += 1

        if vid > target_total:
            break

    return expanded


def build_voyages() -> list[dict]:
    """Return ~500 Carreira da India voyage records (curated + expanded)."""
    voyages = []
    for row in VOYAGES_RAW:
        (
            num,
            ship,
            capt,
            tons,
            dep,
            dep_port,
            arr,
            dest,
            armada_yr,
            fleet_cmd,
            fate,
            particulars,
        ) = row
        voyages.append(
            {
                "voyage_id": f"carreira:{num:04d}",
                "ship_name": ship,
                "captain": capt,
                "tonnage": tons,
                "departure_date": dep,
                "departure_port": dep_port,
                "arrival_date": arr,
                "destination_port": dest,
                "armada_year": armada_yr,
                "fleet_commander": fleet_cmd,
                "fate": fate,
                "particulars": particulars,
                "archive": ARCHIVE,
                "is_curated": True,
            }
        )

    # Expand to ~500 with programmatically generated fleet voyages
    start_id = len(VOYAGES_RAW) + 1
    expanded = _expand_voyages(voyages, start_id, target_total=500)
    voyages.extend(expanded)

    return voyages


# ---------------------------------------------------------------------------
# Wreck data — ~100 curated Carreira da India wreck records
# ---------------------------------------------------------------------------
# Each tuple: (num, voyage_id, ship, loss_date, loss_cause, loss_location,
#               region, status, lat, lon, unc_km, depth_m, tonnage, particulars)
WRECKS_RAW = [
    (
        1,
        "carreira:0034",
        "Sao Joao",
        "1552-06-11",
        "storm",
        "Natal coast, South Africa",
        "cape",
        "unfound",
        -31.0,
        30.2,
        50,
        None,
        400,
        "One of the most famous Portuguese shipwrecks. Captain Sepulveda, "
        "his wife Leonor, and children died during the overland march. "
        "Central to the Historia Tragico-Maritima.",
    ),
    (
        2,
        "carreira:0035",
        "Sao Bento",
        "1554-04-22",
        "storm",
        "Msikaba River, Natal coast, South Africa",
        "cape",
        "unfound",
        -31.5,
        29.8,
        30,
        None,
        500,
        "Wrecked on the Natal coast. Survivors endured months of overland "
        "march to reach Mozambique. Account by Manuel de Mesquita Perestrelo "
        "published in the Historia Tragico-Maritima.",
    ),
    (
        3,
        "carreira:0021",
        "Flor de la Mar",
        "1511-11-20",
        "storm",
        "off northeast coast of Sumatra",
        "southeast_asia",
        "unfound",
        5.35,
        97.50,
        50,
        None,
        400,
        "Possibly the richest shipwreck in history. Carried the treasure "
        "of the Sultan of Malacca after Albuquerque's conquest, including "
        "perhaps 60 tons of gold. Albuquerque barely escaped. Despite "
        "many search expeditions, she remains unfound.",
    ),
    (
        4,
        "carreira:0050",
        "Madre de Deus",
        "1592-08-03",
        "captured",
        "off the Azores, Atlantic Ocean",
        "atlantic",
        "unfound",
        38.5,
        -28.5,
        20,
        None,
        1600,
        "Captured by English fleet including Sir Walter Raleigh's ships. "
        "Her enormous cargo of pepper, cloves, cinnamon, silk, calico, "
        "gold, silver, pearls, and jewels was worth half the English "
        "Treasury. This capture directly inspired the founding of the EIC.",
    ),
    (
        5,
        "carreira:0006",
        "Anunciada",
        "1500-05-24",
        "storm",
        "off the Cape of Good Hope",
        "cape",
        "unfound",
        -35.0,
        20.0,
        200,
        None,
        300,
        "Lost rounding the Cape in Cabral's fleet (1500). Part of the "
        "same storm that killed Bartolomeu Dias. All hands lost.",
    ),
    (
        6,
        "carreira:0007",
        "Nau de Vasco de Ataide",
        "1500-03-25",
        "storm",
        "Atlantic Ocean, south of the equator",
        "atlantic",
        "unfound",
        -10.0,
        -25.0,
        500,
        None,
        250,
        "Disappeared in the Atlantic in Cabral's fleet. Exact location "
        "unknown. Bartolomeu Dias, discoverer of the Cape, also perished "
        "when another ship sank in the same storm.",
    ),
    (
        7,
        "carreira:0018",
        "Nau de Jorge de Aguiar",
        "1508-09-15",
        "storm",
        "near Mozambique Island, East Africa",
        "indian_ocean",
        "unfound",
        -15.0,
        40.5,
        100,
        None,
        500,
        "Fleet commander Aguiar's ship lost in a storm near Mozambique.",
    ),
    (
        8,
        "carreira:0037",
        "Sao Paulo",
        "1561-01-28",
        "grounding",
        "reef off Sumatra",
        "southeast_asia",
        "unfound",
        2.0,
        100.0,
        50,
        None,
        500,
        "Wrecked on a reef off Sumatra in 1561. Survivors built a boat "
        "from the wreckage -- one of the great survival stories of the era.",
    ),
    (
        9,
        "carreira:0048",
        "Santo Alberto",
        "1593-03-24",
        "grounding",
        "Natal coast near Umtata River, South Africa",
        "cape",
        "unfound",
        -31.6,
        29.5,
        30,
        None,
        700,
        "Wrecked on the return voyage from India. Another Natal coast wreck "
        "from the Historia Tragico-Maritima.",
    ),
    (
        10,
        "carreira:0051",
        "Chagas",
        "1594-06-29",
        "fire",
        "near the Azores, Atlantic Ocean",
        "atlantic",
        "unfound",
        38.0,
        -29.0,
        30,
        None,
        2000,
        "Enormous 2,000-ton carrack attacked by English raiders. Caught "
        "fire and exploded. Over 600 died. One of the greatest maritime "
        "disasters of the era.",
    ),
    (
        11,
        "carreira:0054",
        "Nossa Senhora dos Martires",
        "1606-09-14",
        "storm",
        "mouth of the Tagus, near Sao Juliao da Barra",
        "atlantic",
        "found",
        38.67,
        -9.32,
        1,
        10,
        600,
        "Wrecked almost within sight of Lisbon at the Tagus bar. "
        "Archaeologically excavated in 1996-2001. Important source of "
        "information on Carreira cargo and ship construction.",
    ),
    (
        12,
        "carreira:0061",
        "Nossa Senhora do Carmo",
        "1624-07-20",
        "storm",
        "Mozambique Channel",
        "indian_ocean",
        "unfound",
        -14.0,
        41.0,
        100,
        None,
        700,
        "Lost in a storm in the Mozambique Channel.",
    ),
    (
        13,
        "carreira:0062",
        "Sao Goncalo",
        "1630-08-05",
        "storm",
        "Natal coast, South Africa",
        "cape",
        "unfound",
        -30.5,
        30.5,
        40,
        None,
        600,
        "Wrecked on the Natal coast. Yet another tragedy of the South "
        "African coast. Account in the Historia Tragico-Maritima.",
    ),
    (
        14,
        "carreira:0063",
        "Sacramento",
        "1647-06-30",
        "storm",
        "Schoenmakerskop, near Port Elizabeth, South Africa",
        "cape",
        "found",
        -33.98,
        25.80,
        2,
        8,
        800,
        "Wrecked off Schoenmakerskop. One of the earliest South African "
        "wreck sites to be archaeologically investigated (1977).",
    ),
    (
        15,
        "carreira:0068",
        "Santissimo Sacramento",
        "1668-06-26",
        "storm",
        "near Mozambique Island",
        "indian_ocean",
        "approximate",
        -15.05,
        40.70,
        10,
        15,
        700,
        "Major warship/cargo vessel lost near Mozambique. The wreck site "
        "has been approximately located.",
    ),
    (
        16,
        "carreira:0081",
        "Sao Jose",
        "1756-11-15",
        "storm",
        "off Lisbon",
        "atlantic",
        "unfound",
        38.6,
        -9.4,
        20,
        None,
        400,
        "Lost in the aftermath of the Great Lisbon Earthquake (1755). "
        "Harbor infrastructure destroyed.",
    ),
    (
        17,
        "carreira:0092",
        "Sao Pedro de Alcantara",
        "1786-02-02",
        "storm",
        "off Peniche, Portugal",
        "atlantic",
        "found",
        39.37,
        -9.40,
        1,
        15,
        600,
        "Wrecked off Peniche on the Portuguese coast. Cargo included "
        "valuables from Goa. Wreck located and studied.",
    ),
    (
        18,
        "carreira:0094",
        "Sao Jose Indiano",
        "1798-12-27",
        "storm",
        "off the Cape of Good Hope",
        "cape",
        "found",
        -34.20,
        18.30,
        2,
        12,
        350,
        "Slave ship wrecked off the Cape of Good Hope. Archaeological "
        "excavation (2010-2015) recovered the first known slave ship "
        "artifacts from the Carreira.",
    ),
    (
        19,
        "carreira:0098",
        "Santo Antonio",
        "1806-06-15",
        "captured",
        "off the Canary Islands, Atlantic",
        "atlantic",
        "unfound",
        28.0,
        -16.0,
        50,
        None,
        300,
        "Captured by a French privateer during the Napoleonic Wars.",
    ),
    (
        20,
        "carreira:0114",
        "Cinco Chagas",
        "1559-07-15",
        "storm",
        "near the Azores, Atlantic",
        "atlantic",
        "unfound",
        38.0,
        -28.0,
        50,
        None,
        1500,
        "Enormous carrack lost near the Azores. One of the largest ships "
        "afloat at the time. Significant cargo of spices and valuables.",
    ),
    (
        21,
        "carreira:0115",
        "Santa Maria de Deus",
        "1600-04-20",
        "captured",
        "near Saint Helena Island, South Atlantic",
        "south_atlantic",
        "unfound",
        -16.0,
        -5.7,
        30,
        None,
        900,
        "Captured by the Dutch near Saint Helena. One of the early Dutch "
        "seizures of Carreira ships, foreshadowing the loss of the spice trade.",
    ),
    (
        22,
        None,
        "Santiago",
        "1585-09-01",
        "storm",
        "Bassas da India, Mozambique Channel",
        "indian_ocean",
        "unfound",
        -21.5,
        39.7,
        15,
        None,
        600,
        "Wrecked on the Bassas da India atoll, a treacherous low-lying reef "
        "in the Mozambique Channel. Many Carreira ships lost here.",
    ),
    (
        23,
        None,
        "Sao Tome",
        "1589-04-15",
        "storm",
        "Natal coast, South Africa",
        "cape",
        "unfound",
        -31.2,
        30.0,
        40,
        None,
        500,
        "Another ship lost on the treacherous Natal coast.",
    ),
    (
        24,
        None,
        "Nossa Senhora da Candelaria",
        "1606-07-20",
        "grounding",
        "shoals off Mozambique",
        "indian_ocean",
        "unfound",
        -13.5,
        41.5,
        30,
        None,
        500,
        "Wrecked on shoals near the coast of Mozambique.",
    ),
    (
        25,
        None,
        "Sao Francisco",
        "1614-08-22",
        "storm",
        "off the coast of East Africa",
        "indian_ocean",
        "unfound",
        -10.0,
        42.0,
        100,
        None,
        400,
        "Lost in a cyclone in the Indian Ocean.",
    ),
    (
        26,
        None,
        "Bom Jesus",
        "1533-04-16",
        "storm",
        "off the coast of Namibia, near Oranjemund",
        "south_atlantic",
        "found",
        -28.63,
        16.43,
        1,
        5,
        300,
        "The 'Diamond Shipwreck' discovered in 2008 during diamond mining "
        "operations. Found with gold coins, copper ingots, elephant tusks, "
        "and personal effects. Remarkably well preserved.",
    ),
    (
        27,
        None,
        "Santa Maria da Barca",
        "1559-09-01",
        "storm",
        "Bassas da India, Mozambique Channel",
        "indian_ocean",
        "unfound",
        -21.5,
        39.8,
        20,
        None,
        700,
        "Lost on the Bassas da India atoll.",
    ),
    (
        28,
        None,
        "Sao Joao Baptista",
        "1622-05-20",
        "storm",
        "off Mombasa, East Africa",
        "indian_ocean",
        "unfound",
        -4.0,
        39.7,
        30,
        None,
        600,
        "Lost in a storm off the coast of Mombasa.",
    ),
    (
        29,
        None,
        "Nossa Senhora da Luz",
        "1615-03-10",
        "fire",
        "near Mozambique Island",
        "indian_ocean",
        "unfound",
        -15.0,
        40.8,
        20,
        None,
        500,
        "Caught fire and burned near Mozambique Island.",
    ),
    (
        30,
        None,
        "Sao Bartholomeu",
        "1570-08-14",
        "storm",
        "Table Bay, Cape of Good Hope",
        "cape",
        "unfound",
        -33.9,
        18.4,
        10,
        None,
        400,
        "Lost in Table Bay. The Cape was a frequent location for shipwrecks.",
    ),
    (
        31,
        None,
        "Garca",
        "1559-06-01",
        "grounding",
        "off Sofala, Mozambique",
        "indian_ocean",
        "unfound",
        -20.0,
        35.0,
        30,
        None,
        300,
        "Wrecked on the coast near Sofala.",
    ),
    (
        32,
        None,
        "Santa Clara",
        "1564-09-15",
        "storm",
        "near Madagascar",
        "indian_ocean",
        "unfound",
        -12.0,
        49.0,
        100,
        None,
        500,
        "Lost in a cyclone near northern Madagascar.",
    ),
    (
        33,
        None,
        "Sao Lourenco",
        "1649-07-10",
        "storm",
        "Mozambique Channel",
        "indian_ocean",
        "unfound",
        -16.0,
        42.0,
        50,
        None,
        500,
        "Lost in the Mozambique Channel during monsoon.",
    ),
    (
        34,
        None,
        "Nossa Senhora do Rosario",
        "1580-05-25",
        "storm",
        "off Cape Correntes, Mozambique",
        "indian_ocean",
        "unfound",
        -23.5,
        35.5,
        30,
        None,
        600,
        "Lost near Cape Correntes, one of the most dangerous points on the Mozambique coast.",
    ),
    (
        35,
        None,
        "Sao Antonio",
        "1527-08-18",
        "grounding",
        "near Mombasa, East Africa",
        "indian_ocean",
        "unfound",
        -4.0,
        39.5,
        20,
        None,
        300,
        "Early Carreira wreck off the East African coast.",
    ),
    (
        36,
        None,
        "Conceicao",
        "1555-07-22",
        "storm",
        "Natal coast, South Africa",
        "cape",
        "unfound",
        -30.0,
        31.0,
        40,
        None,
        400,
        "Yet another Natal coast wreck. The stretch between the "
        "Cape and Mozambique was the most dangerous part of the route.",
    ),
    (
        37,
        None,
        "Sao Bento Novo",
        "1640-11-15",
        "storm",
        "off the Cape of Good Hope",
        "cape",
        "unfound",
        -34.5,
        19.0,
        50,
        None,
        500,
        "Lost near the Cape of Good Hope in a winter storm.",
    ),
    (
        38,
        None,
        "Nossa Senhora de Belem",
        "1635-06-20",
        "grounding",
        "reefs near Inhambane, Mozambique",
        "indian_ocean",
        "unfound",
        -23.8,
        35.4,
        20,
        None,
        600,
        "Wrecked on reefs near Inhambane on the Mozambique coast.",
    ),
    (
        39,
        None,
        "Sao Marcos",
        "1708-09-01",
        "storm",
        "off Madagascar",
        "indian_ocean",
        "unfound",
        -13.0,
        48.0,
        80,
        None,
        400,
        "Lost during cyclone season near Madagascar.",
    ),
    (
        40,
        None,
        "Nau de Bartolomeu Dias",
        "1500-05-24",
        "storm",
        "off the Cape of Good Hope",
        "cape",
        "unfound",
        -35.0,
        21.0,
        200,
        None,
        250,
        "Ship of Bartolomeu Dias, first European to round the Cape in 1488. "
        "He perished in the same storm that struck Cabral's fleet in 1500, "
        "a tragic irony: the man who discovered the Cape route died there.",
    ),
]


# Wreck location templates for programmatic expansion along the Carreira route
_WRECK_LOCATIONS = [
    ("off the Cape of Good Hope", "cape", -34.5, 19.0, 50),
    ("Natal coast, South Africa", "cape", -30.5, 30.5, 40),
    ("Mozambique Channel", "indian_ocean", -16.0, 42.0, 80),
    ("near Mozambique Island", "indian_ocean", -15.0, 40.7, 30),
    ("off Cape Correntes, Mozambique", "indian_ocean", -23.5, 35.5, 30),
    ("reefs off Sofala, Mozambique", "indian_ocean", -20.0, 35.0, 25),
    ("Bassas da India, Mozambique Channel", "indian_ocean", -21.5, 39.7, 15),
    ("near Madagascar", "indian_ocean", -13.0, 48.0, 100),
    ("off the Azores, Atlantic", "atlantic", 38.0, -28.0, 50),
    ("off Lisbon, Portugal", "atlantic", 38.7, -9.4, 20),
    ("Bay of Biscay", "atlantic", 45.0, -5.0, 80),
    ("off the Canary Islands", "atlantic", 28.0, -16.0, 40),
    ("Table Bay, Cape of Good Hope", "cape", -33.9, 18.4, 10),
    ("near Mombasa, East Africa", "indian_ocean", -4.0, 39.7, 30),
    ("off Goa, India", "indian_ocean", 15.4, 73.8, 15),
]

_WRECK_CAUSES = ["storm", "storm", "storm", "grounding", "grounding", "fire", "captured"]
_WRECK_CONTEXTS = [
    "Lost on the treacherous passage around the Cape of Good Hope.",
    "Wrecked on the coast during monsoon season.",
    "Driven ashore in a storm. Crew took to the boats.",
    "Struck an uncharted reef and foundered rapidly.",
    "Caught fire in the holds. Crew abandoned ship.",
    "Lost in heavy seas. Position approximate.",
    "Overwhelmed by a cyclone in the Mozambique Channel.",
]


def _expand_wrecks(
    curated_wrecks: list[dict],
    voyages: list[dict],
    start_id: int,
    target_total: int,
) -> list[dict]:
    """Generate additional wreck records from wrecked/captured voyages."""
    # Find wrecked/captured voyages that don't already have a wreck entry
    curated_vids = {w.get("voyage_id") for w in curated_wrecks if w.get("voyage_id")}
    wrecked_voyages = [
        v
        for v in voyages
        if v["fate"] in ("wrecked", "captured", "missing") and v["voyage_id"] not in curated_vids
    ]

    expanded = []
    wid = start_id

    for v in wrecked_voyages:
        if wid > target_total:
            break

        year = v.get("armada_year", 1600)
        loc_idx = (year * 7 + wid * 3) % len(_WRECK_LOCATIONS)
        loc_name, region, lat, lon, unc = _WRECK_LOCATIONS[loc_idx]

        cause_idx = (year * 11 + wid * 5) % len(_WRECK_CAUSES)
        cause = _WRECK_CAUSES[cause_idx]
        if v["fate"] == "captured":
            cause = "captured"

        ctx_idx = (year * 13 + wid * 7) % len(_WRECK_CONTEXTS)
        context = _WRECK_CONTEXTS[ctx_idx]

        # Loss date: approximate from departure date
        dep = v.get("departure_date", f"{year}-06-15")
        loss_month = int(dep[5:7]) + 2 + (wid % 4)
        loss_year = year
        if loss_month > 12:
            loss_month -= 12
            loss_year += 1
        loss_day = 5 + (wid * 3) % 23
        loss_date = f"{loss_year}-{loss_month:02d}-{loss_day:02d}"

        expanded.append(
            {
                "wreck_id": f"carreira_wreck:{wid:04d}",
                "voyage_id": v["voyage_id"],
                "ship_name": v["ship_name"],
                "loss_date": loss_date,
                "loss_cause": cause,
                "loss_location": loc_name,
                "region": region,
                "status": "unfound",
                "position": {
                    "lat": lat + ((wid * 7) % 20 - 10) * 0.1,
                    "lon": lon + ((wid * 11) % 20 - 10) * 0.1,
                    "uncertainty_km": unc,
                },
                "depth_estimate_m": None,
                "tonnage": v.get("tonnage", 400),
                "archive": ARCHIVE,
                "particulars": context,
                "is_curated": False,
            }
        )
        wid += 1

    return expanded


def build_wrecks(voyages: list[dict] | None = None) -> list[dict]:
    """Return ~100 Carreira da India wreck records (curated + expanded)."""
    wrecks = []
    for row in WRECKS_RAW:
        (
            num,
            vid,
            ship,
            loss_date,
            cause,
            location,
            region,
            status,
            lat,
            lon,
            unc,
            depth,
            tons,
            particulars,
        ) = row
        wrecks.append(
            {
                "wreck_id": f"carreira_wreck:{num:04d}",
                "voyage_id": vid,
                "ship_name": ship,
                "loss_date": loss_date,
                "loss_cause": cause,
                "loss_location": location,
                "region": region,
                "status": status,
                "position": {"lat": lat, "lon": lon, "uncertainty_km": unc},
                "depth_estimate_m": depth,
                "tonnage": tons,
                "archive": ARCHIVE,
                "particulars": particulars,
                "is_curated": True,
            }
        )

    # Expand wrecks from wrecked/captured expanded voyages
    if voyages:
        start_id = len(WRECKS_RAW) + 1
        expanded = _expand_wrecks(wrecks, voyages, start_id, target_total=100)
        wrecks.extend(expanded)

    return wrecks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = parse_args("Generate Portuguese Carreira da India data")

    print("=" * 60)
    print("Carreira da India Data Generation -- chuk-mcp-maritime-archives")
    print("=" * 60)
    print(f"\nData directory: {DATA_DIR}\n")

    if not args.force and is_cached(VOYAGES_OUTPUT, args.cache_max_age):
        print(f"Using cached {VOYAGES_OUTPUT.name} (use --force to regenerate)")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # -- Voyages --
    print("Step 1: Generating Carreira voyage records ...")
    voyages = build_voyages()
    with open(VOYAGES_OUTPUT, "w") as f:
        json.dump(voyages, f, indent=2, ensure_ascii=False)
    print(f"  {VOYAGES_OUTPUT}")
    print(f"  {len(voyages)} voyages written ({VOYAGES_OUTPUT.stat().st_size:,} bytes)")

    # Validate
    expected_ids = {f"carreira:{i:04d}" for i in range(1, len(voyages) + 1)}
    actual_ids = {v["voyage_id"] for v in voyages}
    assert expected_ids == actual_ids, f"ID mismatch: {expected_ids - actual_ids}"
    for v in voyages:
        assert v["archive"] == ARCHIVE

    fates = {}
    for v in voyages:
        fates[v["fate"]] = fates.get(v["fate"], 0) + 1
    print(f"  Fate breakdown: {fates}")

    dates = [v["departure_date"] for v in voyages if v.get("departure_date")]
    print(f"  Date range: {min(dates)} to {max(dates)}")

    armada_years = [v["armada_year"] for v in voyages if v.get("armada_year")]
    print(f"  Armada years: {min(armada_years)} to {max(armada_years)}")

    # -- Wrecks --
    print("\nStep 2: Generating Carreira wreck records ...")
    wrecks = build_wrecks(voyages)
    with open(WRECKS_OUTPUT, "w") as f:
        json.dump(wrecks, f, indent=2, ensure_ascii=False)
    print(f"  {WRECKS_OUTPUT}")
    print(f"  {len(wrecks)} wrecks written ({WRECKS_OUTPUT.stat().st_size:,} bytes)")

    expected_wids = {f"carreira_wreck:{i:04d}" for i in range(1, len(wrecks) + 1)}
    actual_wids = {w["wreck_id"] for w in wrecks}
    assert expected_wids == actual_wids, f"Wreck ID mismatch: {expected_wids - actual_wids}"
    for w in wrecks:
        assert w["archive"] == ARCHIVE

    causes = {}
    for w in wrecks:
        causes[w["loss_cause"]] = causes.get(w["loss_cause"], 0) + 1
    print(f"  Loss causes: {causes}")

    regions = {}
    for w in wrecks:
        regions[w["region"]] = regions.get(w["region"], 0) + 1
    print(f"  Regions: {regions}")

    print(f"\n{'=' * 60}")
    print("Carreira da India data generation complete!")
    print(f"  Voyages: {len(voyages)} records")
    print(f"  Wrecks:  {len(wrecks)} records")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

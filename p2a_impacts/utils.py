import requests
import csv
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

csv.field_size_limit(1_000_000)

REGIONS = {
    "bc": "British Columbia",
    "alberni_clayoquot": "Alberni-Clayoquot",
    "boreal_plains": "Boreal Plains",
    "bulkley_nechako": "Bulkley-Nechako",
    "capital": "Capital",
    "cariboo": "Cariboo",
    "central_coast": "Central Coast",
    "central_kootenay": "Central Kootenay",
    "central_okanagan": "Central Okanagan",
    "columbia_shuswap": "Columbia-Shuswap",
    "comox_valley": "Comox Valley",
    "cowichan_valley": "Cowichan Valley",
    "east_kootenay": "East Kootenay",
    "fraser_fort_george": "Fraser-Fort George",
    "fraser_valley": "Fraser Valley",
    "greater_vancouver": "Greater Vancouver",
    "kitimat_stikine": "Kitimat-Stikine",
    "kootenay_boundary": "Kootenay Boundary",
    "mt_waddington": "Mount Waddington",
    "nanaimo": "Nanaimo",
    "northern_rockies": "Northern Rockies",
    "north_okanagan": "North Okanagan",
    "okanagan_similkameen": "Okanagan-Similkameen",
    "peace_river": "Peace River",
    "powell_river": "Powell River",
    "skeena_queen_charlotte": "Skeena-Queen Charlotte",
    "squamish_lillooet": "Squamish-Lillooet",
    "stikine": "Stikine",
    "strathcona": "Strathcona",
    "sunshine_coast": "Sunshine Coast",
    "thompson_nicola": "Thompson-Nicola",
    "interior": "Interior",
    "northern": "Northern",
    "vancouver_coast": "Vancouver Coast",
    "vancouver_fraser": "Vancouver Fraser",
    "vancouver_island": "Vancouver Island",
    "central_interior": "Central Interior",
    "coast_and_mountains": "Coast and Mountains",
    "georgia_depression": "Georgia Depression",
    "northern_boreal_mountains": "Northern Boreal Mountains",
    "southern_interior": "Southern Interior",
    "southern_interior_mountains": "Southern Interior Mountains",
    "sub_boreal_mountains": "Sub Boreal Mountains",
    "taiga_plains": "Taiga Plains",
    "cariboo": "Cariboo",
    "kootenay_/_boundary": "Kootenay / Boundary",
    "northeast": "Northeast",
    "omineca": "Omineca",
    "skeena": "Skeena",
    "south_coast": "South Coast",
    "thompson_okanagan": "Thompson / Okanagan",
    "west_coast": "West Coast",
    "vic_test": "Vic Test",
    "algonquian": "Algonquian",
    "athabaskan-eyak-tlingit": "Athabaskan-Eyak-Tlingit",
    "coast_salish": "Coast Salish",
    "haida": "Haida",
    "interior_salish": "Interior Salish",
    "ktunaxa": "Ktunaxa",
    "tsimshianic": "Tsimshianic",
    "wakashan": "Wakashan",
    "babine-witsuwiten": "Babine-Witsuwit'en",
    "beaver_dene": "Beaver Dene",
    "bella_bella": "Bella Bella",
    "bella_coola": "Bella Coola",
    "carrier_dene": "Carrier Dene",
    "chilcotin": "Chilcotin",
    "coast_tsimshian": "Coast Tsimshian",
    "comox-sliammon": "Comox-Sliammon",
    "ditidaht": "Ditidaht",
    "gitksan": "Gitksan",
    "halkomelem": "Halkomelem",
    "inland_tlingit": "Inland Tlingit",
    "kaska_dene": "Kaska Dene",
    "kitimat": "Kitimat",
    "kootenay": "Kootenay",
    "kwakiutl": "Kwakiutl",
    "lake_babine_nadoten": "Lake Babine Nadot’en",
    "lillooet": "Lillooet",
    "nishga": "Nishga",
    "northern_straits_salish": "Northern Straits Salish",
    "nuu-chah-nulth": "Nuu-chah-nulth",
    "okanagan": "Okanagan",
    "oweekala": "Oweek’ala",
    "plains_cree": "Plains Cree",
    "sechelt": "Sechelt",
    "sekani": "Sekani",
    "shuswap": "Shuswap",
    "slavey": "Slavey",
    "southern_tutchone": "Southern Tutchone",
    "squamish": "Squamish",
    "tahltan": "Tahltan",
    "thompson": "Thompson",
    "tlingit": "Tlingit",
}


def get_region(region_name, url):
    """Given a region name and URL retrieve a csv row from Geoserver

    The region_name variable should be a selection from the REGIONS
    dictionary object.  This object contains all the options available in
    Geoserver.

    The URL in the default case is for the Geoserver instance running on
    docker-dev01.

    The return value from this method is a csv row output from
    Geoserver.  The row contains several columns but the ones used are
    coast_bool and WKT.  These contain whether or not the region is coastal
    and the polygon describing the region respectively.
    """
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typename": "bc_regions:BC-regions-FNLF-84",
        "maxFeatures": "100",
        "outputFormat": "csv",
    }
    data = requests.get(url, params=params)

    decoded_data = data.content.decode("utf-8")
    csv_data = csv.DictReader(decoded_data.splitlines(), delimiter=",")

    region = REGIONS[region_name]

    for row in csv_data:
        if row["english_na"] == region:
            return row


def setup_logging(log_level):
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger("scripts")
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level))
    return logger


def create_session(connection_string):
    """Given a database connection URL, create a session object to be used
    for resolve_rules.
    """
    Session = sessionmaker(create_engine(connection_string))
    sesh = Session()
    return sesh

'''
The purpose of this script is to run the rule resolver with some parameters
that could be expected from the p2a front end.
'''
import requests
from argparse import ArgumentParser
import csv

from resolver import resolve_rules


regions = {
    'bc': 'British Columbia',
    'alberni_clayoquot': 'Alberni-Clayoquot',
    'boreal_plains': 'Boreal Plains',
    'bulkley_nechako': 'Bulkley-Nechako',
    'capital': 'Capital',
    'cariboo': 'Cariboo',
    'central_coast': 'Central Coast',
    'central_kootenay': 'Central Kootenay',
    'central_okanagan': 'Central Okanagan',
    'columbia_shuswap': 'Columbia-Shuswap',
    'comox_valleyecaus': 'Comox Valleyecaus',
    'cowichan_valley': 'Cowichan Valley',
    'east_kootenay': 'East Kootenay',
    'fraser_fort_george': 'Fraser-Fort George',
    'fraser_valley': 'Fraser Valley',
    'greater_vancouver': 'Greater Vancouver',
    'kitimat_stikine': 'Kitimat-Stikine',
    'kootenay_boundary': 'Kootenay Boundary',
    'mt_waddington': 'Mount Waddington',
    'nanaimo': 'Nanaimo',
    'northern_rockies': 'Northern Rockies',
    'north_okanagan': 'North Okanagan',
    'okanagan_similkameen': 'Okanagan-Similkameen',
    'peace_river': 'Peace River',
    'powell_river': 'Powell River',
    'skeena_queen_charlotte': 'Skeena-Queen Charlotte',
    'squamish_lillooet': 'Squamish-Lillooet',
    'stikine': 'Stikine',
    'strathcona': 'Strathcona',
    'sunshine_coast': 'Sunshine Coast',
    'thompson_nicola': 'Thompson-Nicola',
    'interior': 'Interior',
    'northern': 'Northern',
    'vancouver_coast': 'Vancouver Coast',
    'vancouver_fraser': 'Vancouver Fraser',
    'vancouver_island': 'Vancouver Island',
    'central_interior': 'Central Interior',
    'coast_and_mountains': 'Coast and Mountains',
    'georgia_depression': 'Georgia Depression',
    'northern_boreal_mountains': 'Northern Boreal Mountains',
    'southern_interior': 'Southern Interior',
    'southern_interior_mountains': 'Southern Interior Mountains',
    'sub_boreal_mountains': 'Sub Boreal Mountains',
    'taiga_plains': 'Taiga Plains',
    'cariboo': 'Cariboo',
    'kootenay_/_boundary': 'Kootenay / Boundary',
    'northeast': 'Northeast',
    'omineca': 'Omineca',
    'skeena': 'Skeena',
    'south_coast': 'South Coast',
    'thompson_okanagan': 'Thompson / Okanagan',
    'west_coast': 'West Coast'
}


def get_region(region_name, url):
    params = {
        'service': 'WFS',
        'version': '1.0.0',
        'request': 'GetFeature',
        'typename': 'bc_regions:bc-regions-polygon',
        'maxFeatures': '100',
        'outputFormat': 'csv'
    }
    data = requests.get(url, params=params)

    decoded_data = data.content.decode('utf-8')
    csv_data = csv.DictReader(decoded_data.splitlines(), delimiter=',')

    region = regions[region_name]

    for row in csv_data:
        if row['english_na'] == region:
            return row


def pretty_print(rules):
    print('{')
    for rule, result in rules.items():
        print('\t{}: {}'.format(rule, result))
    print('}')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-c', '--csv', help='CSV file containing rules',
                        required=True)
    parser.add_argument('-d', '--date-range', help='30 year period for data',
                        required=True)
    parser.add_argument('-r', '--region', help='Selected region',
                        required=True, choices=regions.keys())
    parser.add_argument('-u', '--url', help='Geoserver URL', required=True,
                        default="http://docker-dev01.pcic.uvic.ca:30123/geoserver/bc_regions/ows")
    parser.add_argument('-l', '--log-level', help='Logging level',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR',
                                 'CRITICAL'],
                        default='INFO')
    args = parser.parse_args()
    region = get_region(args.region, args.url)

    if not region:
        raise Exception('{} region was not found'.format(args.region))

    rules = resolve_rules(args.csv, args.date_range, region, args.log_level)
    pretty_print(rules)

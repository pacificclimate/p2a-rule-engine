'''
The purpose of this script is to run the rule resolver with some parameters
that could be expected from the p2a front end.
'''
import requests
from argparse import ArgumentParser
import csv

from p2a_impacts.resolver import resolve_rules


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
    'comox_valley': 'Comox Valley',
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
    '''Given a region name and URL retrieve a csv row from Geoserver

       The region_name variable should be a selection from the regions
       dictionary object.  This object contains all the options available in
       Geoserver.

       The URL in the default case is for the Geoserver instance running on
       docker-dev01.

       The return value from this method is a csv row output from
       Geoserver.  The row contains several columns but the ones used are
       coast_bool and WKT.  These contain whether or not the region is coastal
       and the polygon describing the region respectively.
    '''
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
    '''Display the result of the rule resolver'''
    print('{')
    for rule, result in rules.items():
        print('\t{}: {}'.format(rule, result))
    print('}')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-c', '--csv', help='CSV file containing rules',
                        required=True)
    parser.add_argument('-d', '--date-range', help='30 year period for data',
                        choices=['2020', '2050', '2080'],
                        default='2080', required=False)
    parser.add_argument('-r', '--region', help='Selected region',
                        required=True, choices=regions.keys())
    parser.add_argument('-u', '--url', help='Geoserver URL',
                        default="http://docker-dev01.pcic.uvic.ca:30123/geoserver/bc_regions/ows")
    parser.add_argument('-x', '--connection-string',
                        help='Database connection string',
                        default='postgres://ce_meta_ro@db3.pcic.uvic.ca/ce_meta')
    parser.add_argument('-e', '--ensemble',
                        help='Ensemble name filter for data files',
                        default='p2a_files')
    parser.add_argument('-l', '--log-level', help='Logging level',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR',
                                 'CRITICAL'],
                        default='INFO')
    args = parser.parse_args()
    region = get_region(args.region, args.url)

    if not region:
        raise Exception('{} region was not found'.format(args.region))

    rules = resolve_rules(args.csv, args.date_range, region, args.ensemble,
                          args.connection_string, args.log_level)
    pretty_print(rules)

# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

import time
import os
import itertools
from pathlib import Path
import sys
import ast
import re
# import threading


# https://www.google.com/flights?hl=en#flt={DEPART CODE}.{DEST CODE}.{DEPART DATE (YYYY-MM-DD)}*{DEST CODE}.{DEPART CODE}.{RETURN DATE (YYYY-MM-DD)};c:{CURRENCY (EUR or USD)};e:1;{MAX NUMBER OF STOPS (s:1*1;)}{MAX STOPOVER TIME (ld:-180*-180;)}{DEPART TIME (dt:1500-2400;)}sd:1;t:f

URL_TEMPLATE = 'https://www.google.com/flights?hl=en#flt={DEPART CODE}'
URL_TEMPLATE += '.{DEST CODE}.{DEPART DATE (YYYY-MM-DD)}*{DEST CODE}.{DEPART CODE}'
URL_TEMPLATE += '.{RETURN DATE (YYYY-MM-DD)};c:{CURRENCY (EUR or USD)};e:1;'
URL_TEMPLATE += '{MAX NUMBER OF STOPS (s:1*1;)}{MAX STOPOVER TIME (ld:-180*-180;)}'
URL_TEMPLATE += '{DEPART TIME (dt:1500-2400;)}sd:1;t:f'

LOCATION_CODES = {
    'Cork': 'ORK',
    'Dublin': 'DUB',
    'Amsterdam-ANY': '/m/0k3p',
    'Prague-ANY': '/m/05ywg',
    'Budapest': 'BUD',
    'Bucharest': 'OTP',
    'Rome': '/m/06c62',
    'Porto': 'OPO',
    'Florence': '/m/031y2',
    'Athens': 'ATH',
    'Barcelona': '/m/01f62',
    'Seville': 'SVQ',
    'Madrid': 'MAD',
}

CURRENCY_CHOICES = ['EUR', 'USD']

MAX_NUMBER_STOPS = {
    1: 's:1*1;'
}
# Max stopovers in minutes
MAX_STOPOVER_TIMES = {
    180: 'ld:-180*-180;'
}

    
def build_all_urls(unique_schedules, currency, 
                    max_stopovers, max_stopover_time, 
                    departure_time_range_start, 
                    departure_time_range_end):
    all_urls = []
    for combo in unique_schedules:
        for trip in combo:
            if not('xxxNONExxx' in trip['dest']):
                builder_url = trip['url']
                trip['url'] = (builder_url.replace('{DEPART CODE}', trip['orig'])
                    .replace('{DEST CODE}', trip['dest'])
                    .replace('{DEPART DATE (YYYY-MM-DD)}', trip['depart_date'])
                    .replace('{RETURN DATE (YYYY-MM-DD)}', trip['return_date'])
                    .replace('{CURRENCY (EUR or USD)}', currency)
                    .replace('{MAX NUMBER OF STOPS (s:1*1;)}', max_stopovers)
                    .replace('{MAX STOPOVER TIME (ld:-180*-180;)}', max_stopover_time)
                    .replace('{DEPART TIME (dt:1500-2400;)}', 
                        'dt:' + str(departure_time_range_start) + '-' + str(departure_time_range_end) + ';'
                    ))
                all_urls.append(trip['url'])
    return unique_schedules, list(set(all_urls))


def get_cheapest_prices(chrome_driver):
    cheapest_prices = {}
    number_of_windows = len(chrome_driver.window_handles)
    NOT_FOUND_TEXT = 'Oh dear – no results found!'
    print('Finding some of the cheapest prices (' + str(number_of_windows) + ')')
    for idx in range(number_of_windows):
        chrome_driver.switch_to.window(chrome_driver.window_handles[idx])
        try:
            if (NOT_FOUND_TEXT in chrome_driver.page_source):
                cheapest_prices[chrome_driver.current_url] = 999999
                print('.', end='', flush=True)
            else:
                element1 = WebDriverWait(chrome_driver, 20).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".flt-subhead1.gws-flights-results__price.gws-flights-results__cheapest-price")
                        )
                    )
                cheapest_prices[chrome_driver.current_url] = int(re.sub(r"\D", "", element1.text))
                print('.', end='', flush=True)
        except TimeoutException:
            if (NOT_FOUND_TEXT in chrome_driver.page_source):
                cheapest_prices[chrome_driver.current_url] = 999999
                print('.', end='', flush=True)
            else:
                print('Error', element1)


    return cheapest_prices


def openWebpages(all_possible_urls):
    # WebDriver setup
    # Windows
    # DRIVER_PATH = "C:\\Users\\carpe\\Desktop\\ChromeDriver\\chromedriver77"
    # Linux
    DRIVER_PATH = Path("/mnt/c/Users/carpe/Desktop/ChromeDriver/chromedriver77.exe")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    # chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # chrome_options.add_argument("--window-size=%s" % "1920,1080")
    
    windows_per_driver = 8
    
    print('Opening webpages')

    prices_dict = {}

    cur_url_idx = 0
    while (cur_url_idx < len(all_possible_urls)):
        driver = webdriver.Chrome(executable_path=DRIVER_PATH, options=chrome_options)
        driver.get(all_possible_urls[cur_url_idx])
        cur_url_idx += 1
        for i in range(1, windows_per_driver):
            if cur_url_idx < len(all_possible_urls):
                driver.execute_script("window.open('" + all_possible_urls[cur_url_idx] + "')")
                cur_url_idx += 1

        partial_prices = get_cheapest_prices(driver)
        prices_dict = {**prices_dict, **partial_prices}
        driver.quit()
    print('\nCheapest prices found')
    return prices_dict


def create_fixed_trips_fun(fixed_trips):
    def filter_fixed_trips(schedule):
        found_trips = []
        for fix in fixed_trips:
            found_trip = False
            for trip in schedule[0]:
                if (fix['dest'] == trip['dest'] and 
                    fix['depart_date'] == trip['depart_date'] and 
                    fix['return_date'] == trip['return_date']):
                    found_trip = True
            found_trips.append(found_trip)
        return all(found_trips)
    return filter_fixed_trips


# Best departing flights section
# gws-flights-results__best-flights
def pingGoogleFlights():
    # Inputs
    # sys.argv[1]
    # tmp_origin_locations = [
    #     'Dublin'
    # ]
    tmp_origin_locations = sys.argv[1]
    # sys.argv[2]
    # tmp_destination_locations = [
    #     'Porto',
    #     'Florence'
    # ]
    tmp_destination_locations = sys.argv[2]
    # sys.argv[3]
    # FIXED_TRIPS = [{
    #     'dest': 'Florence',
    #     'depart_date': '2019-11-14',
    #     'return_date': '2019-11-17'
    # },{
    #     'dest': 'Porto',
    #     'depart_date': '2019-10-31',
    #     'return_date': '2019-11-03'
    # }]
    FIXED_TRIPS = sys.argv[3]
    # tmp_origin_locations = [
    #     LOCATION_CODES['Cork'],
    #     LOCATION_CODES['Dublin']
    # ]
    # tmp_destination_locations = [
    #     LOCATION_CODES['Amsterdam-ANY'], 
    #     LOCATION_CODES['Prague-ANY'], 
    #     LOCATION_CODES['Porto'],
    #     LOCATION_CODES['Florence'],
    #     LOCATION_CODES['Madrid'],
    #     LOCATION_CODES['Bucharest'],
    #     LOCATION_CODES['Budapest'],
    #     LOCATION_CODES['Seville'],
    #     LOCATION_CODES['Barcelona']
    # ]
    # Travel dates example: [[depart, return],[depart, return],[depart, return]]
    # TODO add overlapping dates constraint
    # sys.argv[4]
    # TRAVEL_DATES = [
        # ['2019-10-17', '2019-10-20'],
        # ['2019-10-24', '2019-10-27'],
        # ['2019-10-31', '2019-11-03'],
        # ['2019-11-14', '2019-11-17'],
        # ['2019-11-21', '2019-11-24']
    # ]
    TRAVEL_DATES = sys.argv[4]
    # sys.argv[5]
    # DEPARTURE_TIME_RANGE_START = 1500
    # print(sys.argv[5], flush=True)
    DEPARTURE_TIME_RANGE_START = int(sys.argv[5])
    # sys.argv[6]
    # DEPARTURE_TIME_RANGE_END = 2400
    # print(sys.argv[6], flush=True)
    DEPARTURE_TIME_RANGE_END = int(sys.argv[6])
    # sys.argv[7]
    # INPUT_STOPOVER_MINUTES = 180
    # print(sys.argv[7], flush=True)
    INPUT_STOPOVER_MINUTES = int(sys.argv[7])
    # sys.argv[8]
    # INPUT_MAX_STOPS = 1
    # print(sys.argv[8], flush=True)
    INPUT_MAX_STOPS = int(sys.argv[8])
    # sys.argv[9]
    # INPUT_CURRENCY_CHOICE = 0
    # print(sys.argv[9], flush=True)
    INPUT_CURRENCY_CHOICE = int(sys.argv[9])

    # converting inputs to correct codes
    print(FIXED_TRIPS, flush=True)
    FIXED_TRIPS = [dict(fixed_trip, **{'dest':LOCATION_CODES[fixed_trip['dest']]}) for fixed_trip in ast.literal_eval(FIXED_TRIPS)]
    tmp_origin_locations = [LOCATION_CODES[origin] for origin in ast.literal_eval(tmp_origin_locations)]
    tmp_destination_locations = [LOCATION_CODES[dest] for dest in ast.literal_eval(tmp_destination_locations)]
    TRAVEL_DATES = ast.literal_eval(TRAVEL_DATES)

    # CONSTANTS
    NO_TRAVEL_CODE = 'xxxNONExxx'
    EMPTY_DATE_COST = 99999

    # adjusting travel destinations list for possibility of date ranges without travel
    if len(tmp_destination_locations) < len(TRAVEL_DATES):
        for i in range(len(TRAVEL_DATES) - len(tmp_destination_locations)):
            tmp_destination_locations.append(NO_TRAVEL_CODE + str(i))

    # Error handling
    if not tmp_origin_locations or not tmp_destination_locations:
        print('Must have at least one origin location and one destination location')
        return
    elif len(FIXED_TRIPS) > len(TRAVEL_DATES):
        print('Cannot fix more trips than you have date ranges')
        return

    # Generates all possible combinations of trips to form possible schedules
    possible_trips = {}
    for weekend in TRAVEL_DATES:
        combinations = []
        for origin_airport in tmp_origin_locations:
            for dest_airport in tmp_destination_locations:
                combinations.append(
                    {
                        'orig': origin_airport, 
                        'dest': dest_airport if not(NO_TRAVEL_CODE in dest_airport) else (NO_TRAVEL_CODE + weekend[0] + weekend[1]),
                        'depart_date': weekend[0],
                        'return_date': weekend[1],
                        'url': URL_TEMPLATE,
                        'best_price': EMPTY_DATE_COST
                        #'best_price': '' if not(NO_TRAVEL_CODE in dest_airport) else EMPTY_DATE_COST
                    }
                )
        possible_trips[weekend[0] + ' >>> ' + weekend[1]] = {
            'combinations': combinations
        }    
    weekends = possible_trips.keys()
    all_schedules = list(itertools.product(*[possible_trips[key]['combinations'] for key in weekends]))
    
    # Filters to allow schedules that do not have repeating destinations
    # Based on the fact that you would not want to go to the same place twice
    unique_schedules = []
    for trip_pairing in all_schedules:
        pairing_destinations = [trip['dest'] for trip in trip_pairing]
        # print(pairing_destinations, len(set(pairing_destinations)), len(pairing_destinations))
        if len(set(pairing_destinations)) == len(pairing_destinations):
            unique_schedules.append(trip_pairing)

    # Builds all urls
    # TODO move the inputs below up into the inputs section
    unique_schedules, unique_urls = build_all_urls(
        unique_schedules,
        CURRENCY_CHOICES[INPUT_CURRENCY_CHOICE], 
        MAX_NUMBER_STOPS[INPUT_MAX_STOPS],
        MAX_STOPOVER_TIMES[INPUT_STOPOVER_MINUTES],
        DEPARTURE_TIME_RANGE_START,
        DEPARTURE_TIME_RANGE_END
    )
    print('Total combinations built:', len(unique_schedules), sep=' ', flush=True)

    # print(unique_schedules)
    print('Total URLs built: ' + str(len(unique_urls)))
    # print(unique_urls)

    # Gets cheapest prices for each destination on each date range
    cheapest_prices = openWebpages(unique_urls)

    # Merges the cheapest prices with all possible combinations of schedules and calculates total schedule prices
    schedule_totals = []
    print('Calculating schedule prices')
    for schedule in unique_schedules:
        schedule_price = 0
        for trip in schedule:
            if (trip['url'] in cheapest_prices):
                trip['best_price'] = cheapest_prices[trip['url']]
                # TODO Remove code specific to leaving from Dublin
                if (trip['orig'] == LOCATION_CODES['Dublin'] and not(NO_TRAVEL_CODE in trip['dest'])):
                    trip['best_price'] += 20
                schedule_price += trip['best_price']
            else:
               schedule_price += trip['best_price'] 
        schedule_totals.append((schedule, schedule_price))
        print('.', end='', flush=True)
    
    # for obj in schedule_totals:
    #     print(obj)

    # Filters trips based on fixed dates set as inputs
    filter_given_trips = create_fixed_trips_fun(FIXED_TRIPS)
    schedule_totals = filter(filter_given_trips, schedule_totals)

    # Sorts total prices so that the cheapest flight can easily be found (as well as secondary options)
    sorted_by_price = sorted(schedule_totals, key=(lambda tup: tup[1]))
    #print(sorted_by_price)
    print('\nSchedule prices calculated')
    # RUNNING = False
    # print('\n')
    # time.sleep(1)

    # Counts number of date ranges with no travel (in the cheapest schedule) so that it can adjust the price
    # The price needs to be adjusted because of the weird way I added a large number to make the program run
    #   and find the cheapest total. This adjustment is only for the display of the final price. It does not 
    #   change the underlying data of the object
    empty_dates = 0
    for daterange in sorted_by_price[0][0]:
        if NO_TRAVEL_CODE in daterange['dest']:
            empty_dates += 1
    
    CURRENCY_SYMBOL_CODES = {
        'EUR': '\u20ac',
        'USD': '\u0024'
    }

    CURRENCY_SYMBOL = CURRENCY_SYMBOL_CODES[CURRENCY_CHOICES[INPUT_CURRENCY_CHOICE]]

    print(f'Best Price: {CURRENCY_SYMBOL}', sorted_by_price[0][1] - (empty_dates * EMPTY_DATE_COST), sep='')

    # print('Worst Price: \u20ac', sorted_by_price[-1][1], sep='')
    print('Best Price Itinerary')

    # Builds inverse location lookup dictionary
    inverse_location_lookup = {val: key for key, val in LOCATION_CODES.items()}

    # Formats output of cheapest travel itinerary
    for obj in sorted_by_price[0][0]:
        if not(NO_TRAVEL_CODE in obj["dest"]):
            print( '########################################################################################')
            print(f'#  Dates (YYYY-MM-DD):          {obj["depart_date"]} >>> {obj["return_date"]}')
            print(f'#  Origin:                      {inverse_location_lookup[obj["orig"]]}')
            print(f'#  Destination:                 {inverse_location_lookup[obj["dest"]]}')
            print(f'#  Price:                       {CURRENCY_SYMBOL}{obj["best_price"]}')
            print(f'#  Flight URL:')
            print(f'#    {obj["url"]}\n')
        elif NO_TRAVEL_CODE in obj["dest"]:
            print( '########################################################################################')
            print(f'#  Dates (YYYY-MM-DD):          {obj["depart_date"]} >>> {obj["return_date"]}')
            print(f'#  No Travel These Dates')
            print(f'#  Price:                       {CURRENCY_SYMBOL}0')


# def show_waiting():
#     while RUNNING:
#         time.sleep(1)
#         print('.', end = '')


# threading.Thread(target=show_waiting).start()
# threading.Thread(target=pingGoogleFlights).start()

def main():
    pingGoogleFlights()

main()

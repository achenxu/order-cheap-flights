from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

import time
import os
import itertools
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

# Travel dates example: [[depart, return],[depart, return],[depart, return]]
TRAVEL_DATES = [
    ['2019-10-17', '2019-10-20'],
    ['2019-10-24', '2019-10-27'],
    ['2019-10-31', '2019-11-03'],
    ['2019-11-14', '2019-11-17'],
    ['2019-11-21', '2019-11-24']
]

CURRENCY_CHOICES = ['EUR', 'USD']

MAX_NUMBER_STOPS = {
    1: 's:1*1;'
}
# Max stopovers in minutes
MAX_STOPOVER_TIMES = {
    180: 'ld:-180*-180;'
}

DEPARTURE_TIME_RANGE_START = 1500
DEPARTURE_TIME_RANGE_END = 2400

    
def build_all_urls(unique_schedules, currency, 
                    max_stopovers, max_stopover_time, 
                    departure_time_range_start, 
                    departure_time_range_end):
    all_urls = []
    for combo in unique_schedules:
        for trip in combo:
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
    print('Finding some of the cheapest prices (' + str(number_of_windows) + ')')
    for idx in range(number_of_windows):
        chrome_driver.switch_to.window(chrome_driver.window_handles[idx])
        try:
            element1 = WebDriverWait(chrome_driver, 60).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".flt-subhead1.gws-flights-results__price.gws-flights-results__cheapest-price")
                    )
                )
            cheapest_prices[chrome_driver.current_url] = int(element1.text[1:])
            print('.', end='', flush=True)
        except:
            print('Error', element1)
    return cheapest_prices


def openWebpages(all_possible_urls):
    # WebDriver setup
    DRIVER_PATH = "C:\\Users\\carpe\\Desktop\\ChromeDriver\\chromedriver77"

    chrome_options = Options()  
    chrome_options.add_argument("--headless")  
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


# Best departing flights section
# gws-flights-results__best-flights
def pingGoogleFlights():
    # tmp_origin_locations = [
    #     LOCATION_CODES['Dublin']
    # ]
    # tmp_destination_locations = [
    #     LOCATION_CODES['Amsterdam-ANY'], 
    #     LOCATION_CODES['Prague-ANY'], 
    #     LOCATION_CODES['Porto'],
    #     LOCATION_CODES['Florence'],
    #     LOCATION_CODES['Madrid']
    # ]

    tmp_origin_locations = [
        LOCATION_CODES['Cork'],
        LOCATION_CODES['Dublin']
    ]
    tmp_destination_locations = [
        LOCATION_CODES['Amsterdam-ANY'], 
        LOCATION_CODES['Prague-ANY'], 
        LOCATION_CODES['Porto'],
        LOCATION_CODES['Florence'],
        LOCATION_CODES['Madrid'],
        LOCATION_CODES['Bucharest'],
        LOCATION_CODES['Budapest'],
        LOCATION_CODES['Seville'],
        LOCATION_CODES['Barcelona']
    ]

    if len(tmp_destination_locations) < len(TRAVEL_DATES):
        print('You need to have more destinations than date ranges')
        return

    possible_trips = {}

    for weekend in TRAVEL_DATES:
        combinations = []
        for origin_airport in tmp_origin_locations:
            for dest_airport in tmp_destination_locations:
                combinations.append(
                    {
                        'orig': origin_airport, 
                        'dest': dest_airport,
                        'depart_date': weekend[0],
                        'return_date': weekend[1],
                        'url': URL_TEMPLATE,
                        'best_price': ''
                    }
                )
        possible_trips[weekend[0] + ' >>> ' + weekend[1]] = {
            'combinations': combinations
        }    
    weekends = possible_trips.keys()
    all_schedules = list(itertools.product(*[possible_trips[key]['combinations'] for key in weekends]))
    unique_schedules = []

    for trip_pairing in all_schedules:
        pairing_destinations = [trip['dest'] for trip in trip_pairing]
        # print(pairing_destinations, len(set(pairing_destinations)), len(pairing_destinations))
        if len(set(pairing_destinations)) == len(pairing_destinations):
            unique_schedules.append(trip_pairing)

    unique_schedules, unique_urls = build_all_urls(
        unique_schedules,
        CURRENCY_CHOICES[0], MAX_NUMBER_STOPS[1],
        MAX_STOPOVER_TIMES[180],
        DEPARTURE_TIME_RANGE_START,
        DEPARTURE_TIME_RANGE_END
    )
    print('Total combinations built:', end=' ', flush=True)

    # print(unique_schedules)
    print(len(unique_schedules))
    print('Total URLs built: ' + str(len(unique_urls)))
    # print(unique_urls)

    cheapest_prices = openWebpages(unique_urls)

    schedule_totals = []
    print('Calculating schedule prices')
    for schedule in unique_schedules:
        schedule_price = 0
        for trip in schedule:
            try:
                trip['best_price'] = cheapest_prices[trip['url']]
                schedule_price += trip['best_price']
            except KeyError:
                pass
        schedule_totals.append((schedule, schedule_price))
        print('.', end='', flush=True)

    sorted_by_price = sorted(schedule_totals, key=lambda tup: tup[1])
    print('\nSchedule prices calculated')
    # RUNNING = False
    # print('\n')
    # time.sleep(1)

    print('Best Price: \u20ac', sorted_by_price[0][1], sep='')
    print('Worst Price: \u20ac', sorted_by_price[-1][1], sep='')
    print('Best Price Itinerary')

    inverse_location_lookup = {val: key for key, val in LOCATION_CODES.items()}

    for obj in sorted_by_price[0][0]:
        print( '########################################################################################')
        print(f'#  Dates (YYYY-MM-DD):          {obj["depart_date"]} >>> {obj["return_date"]}')
        print(f'#  Origin:                      {inverse_location_lookup[obj["orig"]]}')
        print(f'#  Destination:                 {inverse_location_lookup[obj["dest"]]}')
        print(f'#  Price:                       \u20ac{obj["best_price"]}')
        print(f'#  Flight URL:')
        print(f'#    {obj["url"]}\n')


# def show_waiting():
#     while RUNNING:
#         time.sleep(1)
#         print('.', end = '')


# threading.Thread(target=show_waiting).start()
# threading.Thread(target=pingGoogleFlights).start()
pingGoogleFlights()

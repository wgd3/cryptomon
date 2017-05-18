#!/usr/bin/env python
import sys, urllib3, time, json
import argparse, ConfigParser
from xml.dom import minidom
from termcolor import colored

import logging
from logging.config import dictConfig

from api import ExchangeAPI

config = ConfigParser.SafeConfigParser()

# init logging
# logging.getLogger("urllib3").setLevel(logger.debug)
# TODO Fix urllib3 logging

logging_config = dict(
    version = 1,
    formatters = {
        'f': {'format':
              '%(asctime)s|%(name)-25s|%(levelname)-5s| %(message)s',
              'datefmt': '%m/%d/%Y %I:%M:%S'}
        },
    handlers = {
        'h': {'class': 'logging.StreamHandler',
              'formatter': 'f',
              'level': logging.DEBUG}
        },
    root = {
        'handlers': ['h'],
        'level': logging.DEBUG,
        },
    urllib3 = {
        'handlers': ['h'],
        'level': logging.DEBUG,
        },
)

dictConfig(logging_config)
logger = logging.getLogger('cryptomon')

# create parser
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--currency", help="currency name [ethereum, bitcoin]")
parser.add_argument("-v", "--verbose", action="store_true", help="enable verbose output")
parser.add_argument("--config", help="path to config file")
parser.add_argument("-r", "--range", help="+/- dollar range from current price")

args = parser.parse_args()

if args.verbose:
    logger.setLevel(logging.DEBUG)
    logger.debug("Parser args: " + str(args))
else:
    logger.setLevel(logging.INFO)

# must be read/set before configuring global variables
if args.config:
    pass # TODO add custom settings file handling
else:
    config.read('settings.cfg')

# create list containing all exchanges
AVAIL_EXCHANGES = []

# setting globals - refer to settings.ini for notes and definitions
CMC_BASEURL = config.get('coinmarketcap', 'baseurl')
CMC_MAX_CALLS_PER_MINUTE = int(config.get('coinmarketcap', 'max_calls_per_minute'))
CM_CURRENCY = config.get('cryptomon', 'default_currency')
CM_WATCH_PRICE = config.get('cryptomon', 'default_watch_price')
CM_PRICE_RANGE = float(config.get('cryptomon', 'default_range'))
PROWL_API = config.get('prowl', 'api_key')
PROWL_PRIO = config.get('prowl', 'defaul_priority')
PROWL_BASEURL = config.get('prowl', 'baseurl')

# the following globals only get updated if they are overriden by parsed arguments
if args.currency:
    logger.debug("Changing CM_CURRENCY to {0}".format(args.currency))
    CM_CURRENCY = args.currency.lower()

if args.range:
    CM_PRICE_RANGE = float(args.range)

# unsafe HTTPS handling
urllib3.disable_warnings()
logger.debug("Disabled urllib3 SSL warnings.")

# initialize urllib3 manager
http = urllib3.PoolManager()
logger.debug("Initilized urllib3 PoolManager.")

def pushAlert(price, msg):
    """Method to push notifications to Prowl"""

    logger.info("Sending notification to Prowl...")
    event_time = time.strftime("%m/%d/%y %H:%M:%S")

    event_title = '{0}'.format(CM_CURRENCY.capitalize())
    # if CM_WATCH_DIRECTION == 'rise':
    #     event_title = event_title + ' exceeded target!'
    # else:
    #     event_title = event_title + ' fell below target!'

    try:
        logger.debug("Opening connection to Prowl API...")
        req = http.request(
            'GET',
            PROWL_BASEURL,
            fields={'apikey': PROWL_API,
                    'priority': PROWL_PRIO,
                    'application': 'CryptoMon',
                    'event': event_title,
                    'description': '{0} - {1}'.format(event_time, msg)}
        )
        logger.debug("Notification sent!")

        # check for errors in the response
        logger.debug("Checking returned XML for errors..")
        xmldoc = minidom.parseString(req.data)
        err_nodes = xmldoc.getElementsByTagName('error')
        if len(err_nodes) > 0: # error XML tag found in response
            err_node = err_nodes[0] # there's only ever 1 in the response XML
            err_code = err_node.getAttribute('code')
            err_msg = err_node.firstChild.nodeValue
            logger.error("Prowl API Error: {0} - {1}".format(err_code, err_msg))
        else:
            # if there's no error node, then it's a success node, and there's only one
            success_node = xmldoc.getElementsByTagName('success')[0]
            remaining_calls = success_node.getAttribute('remaining')
            logger.debug("Your API key for Prowl has {0} API calls remaining".format(remaining_calls))

    except Exception as e:
        logger.debug("urllib3 Exception: {0}".format(str(e)))
        logger.error("Error sending push notification.")

def cmcRequest(currency):
    """Dedicated method for urllib3 request

    # TODO update docstring
    """
    # logger.debug("cmcRequest called for {0}".format(currency))

    try:
        req = http.request(
            'GET',
            CMC_BASEURL + '/ticker/' + currency + '/',
            fields={'convert': 'USD'}
        )
        return req
    except urllib3.exceptions.NewConnectionError as e:
        logger.error("NewConnectionError: {0}".format(str(e)))

    return False

def getCurrentPrice(currency):
    """Method for returning the current asking price"""
    # logger.debug("getCurrentPrice called")

    resp = cmcRequest(currency)
    resp_data = json.loads(resp.data)[0]
    return resp_data['price_usd']

def getByDotNotation( obj, ref ):
    """Use dot notation to refer to an arbitrary depth within a JSON object"""
    val = obj
    for key in ref.split( '.' ):
        val = val[key]
        return val

def getAllExchangeAskingPrices(currency):
    """Method for returning the current asking price from all exchanges"""
    # logger.debug("getAllExchangeAskingPrices called")

    prices = []

    for ex in AVAIL_EXCHANGES:
        exDict = {}
        exDict['name'] = ex.exchange_name

        # lookup symbol
        currency_symbol = ''
        if currency == 'ethereum':
            currency_symbol = config.get(exDict['name'], 'ethereum_symbol')

        # translate currency pair
        # cur_pairs = ex.getSupportedCurrencies()
        # exchangeDebugMsg(exDict['name'], "cur_pairs: {0}".format(cur_pairs))

        # for index, cp in enumerate(cur_pairs, start=0):
        #     exchangeDebugMsg(exDict['name'], "Checking for {0} at index {1} in cur_pairs".format(cp, index))
        #     if currency in cp: # checking lower case
        #         exchangeDebugMsg(exDict['name'], "Found matching symbol of {0}".format(cp))
        #         exDict['price'] = ex.getUsdVal(cur_pairs[index])
        #     if currency in cp.lower(): # convert upper case symbols and check
        #         exchangeDebugMsg(exDict['name'], "Found matching symbol of {0}".format(cp))
        #         exDict['price'] = ex.getUsdVal(cur_pairs[index])

        price_data = ex.getUsdVal(currency_symbol)
        # logger.debug("getByDotNotation price: {0}".format(getByDotNotation(price_data, config.get(ex.exchange_name, 'response_dict_path'))))

        exDict['price'] = getByDotNotation(price_data, config.get(ex.exchange_name, 'response_dict_path'))
        logger.debug("Adding asking price of ${0} from the {1} exchange for {2}".format(exDict['price'], ex.exchange_name, currency_symbol))
        prices.append(exDict)

    return prices


def exchangeDebugMsg(exchange, msg):
    logger.debug("{0} - {1}".format(colored(exchange.capitalize(), 'green'), msg))


def createExchanges():
    logger.debug("Started to build exchange objects...")

    try:
        exchanges = config.get('exchanges', 'supported_exchanges').split(',')
        logger.debug("Found the following exchanges: " + str(exchanges))

        for exchange in exchanges:
            # logger.debug("Finding configuration for {0} exchange".format(exchange))
            curExchangeName = config.get(exchange, 'name')
            curExchangeUrl = config.get(exchange, 'base_url')
            curExchangeMaxRequests = config.get(exchange, 'max_requests_per_minute')
            curExchangeCurrencies = config.get(exchange, 'supported_currencies').split(',')
            exchangeDebugMsg(curExchangeName, curExchangeCurrencies)

            # create the ExchangeAPI object
            newExchange = ExchangeAPI(curExchangeName, curExchangeUrl, curExchangeMaxRequests)
            # exchangeDebugMsg(curExchangeName, "Created ExchangeAPI object: {0}".format(newExchange.__str__()))

            # configure the new ExchangeAPI object
            # logger.debug("Adding these currencies to the exchange: {0}".format(curExchangeCurrencies))
            for cur_pair in curExchangeCurrencies:
                exchangeDebugMsg(curExchangeName, "Adding {0} to supported currencies".format(cur_pair))
                newExchange.addSupportedCurrency(cur_pair)

            # exchangeDebugMsg(curExchangeName, "cur_pairs: {0}".format(newExchange.getSupportedCurrencies()))

            newExchange.setUsdValEndpoint(config.get(exchange, 'usd_val_endpoint'))

            AVAIL_EXCHANGES.append(newExchange)
            logger.debug("Added {0} exchange to available exchanges".format(curExchangeName))

        for ex in exchanges:
            exchangeDebugMsg(config.get(ex, 'name'), config.get(ex, 'supported_currencies').split(','))

    except ConfigParser.NoSectionError as e:
        logger.error("Could not find config section: {0}".format(str(e)))
    except ConfigParser.NoOptionError as e:
        logger.error("Could not find config option: {0}".format(str(e)))
    except ConfigParser.Error as e:
        logger.error("Config file error: {0}".format(str(e)))

def main():

    CM_START_PRICE = float(getCurrentPrice(CM_CURRENCY))
    CM_HIGH_PRICE = CM_START_PRICE + CM_PRICE_RANGE
    CM_LOW_PRICE = CM_START_PRICE - CM_PRICE_RANGE
    logger.debug("Found CM_START_PRICE of ${0}".format(CM_START_PRICE))
    logger.info("Starting main loop, watching for prices above {0} and below {1}".format(CM_HIGH_PRICE, CM_LOW_PRICE))

    while True:

        current_price = getCurrentPrice(CM_CURRENCY)
        current_prices = getAllExchangeAskingPrices(CM_CURRENCY)

        for exchange in current_prices:
            exchangeDebugMsg(exchange['name'], "Evaluating current ask price of {0}".format(exchange['price']))



        logger.debug("Comparing current ${0} >= ${1}".format(current_price, CM_HIGH_PRICE))
        comp = float(current_price) >= float(CM_HIGH_PRICE)
        logger.debug("Comparison: {0}".format(comp))
        if float(current_price) >= float(CM_HIGH_PRICE):
            logger.debug("Current currency price ${0} exceeds target ${1}".format(current_price, CM_HIGH_PRICE))
            logger.info("Currency price (${0}) has risen above your target!".format(current_price))
            # DO SOMETHING
            pushAlert(current_price, "Price triggered at {0}".format(current_price))
            sys.exit(0)

        logger.debug("Comparing current ${0} <= ${1}".format(current_price, CM_LOW_PRICE))
        comp = float(current_price) <= float(CM_LOW_PRICE)
        logger.debug("Comparison: {0}".format(comp))
        if float(current_price) <= float(CM_LOW_PRICE):
            logger.debug("Current currency price ${0} dropped below target ${1}".format(current_price, CM_LOW_PRICE))
            logger.info("Currency price (${0}) has dropped below your target!".format(current_price))
            # DO SOMETHING
            pushAlert(current_price, "Price triggered at {0}".format(current_price))
            sys.exit(0)

        logger.info("Currency price (${0}) has not yet met range of ${1} - ${2}.".format(current_price, CM_LOW_PRICE, CM_HIGH_PRICE))

        count = 0
        while count < (60 / CMC_MAX_CALLS_PER_MINUTE):
            sys.stdout.write('Waiting {0} seconds...\r'.format((60 / CMC_MAX_CALLS_PER_MINUTE) - count))
            sys.stdout.flush()
            count += 1
            time.sleep(1)


if __name__ == '__main__':

    logger.debug("Starting cryptomon program")
    logger.debug("Monitoring currency: {0}".format(CM_CURRENCY))
    logger.debug("Update interval: {0}s".format(60 / CMC_MAX_CALLS_PER_MINUTE))

    createExchanges()
    main()

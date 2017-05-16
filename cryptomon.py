#!/usr/bin/env python
import sys, urllib3, time, json
import argparse, ConfigParser
from xml.dom import minidom

import logging
from logging.config import dictConfig

config = ConfigParser.SafeConfigParser()
config.read('settings.cfg')

# setting globals - refer to settings.ini for notes and definitions
CMC_BASEURL = config.get('coinmarketcap', 'baseurl')
CMC_MAX_CALLS_PER_MINUTE = int(config.get('coinmarketcap', 'max_calls_per_minute'))
CM_CURRENCY = config.get('cryptomon', 'default_currency')
CM_WATCH_PRICE = config.get('cryptomon', 'default_watch_price')
CM_WATCH_DIRECTION = config.get('cryptomon', 'default_direction')
PROWL_API = config.get('prowl', 'api_key')
PROWL_PRIO = config.get('prowl', 'defaul_priority')
PROWL_BASEURL = config.get('prowl', 'baseurl')

# init logging
# logging.getLogger("urllib3").setLevel(logging.DEBUG)
# TODO Fix urllib3 logging

logging_config = dict(
    version = 1,
    formatters = {
        'f': {'format':
              '%(asctime)s|%(name)-9s|%(levelname)-5s| %(message)s',
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
#urllib_logger = logging.getLogger("urllib3")
#urllib_logger.setLevel(logging.DEBUG)
# urllib_logger = urllib3.add_stderr_logger()
# urllib_logger.setLevel(logging.DEBUG)

# create parser
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--currency", help="currency name [ethereum, bitcoin]")
parser.add_argument("-v", "--verbose", action="store_true", help="enable verbose output")
parser.add_argument("direction", help="specify [rise,drop] to specified price")
parser.add_argument("price", help="price to monitor for currency")

args = parser.parse_args()

# TODO validate args.direction
# if args.direction.lower != 'rise' and args.direction.lower != 'drop':
#     logging.error("Please specify only either 'rise' or 'fall' as the price direction.")
#     sys.exit(1)

CM_WATCH_DIRECTION = args.direction.lower()

if args.verbose:
    logger.setLevel(logging.DEBUG)
    logger.debug("Parser args: " + str(args))
else:
    logger.setLevel(logging.INFO)

if args.currency:
    logger.debug("Changing CM_CURRENCY to {0}".format(args.currency))
    CM_CURRENCY = args.currency.lower()

CM_WATCH_PRICE = args.price
logger.debug("Watching {0} for a price of ${1}".format(CM_CURRENCY, CM_WATCH_PRICE))

urllib3.disable_warnings()
logger.debug("Disabled urllib3 SSL warnings.")
http = urllib3.PoolManager()
logger.debug("Initilized urllib3 PoolManager.")

def pushAlert(price, msg):
    """Method to push notifications to Prowl"""

    logger.info("Sending notification to Prowl...")
    event_time = time.strftime("%m/%d/%y %H:%M:%S")
    # event_time=event_time.replace(' ', '%20') # replace spaces with URL chars

    event_title = '{0}'.format(CM_CURRENCY.capitalize())
    if CM_WATCH_DIRECTION == 'rise':
        event_title = event_title + ' exceeded target!'
    else:
        event_title = event_title + ' fell below target!'
    # event_title = event_title.replace(' ', '%20')

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
            err_node = err_nodes[0] # there's only ever 1 in their response XML
            err_code = err_node.getAttribute('code')
            err_msg = err_node.firstChild.nodeValue
            logger.error("Prowl API Error: {0} - {1}".format(err_code, err_msg))
        else:
            pass
            # TODO Add debug output to show remaining API calls on Prowl

    except Exception as e:
        logger.debug("urllib3 Exception: {0}".format(str(e)))
        logger.error("Error sending push notification.")

def main():

    while True:

        logger.info("Checking prices...")

        try:
            req = http.request(
                'GET',
                CMC_BASEURL + '/ticker/ethereum/',
                fields={'convert': 'USD'}
            )
        except urllib3.exceptions.NewConnectionError as e:
            logger.error("NewConnectionError: {0}".format(str(e)))

        eth_data = json.loads(req.data)[0]
        current_price = eth_data['price_usd']
        logger.info("ETHUSD = ${0}".format(current_price))

        # evaluate price based on watch price
        if CM_WATCH_DIRECTION == 'rise':
            # logger.debug("Looking for higher price...")
            if float(current_price) >= float(CM_WATCH_PRICE):
                logger.debug("Current currency price ${0} exceeds target ${1}".format(current_price, CM_WATCH_PRICE))
                logger.info("Currency price (${0}) has risen above your target!".format(current_price))
                # DO SOMETHING
                pushAlert(current_price, "Price triggered at {0}".format(current_price))
                sys.exit(0)
        else: # looking for lower price
            # logger.debug("Looking for lower price...")
            if float(current_price) <= float(CM_WATCH_PRICE):
                logger.debug("Current currency price ${0} dropped below target ${1}".format(current_price, CM_WATCH_PRICE))
                logger.info("Currency price (${0}) has dropped below your target!".format(current_price))
                # DO SOMETHING
                pushAlert(current_price, "Price triggered at {0}".format(current_price))
                sys.exit(0)

        logger.debug("Currency price (${0}) has not yet met target of ${1}.".format(current_price, CM_WATCH_PRICE))

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

    main()

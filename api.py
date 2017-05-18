import sys, urllib3, time, json
import logging

# init logging
logger = logging.getLogger(__name__)

# create HTTP connection PoolManager
http = urllib3.PoolManager()
urllib3.disable_warnings()

def functionBuilder(name, args):
    """Function meant to allow dynamic definition of other functions. Used to build HTTP request methods
    specific to each instance of a class

    name -- set the value of the method's __name__
    """
    pass

class APIPool(object):
    pass

class BaseAPI(object):
    """Base class for API usage"""

    BASE_API_URL = ''
    MAX_REQUEST_PER_MIN = ''

    def __init__(self, baseurl, maxrequests):
        self.BASE_API_URL = baseurl
        self.MAX_REQUEST_PER_MIN = maxrequests

    def getRequest(self, endpoint, fields=None):
        """Base method for creating a GET HTTP request. Can be overriden for more specific URL endpoint configuration.

        Keyword arguments:
        endpoint -- what should be added to the base API url
        fields -- dict representing any vairables that should be added to the URL in the form '?foo=bar'
        """

        try:
            req = http.request(
                'GET',
                self.BASE_API_URL + endpoint,
                fields=fields
            )
            return req
        except urllib3.exceptions.NewConnectionError as e:
            logger.error("NewConnectionError: {0}".format(str(e)))

class ExchangeAPI(BaseAPI):
    """Class for exchange-specific APIs"""

    exchange_name = ''
    usd_val_endpoint = ''
    supported_currencies = []

    def __init__(self, name, baseurl, maxrequests):
        logger.debug("Creating ExchangeAPI object for the {0} exchange".format(name))
        BaseAPI.__init__(self, baseurl, maxrequests)
        self.exchange_name = name

    def __repr__(self):
        print "<ExchangeAPI instance for {0}>".format(self.exchange_name)

    def setUsdValEndpoint(self, endpoint):
        """Set object's basic 'check current USD buy price' variable.

        """


        self.usd_val_endpoint = endpoint
        return self.usd_val_endpoint

    def addSupportedCurrency(self, currency):
        logger.debug("Adding {0} to {1}'s exchange supported currency pairs'")
        self.supported_currencies.append(currency)

        return True

    def getUsdVal(self, cur_pair):
        if cur_pair not in self.supported_currencies:
            logger.error("Currency pair {0} is not a supported currency on the {1} exchange".format(cur_pair, self.exchange_name))
            return False

        modEndpoint = self.usd_val_endpoint.replace('CUR_PAIR', cur_pair)
        # logger.debug("Using modified endpoint: {0}".format(modEndpoint))

        resp = self.getRequest(modEndpoint)
        ticker_data = json.loads(resp.data)
        logger.debug("ticker_data for {0}: {1}".format(cur_pair, ticker_data))
        return ticker_data['ask']

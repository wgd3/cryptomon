import sys, urllib3, time, json
import logging

# init logging
module_logger = logging.getLogger('cryptomon.api')

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
        self.logger = logging.getLogger('cryptomon.api.BaseAPI')
        # self.logger.info('Created an instance of BaseAPI')

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
            self.logger.error("NewConnectionError: {0}".format(str(e)))

class ExchangeAPI(BaseAPI):
    """Class for exchange-specific APIs"""

    exchange_name = ''
    usd_val_endpoint = ''
    supported_currencies = []

    def __init__(self, name, baseurl, maxrequests):
        BaseAPI.__init__(self, baseurl, maxrequests)
        self.logger = logging.getLogger('cryptomon.api.ExchangeAPI')
        # self.logger.debug("Creating ExchangeAPI object for the {0} exchange".format(name))
        self.exchange_name = name

    def __repr__(self):
        print "<ExchangeAPI instance for {0}>".format(self.exchange_name)

    def setUsdValEndpoint(self, endpoint):
        """Set object's basic 'check current USD buy price' variable.

        """


        self.usd_val_endpoint = endpoint
        return self.usd_val_endpoint

    def addSupportedCurrency(self, currency):
        self.logger.debug("Adding {0} to {1}'s exchange supported currency pairs".format(currency, self.exchange_name))
        self.supported_currencies.append(currency)

        return True

    def getSupportedCurrencies(self):
        return self.supported_currencies

    def getUsdVal(self, currency):

        self.logger.debug("Getting USD value for {0}".format(currency))
        # currency_pair = ''
        #
        # if currency == 'ethereum':
        #     # find which currency pair matches ethereum
        #     self.logger.debug("Looking for matching ethereum symbol in {0}".format(self.supported_currencies))
        #     for index, cp in enumerate(self.supported_currencies):
        #         if 'eth' in cp:
        #             self.logger.debug("Found eth matches currency pair: {0}".format(self.supported_currencies[index]))
        #             currency_pair = self.supported_currencies[index]
        #         if 'ETH' in cp:
        #             self.logger.debug("Found ETH matches currency pair: {0}".format(self.supported_currencies[index]))
        #             currency_pair = self.supported_currencies[index]
        #
        # if currency == 'bitcoin':
        #     pass

        # if currency not in self.supported_currencies:
        #     self.logger.error("Currency pair {0} is not a supported currency on the {1} exchange".format(currency, self.exchange_name))
        #     return False

        modEndpoint = self.usd_val_endpoint.replace('CUR_PAIR', currency)
        self.logger.debug("Using modified endpoint: {0}".format(modEndpoint))

        resp = self.getRequest(modEndpoint)
        ticker_data = json.loads(resp.data)
        # self.logger.debug("ticker_data for {0}: {1}".format(currency, ticker_data))
        # return full HTTPResponse so that the main module can reference the config for the response_dict_path
        return ticker_data

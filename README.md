# CryptoMon

CryptoMon is a Python script for monitoring cryptocurrency prices and providing push notifications using Prowl when a certain target is hit.

## Getting Started
Start by cloning this repository
```
# git clone https://github.com/wgd3/cryptomon
```
Create a virtual environment in the cryptomon folder
```
# cd cryptomon
# virtualenv venv
# source venv/bin/activate
```
Install any dependencies
```
# pip install -r requirements.txt
```
## Configuration
Settings for cryptomon are stored in `settings.sample` - this needs to be cloned and altered
```
# cp settings.sample settings.cfg
# vim settings.cfg
```
*__Note:__ the settings file can be named whatever you like, but right now is hardcoded to read from `settings.cfg`*

A Prowl API account can be signed up for on [Prowl's website](https://www.prowlapp.com/). You will need to retrieve your API key and add that to the `api_key` line in the settings file.

Cryptomon's code reads the comma-separated list of exchange names as expected sections elsewhere in the `settings.cfg` file.

## Running cryptomon
By default cryptomon uses a range of +/- $4 from the current asking price on each exchange, but this can be overridden at run time with the `-r` flag. Cryptomon also defaults to ethereum monitoring, bitcoin and other coin support is in progress.
```
$ ./cryptomon.py -h
usage: cryptomon.py [-h] [-c CURRENCY] [-v] [--config CONFIG] [-r RANGE]

optional arguments:
  -h, --help            show this help message and exit
  -c CURRENCY, --currency CURRENCY
                        currency name [ethereum, bitcoin]
  -v, --verbose         enable verbose output
  --config CONFIG       path to config file
  -r RANGE, --range RANGE
                        +/- dollar range from current price
```
Non-verbose output looks like this:
```
$ ./cryptomon.py -r2
05/19/2017 11:37:15 | cryptomon                 | INFO  | Looking up the latest prices ***********************************************
05/19/2017 11:37:15 | cryptomon                 | INFO  | Currency price ($114.96) on gemini has not yet met range of $112.96 - $116.96.
05/19/2017 11:37:15 | cryptomon                 | INFO  | Currency price ($115.91) on coinbase has not yet met range of $113.91 - $117.91.
05/19/2017 11:37:15 | cryptomon                 | INFO  | Currency price ($114.8) on bitfinex has not yet met range of $112.8 - $116.8.
05/19/2017 11:37:30 | cryptomon                 | INFO  | Looking up the latest prices ***********************************************
05/19/2017 11:37:30 | cryptomon                 | INFO  | Currency price ($114.96) on gemini has not yet met range of $112.96 - $116.96.
05/19/2017 11:37:30 | cryptomon                 | INFO  | Currency price ($115.91) on coinbase has not yet met range of $113.91 - $117.91.
05/19/2017 11:37:31 | cryptomon                 | INFO  | Currency price ($114.8) on bitfinex has not yet met range of $112.8 - $116.8.
```

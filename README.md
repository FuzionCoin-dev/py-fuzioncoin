# PyFuzc
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/FuzionCoin-dev/py-fuzioncoin/graphs/commit-activity)
[![GitHub license](https://badgen.net/github/license/FuzionCoin-dev/py-fuzioncoin)](https://github.com/FuzionCoin-dev/py-fuzioncoin/blob/master/LICENSE)
[![GitHub latest commit](https://badgen.net/github/last-commit/FuzionCoin-dev/py-fuzioncoin)](https://GitHub.com/FuzionCoin-dev/py-fuzioncoin/commit/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)


Official Python implementation of the FuzionCoin protocol

### WARNING: Under construction. Use at your own risk. Some functions may not work.

## Setup

Install required python packages:
```sh
pip install -r requirements.txt
```

Edit configuration file (`config.json`) to match your requirements.

Remember to add at least 1 valid trusted peer so that a peer can connect to the network.

## Launch peer
You can launch peer with following command:
```sh
python main.py
```
Or with specify configuration file location
```sh
python main.py --config PATH
```

# anzlic-validator-plugin
ANZLIC Metadata Validation

## Requirements
* PyQt4
* QGIS 2.18
* Python 2.7
* Koordinates Python Module
  * `sudo pip install koordinates`

## Install
* Clone anzlic-validator-plugin
  * `git clone https://github.com/linz/anzlic-validator`
* Create a file `.apikey` in home directory with a LDS API Key inside like such:
  * `key0=API_KEY`
 
## Setup - Linux
From inside the anzlic-validator directory run the following. This will
install the koordinates module if not already installed and move anzlic-validator
into the qgis plugins directory.

* `sudo python setup.py`

  



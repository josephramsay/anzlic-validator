[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://github.com/linz/lds-metadata-updater/LICENSE) 
[![codecov](https://codecov.io/gh/linz/lds-metadata-updater/branch/master/graph/badge.svg)](https://codecov.io/gh/linz/lds-metadata-updater) [![Build Status](https://travis-ci.com/linz/lds-metadata-updater.svg?token=4YGqrWWw1nJqpi344cuy&branch=master)](https://travis-ci.com/linz/lds-metadata-updater)


# lds-metadata-updater


This utility updates LINZ (as well as others') Data Service metadata

For installation instructions see [INSTALL.md](INSTALL.md)

## Simple Overview

1. Downloads the xml metadata from the Data Service, for one or many user defined
data sources
2. Takes a back up of the metadaat file (if text replacement is to be made)
3. Finds and replaces text within the metadata file 
4. Updates the LDS metadata with the newly edited XML.


## Execute Metadata Update

### Configuration
A config.yaml file must be provided. This can be created by editing the provided
[config_tempate.yaml](config_tempate.yaml) file. 


#### Configuration Values:

```
Connection:
  Api_key = <ADMIN API KEY>             # See notes below on API Keys
  Domain =  <Data Service Domain>       # e.g. data.linz.govt.nz

Text:
  Mapping:                               
    1:                                  # The order the text replacements are to occur
                                        # DONT NOT DUPLICATE NUMBERS !!!
                                        # ENUSRE NUMBERING IS SEQUENTIAL STARTING AT 1 !!!
       search: the terrace              # The text to search for replacement
                                        # !!! FORMAT: Python Regular Expression
       replace: The Road                # The text that is to replace the search text
       ignore_case: True                # True or False. If True, search text case is ignored 
    2: 
       search: Land Info New Zealand
       replace: Land Information New Zealand
       ignore_case: True     

Output:
  Destination: <Directory>              # The directory where to write 
                                        # metadata file backups

Datasets:
  Layers: <Layers to Process>           # A list of Layers/Table ids or "All"
                                        # All will process All Tables and Layers 
                                        # e.g. [93639,93648, 93649] or "All"
  Sets:                                 # Sets are not currently supported
  Docs:                                 # Documents are not currently supported 


Test:
  Dry_run: False                        # True or False
                                        # If True, metadata xml documents are
                                        # edited and stored but no changes to the
                                        # Data Service made 
  Overwrite_files: True                 # True or Flase
                                        # Useful for dev and testing. When True
                                        # metadata files that are already in 
                                        # the destination dir will be over-written
```
**Text Mapping**

The order that text is searched and replaced is import. For this reason the 
mappings must be formatted as above. That is, each mapping must be sequentially 
number, starting at 1, in the order the search and replace is to be executed.

The script uses [re.sub](https://docs.python.org/2/library/re.html#regular-expression-syntax). 
The search text format must therefore be in the Python Regular Expression format.
Replace text is a standard plain text string that is to replace the regular expression match. 

**API Key**

The (LINZ) Data Service API key must be generated with the required permissions 
to update metadata. It is recommend that a API key is created specifically for 
this task.

The API KEY must have the following permission enabled against it. You will 
need admin rights to be able to enable all of the below 
* Query layer data
* Search and view tables and layers
* Create, edit and delete tables and layers
* View the data catalog and access catalog services (CS-W)

For LDS users, your API key can be managed [here](https://data.linz.govt.nz/my/api/)

There are two options for storing your API Key where the script can utilise the key 
for authentication. The API key can be entered in the config.yml or stored as
an environmental variable. Storing the API Key as an environmental variable is 
the safest and therefore recommended way to do this. The environment variable 
the key is to be assigned to must be `LDS_APIKEY=<lds_apikey>` 



### Execute metadata_update.py
Once the config.yaml file has been updated simply run

```metadata_updater``` (if installed via the recommended setup.py method)

### Output

#### Files
For all edited metadata the script will output a backup and edited 
version of the metadata xml file to the destination directory 
(see configuration notes). These files are output for the purposes of 
record keeping, understanding the changes made and debugging purposes. 

Each output file is named `<Data Type>_<Data Id>_<data Ttile>.iso.xml` 
with the backup being appended with "._bak"

For Example:
Layer 4567 would be:
* `layer_50772_nz-primary-parcels.iso.xml`
* `layer_50772_nz-primary-parcels.iso.xml._bak`

#### Logging 
**Important;** a log will be output to the `metadata_updater.log` file. 
If when the script is finished it reports a number of errors 

For example:

```
'Process failed with 5 error(s). Please see log for critical messages'
```
The log must be grepped/searched for critical errors. Each critical error 
indicates a layer / table failed to be updated. The log will indicate which 
layers / tables and why a failure occurred.

Also of importance: The current scope of this script is to only handle tables
and layers. Therefore when documents and sets are encountered they are skipped
over but their ids are logged out. If you are running the script you may want 
to grep / search for these in the log and edit the metadata manually.

These are of log "WARNING" level and formatted as per the below example:


```
2018-02-26 12:12:45,931 [WARNING]: Dataset 1234: Data is of 
"Document" type. This process only handles tables/layers'

```


## Dev Notes
The script uses the 
[Koordinates Python API client](http://koordinates-python.readthedocs.io/en/stable/)

While the Python API client documentation is clear on method use it does not 
provide well defined user work flows. The Editing of the data is based on the 
work flow of; Create a Draft \>> Edit the Draft  \>> Import the draft \>> and 
then publish the layers together as a pulish group.

This work flow of creating a draft through to publishing is easy enough to
follow in the source code of this project. 

### Tests
Unit tests are provided to test all methods not making requests via the Koordinates
Python client

Integration tests are provided to test all methods making requests via the
Koordinates Python client

Both these test can be ran by executing ~/lds-metadata/updater/tests/test.py

Integration test require that the LDS_APIKEY envi var is set. 

The tests are set to run weekly apart of part of CI via Travis.  

### Future Enhancements:
This is so far an initial minimum viable product release.

There are a number of proposed enhancements. This includes utilising an XML Tree 
to be able target tags and only update text in specific fields 

See the list of [enhancements](https://github.com/linz/lds-metadata-updater/issues) 
as store against the GitHub issues of this project

## Feedback
Please supply any feedback and bug reports to the projects
[GitHub Issues page](https://github.com/linz/lds-metadata-updater/issues)
#!/usr/bin/python3

################################################################################
#
# Copyright 2018 Crown copyright (c)
# Land Information New Zealand and the New Zealand Government.
# All rights reserved
#
# This program is released under the terms of the new BSD license. See the
# LICENSE file for more information.
#
################################################################################

import koordinates
import os
import sys
import fileinput
import yaml
import re
import requests
import logging
import shutil
import argparse
import _locale
_locale._getdefaultlocale = (lambda *args: ['en_US', 'utf8'])

# current solution for setup.py
try: 
    import log
except:
    from . import log
    
logger = logging.getLogger(__name__)
ERRORS = 0

class ConfigReader():
    """
    Create a config object that can
    be passed to the scripts methods
    """

    def __init__(self, cwd = None):
        # READ CONFIG

        # get config path
        if not cwd:
            cwd = os.getcwd()
            regex = re.compile(r'(\\|\/)(metadata_updater)$')
            cwd = regex.sub('', cwd)
            cwd = os.path.join(os.sep, cwd, 'metadata_updater', 'config.yaml')

        #check config exists
        if not os.path.exists(cwd):
            raise FileNotFoundError('Can not find config file')

        with open(cwd, 'r') as f:
            config = yaml.load(f)

        # CONNECTION
        if 'Connection' in config:
            if os.getenv('LDS_APIKEY', None):
                self.api_key = os.environ['LDS_APIKEY']
            else:
                self.api_key = config['Connection']['Api_key']
            if not self.api_key:
                raise SystemExit('No LDS API Key Provided')
            self.domain = config['Connection']['Domain']
        else:
            raise SystemExit('CONFIG ERROR: No "Connection" section')
        
        # FIND AND REPLACE TEXT
        if 'Text' in config:
            self.text_mapping = config['Text']['Mapping']
        else:
            raise SystemExit('CONFIG ERROR: No "Text" section')

        # OUTPUT DIR
        if 'Output' in config:
            self.destination_dir = config['Output']['Destination']
        else:
            self.destination_dir = os.getcwd()  + os.path.sep

        # DATA TO PROCESS
        if 'Datasets' in config:
            self.layers = config['Datasets']['Layers']
        else:
            raise SystemExit('CONFIG ERROR: No "Datasets" section')

        # TEST AND DEV CONFIG
        if 'Test' in config:
            self.test_dry_run = config['Test']['Dry_run']
            if self.test_dry_run not in (True, False):
                raise SystemExit('CONFIG ERROR: "Test Dry Run" must be ' \
                '"True" or "False". Got:"{}" instead'.format(self.test_dry_run))

            self.test_overwrite = config['Test']['Overwrite_files']
            if self.test_overwrite not in (True, False):
                raise SystemExit('CONFIG ERROR: "test_overwrite" must be ' \
                '"True" or "False". Got:"{}" instead'.format(self.test_overwrite))
        else:
            raise SystemExit('CONFIG ERROR: No "Test" section')

def post_metadata(draft, file):
    """
    Update the Data Service draft version for the 
    layer with the edited metadata
    """

    global ERRORS

    try:
        xml = open(file).read()
        draft.set_metadata(xml.encode('utf-8'))
        return True
    except koordinates.exceptions.ServerError as e:
        ERRORS += 1
        logger.critical('metadata update for {0} fail with {1}'.format(draft.id,
                                                                        str(e)))
        return False

def remove_illegal_chars(title):
    """
    Removes illegal (unix + win) path chars
    """

    for illegal in ['<', '>', ':', '"', '/', '\\', '|', '?', '*', ',']: 
        if illegal in title:
             title = title.replace(illegal, '')
    return title

def get_metadata(layer, dir, overwrite):
    """
    Download the layers metadata file
    """

    title = remove_illegal_chars(layer.title)
    file_destination = os.path.join(dir,'{0}_{1}_{2}.iso.xml'.format(layer.type,
                                                                                        layer.id, 
                                                                                        title))

    if overwrite:
        file_exists(file_destination)
        layer.metadata.get_xml(file_destination)
    return file_destination

def update_metadata(dest_file, mapping):
    """
    Using the config text mapping, find and 
    replace text in the metadata file.
    Note. back up taken of the original file
    """

    with fileinput.FileInput(dest_file, inplace=True) as file:
        for line in file:
            if mapping['ignore_case']:
                line = re.sub(mapping['search'], mapping['replace'], line.rstrip(), flags=re.IGNORECASE)
            else: 
                line = re.sub(mapping['search'], mapping['replace'], line.rstrip())
            print(line)

def set_metadata(layer, file, publisher):
    """
    Wraps several update methods.
    Gets Draft version of the layer, updates the metadata, 
    imports the draft and adds it to the publish group
    """

    # GET A DRAFT VERSION OF THE LAYER
    draft = get_draft(layer)
    if not draft:
        return False
    # UPDATE METADATA
    success = post_metadata(draft, file)
    # IMPORT DRAFT  File 
    if success:
        add_to_pub_group(publisher, draft)
    return success

def delete_draft(layer, version):
    """
    Delete a draft version 
    """
    global ERRORS

    try:
        layer.delete_version(version)
        logger.info('A draft already exists for {0}. This draft ' \
                'was deleted and a new one created '.format(layer.id))
        return True
    except koordinates.exceptions.ServerError as e:
        logger.critical('{0}'.format(e))
        ERRORS += 1
        return False

def get_draft(layer):
    """
    If no draft exists, create one. 
    Else return the current draft. 
    """
    
    global ERRORS

    if not draft_exists(layer):
        # Create new draft
        draft = layer.create_draft_version()
        return draft
    # A draft already exists for the layer
    draft = layer.get_draft_version()
    if hasattr(draft, 'active_publish'):
        if draft.active_publish:
            # and someone has attempted to publish it
            #TODO // automate deletion of publish group and then draft
            ERRORS += 1
            logger.critical('A draft already exists for {0} and is in a ' \
                            'publish group. THIS HAS NOT BEEN UPDATED '.format(layer.id))
            return None
        else:
            del_draft = delete_draft(layer, draft.version)
            if not del_draft:
                return None
            draft = layer.create_draft_version()
            return draft
    else:   #A draft exists but we know nothing of its state/ history
        del_draft = delete_draft(layer, draft.version)
        if not del_draft:
            return None
        draft = layer.create_draft_version()
        return draft
    

def draft_exists(layer):
    """
    Test if the published layer version is the
    most current. If not the most current version, 
    a draft version therefore already exists 
    """

    current_ver = str(layer.version.id)
    latest_ver = layer.latest_version
    m = re.search('versions\/([0-9]*)\/', latest_ver)
    latest_ver = m.group(1)
    if latest_ver == current_ver:
        return False
    return True

def add_to_pub_group(publisher, draft):
    """
    Add the draft version to the group 
    of layers to be published
    """

    if draft.type == 'layer':
        publisher.add_layer_item(draft)
    elif draft.type == 'table':
        publisher.add_table_item(draft)

def file_exists(file):
    """
    Remove file if duplicate.
    Useful for developers and testers. 
    """

    if os.path.isfile(file):
        os.remove(file)

def get_layer(client, id):
    """
    Get an object representing the layer as
    per the layer id parameter
    """

    global ERRORS

    # FETCH LAYER OBJECT AND METADATA FILE
    logger.info('Processing dataset: {0}'.format(id))

    try:
        layer = client.layers.get(str(id))
        return layer
    except koordinates.exceptions.ServerError as e:
        logger.critical('{0}'.format(e))
        ERRORS += 1
# 
# def update_doc():
#     """ 
#     TODO// Due to the current small number of CC licensed
#     documents this is out of scope 
#     """
#     pass
# 
# def update_set():
#     """ 
#     TODO// Currently out of development scope
#     """
#     pass

def iterate_all(client):
    """
    Iterate through the entire Data Service catalog.
    Returns a generator of all layer / table ids
    *Currently only layers and tables are handled
    """

    for item in client.catalog.list():
        if type(item) == type(koordinates.layers.Layer()):
            yield item.id
        else:
            try:
                logger.warning('Dataset {0}: Data is of "{1}" type. \
                This process only handles tables/layers'.format(item.id, type(item)))
            except:
                pass

def iterate_selective(layers): 
    """
    Iterate through user supplied (via config.yaml)
    dataset IDs. Returns a generator of layer ids to process
    """

    for layer_id in layers:
        yield layer_id

def file_has_text(search_text, ignore_case, file):
    """
    Test for the search text in the file...
    Because there is no point updating and posting a file
    if there are no changes to be made.
    """

    with open(file, 'r') as f:
        for line in f:
            if ignore_case:
                match = re.search(search_text, line, flags=re.IGNORECASE)
            else:
                match = re.search(search_text, line)
            if match:
                return True
        return False

def create_backup(file, overwrite=False):
    """
    Create backup of metadata file to be edited
    """
    if overwrite:
        file_exists(file+'._bak')

    shutil.copyfile(file, file+'._bak')

def get_client(domain, api_key):
    """
    Return Koordinates API client
    """
    
    return koordinates.Client(domain, api_key)

def parse_args(args):
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument('--config_file', 
                            default=None,
                            nargs='?',
                            help="Path to config file")
    return cli_parser.parse_args()

def main():
    """
    Script for updating LDS Metadata. Written for the purpose
    of replacing CC3 text with CC4 text but with scope for 
    extending to other metadata updating tasks     
    """

    global ERRORS

    cli_parser = parse_args(sys.argv[1:])
    config_file = cli_parser.config_file

    layer_count, layers_edited_count = 0,0

    # CONFIG LOGGING
    log.conf_logging('root')

    #CHECK PYTHON VERSION
    if sys.version_info<(3,3):
        raise SystemExit('Error, Python interpreter must be 3.3 or higher')

    # READ CONFIG IN
    config = ConfigReader(config_file)
    mapping = config.text_mapping
    # CREATE DATA OUT DIR
    os.makedirs(config.destination_dir, exist_ok = True) 
    # API CLIENT
    client = get_client(config.domain, config.api_key)
    # PUBLISHER
    publisher = koordinates.Publish()

    if config.test_dry_run:
        logger.info('RUNNING IN TEST DRY RUN MODE')

    # ITERATE OVER LAYERS
    if config.layers in ('ALL', 'all', 'All'):
        layer_ids = iterate_all(client, config)
    else: 
        layer_ids = iterate_selective(config.layers)

    for layer_id in layer_ids:
        layer_count += 1
        get_layer_attempts = 0

        # GET LAYER OBJECT
        # lds is returning 504s (issue #15)
        while get_layer_attempts <= 3:
            get_layer_attempts += 1 
            layer = get_layer(client, layer_id) 
            if layer: 
                break
        if not layer:
            ERRORS += 1
            logger.critical('Failed to get layer {0}. THIS LAYER HAS NOT BEEN PROCESSED'. format(layer_id))
            continue

        # GET METADATA
        file = get_metadata(layer, config.destination_dir, config.test_overwrite)

        # TEST IF SEARCH TEXT IN FILE (IN ORDER OF PRIORITY)
        text_found, backup_created = False, False
        for i in range(1,len(mapping)+1):
            if file_has_text(mapping[i]['search'], mapping[i]['ignore_case'], file):
                text_found = True
                # Only creating a backup if the original is edited 
                if not backup_created:
                    create_backup(file, config.test_overwrite)
                    backup_created = True
                update_metadata(file, mapping[i])

        if not text_found:
            logger.info('Dataset {0}: Skipping, no changes to be made'. format(layer_id))
            continue

        if config.test_dry_run:
            # i.e Do not update data service metadata
            continue

        if set_metadata(layer, file, publisher):
            layers_edited_count +=1


    # PUBLISH
    if layers_edited_count > 0 and not config.test_dry_run:
        try:
            r = client.publishing.create(publisher)
            logger.info('{0} layer(s) processed | {1} layer(s) edited'. format(layer_count, 
                                                                               layers_edited_count))
        except koordinates.exceptions.ServerError as e:
            logger.critical('Publishing failed with fail with {0}'.format(str(e)))
            ERRORS += 1 
        except koordinates.exceptions.BadRequest as e:
            logger.critical('Publishing failed with fail with {0}'.format(str(e)))
            ERRORS += 1

    if ERRORS > 0:
        # print as well as log out
        print ('Process failed with {0} error(s). Please see log for critical messages'.format(ERRORS))
        logger.critical('Process failed with {0} error(s)'.format(ERRORS))
    else: 
        print('COMPLETE. No errors')
        logger.info('COMPLETE. No errors')

if __name__ == "__main__":
    main() 

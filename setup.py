# -*- coding: utf-8 -*-
"""
anzlic-validator setup.py run by
'sudo python setup.py'

Will Check the current system has the correct versions:
- QGIS v2.18
- PyQT v4
- Koordinates python module is installed, if not will install.
- Python v2.7
- An Api file exists, .apikey

Then move the anzlic-validator directory to the correct
HOME/.qgis2/python/plugins directory.
"""
import pip
import os
import sys
import subprocess
try:
    import qgis.utils
except Exception as e:
    print ("Error Incorrect QGIS Version {}".format(e))
try:
    import PyQt4
except Exception as e:
    print ("Error Incorrect PyQt Version {}".format(e))

def install():
    """
    Check Python, QGIS Version, create .apikey file if doesn't already exist,
    move anzlic-validator from current directory to the QGIS Plugin Directory.
    :return: None
    """
    # Python Version
    if '2.7' not in sys.version:
        raise Exception("Error Incorrect Python Version {}".format(sys.version))

    # QGIS Version
    try:
        if '2.18' not in qgis.utils.QGis.QGIS_VERSION:
            raise Exception(
                "Got Version {}".format(qgis.utils.QGis.QGIS_VERSION))
            return
    except Exception as e:
        raise Exception("Error Incorrect QGIS Version {}".format(e))
        return

    # Koordinates Module (Exists or is installed)
    try:
        packages = [package.project_name for package in
                    pip.get_installed_distributions()]
        if 'koordinates' not in packages:
            print ('Installing Koordinates')
            subprocess.call("sudo python2.7 -m pip install koordinates",
                            shell=True)
    except Exception as e:
        raise Exception("Error Installing Koordinates Module: {}".format(e))
        return

    # .apikey File (Exists or is created)
    try:
        home = os.getenv('HOME')
        if not os.path.isfile(home+'/.apikey'):
            print ('Creating File .apikey in {}'.format(home))
            with open(home+'/.apikey') as file:
                file.write('key0=API_KEY')
            print ('Remember to change text "API_KEY" in ' +
                   '{} to your LDS API KEY'.format(home+'/.apikey'))
    except Exception as e:
        raise Exception(
            "Error Creating .apikey file in {}./n{}".format(home, e))

    # Move anzlic-validator from current directory to QGIS Plugin Directory
    try:
        cwd = os.getcwd()
        home = os.getenv('HOME')
        name = cwd.split('/')[len(cwd.split('/'))-1]

        fromDir = cwd
        toDir = '{}/.qgis2/python/plugins/{}'.format(home, name)
        if fromDir != toDir:
            print ('Moving From "{}" To "{}"'.format(fromDir, toDir))
            os.system(
                'sudo -u "$SUDO_USER" cp -rf {} {}'.format(fromDir, toDir))
            os.system('sudo rm -r {}'.format(fromDir))
    except Exception as e:
        raise Exception("Error Moving anzlic-validator to qgis2 plugin " +
                        "directory./n{}".format(e))
        return

if __name__ == "__main__":
    try:
        install()
        print ("Setup Complete")
    except Exception as e:
        print ("Setup Incomplete")
        print (e)

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
    except Exception as er:
        raise Exception("Error Incorrect QGIS Version {}".format(er))

    # Koordinates Module (Exists or is installed)
    try:
        packages = [package.project_name for package in
                    pip.get_installed_distributions()]
        if 'koordinates' not in packages:
            print ('Installing Koordinates')
            subprocess.call("sudo python2.7 -m pip install koordinates",
                            shell=True)
    except Exception as er:
        raise Exception("Error Installing Koordinates Module: {}".format(er))

    # .apikey File (Exists or is created)
    home = None
    try:
        home = os.getenv('HOME')
        if not os.path.isfile(home+'/.apikey'):
            print ('Creating File .apikey in {}'.format(home))
            with open(home+'/.apikey') as f:
                f.write('key0=API_KEY')
            print ('Remember to change text "API_KEY" in ' +
                   '{} to your LDS API KEY'.format(home+'/.apikey'))
    except Exception as er:
        raise Exception(
            "Error Creating .apikey file in {}./n{}".format(home, er))

    # Move anzlic-validator from current directory to QGIS Plugin Directory
    try:
        cwd = os.getcwd()
        home = os.getenv('HOME')
        name = cwd.split('/')[len(cwd.split('/'))-1]

        from_dir = cwd
        to_dir = '{}/.qgis2/python/plugins/{}'.format(home, name)
        if from_dir != to_dir:
            print ('Moving From "{}" To "{}"'.format(from_dir, to_dir))
            os.system(
                'sudo -u "$SUDO_USER" cp -rf {} {}'.format(from_dir, to_dir))
            os.system('sudo rm -r {}'.format(from_dir))
    except Exception as er:
        raise Exception("Error Moving anzlic-validator to qgis2 plugin " +
                        "directory./n{}".format(er))


if __name__ == "__main__":
    try:
        install()
        print ("Setup Complete")
    except Exception as e:
        print ("Setup Incomplete")
        print (e)

# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LINZ_Metadata
                                 A QGIS plugin
 Plugin to provide a LINZ specific metadata editor and uploader.
                             -------------------
        begin                : 2018-04-27
        copyright            : (C) 2018 by Ashleigh Ross
        email                : aross@linz.govt.nz
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


def classFactory(iface):
    """Load LINZ_Metadata class from file LINZ_Metadata.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from linz_metadata import LINZ_Metadata
    return LINZ_Metadata(iface)

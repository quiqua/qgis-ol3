# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OL3
                                 A QGIS plugin
 Creates OpenLayers map from QGIS layers
                             -------------------
        begin                : 2014-04-25
        copyright            : (C) 2014 by Victor Olaya
        email                : volayaf@gmail.com
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
    from ol3 import OL3Plugin
    return OL3Plugin(iface)

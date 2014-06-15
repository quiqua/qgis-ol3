import os
import re
from PyQt4.QtCore import *
from qgis.core import *
import subprocess

NO_POPUP = 0
ALL_ATTRIBUTES = 1

TYPE_MAP = {
    QGis.WKBPoint: 'Point',
    QGis.WKBLineString: 'LineString',
    QGis.WKBPolygon: 'Polygon',
    QGis.WKBMultiPoint: 'MultiPoint',
    QGis.WKBMultiLineString: 'MultiLineString',
    QGis.WKBMultiPolygon: 'MultiPolygon',
    }
    
def tempFolder():
    tempDir = os.path.join(unicode(QDir.tempPath()), 'qgis2ol')
    if not QDir(tempDir).exists():
        QDir().mkpath(tempDir)

    return unicode(os.path.abspath(tempDir))
    
def getUsedFields(layer):
    fields = []
    try:
        fields.append(layer.rendererV2().classAttribute())
    except:
        pass
    labelsEnabled = str(layer.customProperty("labeling/enabled")).lower() == "true"
    if labelsEnabled:
        fields.append(layer.customProperty("labeling/fieldName"))
    return fields
        
def exportLayers(layers, folder, precision, optimize, popupField):        
    epsg3587 = QgsCoordinateReferenceSystem("EPSG:3857")
    layersFolder = os.path.join(folder, "layers")
    QDir().mkpath(layersFolder)    
    reducePrecision = re.compile(r"([0-9]+\.[0-9]{%s})([0-9]+)" % str(int(precision)))
    removeSpaces = lambda txt:'"'.join( it if i%2 else ''.join(it.split())
                         for i,it in enumerate(txt.split('"')))
    for layer, popup in zip(layers, popupField):           
        if layer.type() == layer.VectorLayer: 
            usedFields = getUsedFields(layer)           
            if popup != ALL_ATTRIBUTES:            
                uri = TYPE_MAP[layer.wkbType()]
                crs = layer.crs()
                if crs.isValid():
                    uri += '?crs=' + crs.authid() 
                if popup != NO_POPUP:
                    usedFields.append(popup)
                for field in usedFields:
                    fieldType = layer.pendingFields().field(field).type()
                    fieldType = "double" if fieldType == QVariant.Double or fieldType == QVariant.Int else "string"
                    uri += '&field=' + str(field) + ":" + fieldType    
                newlayer = QgsVectorLayer(uri, layer.name(), 'memory')
                writer = newlayer.dataProvider()
                outFeat = QgsFeature()
                for feature in layer.getFeatures():  
                    outFeat.setGeometry(feature.geometry())
                    attrs = [feature[f] for f in usedFields]
                    if attrs:                        
                        outFeat.setAttributes(attrs)              
                    writer.addFeatures([outFeat])
                layer = newlayer            
            
            path = os.path.join(layersFolder, safeName(layer.name()) + ".js")
            QgsVectorFileWriter.writeAsVectorFormat(layer,  path, "utf-8", epsg3587, 'GeoJson')                
            with open(path) as f:
                lines = f.readlines()
            with open(path, "w") as f:            
                f.write("var %s = " % ("geojson_" + safeName(layer.name())))
                for line in lines:                                
                    line = reducePrecision.sub(r"\1", line)
                    if optimize:
                        line = line.strip("\n\t ")
                        line = removeSpaces(line)
                    f.write(line)      
        elif layer.type() == layer.RasterLayer:
            orgFile = layer.source()
            destFile = os.path.join(layersFolder, safeName(layer.name()) + ".jpg")
            settings = QSettings()
            path = unicode(settings.value('/GdalTools/gdalPath', ''))
            envval = unicode(os.getenv('PATH'))
            if not path.lower() in envval.lower().split(os.pathsep):
                envval += '%s%s' % (os.pathsep, path)
                os.putenv('PATH', envval)
            command = ''.join([])
            proc = subprocess.Popen(
                ['gdal_translate -of JPEG -a_srs EPSG:3857 %s %s' % (orgFile, destFile)],
                shell=True,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=False,
                )
            

def safeName(name):
    return name.replace(" ", "")                
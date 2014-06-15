import os
import re
import math
import shutil
from qgis.core import *
from utils import exportLayers, safeName
from qgis.utils import iface
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from utils import ALL_ATTRIBUTES

baseLayers  = {
    "Stamen watercolor": "new ol.layer.Tile({title: 'Stamen watercolor', source: new ol.source.Stamen({layer: 'watercolor'})});",
    "Stamen toner": "new ol.layer.Tile({title: 'Stamen toner', source: new ol.source.Stamen({layer: 'toner'})});",
    "OSM": "new ol.layer.Tile({title: 'OSM', source: new ol.source.OSM()});",
    "MapQuest": "new ol.layer.Tile({title: 'MapQuest', source: new ol.source.MapQuest({layer: 'sat'})});"
}

def writeOL(layers, groups, popup, visible, settings, folder): 
    QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
    try:
        dst = os.path.join(folder, "resources")
        if not os.path.exists(dst):
            shutil.copytree(os.path.join(os.path.dirname(__file__), "resources"), dst)
        precision = settings["Data export"]["Precision"]
        optimize = settings["Data export"]["Minify GeoJSON files"]
        cleanUnusedFields = settings["Data export"]["Delete unused fields"]
        if not cleanUnusedFields:
            usedFields = [ALL_ATTRIBUTES] * len(popup)
        else:
            usedFields = popup
        exportLayers(layers, folder, precision, optimize, usedFields)
        exportStyles(layers, folder)   
        writeLayersAndGroups(layers, groups, visible, folder, settings)   
        geojsonVars ="\n".join(['<script src="layers/%s"></script>' % (safeName(layer.name()) + ".js") 
                                for layer in layers if layer.type() == layer.VectorLayer])                      
        styleVars =  "\n".join(['<script src="styles/%s_style.js"></script>' % (safeName(layer.name())) 
                                for layer in layers if layer.type() == layer.VectorLayer])  
        popupLayers = "popupLayers = [%s];" % ",".join(['"%s"' % field if isinstance(field, basestring) else str(field) for field in popup])    
        controls = []
        if settings["Appearance"]["Add scale bar"]:
            controls.append("new ol.control.ScaleLine({})")
        if settings["Appearance"]["Add layers list"]:
            controls.append('new Boundless.LayersControl({groups: {default: {title: "Layers"}}})')
        mapbounds = bounds(settings["Scale/Zoom"]["Extent"] == "Canvas extent", layers) 
        mapextent = "extent: %s," % mapbounds if settings["Scale/Zoom"]["Restrict to extent"] else ""
        maxZoom = int(settings["Scale/Zoom"]["Max zoom level"])
        minZoom = int(settings["Scale/Zoom"]["Min zoom level"])
        onHover = str(settings["Appearance"]["Show popups on hover"]).lower()
        highlight = str(settings["Appearance"]["Highlight features"]).lower()
        view = "%s maxZoom: %d, minZoom: %d" % (mapextent, maxZoom, minZoom)
        values = {"@STYLEVARS@": styleVars,
                    "@GEOJSONVARS@": geojsonVars,
                    "@BOUNDS@": mapbounds,
                    "@CONTROLS@": ",".join(controls),
                    "@POPUPLAYERS@": popupLayers,
                    "@VIEW@": view,
                    "@ONHOVER@": onHover,
                    "@DOHIGHLIGHT@": highlight}    
        
        with open(os.path.join(folder, "index.html"), "w") as f:
            f.write(replaceInTemplate(settings["Appearance"]["Template"] + ".html", values))            
    finally:
        QApplication.restoreOverrideCursor() 
        
def writeLayersAndGroups(layers, groups, visible, folder, settings):
    baseLayer = "var baseLayer = " + baseLayers[settings["Appearance"]["Base layer"]]   
    scaleVisibility = settings["Scale/Zoom"]["Use layer scale dependent visibility"]
    layerVars = "\n".join([layerToJavascript(layer, scaleVisibility) for layer in layers]) 
    groupVars = ""
    groupedLayers = {}
    for group, groupLayers in groups.iteritems():        
        groupVars +=  ('''var %s = new ol.layer.Group({
                                layers: [%s], 
                                title: "%s"});''' % 
                ("group_" + group, ",".join(["lyr_" + safeName(layer.name()) for layer in groupLayers]),
                group))
        for layer in groupLayers:
            groupedLayers[layer.id()] = group    
    mapLayers = ["baseLayer"] 
    usedGroups = []
    for layer in layers:
        if layer.id() in groupedLayers:
            groupName = groupedLayers[layer.id()]
            if groupName not in usedGroups:
                mapLayers.append("group_" + safeName(groupName))
                usedGroups.append(groupName)
        else:
            mapLayers.append("lyr_" + safeName(layer.name()))
    visibility = "\n".join(["%s.setVisible(%s);" % (layer, str(v).lower()) for layer, v in zip(mapLayers[1:], visible)])
    layersList = "var layersList = [%s];" % ",".join([layer for layer in mapLayers]) 
    path = os.path.join(folder, "layers", "layers.js")  
    with open(path, "w") as f: 
        f.write(baseLayer + "\n")
        f.write(layerVars + "\n")
        f.write(groupVars + "\n")
        f.write(visibility + "\n")
        f.write(layersList)

    
def replaceInTemplate(template, values):
    path = os.path.join(os.path.dirname(__file__), "templates", template)
    with open(path) as f:
        lines = f.readlines()
    s = "".join(lines)    
    for name,value in values.iteritems():
        s = s.replace(name, value)
    return s

def bounds(useCanvas, layers):    
    if useCanvas: 
        canvas = iface.mapCanvas()
        canvasCrs = canvas.mapRenderer().destinationCrs()    
        transform = QgsCoordinateTransform(canvasCrs, QgsCoordinateReferenceSystem("EPSG:3857"))
        extent = transform.transform(canvas.extent())
    else:
        extent = None
        for layer in layers:
            transform = QgsCoordinateTransform(layer.crs(), QgsCoordinateReferenceSystem("EPSG:3857"))
            layerExtent = transform.transform(layer.extent())
            if extent is None:
                extent = layerExtent
            else:
                extent.combineExtentWith(layerExtent)            
                    
    return "[%f, %f, %f, %f]" % (extent.xMinimum(), extent.yMinimum(), 
                                extent.xMaximum(), extent.yMaximum())
        
def layerToJavascript(layer, scaleVisibility):
    #TODO: change scale to resolution
    if scaleVisibility and layer.hasScaleBasedVisibility():
        minResolution = "\nminResolution:%s,\n" % str(layer.minimumScale())
        maxResolution = "maxResolution:%s,\n" % str(layer.maximumScale()) 
    else:
        minResolution = ""
        maxResolution = ""
    layerName = safeName(layer.name()) 
    if layer.type() == layer.VectorLayer:
        return ('''var lyr_%(n)s = new ol.layer.Vector({
                source: new ol.source.GeoJSON({object: geojson_%(n)s}),%(min)s %(max)s
                style: style_%(n)s,
                title: "%(name)s"
            });''' %  
            {"name": layer.name(), "n":layerName, "min": minResolution, 
             "max": maxResolution})
    elif layer.type() == layer.RasterLayer:
        if layer.providerType().lower() == "wms":
            source = layer.source()
            layers = re.search(r"layers=(.*?)(?:&|$)", source).groups(0)[0]
            url = re.search(r"url=(.*?)(?:&|$)", source).groups(0)[0]
            return '''var lyr_%(n)s = new ol.layer.Tile({
                        source: new ol.source.TileWMS(({
                          url: %(url)s,
                          params: {"LAYERS": "%(layers)s", "TILED": "true"},
                        })),
                        title: "%(name)s"
                      });''' % {"layers": layers, "url": url, "n": layerName, "name": layer.name()}
        elif layer.providerType().lower() == "gdal":
            provider = layer.dataProvider()
            transform = QgsCoordinateTransform(provider.crs(), QgsCoordinateReferenceSystem("EPSG:3857"))
            extent = transform.transform(provider.extent())
            sExtent = "[%f, %f, %f, %f]" % (extent.xMinimum(), extent.yMinimum(), 
                                    extent.xMaximum(), extent.yMaximum())
            return '''var lyr_%(n)s = new ol.layer.Image({
                            opacity: 1,
                            title: "%(name)s",
                            source: new ol.source.ImageStatic({
                               url: "./layers/%(n)s.jpg",
                                projection: 'EPSG:3857',
                                alwaysInRange: true,
                                imageSize: [%(col)d, %(row)d],
                                imageExtent: %(extent)s
                            })
                        });''' % {"n": layerName, "extent": sExtent, "col": provider.xSize(), 
                                    "name": layer.name(), "row": provider.ySize()} 

    
def exportStyles(layers, folder):
    stylesFolder = os.path.join(folder, "styles")
    QDir().mkpath(stylesFolder)
    for layer in layers:
        if layer.type() != layer.VectorLayer:
            continue
        labelsEnabled = str(layer.customProperty("labeling/enabled")).lower() == "true"
        if (labelsEnabled):
            labelField = layer.customProperty("labeling/fieldName")
            labelText = 'feature.get("%s")' % labelField
        else:
            labelText = '""'  
        defs = ""
        try:
            renderer = layer.rendererV2()
            if isinstance(renderer, QgsSingleSymbolRendererV2):
                symbol = renderer.symbol()
                style = "var style = " + getSymbolAsStyle(symbol, stylesFolder)  
                value = 'var value = ""'              
            elif isinstance(renderer, QgsCategorizedSymbolRendererV2):                
                defs += "var categories_%s = {" % safeName(layer.name())                
                cats = []
                for cat in renderer.categories():
                    cats.append('"%s": %s' % (cat.value(), getSymbolAsStyle(cat.symbol(), stylesFolder)))
                defs +=  ",\n".join(cats) + "};"     
                value = 'var value = feature.get("%s");' %  renderer.classAttribute()         
                style = '''var style = categories_%s[value]'''  % (safeName(layer.name()))
            elif isinstance(renderer, QgsGraduatedSymbolRendererV2):
                varName = "ranges_" + safeName(layer.name())
                defs += "var %s = [" % varName               
                ranges = []
                for ran in renderer.ranges():
                    symbolstyle = getSymbolAsStyle(ran.symbol(), stylesFolder)
                    ranges.append('[%f, %f, %s]' % (ran.lowerValue(), ran.upperValue(), symbolstyle))
                defs += ",\n".join(ranges) + "];" 
                value = 'var value = feature.get("%s");' %  renderer.classAttribute()                
                style = '''var style = %(v)s[0][2];
                            for (i = 0; i < %(v)s.length; i++){
                                var range = %(v)s[i];
                                if (value > range[0] && value<=range[1]){
                                    style =  range[2];
                                }
                            }
                            ''' % {"v": varName}
            size = layer.customProperty("labeling/fontSize")
            r = layer.customProperty("labeling/textColorR")
            g = layer.customProperty("labeling/textColorG")
            b = layer.customProperty("labeling/textColorB")
            color = "rgba(%s, %s, %s, 255)" % (r,g,b)
            style = '''function(feature, resolution){
                        %(value)s
                        %(style)s;
                        var labelText = %(label)s;
                        var key = value + "_" + labelText

                        if (!%(cache)s[key]){
                            var text = new ol.style.Text({
                                  font: '%(size)spx Calibri,sans-serif',
                                  text: labelText,
                                  fill: new ol.style.Fill({
                                    color: "%(color)s"
                                  }),
                                });
                            %(cache)s[key] = new ol.style.Style({"text": text});
                        }
                        var allStyles = [%(cache)s[key]];
                        allStyles.push.apply(allStyles, style);
                        return allStyles;
                    }''' % {"style": style, "label": labelText, "cache": "styleCache_" + safeName(layer.name()),
                            "size": size, "color": color, "value": value} 
        except Exception, e:      
            style = "{}"
            
        path = os.path.join(stylesFolder, safeName(layer.name()) + "_style.js")  

        with open(path, "w") as f: 
            f.write('''%(defs)s
                    var styleCache_%(name)s={}
                    var style_%(name)s = %(style)s;''' % 
                {"defs":defs, "name":safeName(layer.name()), "style":style})                    
          

def getRGBAColor(color, alpha):
    r,g,b,_ = color.split(",")
    return '"rgba(%s)"' % ",".join([r, g, b, str(alpha)])


def getSymbolAsStyle(symbol, stylesFolder):
    styles = []
    alpha = symbol.alpha()
    for i in xrange(symbol.symbolLayerCount()):
        sl = symbol.symbolLayer(i)
        props = sl.properties()
        if isinstance(sl, QgsSimpleMarkerSymbolLayerV2):                    
            color =  getRGBAColor(props["color"], alpha)                                        
            style = "image: %s" % getCircle(color)
        elif isinstance(sl, QgsSvgMarkerSymbolLayerV2):                    
            path = os.path.join(stylesFolder, os.path.basename(sl.path()))
            shutil.copy(sl.path(), path)                                   
            style = "image: %s" % getIcon(path, sl.size())
        elif isinstance(sl, QgsSimpleLineSymbolLayerV2):
            color = getRGBAColor(props["color"], alpha) 
            style = "stroke: %s" % (getStrokeStyle(color, props["penstyle"] != "solid", props["width"]))
        elif isinstance(sl, QgsSimpleFillSymbolLayerV2):
            borderColor =  getRGBAColor(props["color_border"], alpha) 
            fillColor =  getRGBAColor(props["color"], alpha)                                        
            style = ('''stroke: %s, 
                        fill: %s''' % 
                    (getStrokeStyle(borderColor, props["style_border"] != "solid", props["width_border"]),
                     getFillStyle(fillColor)))
        else:
            style = ""
        styles.append('''new ol.style.Style({
                            %s
                        })
                        ''' % style)
    return "[ %s]" % ",".join(styles)
                             
def getCircle(color):
    return ("new ol.style.Circle({radius: 3, stroke: %s, fill: %s})" % 
                (getStrokeStyle("'rgba(0,0,0,255)'", False, "0.5"), getFillStyle(color)))

def getIcon(path, size):
    size  = math.floor(float(size) * 3.8) 
    anchor = size / 2
    return '''new ol.style.Icon({
                  size: [%(s)d, %(s)d],
                  anchor: [%(a)d, %(a)d],
                  anchorXUnits: "pixels",
                  anchorYUnits: "pixels",
                  src: "%(path)s"
            })''' % {"s": size, "a":anchor, "path": path.replace("\\", "\\\\")}

def getStrokeStyle(color, dashed, width):
    width  = math.floor(float(width) * 3.8) 
    dash = "[3]" if dashed else "null"
    return "new ol.style.Stroke({color: %s, lineDash: %s, width: %d})" % (color, dash, width)

def getFillStyle(color):
    return "new ol.style.Fill({color: %s})" % color


import os

def getTemplates():
	folder = os.path.join(os.path.dirname(__file__), "templates")
	return tuple(f[:f.find(".")] for f in os.listdir(folder) if f.endswith("html"))


paramsOL = {
	"Appearance":{
		"Add layers list": True,
		"Base layer": (			
			"OSM",
			"MapQuest",
			"Stamen watercolor",
			"Stamen toner"
			),
		"Add scale bar": True,
		"Show popups on hover": False,
		"Highlight features": False,
		"Template": getTemplates()
	},
	"Data export" : {
		"Precision": 3,
		"Minify GeoJSON files": True,
		"Delete unused fields": True
	},
	"Scale/Zoom":{
		"Use layer scale dependent visibility": True,
		"Extent": ("Canvas extent", "Fit to layers extent"),
		"Restrict to extent": False,
		"Max zoom level": 28,
		"Min zoom level": 1,
	}

}
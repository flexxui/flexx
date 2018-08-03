# doc-export: PlotlyGeoDemo
"""
A demo with geo data shown with plotly.
"""

from flexx import flx


records = """
Albania,13.40,ALB
Andorra,4.80,AND
Armenia,10.88,ARM
Austria,436.10,AUT
Belgium,527.80,BEL
Bosnia and Herzegovina,19.55,BIH
Bulgaria,55.08,BGR
Croatia,57.18,HRV
Cyprus,21.34,CYP
Czech Republic,205.60,CZE
Denmark,347.20,DNK
Estonia,26.36,EST
Finland,276.30,FIN
France,2902.00,FRA
United Kingdom,2848.00,GBR
Georgia,16.13,GEO
Germany,3820.00,DEU
Greece,246.40,GRC
Hungary,129.70,HUN
Ireland,245.80,IRL
Italy,2129.00,ITA
Jordan,36.55,JOR
Kosovo,5.99,KSV
Kuwait,179.30,KWT
Latvia,32.82,LVA
Luxembourg,63.93,LUX
Malta,10.57,MLT
Moldova,7.74,MDA
Monaco,6.06,MCO
Mongolia,11.73,MNG
Netherlands,880.40,NLD
Norway,511.60,NOR
Poland,552.20,POL
Portugal,228.20,PRT
Romania,199.00,ROU
Slovakia,99.75,SVK
Slovenia,49.93,SVN
Spain,1400.00,ESP
Sweden,559.10,SWE
Switzerland,679.00,CHE
Ukraine,134.90,UKR
"""

# Parse records
country_names = []
country_codes = []
country_gdps = []
for line in records.strip().splitlines():
    name, gdp, code = line.split(',')
    country_names.append(name)
    country_codes.append(code)
    country_gdps.append(float(gdp))


# Define the plot. Its probably easier to use the Python Plotly library,
# but in this way this example does not require additional dependencies.

data = [{
    'type': 'scattergeo',
    'mode': 'markers',
    'locations': country_codes,
    'marker': {
        'size': [v**0.5 for v in country_gdps],
        'color': country_gdps,
        'cmin': 0,
        'cmax': 2000,
        'colorscale': 'Viridis',
        'colorbar': {'title': 'GDP'},
        'line': {'color': 'black'}
    },
    'name': 'Europe GDP'
}]

layout = {
    'geo': {
        'scope': 'europe',
        'resolution': 50
    }
}


class PlotlyGeoDemo(flx.HBox):

    def init(self):
        flx.PlotlyWidget(data=data, layout=layout)


if __name__ == '__main__':
    flx.launch(PlotlyGeoDemo)
    flx.run()

# doc-export: AltairExample
""" 
Example demonstrating an Altair plot in Flexx.
"""


from flexx import flx
import altair as alt
from vega_datasets import data


cars = data.cars()

c = alt.Chart(cars).mark_circle(size=160).encode(
    x='Horsepower',
    y='Miles_per_Gallon',
    color='Origin',
    tooltip=['Name', 'Origin', 'Horsepower', 'Miles_per_Gallon']
).interactive()

spec = c.to_dict()
spec.pop('$schema')  # avoid key error during BSDF encoding
# spec = c.to_json() # alternatively, just stringify now


class AltairExample(flx.HBox):  # HBox and Vega-embed don't play nice together
    def init(self):
        flx.VegaWidget(spec=spec)


if __name__ == '__main__':
    m = flx.launch(AltairExample)
    flx.run()

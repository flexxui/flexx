"""
Example demonstrating how to integrate famous eChart into flexx.
"""

#by Scott_Huang@qq.com   at 2020-02-29

from flexx import flx

# import os
#
# # use local assests, I download the echarts.min.js and put in local folder
# BASE_DIR = os.getcwd()
# with open(BASE_DIR + '/static/echarts/echarts.min.js',encoding="utf-8") as f:
#     script = f.read()
# flx.assets.associate_asset(__name__, 'echart_script.js', script)

# or use the online CDN. For desktop app, would better use local assets
flx.assets.associate_asset(__name__
    , 'https://cdnjs.cloudflare.com/ajax/libs/echarts/4.6.0/echarts.min.js')

class EchartExample(flx.Widget):

    echart_id = "echart_main_default_id"
    echart_options = flx.DictProp({},
            settable=True, doc="""the echarts options""")


    my_default_option ={
            'title': {
                'text': 'ECharts entry example'
            },
            'tooltip': {},
            'legend': {
                'data': ['Sales']
            },
            'xAxis': {
                'data': ["shirt", "cardign", "chiffon shirt",
                         "pants", "heels", "socks"]
            },
            'yAxis': {},
            'series': [{
                'name': 'Sales',
                'type': 'bar',
                'data': [5, 20, 36, 10, 10, 20]}]
        };

    @flx.action
    def change_chart(self):
        global myChart
        self.my_option = self.my_default_option
        self.my_option['series'][0]['data'] = [1, 2, 3, 4, 5, 6]
        # print(repr(self.my_option))
        self._mutate_echart_options(self.my_option)
        myChart.setOption(self.echart_options)


    @flx.action
    def reset_chart(self):
        global myChart
        self.my_option = self.my_default_option
        self.my_option['series'][0]['data'] = [5, 20, 36, 10, 10, 20]
        # print(repr(self.my_option))
        self._mutate_echart_options(self.my_option)
        myChart.setOption(self.echart_options)


    def _render_dom(self):
        node =  [
                    flx.create_element('div',
                    {
                    'id':self.echart_id,
                    'style':'width: 800px;height:400px;'
                    },
                    'Hello Flexx Echart at Create Dom!'),
                    flx.create_element('script', {
                    'type':'text/javascript'
                    }, """
                    // based on prepared DOM, initialize echarts instance
                    var myChart = echarts.init(
                        document.getElementById('""" + self.echart_id + """'
                        ));
                    """),

                    flx.create_element('button', {'onclick': self.change_chart},
                    'Change Chart'),

                    flx.create_element('button', {'onclick': self.reset_chart},
                    'Reset Chart'),
                ]
        self.reset_chart()
        return node

if __name__ == '__main__':
    app = flx.App(EchartExample)
    app.launch("chrome-app")
    flx.run()

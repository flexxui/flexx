# doc-export: Twente
# flake8: noqa
"""
Examample data-viz app. It shows real temperature data from the region
where I live. The data are monthly average temperatures for the pas 65
years. The month can be selected with a slider. Via another slider, the
data can be smoothed so the upward trend can be made more apparent.
This app can be exported to a standalone HTML document.
"""


from flexx import app, ui, event

# Raw data obtained from 
# http://www.knmi.nl/klimatologie/maandgegevens/datafiles/mndgeg_290_tg.txt

raw_data = """
Deze gegevens mogen vrij worden gebruikt mits de volgende bronvermelding wordt gegeven:
KONINKLIJK NEDERLANDS METEOROLOGISCH INSTITUUT (KNMI)

These data can be used freely provided that the following source is acknowledged:
ROYAL NETHERLANDS METEOROLOGICAL INSTITUTE

MAAND- en JAARGEMIDDELDE TEMPERATUREN (0.1 graden Celsius)
MONTHLY AND YEARLY MEAN TEMPERATURES (0.1 degrees Celsius)

STN = stationsnummer / WMO-number = 06... (235=De Kooy,240=Schiphol,260=De Bilt,270=Leeuwarden,280=Eelde,
      290=Twenthe,310=Vlissingen,344=Rotterdam,370=Eindhoven,380=Maastricht)


STN,YYYY,   JAN,   FEB,   MAR,   APR,   MAY,   JUN,   JUL,   AUG,   SEP,   OCT,   NOV,   DEC,  YEAR

290,1951,    35,    35,    34,    74,   120,   154,   169,   171,   155,    85,    82,    44,    97
290,1952,    19,    20,    43,   107,   129,   149,   172,   173,   111,    80,    23,    10,    86
290,1953,    11,    15,    47,    91,   133,   162,   170,   167,   140,   115,    71,    48,    98
290,1954,   -11,   -10,    57,    65,   128,   156,   142,   160,   138,   116,    65,    51,    88
290,1955,    -1,    -5,    16,    82,   100,   146,   179,   181,   146,    92,    58,    42,    86
290,1956,    17,   -71,    50,    50,   127,   130,   166,   140,   146,    94,    46,    49,    79
290,1957,    32,    49,    80,    83,   102,   166,   176,   156,   124,   107,    60,    24,    97
290,1958,    16,    32,    15,    62,   129,   148,   168,   177,   157,   109,    54,    44,    93
290,1959,    12,     7,    72,   103,   131,   164,   192,   180,   156,   111,    52,    39,   102
290,1960,    21,    25,    55,    88,   130,   161,   153,   155,   133,   107,    73,    26,    94
290,1961,    14,    61,    71,   104,   106,   157,   152,   158,   172,   114,    45,     8,    97
290,1962,    31,    21,    14,    80,    99,   135,   145,   152,   127,   104,    39,   -14,    78
290,1963,   -63,   -38,    45,    91,   112,   158,   165,   153,   137,    91,    81,   -15,    76
290,1964,    -1,    28,    23,    91,   143,   156,   169,   161,   142,    78,    58,    20,    89
290,1965,    24,    11,    37,    76,   117,   150,   147,   152,   131,    98,    19,    38,    83
290,1966,    -3,    37,    46,    87,   135,   171,   155,   158,   134,   111,    38,    36,    92
290,1967,    32,    48,    64,    70,   128,   146,   181,   163,   141,   116,    47,    25,    97
290,1968,     7,    13,    59,    95,   106,   155,   161,   168,   142,   111,    50,    -7,    88
290,1969,    37,    -7,    13,    77,   129,   145,   175,   168,   137,   115,    60,   -25,    85
290,1970,    -4,     4,    21,    56,   125,   170,   154,   165,   136,    99,    72,    18,    85
290,1971,    22,    32,    23,    78,   138,   138,   170,   171,   125,    97,    46,    50,    91
290,1972,    -3,    34,    61,    71,   116,   137,   172,   151,   108,    82,    53,    32,    85
290,1973,    23,    23,    49,    54,   119,   160,   171,   176,   145,    83,    49,    23,    90
290,1974,    51,    42,    55,    85,   112,   143,   147,   164,   129,    64,    62,    66,    93
290,1975,    62,    27,    43,    69,   108,   147,   176,   195,   148,    77,    45,    23,    93
290,1976,    26,    19,    22,    71,   129,   173,   188,   170,   134,   107,    61,     7,    92
290,1977,    22,    45,    68,    60,   117,   143,   161,   158,   126,   114,    61,    42,    93
290,1978,    27,     2,    61,    67,   121,   145,   150,   147,   136,   110,    66,    13,    87
290,1979,   -39,   -22,    41,    73,   116,   150,   150,   151,   125,    96,    45,    46,    78
290,1980,    -8,    38,    38,    74,   115,   145,   153,   166,   146,    87,    42,    29,    85
290,1981,    16,     9,    81,    87,   138,   147,   163,   164,   148,    85,    60,   -10,    91
290,1982,     3,    23,    50,    71,   122,   161,   186,   169,   160,   112,    76,    31,    97
290,1983,    57,     0,    56,    89,   111,   159,   191,   174,   134,    94,    54,    27,    96
290,1984,    23,    14,    33,    71,   100,   129,   150,   168,   124,   109,    73,    35,    86
290,1985,   -46,   -14,    35,    81,   132,   131,   165,   150,   132,    97,    17,    52,    78
290,1986,    16,   -46,    45,    68,   137,   160,   162,   151,   105,   109,    77,    41,    85
290,1987,   -40,    17,    13,   103,    99,   137,   163,   155,   145,   104,    61,    38,    83
290,1988,    58,    42,    43,    81,   144,   145,   160,   166,   139,   104,    53,    55,    99
290,1989,    41,    48,    77,    65,   138,   159,   178,   171,   154,   122,    50,    44,   104
290,1990,    50,    73,    79,    84,   138,   151,   161,   182,   122,   119,    54,    35,   104
290,1991,    29,    -9,    83,    81,    97,   126,   188,   173,   147,    94,    50,    32,    91
290,1992,    22,    47,    64,    83,   154,   170,   182,   180,   143,    73,    74,    33,   102
290,1993,    42,    12,    51,   112,   142,   152,   157,   146,   125,    86,    15,    44,    90
290,1994,    44,     6,    70,    81,   123,   151,   213,   174,   133,    86,    87,    48,   101
290,1995,    27,    60,    46,    89,   124,   145,   200,   187,   136,   124,    55,   -16,    98
290,1996,   -16,   -10,    23,    89,   106,   151,   161,   175,   115,    99,    52,    -6,    78
290,1997,   -17,    58,    72,    70,   124,   157,   173,   201,   134,    89,    57,    41,    97
290,1998,    43,    57,    67,    90,   144,   155,   159,   160,   144,    90,    29,    35,    98
290,1999,    45,    26,    66,    97,   135,   149,   188,   172,   177,   101,    59,    41,   105
290,2000,    37,    52,    63,   102,   145,   160,   152,   169,   150,   111,    77,    46,   105
290,2001,    22,    37,    42,    79,   140,   147,   183,   183,   128,   140,    61,    21,    99
290,2002,    39,    65,    64,    89,   135,   167,   174,   186,   139,    86,    71,    16,   103
290,2003,    16,     7,    68,    93,   134,   179,   185,   193,   139,    66,    78,    33,    99
290,2004,    27,    40,    53,   103,   116,   152,   165,   188,   149,   110,    54,    27,    99
290,2005,    43,    14,    58,   102,   125,   162,   176,   157,   152,   129,    61,    33,   101
290,2006,     4,    18,    32,    85,   143,   168,   222,   159,   177,   136,    88,    62,   108
290,2007,    61,    54,    74,   125,   139,   174,   169,   168,   133,    93,    61,    31,   107
290,2008,    59,    47,    53,    83,   150,   164,   180,   173,   131,    97,    62,    18,   101
290,2009,     1,    26,    55,   125,   137,   153,   178,   182,   144,    93,    94,    17,   100
290,2010,   -17,     9,    58,    93,   100,   164,   204,   164,   126,    95,    52,   -27,    85
290,2011,    27,    36,    52,   124,   138,   162,   158,   168,   152,   106,    60,    55,   103
290,2012,    36,     1,    77,    82,   145,   145,   169,   184,   134,    96,    64,    41,    98
290,2013,    15,     9,    12,    82,   116,   154,   188,   179,   138,   118,    59,    55,    94
290,2014,    48,    64,    81,   118,   127,   157,   195,   157,   153,   132,    80,    41,   113
"""

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 
            'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'total']

def parse_data(raw_data):
    years, data = [], [[] for i in range(13)]
    for line in raw_data.splitlines():
        if line.startswith('290'):
            parts = [int(i.strip()) for i in line.split(',')]
            years.append(parts[1])
            for i in range(13):
                data[i].append(parts[i+2]/10.0)
    return years, data

years, data = parse_data(raw_data)


class Twente(ui.Widget):
    
    def init(self):
        
        with ui.HBox():
            ui.Widget(flex=1)
            with ui.VBox(flex=0):
                with ui.GroupWidget(title='Plot options'):
                    with ui.VBox():
                        self.month_label = ui.Label(text='Month')
                        self.month = ui.Slider(max=12, step=1, value=12)
                        self.smoothing_label = ui.Label(text='Smoothing')
                        self.smoothing = ui.Slider(max=20, step=2)
                ui.Widget(flex=1)
            with ui.VBox(flex=4):
                self.plot = ui.PlotWidget(flex=1,
                                            xdata=years, yrange=(-5, 20),
                                            title='Average monthly temperature',
                                            xlabel='year', ylabel=u'temperature (°C)')
                # ui.Widget(flex=0, style='height:30px')
            ui.Widget(flex=1)

    class JS:
        
        def init(self):
            super().init()
            self._update_plot()
        
        @event.connect('month.value', 'smoothing.value')
        def _update_plot(self, *events):
            month = self.month.value
            smoothing = self.smoothing.value
            self.month_label.text = 'Month (%s)' % months[month]
            self.smoothing_label.txt = 'Smoothing (%i)' % smoothing
            
            yy1 = data[month]
            yy2 = []
            
            sm2 = int(smoothing / 2)
            for i in range(len(yy1)):
                val = 0
                n = 0
                for j in range(max(0, i-sm2), min(len(yy1), i+sm2+1)):
                    val += yy1[j]
                    n += 1
                if n == 0:
                    yy2.append(yy1[i])
                else:
                    yy2.append(val / n)
            
            self.plot.ydata = yy2


if __name__ == '__main__':
    m = app.launch(Twente, runtime='app', title='Temperature 1951 - 2014',
                   size=(900, 400))
    m.style = 'background:#eee;'  # more desktop-like
    app.run()

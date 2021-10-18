# util
import datetime
import requests
import configparser
import ast
import csv
# dash dependencies
import dash
import dash_core_components as dcc
import dash_html_components as html
# plotting
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import dash_bootstrap_components as dbc


app = dash.Dash(external_stylesheets=[dbc.themes.LUX])
"""This class is used to load preferences from the config file
    """


class Preferences():
    def __init__(self):
        # load config from file
        config = configparser.RawConfigParser()
        config.read('config.ini')
        config = dict(config.items('coins'))
        self.coins = ast.literal_eval(config['coins'])
        self.start = config['start_date']
        self.end = datetime.datetime.now().strftime('%Y/%m/%d')
        # no longer required
        # self.headers = {'x-messari-api-key': config['api_key']}
        self.headers = {}
        # property used to avoid making api calls
        self.local = config['local'] == "True"
        self.row_style = {
            'marginTop': '2%',
            'marginLeft': '2%',
            'marginRight': '2%',
            'height': 'auto',
            'border': '1px solid grey'}


class MessariHandler():
    def __init__(self, prefs: Preferences):
        # init an empty df to store the data
        self.all_df = pd.DataFrame(
            columns=['coin', 'symbol', 'high_price', 'timestamp', 'volume'])
        coins = pref.coins
        # loop over coins and fetch results
        for coin, items in coins.items():
            # use this prop to specify whether to make the calls or use cached data
            path = ""
            if not prefs.local:
                print(f"Processing from API calls")
                self.call(coins, coin, pref. start, pref.end, pref.headers)
                path = self.write_responses(coins, coin)
            else:
                print(f"Processing from local data")
                # use local csvs to avoid doing API calls
                path = 'results/'+coin+'.csv'

            df = pd.read_csv(path)
            print(type(df), df)
            # extend the dataframe to include new fetched data
            self.all_df = self.all_df.append(df, ignore_index=True)
        pass

        """Writes the responses stored in the dict as csvs
        """

    def write_responses(self, coins, coin):
        with open('results/'+coin+'.csv', 'w') as csvfile:
            # creating a csv writer object
            csvwriter = csv.writer(csvfile)
            # # writing the fields
            csvwriter.writerow(
                ['coin', 'symbol', 'high_price', 'timestamp', 'volume'])
            # writing the data rows
            csvwriter.writerows(coins[coin])
        print("Finished writing for " + coin)
        return 'results/'+coin+'.csv'

        """Makes a call to the Messari api to get the latest data for the period provided
        """

    def call(self, coins, coin, start, end, headers):
        url = "https://data.messari.io/api/v1/assets/" + coin + \
            "/metrics/price/time-series?start="+start+"&end="+end+"&interval=1d"
        news_url = "https://data.messari.io/api/v1/news/" + coin
        print("Initialising for " + coin.upper() + ": " + url)
        response = requests.get(url, headers=headers)
        #  this loads news for the current coin
        # response_news = requests.get(news_url)
        data = response.json()
        values = data['data']['values']
        for value in values:
            timestamp = value[0]
            open_price = round(value[1], 2)
            high_price = round(value[2], 3)
            low_price = round(value[3], 2)
            close_price = round(value[4], 2)
            volume = round(value[5], 2)
            name = data['data']['name']
            date = datetime.datetime.fromtimestamp(
                timestamp/1000.0).strftime("%Y-%m-%d")
            coin_loop = [name, coin.upper(), high_price, date, volume]
            print(f"{date} : {volume}@{high_price} for {coin}-{name} prices fetched")
            coins[coin].append(coin_loop)


pref = Preferences()
handler = MessariHandler(pref)
df = handler.all_df
ch = [dbc.Row(dbc.Col(
    dcc.Graph(
        id='value-over-time',
        figure={
            'data': [
                go.Scatter(
                    y=df[df['coin'] == i]['timestamp'],
                    x=df[df['coin'] == i]['high_price'],
                    text=df[df['coin'] == i]['symbol'],
                    mode='markers',
                    opacity=0.8,
                    marker={
                        'size': 15,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name=i
                ) for i in df["coin"].unique()
            ],
            'layout': go.Layout(
                yaxis={'type': 'date', 'title': 'Timestamp'},
                xaxis={'title': 'Price ($)'},
                margin={'l': 140, 'b': 40, 't': 10, 'r': 140},
                legend={'x': 1, 'y': 1},
                hovermode='closest'
            )
        }
    )), style=pref.row_style)
]

ch1 = []
# add the data from the csvs to a line graph and create a 2x2 layout
for index, coin in enumerate(pref.coins):
    adf = df[df["symbol"] == coin.upper()]
    g = dbc.Col([html.P(coin.upper()), dcc.Graph(
        id=f'value-over-time-{coin}',
        figure=px.line(
            adf,
            x='timestamp',
            y='high_price',
            labels={
                 "timestamp": "Date",
                 "high_price": "High price ($)",
                 },
        )
    )])
    ch1.append(g)
    # this keeps the formats of the coins
    if index % 2 == 1:
        ch.append(dbc.Row(ch1, style=pref.row_style))
        ch1 = []
    elif index == len(pref.coins) - 1:
        # this handles even numbers, otherwise duplicates ids
        ch.append(dbc.Row(ch1, style=pref.row_style))


app.layout = html.Div(children=ch)


if __name__ == '__main__':
    app.run_server(debug=False)

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


app = dash.Dash()
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
        self.headers = {'x-messari-api-key': config['api_key']}

        """Writes the response as a csv file
        """


def write_responses(coins, coin):
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


def call(coins, coin, start, end, headers):
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
# init an empty df to store the data
all_df = pd.DataFrame(
    columns=['coin', 'symbol', 'high_price', 'timestamp', 'volume'])
coins = pref.coins
# loop over coins and fetch results
for coin, items in coins.items():
    call(coins, coin, pref. start, pref.end, pref.headers)
    path = write_responses(coins, coin)
    # use local csvs to avoid doing API calls
    # path = 'results/'+coin+'.csv'
    df = pd.read_csv(path)
    print(type(df), df)
    # extend the dataframe to include new fetched data
    all_df = all_df.append(df, ignore_index=True)

print(all_df)
df = all_df


app.layout = html.Div([
    dcc.Graph(
        id='life-exp-vs-gdp',
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
                ) for i in all_df["coin"].unique()
            ],
            'layout': go.Layout(
                yaxis={'type': 'date', 'title': 'Timestamp'},
                xaxis={'title': 'Price ($)'},
                margin={'l': 140, 'b': 40, 't': 10, 'r': 140},
                legend={'x': 0, 'y': 1},
                hovermode='closest'
            )
        }
    )
])
if __name__ == '__main__':
    app.run_server(debug=True)

import json
import math
import os
import random
import yfinance as yf
import pandas as pd
from flask import Flask, render_template, request, jsonify
from datetime import date, timedelta
from pandas_datareader import data as pdr


app = Flask(__name__)


@app.route('/')
@app.route('/hitesh.html')
def home():
    return render_template('hitesh.html')


def doRender(tname, values={}):  # from labs
    if not os.path.isfile(os.path.join(os.getcwd(), 'templates/' + tname)):  # No such file
        return render_template('hitesh.html')
    return render_template(tname, **values)



# override yfinance with pandas – seems to be a common step
yf.pdr_override()
# Get stock data from Yahoo Finance – here, asking for about 10 years of Gamestop
# which had an interesting time in 2021: https://en.wikipedia.org/wiki/GameStop_short_squeeze
today = date.today()
decadeAgo = today - timedelta(days=3652)
dat = today.strftime("%m/%d/%Y")
data = pdr.get_data_yahoo('GME', start=decadeAgo, end=today)
# Other symbols: TSLA – Tesla, AMZN – Amazon, NFLX – Netflix, BP.L – BP
# Add two columns to this to allow for Buy and Sell signals
# fill with zero
data['Buy'] = 0
data['Sell'] = 0
# Find the 4 different types of signals – uncomment print statements
# if you want to look at the data these pick out in some another way
for i in range(len(data)):
    # Hammer
    realbody = math.fabs(data.Open[i] - data.Close[i])
    bodyprojection = 0.3 * math.fabs(data.Close[i] - data.Open[i])
    if data.High[i] >= data.Close[i] and data.High[i] - bodyprojection <= data.Close[i] and data.Close[i] > data.Open[i] \
            and data.Open[i] > data.Low[i] and data.Open[i] - data.Low[i] > realbody:
        data.at[data.index[i], 'Buy'] = 1
        # print("H", data.Open[i], data.High[i], data.Low[i], data.Close[i])
        # Inverted Hammer
    if data.High[i] > data.Close[i] and data.High[i] - data.Close[i] > realbody and data.Close[i] > data.Open[i] and \
            data.Open[i] >= data.Low[i] and data.Open[i] <= data.Low[i] + bodyprojection:
        data.at[data.index[i], 'Buy'] = 1
        # print("I", data.Open[i], data.High[i], data.Low[i], data.Close[i])
        # Hanging Man
    if data.High[i] >= data.Open[i] and data.High[i] - bodyprojection <= data.Open[i] and data.Open[i] > data.Close[
        i] and data.Close[i] > data.Low[i] and data.Close[i] - data.Low[i] > realbody:
        data.at[data.index[i], 'Sell'] = 1
    # print("M", data.Open[i], data.High[i], data.Low[i], data.Close[i])
    # Shooting Star
    if data.High[i] > data.Open[i] and data.High[i] - data.Open[i] > realbody and data.Open[i] > data.Close[i] and \
            data.Close[i] >= data.Low[i] and data.Close[i] <= data.Low[i] + bodyprojection:
        data.at[data.index[i], 'Sell'] = 1
    # print("S", data.Open[i], data.High[i], data.Low[i], data.Close[i])
    # Now have signals, so if they have the minimum amount of historic data can generate
    # the number of simulated values (shots) needed in line with the mean and standard
    # deviation of the that recent history


global list95, list99, mih, sho, dt
list95, list99,  mih, sho, dt = [], [], [],  [], []


@app.route("/", methods=['POST', 'GET'])
def risk_value():
    if request.method == "POST":
        h = request.form['h']
        s = request.form['s']
        sb = request.form['sb']
        h = int(h)
        s = int(s)
        sb = int(sb)
        mih.clear()
        mih.append(h)
        sho.clear()
        sho.append(s)
        list95.clear()
        list99.clear()
        if sb == 1:
            for i in range(h, len(data)):
                if data.Buy[i] == 1:  # if we were only interested in Buy signals
                    mean = data.Close[i - h:i].pct_change(1).mean()
                    std = data.Close[i - h:i].pct_change(1).std()
                    # generate rather larger (simulated) series with same broad characteristics
                    simulated = [random.gauss(mean, std) for x in range(s)]
                    # sort, and pick 95% and 99% losses (not distinguishing any trading position)
                    simulated.sort(reverse=True)
                    var95 = simulated[int(len(simulated) * 0.95)]
                    list95.append(var95)
                    var99 = simulated[int(len(simulated) * 0.99)]
                    list99.append(var99)
                    print(var95, var99)  # so you can see what is being produced
        else:
            for i in range(h, len(data)):
                if data.Sell[i] == 1:  # if we were only interested in Buy signals
                    mean = data.Close[i - h:i].pct_change(1).mean()
                    std = data.Close[i - h:i].pct_change(1).std()
                    # generate rather larger (simulated) series with same broad characteristics
                    simulated = [random.gauss(mean, std) for x in range(s)]
                    # sort, and pick 95% and 99% losses (not distinguishing any trading position)
                    simulated.sort(reverse=True)
                    var95 = simulated[int(len(simulated) * 0.95)]
                    list95.append(var95)
                    var99 = simulated[int(len(simulated) * 0.99)]
                    list99.append(var99)
                    print(var95, var99)  # so you can see what is being produced
        dt.clear()
        y = dat
        for i in range(len(list95)):
            dt.append(y)
        print(len(dt), len(list99), len(list95), mih, sho)
        return render_template('hitesh.html', date=dt, va95=list95, va99=list99, r_95=list95[-1], r_99=list99[-1],
                               mih=mih, sho=sho)
    else:
        return render_template('hitesh.html')


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)

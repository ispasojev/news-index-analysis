# Uni-variate time series analysis used to predict Hang Seng Index

from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tools.eval_measures import rmse
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import pandas as pd


# https://towardsdatascience.com/time-series-analysis-tutorial-using-financial-data-4d1b846489f9
# -> financial data
# -> ARIMA, SARIMAX & Facebook Prophet

# https://www.kdnuggets.com/2020/01/stock-market-forecasting-time-series-analysis.html
# -> financial data, ARIMA

def get_ARIMA_model(data):
    data_x = data[0]
    data_y = data[1]
    # split data set into training and test data to use for validation of the model
    # for time series, cannot use cross validation; need to make sure we keep order for our splits
    # todo: split data into x and y values
    x_train, x_test, y_train, y_test = train_test_split(data_x, data_y)
    model_ARIMA = ARIMA()
    # TODO improve p, q https://analyticsindiamag.com/quick-way-to-find-p-d-and-q-values-for-arima/
    # finding p, q, and d: https://analyticsindiamag.com/quick-way-to-find-p-d-and-q-values-for-arima/
    model = ARIMA(x_train, order=(p, find_d_val(data), q)).fit()  # create model and fit training data
    print(model.summary())
    # first enr
    forecast, stderr_fc, conf_int_fc = model.forecast()  # todo: inputs: steps=1, exog=None, alpha=0.05; should define steps?
    print("The root mean square error is: ", rmse(x_test, forecast))  # gives score to evaluate result

    plt.plot(data, forecast)


# d is number of required differencing to make the data stationary
def find_d_val(data):
    d = 0
    diff_data = data.copy()  # TODO check that data is copied without pointer
    while not is_stationary(diff_data):
        diff_data = diff_data.diff()
        d += 1
    return d


# https://analyticsindiamag.com/how-to-make-a-time-series-stationary/
def is_stationary(data):
    fuller_result = adfuller(data)
    p_val = fuller_result[1]
    return p_val < 0.05


path = ''
hs_data = pd.read_csv(path)
hs_data.head()  # showing data content
get_ARIMA_model(hs_data)

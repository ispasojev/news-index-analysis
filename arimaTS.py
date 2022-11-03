from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tools.eval_measures import rmse
import matplotlib.pyplot as plt
import pandas as pd
from pmdarima.arima import auto_arima


def split_data(data, p_split=0.8):
    # split data set into training and test data to use for validation of the model
    split_size = round(len(data) * p_split)
    data_train = data[:split_size]
    data_test = data[split_size:]

    return data_train, data_test


def get_arima_model(data_train, data_test):
    # apply auto arima for automatically choosing the best values for p, d, and q
    best_arima = auto_arima(data_train, start_p=0, start_q=0, max_p=3, max_q=3, test="adf", seasonal=True)

    # generate ARIMA model
    model = ARIMA(data_train, order=best_arima.get_params().get("order"))
    model_fit = model.fit()
    print(model_fit.summary())

    forecast = model_fit.forecast(steps=1, alpha=0.05, exog=None)
    print("The root mean square error is: ", rmse(data_test, forecast))  # gives score to evaluate result

    forecast_series = pd.Series(forecast, index=data_test.index)
    univariate_plot(data_train, data_test, forecast_series)


# https://www.kdnuggets.com/2020/01/stock-market-forecasting-time-series-analysis.html
# Uni-variate time series analysis used to predict Hang Seng Index
def univariate_plot(data_train, data_test, data_fc):
    plt.plot(data_train, color='green', label='training')
    plt.plot(data_test, color='blue', label='Actual Stock Price')
    plt.plot(data_fc, color='orange', label='Predicted Stock Price')
    plt.title('Comparison Forecast and current data')
    plt.xlabel('time')
    plt.ylabel('Hang Seng index')
    plt.legend()
    plt.show()


path = 'data/index_data.csv'
hs_data = pd.read_csv(path, header=0, sep=";")
hs_data['Datetime'] = pd.to_datetime(hs_data['Datetime'])

hs_index_data = []
for x in hs_data['Index Value']:
    hs_index_data.append(float(x.replace(',', '')))

hs_data['Index Value'] = hs_index_data
(hs_train, hs_test) = split_data(hs_data)

get_arima_model(hs_train['Index Value'], hs_test['Index Value'])


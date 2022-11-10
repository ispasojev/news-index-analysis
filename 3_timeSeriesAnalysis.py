import itertools
import numpy as np
from prophet import Prophet
import pandas as pd
from sklearn.metrics import mean_absolute_error
from statsmodels.tsa.statespace.sarimax import SARIMAX
import matplotlib.pyplot as plt


def get_prophet_univariate(train_data, test_data):
    # uni-variate model
    model = Prophet()  # initiating prophet using the default parameters
    model.fit(train_data)
    future_model = model.make_future_dataframe(periods=1)
    model_forecast = model.predict(future_model)

    plot_prophet(model, model_forecast)

    eval_univariate = pd.merge(test_data, model_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']][-1:], on='ds')

    univar_mae = mean_absolute_error(eval_univariate['y'], eval_univariate['yhat'])
    print(f'The univariate MAE is : {univar_mae}')


# https://medium.com/grabngoinfo/multivariate-time-series-forecasting-with-seasonality-and-holiday-effect-using-prophet-in-python-d5d4150eeb57
def get_prophet_multivariate(train_data, test_data, param):
    print(train_data)
    model_multivar = Prophet()  # initiating prophet using the default parameters
    for p in param:
        model_multivar.add_regressor(p)

    model_multivar.fit(train_data)

    # future_multivar = create_future_df(model_multivar, param)
    multivar_fc = model_multivar.predict(test_data)

    plot_prophet(model_multivar, multivar_fc)

    # get performance measure
    eval_multivar = pd.merge(test_data, multivar_fc, on='ds', how='inner')
    multivar_mae = mean_absolute_error(eval_multivar['y'], eval_multivar['yhat'])
    print(f'The univariate MAE is : {multivar_mae}')


def create_future_df(model, param):
    future_multivar = model.make_future_dataframe(periods=10)

    for p in param:
        future_multivar.insert(1, p, "")

    return future_multivar.fillna(method='ffill')  # Fills missing values with last occurrence


def plot_prophet(model, model_fc):
    model.plot(model_fc)
    model.plot_components(model_fc)
    plt.show()


# https://towardsdatascience.com/end-to-end-time-series-analysis-and-forecasting-a-trio-of-sarimax-lstm-and-prophet-part-1-306367e57db8
def get_sarimax_model(train, test, param):
    train_data = np.array(train['y'], dtype=float)
    train_data_exo = np.array(train[param], dtype=float)
    sarimax_model_fit = sarimax_best_model(train_data, train_data_exo)

    test['fc'] = sarimax_model_fit.predict(start=0, end=len(test.index)-1, exog=test[['ds', param[0]]], dynamic=True)
    plot_sarimax(train, test)


def sarimax_best_model(train_data, train_data_exo):
    # parameter ranges
    p, d, q = range(0, 3), [1], range(0, 3)
    P, D, Q, s = range(0, 3), [1], range(0, 3), [7]

    param_pdq = list(itertools.product(p, d, q))
    seasonal_pdq = list(itertools.product(P, D, Q, s))
    param_list = list(itertools.product(param_pdq, seasonal_pdq))

    model_list = []

    for param in param_list:
        try:
            sari_mod = SARIMAX(train_data, exog=train_data_exo, order=param[0], seasonal_order=param[1])
            fitted_sarimax = sari_mod.fit(disp=False)
            model_list.append((fitted_sarimax, fitted_sarimax.aic, param))

        except:
            continue

    # first entry in list has the lowest AIC value, is the assumed to be the best model
    best_model_df = pd.DataFrame(model_list, columns=['fitted_model', 'aic', 'param']).sort_values(by=['aic'], ascending=True)
    best_model_param = best_model_df.iloc[0].param
    best_model = SARIMAX(train_data, exog=train_data_exo, order=best_model_param[0], seasonal_order=best_model_param[1])
    return best_model.fit(disp=False)


def plot_sarimax(train, test):
    plt.figure(figsize=(12, 8))

    # plotting actual index data
    plt.plot(train.ds, train.y, label="training data")
    plt.plot(test.ds, test.y, label="testing data")

    # plotting forecasted data
    plt.plot(test.ds, test.fc, label="forecast")

    plt.legend(loc='best')
    plt.title("Forecasting Hang Seng Index")
    plt.show()


path_index = 'data/index_data.csv'
data_index = pd.read_csv(path_index, header=0, sep=";")
# adjust data for use in prophet
data_index.columns = ['ds', 'Index Name', 'y']
data_index['ds'] = pd.to_datetime(data_index['ds'])

hs_index_data = []
for x in data_index['y']:
    hs_index_data.append(float(x.replace(',', '')))

data_index['y'] = hs_index_data

# split data into train and test sets
split_size = round(len(data_index) * 0.8)
train_index = data_index[:split_size]
test_index = data_index[split_size:]

path_exo = 'data/weather_data.csv'
exo_data = pd.read_csv(path_exo, header=0, sep=";") #, parse_dates=['time'], date_parser=date_time_parser)
exo_data.columns = ['ds', 'condition', 'Wind in km/h', 'Humidity in %', 'Precipitation in mm', 'Visibility in km', 'UV index']
exo_data['ds'] = pd.to_datetime(exo_data['ds'])

# split data into train and test sets
split_size = round(len(exo_data) * 0.8)
train_exo = exo_data[:split_size]
test_exo = exo_data[split_size:]

# Prophet model
get_prophet_univariate(train_index, test_index)

multivar_data_train = pd.merge(train_index[['ds', 'y']], train_exo[['ds', 'condition', 'Wind in km/h', 'Humidity in %']], on='ds', how='outer')
multivar_data_train.index = pd.DatetimeIndex(multivar_data_train['ds'], name='index')

multivar_data_test = pd.merge(test_index[['ds', 'y']], test_exo[['ds', 'condition', 'Wind in km/h', 'Humidity in %']], on='ds', how='outer')
multivar_data_test.index = pd.DatetimeIndex(multivar_data_test['ds'], name='index')

get_prophet_multivariate(multivar_data_train, multivar_data_test, ['Wind in km/h', 'Humidity in %'])

# SARIMAX model
get_sarimax_model(multivar_data_train, multivar_data_test, ['Wind in km/h'])

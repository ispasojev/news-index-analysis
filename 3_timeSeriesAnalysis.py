import itertools
import numpy as np
from prophet import Prophet
import pandas as pd
from sklearn.metrics import mean_absolute_error
from statsmodels.tsa.statespace.sarimax import SARIMAX
import matplotlib.pyplot as plt


def split_data(d, split_p):
    # split data into train and test sets
    split_size = round(len(d) * split_p)
    train_data = d[:split_size]
    test_data = d[(split_size - 1):]
    return train_data, test_data


def get_prophet_univariate(d, split_p):
    train, test = split_data(d, split_p)
    # uni-variate model
    model = Prophet()  # initiating prophet using the default parameters
    model.fit(train)
    future_model = model.make_future_dataframe(periods=10)
    model_forecast = model.predict(future_model)

    plot_prophet(model, model_forecast)
    eval_univariate = pd.merge(test, model_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']], on='ds')

    univar_mae = mean_absolute_error(eval_univariate['y'], eval_univariate['yhat'])
    print(f'The univariate MAE is : {univar_mae}')


# https://medium.com/grabngoinfo/multivariate-time-series-forecasting-with-seasonality-and-holiday-effect-using-prophet-in-python-d5d4150eeb57
def get_prophet_multivariate(d, split, param, periods):
    train, test = split_data(d, split)
    model_multivar = Prophet()  # initiating prophet using the default parameters
    for p in param:
        model_multivar.add_regressor(p)

    model_multivar.fit(train)
    future_multivar = create_future_df(model_multivar, param, data, periods)

    multivar_fc = model_multivar.predict(future_multivar)  # predicting values

    plot_prophet(model_multivar, multivar_fc)

    # get performance measure
    eval_multivar = pd.merge(test, multivar_fc, on='ds', how='inner')
    multivar_mae = mean_absolute_error(eval_multivar['y'], eval_multivar['yhat'])
    print(f'The univariate MAE is : {multivar_mae}')


def create_future_df(model, param, d, periods):
    # create new data set with time range for the forecast
    future_multivar = model.make_future_dataframe(periods)

    # appending new regressor values to df
    input_df = param.copy()
    input_df.insert(0, 'ds')
    future_multivar = pd.merge(future_multivar, d[input_df], on='ds', how='outer')

    return future_multivar.fillna(method='ffill')  # Fills missing values with last occurrence


def plot_prophet(model, model_fc):
    model.plot(model_fc)
    model.plot_components(model_fc)
    plt.show()


# https://towardsdatascience.com/end-to-end-time-series-analysis-and-forecasting-a-trio-of-sarimax-lstm-and-prophet-part-1-306367e57db8
def get_sarimax_model(d, split, param):
    train, test = split_data(d, split)
    train_data = np.array(train['y'], dtype=float)
    train_data_exo = np.array(train[param], dtype=float)
    sarimax_model_fit = sarimax_best_model(train_data, train_data_exo)

    test['fc'] = sarimax_model_fit.predict(start=0, end=len(test.index) - 1, exog=test[['ds', param[0]]], dynamic=True)
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
    best_model_df = pd.DataFrame(model_list, columns=['fitted_model', 'aic', 'param']).sort_values(by=['aic'],
                                                                                                   ascending=True)
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


path = 'data/preprocessed_and_merged_datasets.csv'
data = pd.read_csv(path, header=0, sep=";")
# adjust data for use in prophet
data.rename(columns={'datetime': 'ds'}, inplace=True)
data.rename(columns={'Index Value': 'y'}, inplace=True)
data['ds'] = pd.to_datetime(data['ds'])

# Prophet model
get_prophet_univariate(data, 0.75)

get_prophet_multivariate(data, 0.75, ['Wind in km/h', 'ratio_negative_articles'], 16)

# SARIMAX model
# todo: problem is "too few few observations to estimate starting parameters for ARMA and trend. All parameters except for variances will be set to zeros.
#   warn('Too few observations to estimate starting parameters%s."
# get_sarimax_model(data, 0.75, ['Wind in km/h'])

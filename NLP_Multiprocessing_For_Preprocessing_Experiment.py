import pandas as pd
import time
import timeit
import numpy as np

from joblib import Parallel, delayed
import multiprocessing as mp

import ray
import ray.util.multiprocessing

# for the visuals
import matplotlib.pyplot as plt

print(mp.cpu_count())

# read in the data set
all_data = pd.read_csv('./Data/news_data_Experimentation.csv', sep=";")

# read in stop word list
stopwords_list = []
with open('./Data/stopwords.txt') as f:
    for line in f.readlines():
        if str(line)[0] != "#":
            stopwords_list.append(str(line).replace("\n", ""))
original_stopwords_list = stopwords_list


def remove_stop_words(text):
    """ A simple function that first splits text via
    whitespaces and remove then stopwords that appear in list"""

    # split text by whitespace
    x = np.array(text.split(" "))
    # check if word is in  stopwords
    x = x[np.isin(x, stopwords_list) == False]
    # join again
    new_text = ' '.join(x.tolist())

    # if text is longer than 5 characters return modified text
    # else return original text
    if len(new_text) > 5:
        return new_text
    else:
        return text



def measure_time(name, code_snippet,
                 model_name_list, execution_time_list):
    """function to evalute the execution time of a code snippet.
    The results of the evalution will be saved in two lists.
    """

    start_time = time.perf_counter()
    eval(code_snippet)
    execution_time = time.perf_counter() - start_time
    model_name_list = model_name_list.append(name)
    execution_time_list = execution_time_list.append(execution_time)
    print(f"{name} Execution time: {execution_time}")




print(len(stopwords_list))

test_dict = {
    # Number of Stop words to remove
    "#Stopwords": [100, 2070],
    # Number of news articles to include
    "#news_articles": [200, 10000, 500000],
    #libraries and number of cores to test out
    "Libraries": {"Joblib": [2, 4, 8], "Ray":[2, 4],}
}

for number_of_texts in test_dict["#news_articles"]:
    # select the desidered number of articles for the experiment
    df = all_data.head(number_of_texts)
    for number_of_stopwords in test_dict["#Stopwords"]:

        stopwords_list = np.array(original_stopwords_list[:number_of_stopwords])
        # to store the results of the experiment
        model_name_list = []
        execution_time_list = []

        # sequential methods
        # from NLP_Preprocessing_Functions import remove_stop_words
        measure_time("Sequential List", "[remove_stop_words(x) for x in df['text'].to_list()]",
                     model_name_list, execution_time_list)
        measure_time("Sequential lambda", "df['text'].apply(lambda x: remove_stop_words(x))",
                     model_name_list, execution_time_list)

        # multiprocessing methods
        for library in test_dict["Libraries"].keys():

            for n_core in test_dict["Libraries"][library]:
                if library == "Joblib":
                    statement = "Parallel(n_jobs=_CORES_)(delayed(remove_stop_words)(i) for i in df['text'].to_list())"
                else:
                    try:
                        pool = ray.util.multiprocessing.Pool(processes=nprocs)
                        statement = "pool.map(remove_stop_words, df['text'].to_list())"
                    except:
                        pass
                measure_time("Y X Cores".replace("X",
                            str(n_core)).replace("Y", library),
                            statement.replace("_CORES_", str(n_core)), model_name_list, execution_time_list)


        #plot the resutls
        plt.figure(figsize=(10,8), dpi=130)
        plt.style.use("seaborn")
        plt.bar(model_name_list, execution_time_list)
        plt.suptitle("Comparison of Multiprocessing Strategies in Python", fontsize=18)
        plt.title("Number of Texts: " + str(number_of_texts) +
                  ", Number of Stopwords: " + str(number_of_stopwords), fontsize=10)
        plt.ylabel("Execution Time in Seconds")
        plt.xlabel("Multiprocessing Approach")
        plt.axhline(min(execution_time_list), color="red")
        plt.xticks(rotation=20)
        plt.savefig(".\data\images\Multiprocessing_Experiment_Python_" +
                    str(number_of_texts) + "_articles_" +
                    str(number_of_stopwords) + "_stopwords.png")






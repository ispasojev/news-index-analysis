# General libraries
import pandas as pd
import numpy as np

# Spelling correction
import textblob
from textblob import TextBlob

# Text manipulation
import regex as re

# Lemmatization and tokenization
import nltk
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Spacy
import spacy
nlp=spacy.load('en_core_web_sm')

# Creating vecotorization
from collections import Counter

# Inflect
import inflect
inflect = inflect.engine()

# Sentiment analysis with vader
from nltk.sentiment.vader import SentimentIntensityAnalyzer
nltk.download('vader_lexicon')

# Wordcloud
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
nltk.download('stopwords')
from wordcloud import WordCloud, STOPWORDS



def remove_special_characters_and_parts(text):
    # replace all words that just contain one letter
    text = re.sub(r'(?:^| )\w(?:$| )', ' ', str(text)).strip()

    # remove most puntuation
    text = re.sub('([()‘’“”…+\-\{\}])+', ' ', text)
    text = re.sub(r"\\'+", ' ', text)
    text = re.sub(r'\\"+', ' ', text)
    text = re.sub(r'\\^+', ' ', text)
    text = re.sub(r'\.+', ' ', text)
    text = re.sub(r'\;+', ' ', text)
    text = re.sub(r'\!+', ' ', text)
    text = re.sub(r'\,+', ' ', text)
    text = re.sub(r'\?+', ' ', text)
    text = re.sub(r'\'+', ' ', text)
    text = re.sub(r'\"+', ' ', text)
    text = re.sub(r'\'+', ' ', text)

    # remove slashes
    text = re.sub('\n', ' ', text)
    text = re.sub(r'[\\(/)]', ' ', text)
    text = re.sub(r'[\\(\)]', ' ', text)

    # get rid of and as a sign
    text = re.sub(r'\&', ' and ', text)

    # remove unnecessary whitespaces
    text = re.sub(r'\s+', ' ', text)

    return text


def correct_spelling(text):
    # correct any spelling mistakes
    # assumption: spelling mistakes neglactable in news paper
    # TextBlob.correct() leads to weird results, e.g Hong Kong --> Long Long
    # text = str(TextBlob(text).correct())

    # write words out
    text = re.sub(r"’", "'", text)
    text = re.sub(r"n\'t", " not ", text)
    text = re.sub(r"\'re", " are ", text)
    text = re.sub(r"\'s", " is ", text)
    text = re.sub(r"\'d", " would ", text)
    text = re.sub(r"\'ll", " will ", text)
    text = re.sub(r"\'t", " not ", text)
    text = re.sub(r"\'ve", " have ", text)
    text = re.sub(r"\'m", " am ", text)

    return text

def normalize_text(text):
    tokenized_text = nlp(str(text).lstrip().rstrip())
    text = ""

    for token in tokenized_text:

        if (token.tag_ == "NN" or token.tag_ == "NE"):
            # Check if the noun is already singular
            if inflect.singular_noun(str(token)) == False:
                text += " " + str(token).lower()
            else:

                # Step 2
                # singularize a plural noun
                try:
                    singularized_text = inflect.plural(str(token).lower())
                    text += " " + singularized_text.lower()

                except IndexError:
                    print(str(token))
                    text += " " + str(token).lower()
                    pass
        else:

            # filter out stopword based on part of speach tagging
            # see https://machinelearningknowledge.ai/tutorial-on-spacy-part-of-speech-pos-tagging/
            if (token.pos_ == "DET" or token.pos_ == "ADP" or
                    token.pos_ == "ADP" or token.pos_ == "CONJ" or
                    token.pos_ == "PRON"):
                pass

            else:

                # lemmatization sometimes leads to bad results as result
                # we make a check for common letter which should be at least the length of the original string -1
                # else we are not doing the lemmatization
                common_letters = Counter(str(token).lower()) & Counter(str(token.lemma_).lower())

                if sum(common_letters.values()) >= len(str(token)) - 1:
                    text += " " + str(token.lemma_).lower()
                else:
                    text += " " + str(token).lower()

    return text


# load stopwords
stopwords_list = []
with open('./Data/stopwords.txt') as f:
    for line in f.readlines():
        if str(line)[0] != "#":
            stopwords_list.append(str(line).replace("\n", ""))
stopwords_list = np.array(stopwords_list)

def remove_stop_words(text):
    """ A simple function that first splits text via
    whitespaces and remove then stopwords that appear in list"""

    # split text by whitespace
    x = np.array(text.split(" "))
    # check if word is in  stopwords
    x =  x[np.isin(x, stopwords_list) == False]
    # join again
    new_text = ' '.join(x.tolist())

    # if text is longer than 5 characters return modified text
    # else return original text
    if len(new_text) > 5:
        return new_text
    else:
        return text
    
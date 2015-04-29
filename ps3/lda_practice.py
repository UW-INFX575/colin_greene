# http://chrisstrelioff.ws/sandbox/2014/11/13/getting_started_with_latent_dirichlet_allocation_in_python.html

import requests
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import *
from nltk.tokenize import RegexpTokenizer
from nltk.util import ngrams
import csv
import itertools
import numpy as np
import lda
import lda.datasets

# Create list of URLs to pull documents from
urls = []
base_path = "https://s3-us-west-2.amazonaws.com/uspto-patentsclaims/"
extension_number = 6334220
for i in xrange(10):
    urls.append(base_path + str(extension_number + i) + '.txt')

# Create list of 10 documents
documents = []
for url in urls:
    documents.append(requests.get(url).content)

#### Get necessary NLP resources ####

# List of stop words from nltk
stops = stopwords.words('english')

# For extracting stems
stemmer = PorterStemmer()

# To remove all non-alpha characters from a string and convert to a list
tokenizer = RegexpTokenizer(r'[A-Za-z]+')

#### Functions ####
def remove_stops(document):
    return [word for word in document if word not in stops]

def extract_stems(document):
    stems = []
    for word in document:
        stems.append(stemmer.stem(word))
    return stems

# Convert string to all lower case, 
# remove all non-alpha characters and convert to a list
document_arrays = map(lambda x: tokenizer.tokenize(x.lower()), documents)

# Remove stop words from each list
document_arrays = map(remove_stops, document_arrays)

# Extract splits from each list
document_arrays = map(extract_stems, document_arrays)

unique_set_of_words = list(set([item for sublist in document_arrays for item in sublist]))

columns = []
for array in document_arrays:
    column = []
    for word in unique_set_of_words:
        column.append(array.count(word))
    columns.append(column)
len(columns)

#columns = np.transpose(np.array(columns))
columns = np.array(columns)

model = lda.LDA(n_topics=20, n_iter=500, random_state=1)
model.fit(columns)  # model.fit_transform(X) is also available

topic_word = model.topic_word_  # model.components_ also works

n_top_words = 8
for i, topic_dist in enumerate(topic_word):
    topic_words = np.array(unique_set_of_words)[np.argsort(topic_dist)][:-n_top_words:-1]
    print('Topic {}: {}'.format(i, ' '.join(topic_words)))


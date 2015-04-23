import requests
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import *
from nltk.tokenize import RegexpTokenizer
from nltk.util import ngrams
import csv
import itertools

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

def extract_splits(document):
    splits = []
    for word in document:
        splits.append(stemmer.stem(word))
    return splits

# Takes a split string (i.e. a list) and by default returns a dict with the 
# count of unigrams, bigrams, and trigrams that occured in that list. 
# Output looks like:
#  {1:[[unigram, count],[unigram, count]...[unigram, count]], 
#   2:[[bigram,count],[bigram,count]...[bigram,count]], 
#   3:[[trigram,count],[trigram,count]...[trigram,count]]
#   }
def get_n_gram_counts(document, min_n=1, max_n=3):
    n_grams_count = {}
    for i in xrange(min_n, max_n+1):
        n_grams = [' '.join(word) for word in ngrams(document,i)]
        counts = []
        for word in set(n_grams):
            counts.append([word, n_grams.count(word)])
        counts = sorted(counts, key=lambda count: count[1], reverse = True)
        n_grams_count[i] = counts
    return n_grams_count

# Takes list of lists with uniformly structured rows as input 
# Groups by specified column (column zero by default) and applies an aggregate function (sum by default)
# to another specified column (column one by default) 
# Returns a sorted list of the grouped and aggregated results
def group_and_agg(list_of_lists, agg_func=sum, initial_dict_value=0, group_column=0, agg_column=1):

    # Get set of unique values from the first column
    unique = set([line[group_column] for line in list_of_lists])
    
    # Create dictionary with unique set as the keys and 0 as values
    aggregates = dict((key,initial_dict_value) for key in unique)
    
    # For each line in the list of lists, add the count to the value in the dict
    for line in list_of_lists:
        aggregates[line[group_column]] = agg_func([aggregates[line[group_column]], line[agg_column]])
    
    # Convert dict to a list sorted by the word counts 
    aggregates = [[key, aggregates[key]] for key in sorted(aggregates, key=aggregates.get, reverse=True)]
    return aggregates

# Convert string to all lower case, remove all non-alpha characters and convert to a list
document_arrays = map(lambda x: tokenizer.tokenize(x.lower()), documents)

# Remove stop words from each list
document_arrays = map(remove_stops, document_arrays)

# Extract splits from each list
document_arrays = map(extract_splits, document_arrays)

# Create a list of 10 dicts, each of which corresponds to a different document and
# each of which contains 3 lists containing unigram, bigram, and trigram counts
n_grams = map(get_n_gram_counts, document_arrays)

# Create a list of len 3 which groups all unigram, bigram, and trigram from individual documents 
# into three seperate lists
grouped_by_n = []
for n in xrange(1,4):
    temp_list = []
    for doc in n_grams:
        temp_list += doc[n]
    grouped_by_n.append(temp_list)

all_n_counts = map(group_and_agg, grouped_by_n)

# Create file names for counts of ngrams across all documents
all_n_file_names = []
for n in ['unigrams', 'bigrams', 'trigrams']:
        all_n_file_names.append('all_' + n + '.csv')

# Create dict matching each file name to its contents
all_n_files_and_counts = dict(zip(all_n_file_names, all_n_counts))

# Extract and flatten the values from n_grams dict
individual_counts = [x.values() for x in n_grams]
individual_counts = list(itertools.chain(*individual_counts))

# Create list of 30 file names like 6334220unigrams.csv 
individual_file_names = []
for i in xrange(10):
    for n in ['unigrams', 'bigrams', 'trigrams']:
        individual_file_names.append(str(extension_number + i) + n + '.csv')

# Create dict matching each file name to its contents        
individual_files_and_counts = dict(zip(individual_file_names, individual_counts))

# Create 3 files with summary counts for unigrams, bigrams, and trigrams accross all documents
for key in all_n_files_and_counts:
    ofile  = open(key, "wb")
    writer = csv.writer(ofile, delimiter=',')

    for row in all_n_files_and_counts[key]:
        writer.writerow(row)
    ofile.close()

# Create 30 files with counts of unigrams, bigrams, and trigrams for each document
for key in individual_files_and_counts:
    ofile  = open(key, "wb")
    writer = csv.writer(ofile, delimiter=',')

    for row in individual_files_and_counts[key]:
        writer.writerow(row)
    ofile.close()

print 'Documents saved to current working directory.'








import numpy as np
import nltk
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
import re

nltk.download('stopwords')
nltk.download('punkt')

stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

def clean_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def tokenize(sentence):
    # Clean the text first
    sentence = clean_text(sentence)
    # Tokenize
    return nltk.word_tokenize(sentence)

def stem(word):
    return stemmer.stem(word.lower())

def bag_of_words(tokenized_sentence, words):
    # Remove stop words
    sentence_words = [stem(word) for word in tokenized_sentence if word not in stop_words]
    
    # initialize bag with 0 for each word
    bag = np.zeros(len(words), dtype=np.float32)
    
    for idx, w in enumerate(words):
        if w in sentence_words: 
            bag[idx] = 1.0
    
    return bag 
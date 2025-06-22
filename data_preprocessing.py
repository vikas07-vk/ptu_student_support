import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import logging
import joblib

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TextPreprocessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        self.is_fitted = False
        self.label_encoder = LabelEncoder()

    def clean_text(self, text):
        """Clean and normalize text."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text

    def tokenize(self, text):
        """Tokenize text into words."""
        return word_tokenize(text)

    def lemmatize(self, tokens):
        """Lemmatize tokens and remove stop words."""
        return [self.lemmatizer.lemmatize(token) for token in tokens 
                if token not in self.stop_words]

    def vectorize(self, texts, fit=False):
        """Convert text to TF-IDF vectors."""
        if isinstance(texts, str):
            texts = [texts]
            
        if fit:
            self.vectorizer.fit(texts)
            self.is_fitted = True
            
        if not self.is_fitted:
            raise ValueError("Vectorizer needs to be fitted before transform")
            
        return self.vectorizer.transform(texts)

    def preprocess_text(self, text, fit=False):
        """Complete preprocessing pipeline."""
        cleaned_text = self.clean_text(text)
        tokens = self.tokenize(cleaned_text)
        lemmatized = self.lemmatize(tokens)
        processed_text = ' '.join(lemmatized)
        return self.vectorize(processed_text, fit=fit)

    def preprocess_batch(self, texts, fit=False):
        """Preprocess a batch of texts."""
        processed_texts = []
        for text in texts:
            cleaned_text = self.clean_text(text)
            tokens = self.tokenize(cleaned_text)
            lemmatized = self.lemmatize(tokens)
            processed_texts.append(' '.join(lemmatized))
        return self.vectorize(processed_texts, fit=fit)

    def save_vectorizer(self, path):
        """Save the fitted vectorizer."""
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted before saving")
        joblib.dump(self.vectorizer, path)
        logger.info(f"Vectorizer saved to {path}")

    def load_vectorizer(self, path):
        """Load a fitted vectorizer."""
        self.vectorizer = joblib.load(path)
        self.is_fitted = True
        logger.info(f"Vectorizer loaded from {path}")

def load_and_preprocess_data(test_size=0.2, random_state=42):
    logger.info("Loading intents data...")
    with open('intents.json', 'r') as f:
        intents = json.load(f)

    # Prepare data
    texts = []
    labels = []
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            texts.append(pattern)
            labels.append(intent['tag'])

    # Initialize preprocessor
    preprocessor = TextPreprocessor()
    
    logger.info("Preprocessing text data...")
    # Preprocess texts
    processed_texts = [preprocessor.preprocess_text(text) for text in texts]
    
    # Convert text to TF-IDF features
    logger.info("Converting text to TF-IDF features...")
    X = preprocessor.vectorize(processed_texts)
    
    # Encode labels
    logger.info("Encoding labels...")
    y = preprocessor.label_encoder.fit_transform(labels)
    
    # Split the data
    logger.info("Splitting data into train and test sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    return X_train, X_test, y_train, y_test

if __name__ == "__main__":
    # Test the preprocessing pipeline
    X_train, X_test, y_train, y_test = load_and_preprocess_data()
    logger.info(f"Training set shape: {X_train.shape}")
    logger.info(f"Test set shape: {X_test.shape}")

    # Test the preprocessor
    preprocessor = TextPreprocessor()
    
    test_texts = [
        "Hello, how are you doing today?",
        "This is a test message with numbers 123!",
        "Another example of text preprocessing..."
    ]
    
    # Test the complete pipeline
    vectors = preprocessor.preprocess_batch(test_texts, fit=True)
    print(f"Processed {len(test_texts)} texts into vectors of shape {vectors.shape}")
    
    # Test single text preprocessing
    single_vector = preprocessor.preprocess_text("Test message!")
    print(f"Processed single text into vector of shape {single_vector.shape}") 
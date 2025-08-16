import numpy as np
from data_preprocessing import TextPreprocessor
from ensemble_model import EnsembleClassifier
import json
import random
import logging
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_intents():
    with open('data/dataset.csv', 'r') as f:
        # Skip header
        next(f)
        intents = {}
        for line in f:
            try:
                tag, pattern, response = line.strip().split(',', 2)
                if tag not in intents:
                    intents[tag] = {'tag': tag, 'patterns': [], 'responses': []}
                intents[tag]['patterns'].append(pattern)
                intents[tag]['responses'].append(response)
            except ValueError:
                continue
        return {'intents': list(intents.values())}

class ChatBot:
    def _init_(self, model_prefix='ensemble_model'):
        self.preprocessor = TextPreprocessor()
        self.ensemble = EnsembleClassifier()
        try:
            self.ensemble.load_models(model_prefix)
        except:
            logger.warning("Could not load model, initializing new one")
        self.intents = load_intents()
        self.confidence_threshold = 0.5

    def get_response(self, user_input):
        # Preprocess the input
        processed_input = self.preprocessor.clean_text(user_input)
        processed_input = ' '.join(self.preprocessor.lemmatize(self.preprocessor.tokenize(processed_input)))
        
        # Convert to feature vector
        X = self.preprocessor.vectorize([processed_input])
        
        # Get predictions from both classifiers
        voting_proba, stacking_proba = self.ensemble.predict_proba(X)
        
        # Get the highest confidence prediction from each classifier
        voting_conf = np.max(voting_proba)
        stacking_conf = np.max(stacking_proba)
        
        # Use the prediction with higher confidence
        if voting_conf > stacking_conf:
            prediction_idx = np.argmax(voting_proba)
            confidence = voting_conf
        else:
            prediction_idx = np.argmax(stacking_proba)
            confidence = stacking_conf
        
        # If confidence is too low, return a default response
        if confidence < self.confidence_threshold:
            return "I'm not quite sure about that. Could you please rephrase your question?"
        
        # Get the corresponding intent and response
        predicted_tag = list(self.intents.keys())[prediction_idx]
        for intent in self.intents['intents']:
            if intent['tag'] == predicted_tag:
                return random.choice(intent['responses'])
        
        return "I apologize, but I'm having trouble understanding. Could you try asking in a different way?"

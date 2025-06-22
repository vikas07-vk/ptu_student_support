from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.voting import VotingClassifier
import numpy as np
import joblib

class ChatbotModel:
    def __init__(self, random_state=42):
        # Initialize base classifiers
        self.rf = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            random_state=random_state
        )
        
        self.gb = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            random_state=random_state
        )
        
        self.svm = SVC(
            kernel='linear',
            probability=True,
            random_state=random_state
        )
        
        self.nb = MultinomialNB(alpha=0.1)
        
        self.lr = LogisticRegression(
            max_iter=1000,
            random_state=random_state
        )
        
        # Create voting classifier
        self.model = VotingClassifier(
            estimators=[
                ('rf', self.rf),
                ('gb', self.gb),
                ('svm', self.svm),
                ('nb', self.nb),
                ('lr', self.lr)
            ],
            voting='soft'
        )
        
        self.vectorizer = None
        self.label_encoder = None
    
    def train(self, X_train, y_train, vectorizer, label_encoder):
        self.vectorizer = vectorizer
        self.label_encoder = label_encoder
        
        # Train the ensemble model
        self.model.fit(X_train, y_train)
    
    def predict(self, text, threshold=0.3):
        # Preprocess the input text
        text_vector = self.vectorizer.transform([text])
        
        # Get probability predictions
        proba = self.model.predict_proba(text_vector)
        
        # Get the highest probability and its index
        max_prob = np.max(proba)
        pred_idx = np.argmax(proba)
        
        if max_prob >= threshold:
            # Return predicted intent
            return self.label_encoder.inverse_transform([pred_idx])[0], max_prob
        else:
            return None, max_prob
    
    def predict_proba(self, X):
        """Get prediction probabilities from the ensemble model"""
        return self.model.predict_proba(X)
    
    def get_confidence_scores(self, X):
        """Get confidence scores for predictions"""
        probabilities = self.predict_proba(X)
        confidence_scores = np.max(probabilities, axis=1)
        return confidence_scores
    
    def save_model(self, model_path='chatbot_model.pkl'):
        # Save the trained model and preprocessors
        model_data = {
            'model': self.model,
            'vectorizer': self.vectorizer,
            'label_encoder': self.label_encoder
        }
        joblib.dump(model_data, model_path)
    
    @classmethod
    def load_model(cls, model_path='chatbot_model.pkl'):
        # Load the trained model and preprocessors
        model_data = joblib.load(model_path)
        
        chatbot = cls()
        chatbot.model = model_data['model']
        chatbot.vectorizer = model_data['vectorizer']
        chatbot.label_encoder = model_data['label_encoder']
        
        return chatbot 
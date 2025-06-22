import numpy as np
from sklearn.metrics import classification_report, accuracy_score
from data_preprocessing import load_and_preprocess_data
from model import ChatbotModel
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def train_model():
    logger.info("Loading and preprocessing data...")
    X_train, X_test, y_train, y_test = load_and_preprocess_data()
    
    logger.info("Initializing model...")
    model = ChatbotModel(random_state=42)
    
    logger.info("Training model...")
    model.train(X_train, y_train)
    
    # Evaluate model performance
    logger.info("Evaluating model performance...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    logger.info(f"Model accuracy: {accuracy:.4f}")
    
    # Get detailed classification report
    report = classification_report(y_test, y_pred)
    logger.info("\nClassification Report:\n" + report)
    
    # Get confidence scores for test predictions
    confidence_scores = model.get_confidence_scores(X_test)
    avg_confidence = np.mean(confidence_scores)
    logger.info(f"Average prediction confidence: {avg_confidence:.4f}")
    
    # Save the trained model
    logger.info("Saving model...")
    model.save_model('enhanced_chatbot_model.pkl')
    logger.info("Model saved successfully!")

if __name__ == "__main__":
    train_model() 
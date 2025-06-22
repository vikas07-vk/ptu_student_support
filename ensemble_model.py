import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, StackingClassifier
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score, classification_report
import joblib
import logging

logger = logging.getLogger(__name__)

class EnsembleClassifier:
    def __init__(self, random_state=42):
        self.random_state = random_state
        
        # Initialize base classifiers
        self.rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=random_state
        )
        
        self.gb = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=random_state
        )
        
        self.svm = SVC(
            kernel='rbf',
            probability=True,
            random_state=random_state
        )
        
        # Initialize ensemble classifiers
        self.voting_clf = VotingClassifier(
            estimators=[
                ('rf', self.rf),
                ('gb', self.gb),
                ('svm', self.svm)
            ],
            voting='soft'
        )
        
        self.stacking_clf = StackingClassifier(
            estimators=[
                ('rf', self.rf),
                ('gb', self.gb),
                ('svm', self.svm)
            ],
            final_estimator=GradientBoostingClassifier(
                n_estimators=50,
                learning_rate=0.1,
                random_state=random_state
            ),
            cv=5
        )
        
        self.is_fitted = False

    def fit(self, X, y):
        """Train all models in the ensemble."""
        logger.info("Training Voting Classifier...")
        self.voting_clf.fit(X, y)
        
        logger.info("Training Stacking Classifier...")
        self.stacking_clf.fit(X, y)
        
        self.is_fitted = True
        logger.info("Ensemble training completed.")

    def predict(self, X):
        """Get predictions from both voting and stacking classifiers."""
        if not self.is_fitted:
            raise ValueError("Models must be fitted before prediction")
        
        voting_pred = self.voting_clf.predict(X)
        stacking_pred = self.stacking_clf.predict(X)
        
        return voting_pred, stacking_pred

    def predict_proba(self, X):
        """Get probability scores from both voting and stacking classifiers."""
        if not self.is_fitted:
            raise ValueError("Models must be fitted before prediction")
        
        voting_proba = self.voting_clf.predict_proba(X)
        stacking_proba = self.stacking_clf.predict_proba(X)
        
        return voting_proba, stacking_proba

    def evaluate(self, X_test, y_test):
        """Evaluate the ensemble models."""
        if not self.is_fitted:
            raise ValueError("Models must be fitted before evaluation")
        
        # Get predictions
        voting_pred, stacking_pred = self.predict(X_test)
        
        # Calculate accuracy scores
        voting_acc = accuracy_score(y_test, voting_pred)
        stacking_acc = accuracy_score(y_test, stacking_pred)
        
        # Generate classification reports
        voting_report = classification_report(y_test, voting_pred)
        stacking_report = classification_report(y_test, stacking_pred)
        
        logger.info(f"Voting Classifier Accuracy: {voting_acc:.4f}")
        logger.info(f"Stacking Classifier Accuracy: {stacking_acc:.4f}")
        logger.info("\nVoting Classifier Report:")
        logger.info(voting_report)
        logger.info("\nStacking Classifier Report:")
        logger.info(stacking_report)
        
        return {
            'voting_accuracy': voting_acc,
            'stacking_accuracy': stacking_acc,
            'voting_report': voting_report,
            'stacking_report': stacking_report
        }

    def save_models(self, path_prefix):
        """Save all trained models."""
        if not self.is_fitted:
            raise ValueError("Models must be fitted before saving")
        
        joblib.dump(self.voting_clf, f"{path_prefix}_voting.joblib")
        joblib.dump(self.stacking_clf, f"{path_prefix}_stacking.joblib")
        logger.info(f"Models saved with prefix: {path_prefix}")

    def load_models(self, path_prefix):
        """Load trained models."""
        self.voting_clf = joblib.load(f"{path_prefix}_voting.joblib")
        self.stacking_clf = joblib.load(f"{path_prefix}_stacking.joblib")
        self.is_fitted = True
        logger.info(f"Models loaded from prefix: {path_prefix}")

if __name__ == "__main__":
    # Test the ensemble classifier
    from sklearn.datasets import make_classification
    
    # Generate sample data
    X, y = make_classification(
        n_samples=1000,
        n_features=20,
        n_informative=15,
        n_redundant=5,
        random_state=42
    )
    
    # Initialize and train the ensemble
    ensemble = EnsembleClassifier()
    ensemble.fit(X, y)
    
    # Make predictions
    voting_pred, stacking_pred = ensemble.predict(X)
    
    # Evaluate
    results = ensemble.evaluate(X, y)
    print("\nTest Results:")
    print(f"Voting Classifier Accuracy: {results['voting_accuracy']:.4f}")
    print(f"Stacking Classifier Accuracy: {results['stacking_accuracy']:.4f}") 
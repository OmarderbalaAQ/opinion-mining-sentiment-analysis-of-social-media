import os
import joblib
from django.conf import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, 'sentiment', 'text_analysis', 'text_model.joblib')
VECTORIZER_PATH = os.path.join(settings.BASE_DIR, 'sentiment', 'text_analysis', 'vectorizer.joblib')

class TextSentimentAnalyzer:
    def __init__(self):
        try:
            # Try to load pre-trained models
            self.model = joblib.load(MODEL_PATH)
            self.vectorizer = joblib.load(VECTORIZER_PATH)
            print("✓ Loaded pre-trained models")
        except:
            print("⚠ Training new models...")
            self._train_model()
            joblib.dump(self.model, MODEL_PATH)
            joblib.dump(self.vectorizer, VECTORIZER_PATH)

    def _train_model(self):
        """Your existing training code"""
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.svm import SVC
        import pandas as pd
        
        data_path = os.path.join(settings.BASE_DIR, 'sentiment', 'text_analysis', 'train.csv')
        df = pd.read_csv(data_path)[['text', 'sentiment']].dropna()
        
        self.vectorizer = CountVectorizer(analyzer=self._text_clean)
        X = self.vectorizer.fit_transform(df['text'])
        self.model = SVC(C=0.2, kernel='linear', gamma=0.8)
        self.model.fit(X, df['sentiment'])

    def _text_clean(self, text):
        """Your existing text cleaning code (unchanged)"""
        # Paste your existing _text_clean() code here
        import string
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize
        
        nopunc = [char.lower() for char in text if char not in string.punctuation]
        nopunc = ''.join(nopunc)
        tokens = word_tokenize(nopunc)
        nohttp = [word for word in tokens if word[0:4] != 'http']
        nostop = [word for word in nohttp if word not in stopwords.words('english')]
        return nostop

    def analyze_sentiment(self, text):
        """Your existing analysis code (unchanged)"""
        if not text or not isinstance(text, str):
            return [(text, "Neutral", "😐")]
        
        texts = [text] if isinstance(text, str) else text
        predictions = self.vectorizer.transform(texts)
        results = self.model.predict(predictions)
        
        emoji_map = {'positive': '😀', 'negative': '😞', 'neutral': '😐'}
        return [(t, sentiment, emoji_map.get(sentiment.lower(), '❓')) 
                for t, sentiment in zip(texts, results)]

# Create analyzer instance
text_analyzer = TextSentimentAnalyzer()
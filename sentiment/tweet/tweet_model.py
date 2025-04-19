import numpy as np
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
import joblib
import os

# Ensure nltk dependencies are downloaded
nltk.download('stopwords')
nltk.download('punkt')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
train_path = os.path.join(BASE_DIR, 'train.csv')
test_path = os.path.join(BASE_DIR, 'test.csv')

tweets_df = pd.read_csv(train_path)
tweets_df = tweets_df[['text', 'sentiment']]

test_df = pd.read_csv(test_path)
test_df = test_df[['text', 'sentiment']]

# Remove empty or NaN rows from training data
tweets_df.dropna(subset=['text'], inplace=True)
tweets_df = tweets_df[tweets_df['text'].str.strip() != '']

# Ensure the textClean function is defined
def textClean(text):
    """Clean and preprocess the text input."""
    nopunc = [char.lower() for char in text if char not in string.punctuation]
    nopunc = ''.join(nopunc)
    tokens = word_tokenize(nopunc)
    nohttp = [word for word in tokens if word[0:4] != 'http']
    nostop = [word for word in nohttp if word not in stopwords.words('english')]
    return nostop

# Create a vectorizer that uses textClean for preprocessing
vectorizer = CountVectorizer(analyzer=textClean)

# Load and prepare data
message = vectorizer.fit_transform(tweets_df['text'])

# Split the data for training/testing
xtrain, xtest, ytrain, ytest = train_test_split(message, tweets_df.sentiment, test_size=0.20, random_state=20)

# Create and train the model
svc_model = SVC(C=0.2, kernel='linear', gamma=0.8)
svc_model.fit(xtrain, ytrain)

# Save the model and vectorizer
# joblib.dump(svc_model, 'sentiment/final_model.sav')
# joblib.dump(vectorizer, 'sentiment/vectorizer.sav')

# Load the saved model and vectorizer (you can skip the above two lines if already saved)
vectorizer = joblib.load('sentiment/vectorizer.sav')
final_model = joblib.load('sentiment/final_model.sav')

# Define the prediction function
def predict_text_sentiment(text):
    """Predict sentiment for a given text input."""
    # Clean the input text and vectorize it
    text_vector = vectorizer.transform([text])
    
    # Predict sentiment using the SVM model
    prediction = final_model.predict(text_vector)
    
    if prediction[0] == 1:
        return "Positive 😊"
    elif prediction[0] == 0:
        return "Negative 😞"
    else:
        return "Neutral 😐"

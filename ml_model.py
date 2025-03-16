import joblib
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Ensure NLTK resources are downloaded (if not done elsewhere)
nltk.download('punkt')
nltk.download('stopwords')

# Load the model and vectorizer (make sure these files exist from your training notebook)
model = joblib.load('models/expense_classifier.pkl')
vectorizer = joblib.load('models/vectorizer.pkl')

def clean_text(text):
    text = text.lower()
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word.isalpha()]
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    return " ".join(tokens)

def predict_category(raw_text):
    cleaned = clean_text(raw_text)
    prediction = model.predict(vectorizer.transform([cleaned]))[0]
    return prediction

import joblib
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Check and download necessary NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('tokenizers/punkt_tab/english')
except LookupError:
    nltk.download('punkt_tab')

# Load the model and vectorizer (ensure these files exist from your training process)
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

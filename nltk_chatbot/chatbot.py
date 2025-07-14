import nltk
import random
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# Load text file
with open('chatbot_data.txt', 'r', errors='ignore') as f:
    raw = f.read().lower()

sent_tokens = nltk.sent_tokenize(raw)
word_tokens = nltk.word_tokenize(raw)

# Lemmatization
lemmer = nltk.stem.WordNetLemmatizer()

def LemTokens(tokens):
    return [lemmer.lemmatize(token) for token in tokens]

remove_punct_dict = dict((ord(punct), None) for punct in string.punctuation)

def LemNormalize(text):
    return LemTokens(nltk.word_tokenize(text.lower().translate(remove_punct_dict)))

# Greeting
GREETING_INPUTS = ("hello", "hi", "greetings", "sup", "hey", "yo")
GREETING_RESPONSES = ["hi", "hello", "hey there!", "I'm glad you're here!"]

def greeting(sentence):
    for word in sentence.split():
        if word.lower() in GREETING_INPUTS:
            return random.choice(GREETING_RESPONSES)

# Response Generator
def generate_response(user_input):
    robo_response = ''
    sent_tokens.append(user_input)
    vectorizer = TfidfVectorizer(tokenizer=LemNormalize, stop_words='english')
    tfidf = vectorizer.fit_transform(sent_tokens)
    vals = cosine_similarity(tfidf[-1], tfidf)
    idx = vals.argsort()[0][-2]
    flat = vals.flatten()
    flat.sort()
    req_tfidf = flat[-2]

    if req_tfidf == 0:
        robo_response += "I'm sorry, I didn't understand that."
    else:
        robo_response += sent_tokens[idx]

    sent_tokens.remove(user_input)
    return robo_response

# Chat loop
print("BOT: Hello! I'm your chatbot. Type 'bye' to exit.")

while True:
    user_input = input("YOU: ").lower()
    if user_input == 'bye':
        print("BOT: Goodbye! Take care.")
        break
    elif greeting(user_input) is not None:
        print("BOT:", greeting(user_input))
    else:
        print("BOT:", generate_response(user_input))

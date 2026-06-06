from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import nltk
from nltk.corpus import stopwords
import pymorphy3
import re
import ssl

# Исправление ошибки загрузки NLTK из-за SSL сертификатов
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Загружаем стоп-слова
try:
    nltk.download('stopwords', quiet=True)
except:
    pass

morph = pymorphy3.MorphAnalyzer()
russian_stopwords = stopwords.words('russian')

def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    # Очистка и лемматизация
    text = re.sub(r'[^а-яА-ЯёЁ\s]', '', text.lower())
    words = text.split()
    lemmatized = [morph.parse(w)[0].normal_form for w in words if w not in russian_stopwords and len(w) > 2]
    return " ".join(lemmatized)

def get_topics_per_cluster(df_messages):
    """
    df_messages: DataFrame с колонками ['text', 'cluster', 'session_id']
    """
    # 1. Склеиваем сообщения в сессии для контекста
    # Группируем по session_id и соединяем тексты
    session_texts = df_messages.groupby("session_id")["text"].apply(lambda x: " ".join(map(str, x))).reset_index()
    
    # Предварительная лемматизация объединенных текстов сессий
    session_texts["clean_text"] = session_texts["text"].apply(preprocess_text)
    
    # Фильтруем пустые тексты
    df_valid = session_texts[session_texts["clean_text"].str.len() > 0].copy()
    
    if df_valid.empty:
        return {}

    # 2. Инициализируем модель
    vectorizer_model = CountVectorizer(stop_words=russian_stopwords)
    embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    
    topic_model = BERTopic(
        embedding_model=embedding_model, 
        vectorizer_model=vectorizer_model,
        language="multilingual",
        min_topic_size=5,
        calculate_probabilities=True,
        # Биграммы помогают отличить "спокойной ночи" от просто "ночь"
        # но в данном случае они должны быть в одном контексте пожеланий
        n_gram_range=(1, 2)
    )

    docs = df_valid["clean_text"].tolist()
    topics, probs = topic_model.fit_transform(docs)
    
    try:
        # ПЕРЕД авто-уменьшением принудительно схлопываем всё в очень маленькое количество групп
        # Это заставит модель объединить даже "слегка похожие" темы вроде "спокойной ночи" и "котенок, спать"
        
        # 1. Сначала до 7 самых крупных веток (это точно склеит дубликаты пожеланий)
        topic_model.reduce_topics(docs, nr_topics=7)
        
        # 2. А потом разрешаем модели вернуть 1-2 уникальные темы, если они ОЧЕНЬ сильные
        topic_model.reduce_topics(docs, nr_topics="auto")
    except Exception as e:
        print(f"Topic reduction error: {e}")
    
    # Собираем результат: информация о найденных ТЕМАХ СЕССИЙ
    topic_info = topic_model.get_topic_info()
    
    top_topics = topic_info[topic_info["Topic"] != -1].head(10) # Берем до 10 тем
    
    semantic_topics = {}
    for _, row in top_topics.iterrows():
        topic_id = int(row["Topic"])
        count = int(row["Count"])
        words = [w[0] for w in topic_model.get_topic(topic_id)[:5]]
        semantic_topics[topic_id] = {
            "keywords": ", ".join(words),
            "count": count
        }

    return semantic_topics

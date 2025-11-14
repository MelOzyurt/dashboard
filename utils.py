"""
utils.py

Metin temizleme, normalizasyon ve basit NLP ön işleme fonksiyonları.
Streamlit uygulamasındaki müşteri yorumlarını AI analizine hazırlamak için kullanılır.
"""

import re
import pandas as pd
import numpy as np
import nltk
from nltk.corpus import stopwords
from textblob import TextBlob

# NLTK gerekli paketleri yükle (ilk çalıştırmada gerekebilir)
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

# Stopword listesi
STOPWORDS = set(stopwords.words("english"))


# ---------------------------------------------------------
# 🧹 Temel metin temizleme
# ---------------------------------------------------------
def clean_text_basic(text: str) -> str:
    """
    Basit temizlik: HTML, özel karakterler, fazla whitespace.
    AI modeline giden veriyi daha okunabilir hale getirir.
    """

    if not isinstance(text, str):
        return ""

    text = text.strip()

    # HTML tag'leri sil
    text = re.sub(r"<.*?>", " ", text)

    # URL'leri kaldır
    text = re.sub(r"http\S+|www\.\S+", " ", text)

    # Özel karakterler
    text = re.sub(r"[^A-Za-z0-9,.!?'\s]", " ", text)

    # Fazla boşlukları tek boşluğa indir
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ---------------------------------------------------------
# 🔤 NLP normalize (lowercase + stopword removal)
# ---------------------------------------------------------
def normalize_text(text: str) -> str:
    """
    NLP odaklı temizlik: lowercase, stopword çıkarma,
    gereksiz kısa kelimeleri filtreleme.
    """

    if not isinstance(text, str):
        return ""

    text = text.lower()

    words = text.split()
    filtered_words = [w for w in words if w not in STOPWORDS and len(w) > 2]

    return " ".join(filtered_words)


# ---------------------------------------------------------
# ✨ Spelling correction (TextBlob)
# ---------------------------------------------------------
def correct_spelling(text: str, enabled: bool = False) -> str:
    """
    AI modeli daha hatasız input isterse spelling düzeltebilir.
    Bu işlem maliyetli olduğundan default kapalı.
    """

    if not enabled:
        return text

    try:
        return str(TextBlob(text).correct())
    except Exception:
        # Hata durumunda orijinal metni geri ver
        return text


# ---------------------------------------------------------
# 🧠 Ana preprocess fonksiyonu
# ---------------------------------------------------------
def preprocess_reviews(text: str, correct=False) -> str:
    """
    Tüm metinleri temizler:
    - Basic cleaning
    - Normalization
    - (Opsiyonel) spelling correction

    App tarafından direkt kullanılmak üzere optimize edilmiştir.
    """

    if not text:
        return ""

    text = clean_text_basic(text)
    text = normalize_text(text)
    text = correct_spelling(text, enabled=correct)

    return text


# ---------------------------------------------------------
# 📊 DataFrame destek fonksiyonu
# ---------------------------------------------------------
def load_reviews_from_dataframe(df: pd.DataFrame, text_column: str):
    """
    DataFrame'deki text kolonlarını alıp temizler.
    Çok sayıda yorum varsa AI'a gönderilmeden önce temiz input sağlar.
    """
    try:
        reviews = df[text_column].dropna().astype(str).tolist()
        return [preprocess_reviews(r) for r in reviews]
    except Exception as e:
        raise ValueError(f"Error extracting text column '{text_column}': {e}")

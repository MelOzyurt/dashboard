"""
firebase_auth.py

Basit Firebase Authentication yardımcı fonksiyonları:
- init_firebase()   : Firebase Admin SDK'yı başlatır (token doğrulama vs. için)
- sign_up_user()    : Email & password ile yeni kullanıcı oluşturur
- sign_in_user()    : Email & password ile login yapar

Gereken secrets (Streamlit Cloud veya .streamlit/secrets.toml içinde):

[firebase]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "firebase-adminsdk-xxx@YOUR_PROJECT_ID.iam.gserviceaccount.com"
client_id = "1234567890"
token_uri = "https://oauth2.googleapis.com/token"

FIREBASE_API_KEY = "YOUR_WEB_API_KEY"
"""

import json
import requests
import streamlit as st
import firebase_admin
from firebase_admin import credentials


# -----------------------------
# Firebase Admin başlatma
# -----------------------------
def init_firebase():
    """
    Firebase Admin SDK'yı bir kez başlatır.
    - Service account bilgilerini st.secrets["firebase"] içinden alır.
    - Zaten başlatılmışsa tekrar başlatmaz.
    """
    if firebase_admin._apps:
        # Zaten başlatılmış
        return

    if "firebase" not in st.secrets:
        st.warning("⚠️ Firebase config not found in st.secrets['firebase']. Skipping init.")
        return

    firebase_config = dict(st.secrets["firebase"])

    # private_key içindeki \n kaçışlarını gerçek newline'a çevir
    if "private_key" in firebase_config:
        firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")

    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred, {"projectId": firebase_config.get("project_id")})


# -----------------------------
# Yardımcı: REST endpoint'leri
# -----------------------------
def _get_api_key() -> str:
    api_key = st.secrets.get("FIREBASE_API_KEY", None)
    if not api_key:
        raise RuntimeError(
            "FIREBASE_API_KEY not found in Streamlit secrets. "
            "Please set FIREBASE_API_KEY in Streamlit Cloud Secrets."
        )
    return api_key


def _extract_error_message(resp_json: dict) -> str:
    """
    Firebase REST error mesajından okunabilir bir mesaj çıkarır.
    """
    try:
        error = resp_json.get("error", {})
        message = error.get("message", "Unknown error")
        return message
    except Exception:
        return "Unknown error"


# -----------------------------
# Kullanıcı oluşturma (Sign Up)
# -----------------------------
def sign_up_user(email: str, password: str):
    """
    Firebase Authentication ile email/password kullanarak yeni kullanıcı oluşturur.

    Returns:
        (success: bool, message: str)
    """
    if not email or not password:
        return False, "Email and password are required."

    api_key = _get_api_key()
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"

    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True,
    }

    try:
        resp = requests.post(url, data=json.dumps(payload))
        data = resp.json()

        if resp.status_code == 200:
            # data içinde idToken, refreshToken vs. var
            return True, "Account created successfully."
        else:
            msg = _extract_error_message(data)
            return False, f"Sign up failed: {msg}"
    except Exception as e:
        return False, f"Sign up error: {e}"


# -----------------------------
# Login (Sign In)
# -----------------------------
def sign_in_user(email: str, password: str):
    """
    Firebase Authentication ile email/password kullanarak login yapar.

    Returns:
        (success: bool, message: str)

    Not: İstersen buradan idToken vs. de dönecek şekilde genişletebilirsin.
    """
    if not email or not password:
        return False, "Email and password are required."

    api_key = _get_api_key()
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True,
    }

    try:
        resp = requests.post(url, data=json.dumps(payload))
        data = resp.json()

        if resp.status_code == 200:
            # Burada token alabilirsin: data["idToken"], data["localId"], ...
            # Şimdilik sadece başarı mesajı dönüyoruz.
            return True, "Login successful."
        else:
            msg = _extract_error_message(data)
            return False, f"Login failed: {msg}"
    except Exception as e:
        return False, f"Login error: {e}"

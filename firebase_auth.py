"""
firebase_auth.py

Firebase Authentication yardımcı fonksiyonları:
- init_firebase()   : Firebase Admin SDK'yı başlatır (service account ile)
- sign_up_user()    : Email & password ile yeni kullanıcı oluşturur (REST API)
- sign_in_user()    : Email & password ile login yapar (REST API)

Senin Streamlit Cloud secrets formatına göre çalışır:

OPENAI_API_KEY = "..."

FIREBASE_KEY = "{... service account JSON string ...}"
FIREBASE_WEB_API_KEY = "..."

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
    - Service account bilgilerini st.secrets["FIREBASE_KEY"] içindeki JSON'dan alır.
    - Zaten başlatılmışsa tekrar başlatmaz.
    """

    if firebase_admin._apps:
        # Zaten başlatılmış
        return

    if "FIREBASE_KEY" not in st.secrets:
        st.warning(
            "⚠️ FIREBASE_KEY not found in Streamlit secrets. "
            "Admin SDK init skipped. If you only use email/password auth via REST, this is not critical."
        )
        return

    raw_json = st.secrets["FIREBASE_KEY"]

    # FIREBASE_KEY şu anda uzun bir JSON string şeklinde
    # onu dict'e parse ediyoruz
    try:
        if isinstance(raw_json, str):
            firebase_config = json.loads(raw_json)
        else:
            # Bazı durumlarda secrets direkt dict olabilir
            firebase_config = dict(raw_json)
    except Exception as e:
        st.error(f"Failed to parse FIREBASE_KEY JSON: {e}")
        return

    # private_key içindeki \n kaçışlarını gerçek newline'a çevir
    if "private_key" in firebase_config:
        firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")

    try:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {"projectId": firebase_config.get("project_id")})
    except Exception as e:
        st.error(f"Failed to initialize Firebase Admin SDK: {e}")


# -----------------------------
# Yardımcı: Web API key çekme
# -----------------------------
def _get_api_key() -> str:
    """
    Firebase Web API key'i secrets içinden çeker.

    Senin secrets yapına göre:
    - Tercihen FIREBASE_WEB_API_KEY kullanıyoruz.
    - Fallback olarak FIREBASE_API_KEY veya firebase.api_key gibi alternatifleri de deneriz.
    """

    # 1) Senin kullandığın isim
    if "FIREBASE_WEB_API_KEY" in st.secrets and st.secrets["FIREBASE_WEB_API_KEY"]:
        return st.secrets["FIREBASE_WEB_API_KEY"]

    # 2) Alternatif isimler (eski kodla uyumluluk için)
    if "FIREBASE_API_KEY" in st.secrets and st.secrets["FIREBASE_API_KEY"]:
        return st.secrets["FIREBASE_API_KEY"]

    if "firebase" in st.secrets:
        firebase_section = st.secrets["firebase"]
        if "api_key" in firebase_section and firebase_section["api_key"]:
            return firebase_section["api_key"]

    # Hâlâ yoksa debug amaçlı mevcut key isimlerini göster
    available_top = list(st.secrets.keys())
    firebase_nested = (
        list(st.secrets["firebase"].keys()) if "firebase" in st.secrets else None
    )

    raise RuntimeError(
        "Firebase Web API key not found in Streamlit secrets. "
        "Expected one of: FIREBASE_WEB_API_KEY, FIREBASE_API_KEY or firebase.api_key.\n"
        f"Top-level keys: {available_top}, firebase nested: {firebase_nested}.\n"
        "Please define FIREBASE_WEB_API_KEY=\"...\" in Streamlit Cloud Secrets."
    )


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

    İstersen burada idToken vs. de döndürecek şekilde genişletebilirsin.
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
            return True, "Login successful."
        else:
            msg = _extract_error_message(data)
            return False, f"Login failed: {msg}"
    except Exception as e:
        return False, f"Login error: {e}"

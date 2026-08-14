import streamlit as st
import pandas as pd
import json
import requests
import io
import base64
import uuid
import math
from datetime import datetime

# ------------------------------------------------------------
# 1. НАСТРОЙКА СТРАНИЦЫ И СЕССИИ
# ------------------------------------------------------------
st.set_page_config(page_title="SecurLLM — Проектирование ВСП", layout="wide")
st.title("🏢 SecurLLM — проектирование системы безопасности для ВСП")

# Инициализация состояния сессии
if "rooms" not in st.session_state:
    st.session_state.rooms = []  # список словарей с полями: name, length, width, height, doors, windows
if "calc_result" not in st.session_state:
    st.session_state.calc_result = None

# ------------------------------------------------------------
# 2. РЕАЛЬНЫЙ ВЫЗОВ GIGACHAT API (НОВАЯ ФУНКЦИЯ)
# ------------------------------------------------------------
def call_gigachat(prompt, api_key, model="GigaChat-3-Ultra", max_tokens=2000, temperature=0.7):
    """
    Отправляет запрос к GigaChat API и возвращает сгенерированный текст.
    """
    if not api_key:
        return "Ошибка: не указан API-ключ GigaChat."

    # 1. Получение токена доступа (OAuth 2.0)
    auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    auth_headers = {
        "Authorization": f"Basic {api_key}",
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    auth_data = {
        "scope": "GIGACHAT_API_PERS"
    }

    try:
        auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data, timeout=10)
        auth_response.raise_for_status()
        token_data = auth_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return f"Ошибка получения токена: {token_data}"
    except Exception as e:
        return f"Ошибка авторизации GigaChat: {str(e)}"

    # 2. Отправка запроса к модели
    chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    chat_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    chat_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Ты — эксперт по системам физической безопасности и противопожарной защиты. Отвечай строго по делу, используй нормативные документы."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }

    try:
        response = requests.post(chat_url, headers=chat_headers, json=chat_payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return f"Неожиданный формат ответа: {result}"
    except requests.exceptions.Timeout:
        return "Ошибка: таймаут при обращении к GigaChat."
    except Exception as e:
        return f"Ошибка при генерации текста: {str(e)}"

# ------------------------------------------------------------
# 3. БОКОВАЯ ПАНЕЛЬ — КЛЮЧ (ТОЛЬКО ИЗ SECRETS, БЕЗ ПОЛЯ ВВОДА)
# ------------------------------------------------------------
with st.sidebar:
    st.header("🔐 Настройки")
    # Ключ загружается из секретов, поле ввода отсутствует
    try:
        gigachat_key = st.secrets["GIGACHAT_KEY"]
    except KeyError:
        st.error("❌ Не найден GIGACHAT_KEY в .streamlit/secrets.toml")
        st.stop()
    st.markdown("---")
    st.caption("Прототип V2 • зональный подход • поддержка нескольких помещений")

# ------------------------------------------------------------
# 4. ЭКСПЛИКАЦИЯ ПОМЕЩЕНИЙ (БЕЗ ИЗМЕНЕНИЙ)
# ------------------------------------------------------------
st.subheader("📐 Экспликация помещений")

with st.expander("➕ Добавить помещение", expanded=False):
    with st.form("add_room_form"):
        cols = st.columns(4)
        with cols[0]:
            room_name = st.text_input("Название", placeholder="касса №1")
        with cols[1]:
            length = st.number_input("Длина (м)", min_value=0.5, value=6.0, step=0.5)
            width = st.number_input("Ширина (м)", min_value=0.5, value=4.0, step=0.5)
        with cols[2]:
            height = st.number_input("Высота (м)", min_value=2.0, value=3.0, step=0.1)
            doors = st.number_input("Двери", min_value=0, value=1, step=1)
            windows = st.number_input("Окна", min_value=0, value=0, step=1)
        with cols[3]:
            st.write(" ")
            st.write(" ")
            submitted = st.form_submit_button("✅ Добавить помещение")
        if submitted and room_name.strip():
            st.session_state.rooms.append({
                "name": room_name.strip(),
                "length": length,
                "width": width,
                "height": height,
                "doors": doors,
                "windows": windows
            })
            st.success(f"Добавлено: {room_name}")
            st.rerun()

# Отображение списка комнат
if st.session_state.rooms:
    df_rooms = pd.DataFrame(st.session_state.rooms)
    st.dataframe(df_rooms, use_container_width=True, hide_index=True)

    col_clear, col_fill = st.columns(2)
    with col_clear:
        if st.button("🗑️ Очистить список"):
            st.session_state.rooms = []
            st.rerun()
    with col_fill:
        if st.button("📥 Заполнить примером (ВСП)"):
            st.session_state.rooms = [
                {"name": "Кассовый зал", "length": 8, "width": 6, "height": 3.2, "doors": 2, "windows": 0},
                {"name": "Операционный зал", "length": 12, "width": 8, "height": 3.2, "doors": 1, "windows": 2},
                {"name": "Хранилище", "length": 4, "width": 4, "height": 3.0, "doors": 1, "windows": 0},
                {"name": "Серверная", "length": 3, "width": 3, "height": 3.0, "doors": 1, "windows": 0},
            ]
            st.rerun()
else:
    st.info("Пока нет ни одного помещения. Добавьте комнаты для расчёта.")

# ------------------------------------------------------------
# 5. ВЫБОР ЗОН (БЕЗ ЛИШНИХ ЗАГОЛОВКОВ)
# ------------------------------------------------------------
# Инициализация состояний для зон
if "video_zones" not in st.session_state:
    st.session_state.video_zones = []
if "skud_zones" not in st.session_state:
    st.session_state.skud_zones = []
if "ohr_zones" not in st.session_state:
    st.session_state.ohr_zones = []
if "fire_zones" not in st.session_state:
    st.session_state.fire_zones = []
if "soue_zones" not in st.session_state:
    st.session_state.soue_zones = []

# Видеонаблюдение
with st.expander("📹 Видеонаблюдение", expanded=False):
    video_opts = [
        "Входная группа", "Кассовый узел (каждое место)", "Операционный зал",
        "Хранилище", "Коридоры", "Кабинеты", "Периметр", "Банкоматы"
    ]
    selected_video = st.multiselect(
        "Выберите зоны для видеонаблюдения",
        video_opts,
        default=st.session_state.video_zones
    )
    st.session_state.video_zones = selected_video

# СКУД
with st.expander("🚪 СКУД", expanded=False):
    skud_opts = [
        "Главный вход", "Внутренние двери", "Кассовый узел/хранилище",
        "Серверная", "Кабинеты руководства"
    ]
    selected_skud = st.multiselect(
        "Выберите зоны для СКУД",
        skud_opts,
        default=st.session_state.skud_zones
    )
    st.session_state.skud_zones = selected_skud
    ident_type = st.radio("Тип идентификации", ["Карта", "Карта+PIN", "Карта+биометрия"], index=0)
    two_factor = st.checkbox("Двухфакторная для критических зон", value=True)

# Охранная сигнализация
with st.expander("🔔 Охранная сигнализация", expanded=False):
    ohr_opts = [
        "Периметр (двери/окна)", "Объём (движение)", "Предметный (сейфы)",
        "Усиленная охрана кассы/хранилища"
    ]
    selected_ohr = st.multiselect(
        "Выберите зоны для охранной сигнализации",
        ohr_opts,
        default=st.session_state.ohr_zones
    )
    st.session_state.ohr_zones = selected_ohr

# Пожарная сигнализация
with st.expander("🔥 Пожарная сигнализация", expanded=False):
    fire_opts = [
        "Дымовые извещатели", "Тепловые извещатели", "Комбинированные извещатели"
    ]
    selected_fire = st.multiselect(
        "Типы извещателей",
        fire_opts,
        default=st.session_state.fire_zones
    )
    st.session_state.fire_zones = selected_fire
    suspended = st.checkbox("Подвесной потолок (Да)", value=False)
    beams = st.checkbox("Балки > 400 мм", value=False)
    vent_dist = st.number_input("Расстояние до вентиляции (м)", min_value=0.5, value=1.0, step=0.1)

# СОУЭ
with st.expander("📢 СОУЭ", expanded=False):
    soue_opts = ["Звуковое оповещение", "Речевое оповещение"]
    selected_soue = st.multiselect(
        "Тип оповещения",
        soue_opts,
        default=st.session_state.soue_zones

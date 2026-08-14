import streamlit as st
import pandas as pd
import requests
import base64
import uuid
import math
import json
import urllib3
from datetime import datetime

# Отключаем предупреждения о SSL для прототипа
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ------------------------------------------------------------
# 1. НАСТРОЙКА СТРАНИЦЫ
# ------------------------------------------------------------
st.set_page_config(page_title="SecurLLM — проектирование ВСП", layout="centered")

# --- СТИЛИ (SberDesign) ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .main > div { background-color: #f8f9fa; padding-top: 6rem !important; }
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #1a1a1a !important;
        font-family: 'Inter', sans-serif;
    }
    .stMarkdown, .stText, label, .stSelectbox label, .stTextArea label {
        color: #1a1a1a !important;
    }
    .stTextArea textarea, .stSelectbox div, .stButton button {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #d0d7de !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif;
    }
    .stTextArea textarea:focus, .stSelectbox div:focus {
        border-color: #1A991A !important;
        box-shadow: 0 0 0 2px rgba(26, 153, 26, 0.2) !important;
    }
    .stButton button {
        background-color: #1A991A !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        border-radius: 8px !important;
        transition: 0.2s;
        width: 100%;
    }
    .stButton button:hover {
        background-color: #0f7a0f !important;
        box-shadow: 0 4px 12px rgba(26, 153, 26, 0.3);
    }
    .stRadio > div { background-color: transparent !important; }
    .stRadio label { color: #1a1a1a !important; }
    .stCheckbox label { color: #1a1a1a !important; }
    .stAlert, .stInfo, .stSuccess, .stWarning {
        background-color: #ffffff !important;
        border: 1px solid #d0d7de !important;
        color: #1a1a1a !important;
        border-radius: 8px !important;
    }
    .stAlert { border-left: 4px solid #1A991A !important; }
    .stInfo { border-left: 4px solid #2d7b2d !important; }
    .stSuccess { border-left: 4px solid #1A991A !important; }
    .stWarning { border-left: 4px solid #f5a623 !important; }
    hr { border-color: #d0d7de !important; }
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# --- ЛОГОТИП СБЕРА ---
st.markdown("""
<div style="margin-top: 30px; display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem; border-bottom: 1px solid #d0d7de; padding-bottom: 1rem;">
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="36" height="36" rx="8" fill="#1A991A"/>
        <path d="M10 18L14 22L26 10" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <span style="font-size: 24px; font-weight: 700; color: #1A991A; letter-spacing: -0.5px;">Сбер</span>
    <span style="font-size: 18px; color: #333F48; font-weight: 300; margin-left: 4px;">| SecurLLM</span>
</div>
""", unsafe_allow_html=True)

# --- ЗАГОЛОВОК ---
st.markdown("""
    <div style="text-align: left; margin-bottom: 1.5rem;">
        <h1 style="color: #1a1a1a; font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem;">SecurLLM</h1>
        <p style="color: #4a4a4a; font-size: 1rem; margin-top: 0;">Система проектирования, оптимизации и управления безопасностью и противопожарной защитой объектов банка на всех этапах жизненного цикла.</p>
    </div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# 2. ЧТЕНИЕ КЛЮЧА ИЗ SECRETS
# ------------------------------------------------------------
try:
    GIGACHAT_KEY = st.secrets["GIGACHAT_KEY"]
except Exception:
    st.error("❌ Ошибка: не найден секрет GIGACHAT_KEY. Проверьте настройки приложения.")
    st.stop()

# ------------------------------------------------------------
# 3. РЕАЛЬНЫЙ ВЫЗОВ GIGACHAT API (с фиксом SSL и URL)
# ------------------------------------------------------------
def call_gigachat_vision(prompt, image_base64, api_key):
    """
    Отправляет изображение в GigaChat через мультимодальный API.
    Использует модель GigaChat-2-Max.
    """
    if not api_key:
        return "Ошибка: не указан API-ключ GigaChat."

    # Авторизация
    auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    auth_headers = {
        "Authorization": f"Basic {api_key}",
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    auth_data = {"scope": "GIGACHAT_API_PERS"}
    try:
        auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data, timeout=10, verify=False)
        auth_response.raise_for_status()
        access_token = auth_response.json().get("access_token")
        if not access_token:
            return "Ошибка получения токена"
    except Exception as e:
        return f"Ошибка авторизации GigaChat: {str(e)}"

    # Запрос к мультимодальной модели
    vision_url = "https://api.giga.chat/v1/chat/completions"
    vision_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    vision_payload = {
        "model": "GigaChat-2-Max",  # изменено с GigaChat-Vision
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                ]
            }
        ],
        "temperature": 0.2,
        "max_tokens": 2000,
        "stream": False
    }
    
    try:
        response = requests.post(vision_url, headers=vision_headers, json=vision_payload, timeout=120, verify=False)
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
# 3.1. ПРОВЕРКА ДОСТУПНЫХ МОДЕЛЕЙ GIGACHAT
# ------------------------------------------------------------
def get_available_models(api_key):
    """
    Получает список доступных моделей GigaChat.
    Возвращает JSON с моделями или текст ошибки.
    """
    if not api_key:
        return "Ошибка: не указан API-ключ."

    # 1. Получаем токен
    auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    auth_headers = {
        "Authorization": f"Basic {api_key}",
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    auth_data = {"scope": "GIGACHAT_API_PERS"}
    try:
        auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data, timeout=10, verify=False)
        auth_response.raise_for_status()
        access_token = auth_response.json().get("access_token")
        if not access_token:
            return "Ошибка получения токена"
    except Exception as e:
        return f"Ошибка авторизации: {str(e)}"

    # 2. Запрос списка моделей
    url = "https://api.giga.chat/v1/models"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return f"Ошибка получения моделей: {str(e)}"

# ------------------------------------------------------------
# 4. ML-МОДУЛЬ РАСПОЗНАВАНИЯ ЧЕРТЕЖЕЙ (GigaChat Vision)
# ------------------------------------------------------------
def call_gigachat_vision(prompt, image_base64, api_key):
    """
    Отправляет изображение в GigaChat Vision через мультимодальный API.
    """
    if not api_key:
        return "Ошибка: не указан API-ключ GigaChat."

    # Авторизация (та же, что и для обычного GigaChat)
    auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    auth_headers = {
        "Authorization": f"Basic {api_key}",
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    auth_data = {"scope": "GIGACHAT_API_PERS"}
    try:
        auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data, timeout=10, verify=False)
        auth_response.raise_for_status()
        access_token = auth_response.json().get("access_token")
        if not access_token:
            return "Ошибка получения токена"
    except Exception as e:
        return f"Ошибка авторизации GigaChat: {str(e)}"

    # Запрос к Vision API
    vision_url = "https://api.giga.chat/v1/chat/completions"
    vision_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    vision_payload = {
        "model": "GigaChat-Vision",  # мультимодальная модель
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                ]
            }
        ],
        "temperature": 0.2,
        "max_tokens": 2000,
        "stream": False
    }
    
    try:
        response = requests.post(vision_url, headers=vision_headers, json=vision_payload, timeout=120, verify=False)
        response.raise_for_status()
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return f"Неожиданный формат ответа: {result}"
    except requests.exceptions.Timeout:
        return "Ошибка: таймаут при обращении к GigaChat Vision."
    except Exception as e:
        return f"Ошибка при генерации текста: {str(e)}"

def recognize_floor_plan(image_bytes, api_key):
    """
    Отправляет изображение чертежа в GigaChat Vision.
    Возвращает список помещений с параметрами.
    """
    # Кодируем изображение в base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    prompt = """
Ты — эксперт по анализу архитектурных планов.
Проанализируй план помещения на изображении.
Извлеки все помещения, их размеры (длина, ширина), количество дверей и окон,
назначение (если подписано).

Верни результат строго в формате JSON (массив объектов):
[
    {
        "name": "название помещения",
        "length": длина в метрах (число),
        "width": ширина в метрах (число),
        "doors": количество дверей (число),
        "windows": количество окон (число),
        "purpose": "назначение"
    }
]
Если какие-то данные отсутствуют — укажи null.
Если на чертеже нет помещений — верни пустой массив: []
Не добавляй никаких пояснений, только JSON.
"""
    
    response_text = call_gigachat_vision(prompt, image_base64, api_key)
    
    # Парсим JSON из ответа
    try:
        # Пробуем найти JSON в тексте (на случай, если модель добавила пояснения)
        import re
        json_match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
        if json_match:
            rooms = json.loads(json_match.group())
        else:
            rooms = json.loads(response_text)
        return rooms
    except json.JSONDecodeError as e:
        st.error(f"Ошибка парсинга JSON: {e}")
        st.text_area("Сырой ответ модели:", response_text, height=200)
        return []

# ------------------------------------------------------------
# 5. СОСТОЯНИЕ СЕССИИ
# ------------------------------------------------------------
if "rooms" not in st.session_state:
    st.session_state.rooms = []
if "calc_result" not in st.session_state:
    st.session_state.calc_result = None
if "manual_mode" not in st.session_state:
    st.session_state.manual_mode = False

# ------------------------------------------------------------
# 6. ЗАГРУЗКА ЧЕРТЕЖА (реальный ML-модуль)
# ------------------------------------------------------------
st.subheader("📄 Загрузка чертежа")

uploaded_file = st.file_uploader(
    "Загрузите чертёж (PDF, PNG, JPG) — данные будут извлечены автоматически",
    type=["pdf", "png", "jpg", "jpeg"],
    help="Для прототипа поддерживаются растровые изображения (PNG, JPG). PDF обрабатывается как изображение."
)

if uploaded_file is not None:
    with st.spinner("🔄 Распознавание чертежа с помощью GigaChat Vision..."):
        # Читаем файл в байты (для PDF нужно конвертировать в изображение, но пока упрощённо)
        file_bytes = uploaded_file.read()
        
        # Определяем тип файла
        if uploaded_file.type == "application/pdf":
            st.warning("⚠️ Для PDF требуется дополнительная обработка (конвертация в изображение). В текущей версии рекомендуется использовать PNG или JPG.")
            # Для прототипа: если PDF, показываем сообщение
        else:
            # Вызываем ML-модуль
            recognized_rooms = recognize_floor_plan(file_bytes, GIGACHAT_KEY)
            
            if recognized_rooms and len(recognized_rooms) > 0:
                st.success(f"✅ Распознано {len(recognized_rooms)} помещений")
                df_recognized = pd.DataFrame(recognized_rooms)
                st.dataframe(df_recognized, use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📥 Применить распознанные данные", use_container_width=True):
                        st.session_state.rooms = recognized_rooms
                        st.session_state.manual_mode = False
                        st.rerun()
                with col2:
                    if st.button("✏️ Редактировать вручную", use_container_width=True):
                        st.session_state.manual_mode = True
                        st.rerun()
            else:
                st.warning("⚠️ Не удалось распознать помещения на чертеже. Заполните данные вручную.")
                if st.button("✏️ Перейти к ручному вводу"):
                    st.session_state.manual_mode = True
                    st.rerun()

# ------------------------------------------------------------
# 7. ЭКСПЛИКАЦИЯ ПОМЕЩЕНИЙ (ручной ввод + автозаполнение)
# ------------------------------------------------------------
if st.session_state.manual_mode or not st.session_state.rooms:
    st.subheader("📐 Экспликация помещений (ручной ввод)")

    with st.expander("➕ Добавить помещение", expanded=False):
        with st.form("add_room_form"):
            st.markdown("**Основные параметры**")
            col1, col2, col3 = st.columns(3)
            with col1:
                room_name = st.text_input("Название", placeholder="касса №1")
                length = st.number_input("Длина (м)", min_value=0.5, value=6.0, step=0.5)
                width = st.number_input("Ширина (м)", min_value=0.5, value=4.0, step=0.5)
                height = st.number_input("Высота потолка (м)", min_value=2.0, value=3.0, step=0.1)
                floor = st.number_input("Этаж", min_value=1, value=1, step=1)
            with col2:
                doors = st.number_input("Двери", min_value=0, value=1, step=1)
                windows = st.number_input("Окна", min_value=0, value=0, step=1)
                occupancy = st.number_input("Количество людей", min_value=0, value=5, step=1)
                has_valuables = st.checkbox("Наличие ценностей (сейфы, касса)")
                is_critical = st.checkbox("Критичное помещение (серверная, хранилище)")
            with col3:
                fire_category = st.selectbox(
                    "Категория пожарной опасности",
                    ["А", "Б", "В", "Г", "Д"],
                    index=2
                )
                has_suspended = st.checkbox("Подвесной потолок")
                has_beams = st.checkbox("Балки > 400 мм")
                purpose_type = st.selectbox(
                    "Назначение помещения",
                    ["Кассовый узел", "Операционный зал", "Серверная", "Хранилище", 
                     "Кабинет", "Коридор", "Офис", "Санузел", "Другое"]
                )
                if purpose_type == "Другое":
                    purpose = st.text_input("Укажите назначение", placeholder="например: архив")
                else:
                    purpose = purpose_type

            submitted = st.form_submit_button("✅ Добавить помещение")
            if submitted and room_name.strip():
                st.session_state.rooms.append({
                    "name": room_name.strip(),
                    "length": length,
                    "width": width,
                    "height": height,
                    "area": length * width,
                    "floor": floor,
                    "doors": doors,
                    "windows": windows,
                    "occupancy": occupancy,
                    "has_valuables": has_valuables,
                    "is_critical": is_critical,
                    "fire_category": fire_category,
                    "has_suspended": has_suspended,
                    "has_beams": has_beams,
                    "purpose": purpose
                })
                st.success(f"✅ Добавлено: {room_name}")
                st.rerun()

# Отображение списка комнат
if st.session_state.rooms:
    df_rooms = pd.DataFrame(st.session_state.rooms)
    display_cols = ["name", "length", "width", "height", "area", "floor", "doors", "windows", "occupancy", "purpose"]
    st.dataframe(df_rooms[display_cols], use_container_width=True, hide_index=True)

    col_clear, col_fill = st.columns(2)
    with col_clear:
        if st.button("🗑️ Очистить список"):
            st.session_state.rooms = []
            st.session_state.manual_mode = False
            st.rerun()
    with col_fill:
        if st.button("📥 Заполнить примером (ВСП)"):
            st.session_state.rooms = [
                {"name": "Кассовый зал", "length": 8, "width": 6, "height": 3.2, "area": 48, "floor": 1,
                 "doors": 2, "windows": 0, "occupancy": 10, "has_valuables": True, "is_critical": False,
                 "fire_category": "В", "has_suspended": False, "has_beams": False, "purpose": "Кассовый узел"},
                {"name": "Операционный зал", "length": 12, "width": 8, "height": 3.2, "area": 96, "floor": 1,
                 "doors": 1, "windows": 2, "occupancy": 25, "has_valuables": False, "is_critical": False,
                 "fire_category": "В", "has_suspended": True, "has_beams": False, "purpose": "Операционный зал"},
                {"name": "Хранилище", "length": 4, "width": 4, "height": 3.0, "area": 16, "floor": 1,
                 "doors": 1, "windows": 0, "occupancy": 0, "has_valuables": True, "is_critical": True,
                 "fire_category": "В", "has_suspended": False, "has_beams": False, "purpose": "Хранилище"},
                {"name": "Серверная", "length": 3, "width": 3, "height": 3.0, "area": 9, "floor": 1,
                 "doors": 1, "windows": 0, "occupancy": 2, "has_valuables": False, "is_critical": True,
                 "fire_category": "В", "has_suspended": False, "has_beams": False, "purpose": "Серверная"},
            ]
            st.session_state.manual_mode = False
            st.rerun()
else:
    if not st.session_state.manual_mode:
        st.info("ℹ️ Загрузите чертёж или заполните данные вручную, нажав кнопку ниже.")
        if st.button("✏️ Перейти к ручному вводу"):
            st.session_state.manual_mode = True
            st.rerun()

# ------------------------------------------------------------
# 8. ВЫБОР СЦЕНАРИЯ (4 кнопки)
# ------------------------------------------------------------
if st.session_state.rooms:
    st.markdown("---")
    st.subheader("📄 Выберите сценарий генерации")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        btn_info = st.button("📋 Справка", use_container_width=True)
    with col2:
        btn_estimate = st.button("💰 Смета", use_container_width=True)
    with col3:
        btn_rd = st.button("📐 Рабочая документация", use_container_width=True)
    with col4:
        btn_application = st.button("📨 Заявка", use_container_width=True)

# ------------------------------------------------------------
# 9. ЛОГИКА ОПРЕДЕЛЕНИЯ СИСТЕМ (автоматически)
# ------------------------------------------------------------
def get_systems_for_room(room):
    purpose = room.get("purpose", "").lower()
    is_critical = room.get("is_critical", False)
    has_valuables = room.get("has_valuables", False)
    occupancy = room.get("occupancy", 0)
    
    systems = {
        "video": False,
        "skud": False,
        "security": False,
        "fire": False,
        "soue": False
    }
    
    if "касс" in purpose or "касса" in purpose:
        systems["video"] = True
        systems["skud"] = True
        systems["security"] = True
        systems["fire"] = True
        systems["soue"] = True
    elif "сервер" in purpose or "цод" in purpose:
        systems["video"] = True
        systems["skud"] = True
        systems["security"] = True
        systems["fire"] = True
        systems["soue"] = True
    elif "операцион" in purpose or "зал" in purpose:
        systems["video"] = True
        systems["fire"] = True
        systems["soue"] = True
    elif "кабинет" in purpose or "офис" in purpose:
        systems["video"] = True
        systems["fire"] = True
        systems["soue"] = True
        if is_critical:
            systems["skud"] = True
            systems["security"] = True
    elif "хранилищ" in purpose or "архив" in purpose:
        systems["video"] = True
        systems["skud"] = True
        systems["security"] = True
        systems["fire"] = True
        systems["soue"] = True
    elif "коридор" in purpose or "холл" in purpose:
        systems["video"] = True
        systems["fire"] = True
        if occupancy > 10:
            systems["soue"] = True
    else:
        systems["video"] = True
        systems["fire"] = True
        systems["soue"] = True if occupancy > 5 else False
    
    if has_valuables and not systems["security"]:
        systems["security"] = True
        systems["skud"] = True
    if is_critical and not systems["skud"]:
        systems["skud"] = True
        systems["security"] = True
    
    return systems

# ------------------------------------------------------------
# 10. ФУНКЦИИ РАСЧЁТА ОБОРУДОВАНИЯ (оптимальные)
# ------------------------------------------------------------
def calc_video(room):
    equip = {}
    if room.get("has_valuables") or "касс" in room.get("purpose", "").lower():
        equip["Купол LTV-3CND40-M2714"] = 1
    if "операцион" in room.get("purpose", "").lower():
        cnt = max(1, math.ceil(room["area"] / 20))
        equip["Купол LTV-3CNB40-F28"] = cnt
    if "коридор" in room.get("purpose", "").lower():
        equip["Купол LTV-3CNB40-F28"] = 1
    if room.get("is_critical") or "сервер" in room.get("purpose", "").lower():
        equip["Купол LTV-3CND40-M2714"] = equip.get("Купол LTV-3CND40-M2714", 0) + 1
        equip["Цилиндрическая LTV-3CNB40-F28"] = 2  # угловые камеры
    return equip

def calc_skud(room):
    equip = {}
    doors = room.get("doors", 0)
    if room.get("is_critical") or "сервер" in room.get("purpose", "").lower():
        equip["Считыватель биометрический FS6/FS8"] = 1
        equip["Считыватель ER 1402"] = 1
        equip["Контроллер NG-1000"] = 1
    elif "касс" in room.get("purpose", "").lower() or room.get("has_valuables"):
        equip["Считыватель ER 1402"] = 1
        equip["Контроллер NG-1000"] = 1
        equip["Считыватель биометрический FS6/FS8"] = 1
    elif doors > 0:
        equip["Считыватель Esmart Reader"] = doors
        equip["Контроллер MB-NET II"] = doors
    return equip

def calc_security(room):
    equip = {}
    doors = room.get("doors", 0)
    windows = room.get("windows", 0)
    area = room.get("area", 0)
    if doors + windows > 0:
        equip["Извещатель «Стекло-3»"] = doors + windows
    if area > 0:
        cnt = max(1, math.ceil(area / 30))
        equip["Извещатель «Фотон-9»"] = cnt
    if room.get("has_valuables") or "касс" in room.get("purpose", "").lower():
        equip["Извещатель С2000-СМК"] = 1
        equip["Извещатель «Фотон-9»"] = equip.get("Извещатель «Фотон-9»", 0) + 2
        equip["Извещатель «Стекло-3»"] = equip.get("Извещатель «Стекло-3»", 0) + 2
    return equip

def calc_fire(room):
    equip = {}
    area = room.get("area", 0)
    height = room.get("height", 3.0)
    suspended = room.get("has_suspended", False)
    beams = room.get("has_beams", False)
    coeff = 1.0
    if suspended:
        coeff *= 1.2
    if beams:
        coeff *= 1.3
    if height > 4.0:
        coeff *= 1.1
    cnt = max(1, math.ceil(area / 20 * coeff))
    equip["Дымовой ИП 212-141"] = cnt
    equip["ППКУП «Сириус»"] = 1
    equip["С2000-КДЛ"] = 1
    return equip

def calc_soue(room):
    equip = {}
    area = room.get("area", 0)
    occupancy = room.get("occupancy", 0)
    floor = room.get("floor", 1)
    cnt = max(1, math.ceil(area / 30))
    if occupancy > 10:
        equip["Оповещатель речевой «Рупор-Р»"] = cnt
    else:
        equip["Оповещатель «Рупор»"] = cnt
    equip["Световой оповещатель «Выход»"] = max(1, floor)
    return equip

# ------------------------------------------------------------
# 11. АГРЕГАЦИЯ И SVG
# ------------------------------------------------------------
def aggregate_equipment(rooms):
    total_equip = {"video": {}, "skud": {}, "security": {}, "fire": {}, "soue": {}}
    room_details = []
    for room in rooms:
        sys = get_systems_for_room(room)
        video = calc_video(room) if sys["video"] else {}
        skud = calc_skud(room) if sys["skud"] else {}
        security = calc_security(room) if sys["security"] else {}
        fire = calc_fire(room) if sys["fire"] else {}
        soue = calc_soue(room) if sys["soue"] else {}
        
        for k, v in video.items():
            total_equip["video"][k] = total_equip["video"].get(k, 0) + v
        for k, v in skud.items():
            total_equip["skud"][k] = total_equip["skud"].get(k, 0) + v
        for k, v in security.items():
            total_equip["security"][k] = total_equip["security"].get(k, 0) + v
        for k, v in fire.items():
            total_equip["fire"][k] = total_equip["fire"].get(k, 0) + v
        for k, v in soue.items():
            total_equip["soue"][k] = total_equip["soue"].get(k, 0) + v
        
        room_details.append({
            "name": room["name"],
            "systems": sys,
            "video": video,
            "skud": skud,
            "security": security,
            "fire": fire,
            "soue": soue,
            "room": room
        })
    return total_equip, room_details

def generate_svg(rooms, details):
    if not rooms:
        return "<svg><text>Нет помещений</text></svg>"
    scale = 20
    margin = 30
    x_offset = margin
    y_offset = margin
    colors = {
        "video": "#3498db",
        "skud": "#2ecc71",
        "security": "#e67e22",
        "fire": "#e74c3c",
        "soue": "#9b59b6"
    }
    symbols = {
        "video": '<circle cx="0" cy="0" r="6" fill="{color}"/><circle cx="0" cy="0" r="8" fill="none" stroke="{color}" stroke-width="1"/>',
        "skud": '<rect x="-6" y="-6" width="12" height="12" fill="{color}" rx="2"/>',
        "security": '<polygon points="0,-8 7,6 -7,6" fill="{color}"/>',
        "fire": '<circle cx="0" cy="0" r="7" fill="{color}"/><line x1="-5" y1="0" x2="5" y2="0" stroke="white" stroke-width="2"/>',
        "soue": '<rect x="-6" y="-4" width="12" height="8" fill="{color}" rx="2"/><rect x="-3" y="-8" width="6" height="4" fill="{color}" rx="1"/>'
    }
    
    svg_parts = []
    svg_w = max(500, len(rooms) * 180 + margin * 2)
    svg_h = 400 + len(rooms) * 20
    svg_parts.append(f'<svg width="{svg_w}" height="{svg_h}" xmlns="http://www.w3.org/2000/svg">')
    svg_parts.append('<rect width="100%" height="100%" fill="#f8f9fa"/>')
    svg_parts.append('<style>text { font-family: Inter, Arial, sans-serif; font-size: 11px; fill: #333; }</style>')
    
    for idx, (room, det) in enumerate(zip(rooms, details)):
        w = room["length"] * scale
        h = room["width"] * scale
        x = x_offset
        y = y_offset + (idx % 2) * (h + 20)
        if idx % 2 == 0:
            x_offset += w + 30
        else:
            x_offset = margin
        
        svg_parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#ffffff" stroke="#2c3e50" stroke-width="2" rx="2"/>')
        svg_parts.append(f'<text x="{x+8}" y="{y+18}" font-weight="bold">{room["name"]}</text>')
        svg_parts.append(f'<text x="{x+8}" y="{y+34}">{room["length"]:.1f}×{room["width"]:.1f} м</text>')
        svg_parts.append(f'<text x="{x+8}" y="{y+50}">эт.{room["floor"]}</text>')
        
        if room.get("doors", 0) > 0:
            for d in range(min(room["doors"], 3)):
                dx = x + 10 + d * 20
                dy = y + h - 12
                svg_parts.append(f'<line x1="{dx}" y1="{dy}" x2="{dx+15}" y2="{dy}" stroke="#f39c12" stroke-width="3"/>')
                svg_parts.append(f'<path d="M{dx+15},{dy} A12,12 0 0,0 {dx+3},{dy-10}" fill="none" stroke="#f39c12" stroke-width="1.5"/>')
        
        if room.get("windows", 0) > 0:
            for wnd in range(min(room["windows"], 3)):
                wx = x + w - 30 - wnd * 25
                wy = y + 12
                svg_parts.append(f'<rect x="{wx}" y="{wy}" width="20" height="10" fill="#a8d8ea" stroke="#2c3e50" stroke-width="1.5" rx="1"/>')
                svg_parts.append(f'<line x1="{wx+10}" y1="{wy}" x2="{wx+10}" y2="{wy+10}" stroke="#2c3e50" stroke-width="1"/>')
        
        icon_x = x + 8
        icon_y = y + 65
        for sys in ["video", "skud", "security", "fire", "soue"]:
            equip_list = det.get(sys, {})
            if equip_list and det["systems"].get(sys, False):
                color = colors.get(sys, "#95a5a6")
                for eq_name, cnt in equip_list.items():
                    symbol = symbols.get(sys, '<circle cx="0" cy="0" r="5" fill="{color}"/>')
                    svg_parts.append(f'<g transform="translate({icon_x},{icon_y})">{symbol.format(color=color)}</g>')
                    short_name = eq_name[:12] + ("..." if len(eq_name) > 12 else "")
                    svg_parts.append(f'<text x="{icon_x+12}" y="{icon_y+3}" font-size="9">{short_name} ({cnt})</text>')
                    icon_y += 16
                    if icon_y > y + h - 20:
                        icon_y = y + 65
                        icon_x += 100
    
    legend_x = margin
    legend_y = svg_h - 60
    svg_parts.append(f'<rect x="{legend_x}" y="{legend_y}" width="380" height="50" fill="#ffffff" stroke="#d0d7de" stroke-width="1" rx="4"/>')
    svg_parts.append(f'<text x="{legend_x+10}" y="{legend_y+18}" font-weight="bold" font-size="12">Условные обозначения:</text>')
    legend_items = [
        ("video", "Видео"),
        ("skud", "СКУД"),
        ("security", "Охрана"),
        ("fire", "Пожар"),
        ("soue", "СОУЭ")
    ]
    for i, (sys, name) in enumerate(legend_items):
        lx = legend_x + 10 + i * 70
        ly = legend_y + 32
        color = colors.get(sys, "#95a5a6")
        svg_parts.append(f'<g transform="translate({lx},{ly})">{symbols.get(sys, "").format(color=color)}</g>')
        svg_parts.append(f'<text x="{lx+14}" y="{ly+3}" font-size="9">{name}</text>')
    
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)

# ------------------------------------------------------------
# 12. ГЕНЕРАЦИЯ ДОКУМЕНТОВ
# ------------------------------------------------------------
def generate_document(scenario, rooms, total_equip, room_details, svg_code):
    rooms_desc = ", ".join([f"{r['name']} ({r['length']}×{r['width']} м, эт.{r['floor']})" for r in rooms])
    total_area = sum(r["area"] for r in rooms)
    
    if scenario == "info":
        rooms_details_for_prompt = ""
        for room in rooms:
            rooms_details_for_prompt += f"""
- Название: {room['name']}
  Назначение: {room['purpose']}
  Размеры: {room['length']}×{room['width']} м, высота {room['height']} м
  Этаж: {room['floor']}
  Двери: {room['doors']}, Окна: {room['windows']}
  Количество людей: {room['occupancy']}
  Наличие ценностей: {'Да' if room['has_valuables'] else 'Нет'}
  Критичность: {'Да' if room['is_critical'] else 'Нет'}
  Подвесной потолок: {'Да' if room['has_suspended'] else 'Нет'}
  Балки > 400 мм: {'Да' if room['has_beams'] else 'Нет'}
  Категория пожарной опасности: {room['fire_category']}
"""
        
        prompt = f"""
Ты — эксперт по системам физической безопасности и противопожарной защиты для объектов ПАО Сбербанк.

Нормативная база (приоритет):
1. Внутренний «Сборник стандартов по комплексной безопасности № 4461» (ПАО Сбербанк) — главный документ.
2. ФЗ-123, ФЗ-384, ФЗ-69, ФЗ-152, ФЗ-187.
3. Р 102-2024 (Росгвардия), СП 484.1311500.2020 (с Изм.1), СП 3.13130.2026, СП 76.
4. ГОСТ Р 57580.1, 57580.2, 57580.4, Положения ЦБ РФ 851-П, 850-П, 382-П.
5. ГОСТ Р 51558-2014, ГОСТ Р 51241-2008, ГОСТ 31565-2012, ГОСТ Р 70444-2022, ГОСТ 21.110, ГОСТ Р 21.1101.
6. ПУЭ, СП 60, СП 134.
7. Документация производителей (Болид, ТвинПро, ЦРТ, LTV).

Для КАЖДОГО помещения выполни классификацию по зонам:

**Зона 0 (минимальная ценность)**: санузлы, душевые, подсобные помещения, кладовые, технические комнаты.
**Зона 1 (клиентская / общедоступная)**: операционные залы, вестибюли, коридоры, холлы, столовые.
**Зона 2 (офисная / ограниченного доступа)**: кабинеты, ИТ-отделы, переговорные.
**Зона 3A (ЦОД / серверная)**: серверные, коммутационные.
**Зона 3B (хранилище ценностей)**: сейфовые комнаты, депозитарии.
**Зона 3C (кассовый узел)**: операционные кассы, кассовые комнаты.
**Зона 3D (служба безопасности)**: помещения охраны, пультовые.

Помещения:
{rooms_details_for_prompt}

Для каждого помещения:
1. Определи категорию (зону) по функциональному назначению.
2. Сформируй рекомендуемый состав ИТСО и пожарной безопасности строго в соответствии с требованиями для этой зоны.
3. В обосновании укажи конкретные пункты нормативных документов.

Формат ответа для КАЖДОГО помещения:

**Помещение:** [название]
**Категория (Зона):** ...
**Рекомендуемый состав ИТСО и ПБ:** ...
**Обоснование:** ... (с указанием пунктов документов)

---
"""
        return call_gigachat(prompt, GIGACHAT_KEY)
    
    elif scenario == "estimate":
        prompt = f"""
Составь смету на оборудование для ВСП банка.
Оборудование (агрегированное):
{json.dumps(total_equip, ensure_ascii=False, indent=2)}

Формат: таблица с колонками:
№ п/п, Наименование, Тип, Кол-во, Цена за ед. (руб.), Сумма (руб.), Примечание.
Цены — примерные, справочные.
Итого по разделам и общая сумма.
"""
        return call_gigachat(prompt, GIGACHAT_KEY)
    
    elif scenario == "rd":
        prompt = f"""
Сформируй рабочую документацию (РД) на системы безопасности для ВСП банка.

Помещения: {rooms_desc}
Общая площадь: {total_area} м²
Оборудование: {json.dumps(total_equip, ensure_ascii=False, indent=2)}

Включи разделы:
1. Пояснительная записка: описание решений, обоснование со ссылками на нормативы.
2. Спецификация оборудования по ГОСТ 21.110-2013 (таблица).
3. Кабельный журнал (упрощённый): откуда, куда, марка, длина.
4. Задания на смежные системы (СКС, электроснабжение, вентиляция).
"""
        return call_gigachat(prompt, GIGACHAT_KEY)
    
    elif scenario == "application":
        prompt = f"""
Сформируй заявку на выполнение работ по установке системы безопасности.
Включи всё, что в РД, и добавь:
- Статус: «Заявка сформирована и направлена исполнителям».
- Исполнитель: назначен автоматически.
- Статус выполнения: принята в работу.

Помещения: {rooms_desc}
Оборудование: {json.dumps(total_equip, ensure_ascii=False, indent=2)}
"""
        return call_gigachat(prompt, GIGACHAT_KEY)
    
    return "Неизвестный сценарий"

# ------------------------------------------------------------
# 13. ОБРАБОТКА КНОПОК
# ------------------------------------------------------------
if not st.session_state.rooms:
    st.warning("⚠️ Добавьте хотя бы одно помещение для расчёта.")
else:
    scenario = None
    if 'btn_info' in locals() and btn_info:
        scenario = "info"
    elif 'btn_estimate' in locals() and btn_estimate:
        scenario = "estimate"
    elif 'btn_rd' in locals() and btn_rd:
        scenario = "rd"
    elif 'btn_application' in locals() and btn_application:
        scenario = "application"
    
    if scenario:
        with st.spinner(f"🔄 Генерация {scenario}..."):
            total_equip, room_details = aggregate_equipment(st.session_state.rooms)
            svg_code = generate_svg(st.session_state.rooms, room_details) if scenario in ["rd", "application"] else None
            document_text = generate_document(scenario, st.session_state.rooms, total_equip, room_details, svg_code)
            
            st.session_state.calc_result = {
                "scenario": scenario,
                "document": document_text,
                "svg": svg_code,
                "total_equip": total_equip
            }
            st.success(f"✅ Документ сгенерирован!")
            st.rerun()

# ------------------------------------------------------------
# 14. ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ
# ------------------------------------------------------------
if st.session_state.calc_result:
    res = st.session_state.calc_result
    st.markdown("---")
    st.subheader(f"📄 Результат: {res['scenario']}")
    
    st.markdown(res["document"])
    
    if res.get("svg"):
        st.markdown("---")
        st.subheader("🖼️ Схема расстановки оборудования")
        st.components.v1.html(res["svg"], height=500)
        b64 = base64.b64encode(res["svg"].encode()).decode()
        st.markdown(f'<a href="data:image/svg+xml;base64,{b64}" download="scheme.svg">📥 Скачать SVG</a>', unsafe_allow_html=True)

# ------------------------------------------------------------
# 15. ПРИМЕЧАНИЕ
# ------------------------------------------------------------
st.caption("""
SecurLLM V3 — ML-распознавание чертежей через GigaChat Vision.
- Загрузите чертёж (PNG, JPG) для автоматического заполнения.
- Данные можно корректировать вручную.
- Выберите сценарий: Справка, Смета, Рабочая документация, Заявка.
""")

# --- ПРОВЕРКА ДОСТУПНЫХ МОДЕЛЕЙ (для отладки) ---
with st.expander("🔧 Диагностика: доступные модели GigaChat"):
    if st.button("Получить список моделей"):
        with st.spinner("Загрузка..."):
            models_data = get_available_models(GIGACHAT_KEY)
            if isinstance(models_data, dict) and "data" in models_data:
                st.success(f"✅ Доступно {len(models_data['data'])} моделей")
                st.json(models_data)
            else:
                st.error(f"Ошибка: {models_data}")

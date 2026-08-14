import streamlit as st
import pandas as pd
import requests
import base64
import uuid
import math
import json
from datetime import datetime

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
# 3. РЕАЛЬНЫЙ ВЫЗОВ GIGACHAT API
# ------------------------------------------------------------
def call_gigachat(prompt, api_key, model="GigaChat-3-Ultra", max_tokens=3000, temperature=0.7):
    if not api_key:
        return "Ошибка: не указан API-ключ GigaChat."

    auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    auth_headers = {
        "Authorization": f"Basic {api_key}",
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    auth_data = {"scope": "GIGACHAT_API_PERS"}
    try:
        auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data, timeout=10)
        auth_response.raise_for_status()
        access_token = auth_response.json().get("access_token")
        if not access_token:
            return "Ошибка получения токена"
    except Exception as e:
        return f"Ошибка авторизации GigaChat: {str(e)}"

    chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    chat_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    chat_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": """Ты — эксперт по системам физической безопасности и противопожарной защиты для объектов ПАО Сбербанк.
Приоритетная нормативная база (от высшего к низшему):
1. Сборник стандартов по комплексной безопасности № 4461 (ПАО Сбербанк) — главный документ.
2. ФЗ-123, ФЗ-384, ФЗ-69.
3. Р 102-2024 (Росгвардия), СП 484.1311500.2020 (с Изм.1), СП 3.13130.2026.
4. ГОСТ Р 51558-2014, ГОСТ Р 51241-2008, ГОСТ 31565-2012, ГОСТ Р 70444-2022.
5. ПУЭ, СП 76, СП 60, СП 134.

При генерации решений ссылайся на конкретные пункты документов.
Отвечай строго по делу, используй профессиональную терминологию."""},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    try:
        response = requests.post(chat_url, headers=chat_headers, json=chat_payload, timeout=90)
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
# 4. СОСТОЯНИЕ СЕССИИ
# ------------------------------------------------------------
if "rooms" not in st.session_state:
    st.session_state.rooms = []
if "calc_result" not in st.session_state:
    st.session_state.calc_result = None
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

# ------------------------------------------------------------
# 5. ЭКСПЛИКАЦИЯ ПОМЕЩЕНИЙ (расширенная)
# ------------------------------------------------------------
st.subheader("📐 Экспликация помещений")

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
                index=2  # В — наиболее частая для офисов
            )
            has_suspended = st.checkbox("Подвесной потолок")
            has_beams = st.checkbox("Балки > 400 мм")
            purpose = st.text_input("Назначение (для классификации)", placeholder="кассовый узел")

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
                "purpose": purpose.strip() or "помещение"
            })
            st.success(f"✅ Добавлено: {room_name}")
            st.rerun()

# Отображение списка комнат
if st.session_state.rooms:
    df_rooms = pd.DataFrame(st.session_state.rooms)
    # Выбираем основные колонки для отображения
    display_cols = ["name", "length", "width", "height", "area", "floor", "doors", "windows", "occupancy"]
    st.dataframe(df_rooms[display_cols], use_container_width=True, hide_index=True)

    col_clear, col_fill = st.columns(2)
    with col_clear:
        if st.button("🗑️ Очистить список"):
            st.session_state.rooms = []
            st.rerun()
    with col_fill:
        if st.button("📥 Заполнить примером (ВСП)"):
            st.session_state.rooms = [
                {"name": "Кассовый зал", "length": 8, "width": 6, "height": 3.2, "area": 48, "floor": 1,
                 "doors": 2, "windows": 0, "occupancy": 10, "has_valuables": True, "is_critical": False,
                 "fire_category": "В", "has_suspended": False, "has_beams": False, "purpose": "кассовый узел"},
                {"name": "Операционный зал", "length": 12, "width": 8, "height": 3.2, "area": 96, "floor": 1,
                 "doors": 1, "windows": 2, "occupancy": 25, "has_valuables": False, "is_critical": False,
                 "fire_category": "В", "has_suspended": True, "has_beams": False, "purpose": "операционный зал"},
                {"name": "Хранилище", "length": 4, "width": 4, "height": 3.0, "area": 16, "floor": 1,
                 "doors": 1, "windows": 0, "occupancy": 0, "has_valuables": True, "is_critical": True,
                 "fire_category": "В", "has_suspended": False, "has_beams": False, "purpose": "хранилище"},
                {"name": "Серверная", "length": 3, "width": 3, "height": 3.0, "area": 9, "floor": 1,
                 "doors": 1, "windows": 0, "occupancy": 2, "has_valuables": False, "is_critical": True,
                 "fire_category": "В", "has_suspended": False, "has_beams": False, "purpose": "серверная"},
            ]
            st.rerun()
else:
    st.info("Пока нет ни одного помещения. Добавьте комнаты для расчёта.")

# ------------------------------------------------------------
# 6. ВЫБОР ЗОН ДЛЯ СИСТЕМ
# ------------------------------------------------------------
st.subheader("🎯 Выбор зон для систем безопасности")

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
    vent_dist = st.number_input("Расстояние до вентиляции (м)", min_value=0.5, value=1.0, step=0.1)

# СОУЭ
with st.expander("📢 СОУЭ", expanded=False):
    soue_opts = ["Звуковое оповещение", "Речевое оповещение"]
    selected_soue = st.multiselect(
        "Тип оповещения",
        soue_opts,
        default=st.session_state.soue_zones
    )
    st.session_state.soue_zones = selected_soue
    light_exit = st.checkbox("Световые оповещатели «Выход»", value=True)

# ------------------------------------------------------------
# 7. ВЫБОР СЦЕНАРИЯ (кнопки)
# ------------------------------------------------------------
st.markdown("---")
st.subheader("📄 Выберите сценарий генерации")

col_tz, col_smeta, col_rd, col_zayavka = st.columns(4)
with col_tz:
    btn_tz = st.button("📋 ТЗ", use_container_width=True)
with col_smeta:
    btn_smeta = st.button("💰 Смета", use_container_width=True)
with col_rd:
    btn_rd = st.button("📐 Рабочая документация", use_container_width=True)
with col_zayavka:
    btn_zayavka = st.button("📨 Заявка", use_container_width=True)

# ------------------------------------------------------------
# 8. ФУНКЦИИ РАСЧЁТА (обновлённые)
# ------------------------------------------------------------
def calc_video(room, video_zones):
    equip = {}
    area = room["area"]
    
    if "Входная группа" in video_zones:
        equip["Купол LTV-3CND40-M2714"] = equip.get("Купол LTV-3CND40-M2714", 0) + 1
        if room["windows"] > 0:
            equip["Уличная LTV-3RN6481-R"] = equip.get("Уличная LTV-3RN6481-R", 0) + 1
    if "Кассовый узел (каждое место)" in video_zones:
        equip["Купол LTV-3CND40-M2714"] = equip.get("Купол LTV-3CND40-M2714", 0) + 1
    if "Операционный зал" in video_zones:
        cnt = max(1, math.ceil(area / 20))
        equip["Купол LTV-3CNB40-F28"] = equip.get("Купол LTV-3CNB40-F28", 0) + cnt
    if "Хранилище" in video_zones:
        equip["Купол LTV-3CND40-M2714"] = equip.get("Купол LTV-3CND40-M2714", 0) + 1
    if "Коридоры" in video_zones:
        equip["Купол LTV-3CNB40-F28"] = equip.get("Купол LTV-3CNB40-F28", 0) + 1
    if "Кабинеты" in video_zones:
        equip["Купол LTV-3CND40-M2714"] = equip.get("Купол LTV-3CND40-M2714", 0) + 1
    if "Периметр" in video_zones:
        equip["Уличная LTV-3RN6481-R"] = equip.get("Уличная LTV-3RN6481-R", 0) + 1
    if "Банкоматы" in video_zones:
        equip["Купол LTV-3CND40-M2714"] = equip.get("Купол LTV-3CND40-M2714", 0) + 1
    return {k: v for k, v in equip.items() if v > 0}

def calc_skud(room, skud_zones, ident_type, two_factor):
    equip = {}
    doors = room["doors"]
    is_critical = room["is_critical"]
    
    if "Главный вход" in skud_zones:
        equip["Считыватель ER 1402"] = equip.get("Считыватель ER 1402", 0) + 1
        equip["Контроллер NG-1000"] = equip.get("Контроллер NG-1000", 0) + 1
    if "Внутренние двери" in skud_zones:
        equip["Считыватель Esmart Reader"] = equip.get("Считыватель Esmart Reader", 0) + doors
        equip["Контроллер MB-NET II"] = equip.get("Контроллер MB-NET II", 0) + doors
    if "Кассовый узел/хранилище" in skud_zones:
        equip["Считыватель ER 1402"] = equip.get("Считыватель ER 1402", 0) + 1
        equip["Контроллер NG-1000"] = equip.get("Контроллер NG-1000", 0) + 1
        if two_factor or is_critical:
            equip["Считыватель биометрический FS6/FS8"] = equip.get("Считыватель биометрический FS6/FS8", 0) + 1
    if "Серверная" in skud_zones or (is_critical and "Серверная" not in skud_zones):
        # Если серверная есть в списке или помещение критичное
        if "Серверная" in skud_zones:
            equip["Считыватель ER 1402"] = equip.get("Считыватель ER 1402", 0) + 1
            equip["Контроллер NG-1000"] = equip.get("Контроллер NG-1000", 0) + 1
            if two_factor:
                equip["Считыватель биометрический FS6/FS8"] = equip.get("Считыватель биометрический FS6/FS8", 0) + 1
    if "Кабинеты руководства" in skud_zones:
        equip["Считыватель Esmart Reader"] = equip.get("Считыватель Esmart Reader", 0) + 1
        equip["Контроллер MB-NET II"] = equip.get("Контроллер MB-NET II", 0) + 1
    return {k: v for k, v in equip.items() if v > 0}

def calc_ohr(room, ohr_zones):
    equip = {}
    area = room["area"]
    doors = room["doors"]
    windows = room["windows"]
    has_valuables = room["has_valuables"]
    
    if "Периметр (двери/окна)" in ohr_zones:
        cnt = doors + windows
        equip["Извещатель «Стекло-3»"] = equip.get("Извещатель «Стекло-3»", 0) + max(cnt, 1)
    if "Объём (движение)" in ohr_zones:
        cnt = max(1, math.ceil(area / 30))
        equip["Извещатель «Фотон-9»"] = equip.get("Извещатель «Фотон-9»", 0) + cnt
    if "Предметный (сейфы)" in ohr_zones:
        equip["Извещатель С2000-СМК"] = equip.get("Извещатель С2000-СМК", 0) + 1
    if "Усиленная охрана кассы/хранилища" in ohr_zones or has_valuables:
        equip["Извещатель «Фотон-9»"] = equip.get("Извещатель «Фотон-9»", 0) + 2
        equip["Извещатель «Стекло-3»"] = equip.get("Извещатель «Стекло-3»", 0) + 2
    return {k: v for k, v in equip.items() if v > 0}

def calc_fire(room, fire_types, vent_dist):
    equip = {}
    area = room["area"]
    height = room["height"]
    has_suspended = room["has_suspended"]
    has_beams = room["has_beams"]
    
    # Коэффициенты по СП 484.1311500.2020 (с Изм.1)
    coeff = 1.0
    if has_suspended:
        coeff *= 1.2
    if has_beams:
        coeff *= 1.3
    if height > 4.0:
        coeff *= 1.1
    
    # Радиус зоны контроля по СП 484 (Изм.1): дымовые 6.4 м, тепловые 3.5 м
    # Ориентировочно: 1 извещатель на 20 кв.м с коэффициентами
    base_cnt = max(1, math.ceil(area / 20 * coeff))
    
    if "Дымовые извещатели" in fire_types:
        equip["Дымовой ИП 212-141"] = equip.get("Дымовой ИП 212-141", 0) + base_cnt
    if "Тепловые извещатели" in fire_types:
        equip["Тепловой ИП 101-3А"] = equip.get("Тепловой ИП 101-3А", 0) + base_cnt
    if "Комбинированные извещатели" in fire_types:
        equip["Комбинированный ИП 212/101"] = equip.get("Комбинированный ИП 212/101", 0) + base_cnt
    
    # Приборы управления (на помещение или на группу — упрощённо)
    equip["ППКУП «Сириус»"] = equip.get("ППКУП «Сириус»", 0) + 1
    equip["С2000-КДЛ"] = equip.get("С2000-КДЛ", 0) + 1
    
    return {k: v for k, v in equip.items() if v > 0}

def calc_soue(room, soue_types, light_exit):
    equip = {}
    area = room["area"]
    occupancy = room["occupancy"]
    
    # По СП 3.13130.2026: количество оповещателей по площади
    cnt_area = max(1, math.ceil(area / 30))
    # По количеству людей: если > 50, то речевое (но это в промпте GigaChat)
    
    if "Звуковое оповещение" in soue_types:
        equip["Оповещатель «Рупор»"] = equip.get("Оповещатель «Рупор»", 0) + cnt_area
    if "Речевое оповещение" in soue_types:
        equip["Оповещатель речевой «Рупор-Р»"] = equip.get("Оповещатель речевой «Рупор-Р»", 0) + cnt_area
    if light_exit:
        equip["Световой оповещатель «Выход»"] = equip.get("Световой оповещатель «Выход»", 0) + max(1, room["floor"])
    return {k: v for k, v in equip.items() if v > 0}

# ------------------------------------------------------------
# 9. АГРЕГАЦИЯ И ГЕНЕРАЦИЯ SVG (улучшенная)
# ------------------------------------------------------------
def aggregate_equipment(rooms, zones):
    total_equip = {"video": {}, "skud": {}, "ohr": {}, "fire": {}, "soue": {}}
    room_details = []
    
    for room in rooms:
        v = calc_video(room, zones["video"])
        for k, cnt in v.items():
            total_equip["video"][k] = total_equip["video"].get(k, 0) + cnt
        s = calc_skud(room, zones["skud"], zones["skud_ident"], zones["skud_2fa"])
        for k, cnt in s.items():
            total_equip["skud"][k] = total_equip["skud"].get(k, 0) + cnt
        o = calc_ohr(room, zones["ohr"])
        for k, cnt in o.items():
            total_equip["ohr"][k] = total_equip["ohr"].get(k, 0) + cnt
        f = calc_fire(room, zones["fire"], zones["fire_vent_dist"])
        for k, cnt in f.items():
            total_equip["fire"][k] = total_equip["fire"].get(k, 0) + cnt
        se = calc_soue(room, zones["soue"], zones["soue_light"])
        for k, cnt in se.items():
            total_equip["soue"][k] = total_equip["soue"].get(k, 0) + cnt
        room_details.append({
            "name": room["name"],
            "video": v,
            "skud": s,
            "ohr": o,
            "fire": f,
            "soue": se
        })
    return total_equip, room_details

def generate_svg(rooms, details):
    """Улучшенная SVG-генерация с условными обозначениями"""
    if not rooms:
        return "<svg><text>Нет помещений для отображения</text></svg>"
    
    scale = 20
    margin = 30
    x_offset = margin
    y_offset = margin
    
    # Цвета систем
    colors = {
        "video": "#3498db",
        "skud": "#2ecc71",
        "ohr": "#e67e22",
        "fire": "#e74c3c",
        "soue": "#9b59b6"
    }
    
    # Символы для оборудования (стандартизированные)
    symbols = {
        "video": '<circle cx="0" cy="0" r="6" fill="{color}"/><circle cx="0" cy="0" r="8" fill="none" stroke="{color}" stroke-width="1"/>',
        "skud": '<rect x="-6" y="-6" width="12" height="12" fill="{color}" rx="2"/>',
        "ohr": '<polygon points="0,-8 7,6 -7,6" fill="{color}"/>',
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
        
        # Комната
        svg_parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#ffffff" stroke="#2c3e50" stroke-width="2" rx="2"/>')
        svg_parts.append(f'<text x="{x+8}" y="{y+18}" font-weight="bold">{room["name"]}</text>')
        svg_parts.append(f'<text x="{x+8}" y="{y+34}">{room["length"]:.1f}×{room["width"]:.1f} м</text>')
        svg_parts.append(f'<text x="{x+8}" y="{y+50}">эт.{room["floor"]}</text>')
        
        # Двери (по ГОСТ 21.501-93)
        if room["doors"] > 0:
            for d in range(min(room["doors"], 3)):
                dx = x + 10 + d * 20
                dy = y + h - 12
                svg_parts.append(f'<line x1="{dx}" y1="{dy}" x2="{dx+15}" y2="{dy}" stroke="#f39c12" stroke-width="3"/>')
                svg_parts.append(f'<path d="M{dx+15},{dy} A12,12 0 0,0 {dx+3},{dy-10}" fill="none" stroke="#f39c12" stroke-width="1.5"/>')
        
        # Окна
        if room["windows"] > 0:
            for wnd in range(min(room["windows"], 3)):
                wx = x + w - 30 - wnd * 25
                wy = y + 12
                svg_parts.append(f'<rect x="{wx}" y="{wy}" width="20" height="10" fill="#a8d8ea" stroke="#2c3e50" stroke-width="1.5" rx="1"/>')
                svg_parts.append(f'<line x1="{wx+10}" y1="{wy}" x2="{wx+10}" y2="{wy+10}" stroke="#2c3e50" stroke-width="1"/>')
        
        # Оборудование
        icon_x = x + 8
        icon_y = y + 65
        for sys, equip_list in det.items():
            if equip_list:
                color = colors.get(sys, "#95a5a6")
                for eq_name, cnt in equip_list.items():
                    # Символ
                    symbol = symbols.get(sys, '<circle cx="0" cy="0" r="5" fill="{color}"/>')
                    symbol_rendered = symbol.format(color=color)
                    svg_parts.append(f'<g transform="translate({icon_x},{icon_y})">{symbol_rendered}</g>')
                    # Подпись
                    short_name = eq_name[:12] + ("..." if len(eq_name) > 12 else "")
                    svg_parts.append(f'<text x="{icon_x+12}" y="{icon_y+3}" font-size="9">{short_name} ({cnt})</text>')
                    icon_y += 16
                    if icon_y > y + h - 20:
                        icon_y = y + 65
                        icon_x += 100
    
    # Легенда
    legend_x = margin
    legend_y = svg_h - 60
    svg_parts.append(f'<rect x="{legend_x}" y="{legend_y}" width="380" height="50" fill="#ffffff" stroke="#d0d7de" stroke-width="1" rx="4"/>')
    svg_parts.append(f'<text x="{legend_x+10}" y="{legend_y+18}" font-weight="bold" font-size="12">Условные обозначения:</text>')
    legend_items = [
        ("video", "Видео"),
        ("skud", "СКУД"),
        ("ohr", "Охрана"),
        ("fire", "Пожар"),
        ("soue", "СОУЭ")
    ]
    for i, (sys, name) in enumerate(legend_items):
        lx = legend_x + 10 + i * 70
        ly = legend_y + 32
        color = colors.get(sys, "#95a5a6")
        symbol = symbols.get(sys, '<circle cx="0" cy="0" r="5" fill="{color}"/>')
        symbol_rendered = symbol.format(color=color)
        svg_parts.append(f'<g transform="translate({lx},{ly})">{symbol_rendered}</g>')
        svg_parts.append(f'<text x="{lx+14}" y="{ly+3}" font-size="9">{name}</text>')
    
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)

# ------------------------------------------------------------
# 10. ГЕНЕРАЦИЯ ДОКУМЕНТОВ (запуск по кнопкам)
# ------------------------------------------------------------
def generate_document(scenario, rooms, zones, total_equip, room_details, svg_code):
    """Генерация документа через GigaChat по выбранному сценарию"""
    rooms_desc = ", ".join([f"{r['name']} ({r['length']}×{r['width']} м, эт.{r['floor']})" for r in rooms])
    total_area = sum(r["area"] for r in rooms)
    
    # Базовый системный промпт уже в call_gigachat
    
    if scenario == "tz":
        prompt = f"""
Составь детальное техническое задание (ТЗ) на проектирование системы безопасности для ВСП банка.
В ТЗ включи:
1. Общие положения (объект, нормативная база с приоритетами).
2. Требования к интеграции со смежными системами (СКС, вентиляция, кондиционирование).
3. Требования по каждой системе: САПС, СОУЭ, СКУД, СОТС, СОТ.
   - Для каждой системы укажи: общие положения, оборудование (целевой перечень), защиту помещений, управление и интеграцию, электропитание, кабельные линии.
4. Состав рабочей документации (по ГОСТ Р 21.1101-2013).
5. Общие требования к монтажу и пусконаладке.

Помещения: {rooms_desc}
Общая площадь: {total_area} м²
Оборудование (агрегированное по системам): {json.dumps(total_equip, ensure_ascii=False, indent=2)}
Зоны: {zones}

Используй ссылки на конкретные пункты нормативных документов.
Приоритет: Сборник № 4461 → ФЗ-123 → Р 102-2024 → СП 484 → ГОСТ.
"""
        return call_gigachat(prompt, GIGACHAT_KEY)
    
    elif scenario == "smeta":
        prompt = f"""
Составь смету на оборудование для объекта (ВСП банка) на основе спецификации.
Смета должна содержать таблицу с колонками: № п/п, Наименование, Тип, Кол-во, Цена за ед. (руб.), Сумма (руб.), Примечание.
Итого по разделам и общая сумма.
Цены — примерные, справочные.

Помещения: {rooms_desc}
Общая площадь: {total_area} м²
Оборудование: {json.dumps(total_equip, ensure_ascii=False, indent=2)}
"""
        return call_gigachat(prompt, GIGACHAT_KEY)
    
    elif scenario == "rd":
        prompt = f"""
Сформируй рабочую документацию (РД) на систему безопасности для ВСП банка.
Включи следующие разделы:
1. Пояснительная записка (описание решений, обоснование со ссылками на нормативы).
2. Структурная схема (описание взаимосвязи оборудования).
3. Спецификация оборудования (по ГОСТ 21.110-2013) — таблица с позициями, названием, типом, кол-вом.
4. Кабельный журнал (упрощённый) — таблица: откуда, куда, марка кабеля, длина.
5. Задания на смежные системы (СКС, электроснабжение, вентиляция).

Помещения: {rooms_desc}
Общая площадь: {total_area} м²
Оборудование: {json.dumps(total_equip, ensure_ascii=False, indent=2)}
Зоны: {zones}
"""
        return call_gigachat(prompt, GIGACHAT_KEY)
    
    elif scenario == "zayavka":
        prompt = f"""
Сформируй заявку на выполнение работ по установке системы безопасности.
Включи всё, что в РД, и добавь:
- Статус: «Заявка сформирована и направлена исполнителям».
- Исполнитель: назначен автоматически.
- Статус выполнения: принята в работу.

Помещения: {rooms_desc}
Общая площадь: {total_area} м²
Оборудование: {json.dumps(total_equip, ensure_ascii=False, indent=2)}
"""
        return call_gigachat(prompt, GIGACHAT_KEY)
    
    return "Неизвестный сценарий"

# ------------------------------------------------------------
# 11. ОБРАБОТКА КНОПОК
# ------------------------------------------------------------
if not st.session_state.rooms:
    st.warning("⚠️ Добавьте хотя бы одно помещение для расчёта.")
else:
    # Проверка: выбраны ли зоны для систем
    zones_defined = (
        st.session_state.video_zones or
        st.session_state.skud_zones or
        st.session_state.ohr_zones or
        st.session_state.fire_zones or
        st.session_state.soue_zones
    )
    if not zones_defined:
        st.info("ℹ️ Выберите зоны для систем безопасности в разделах выше.")
    
    # Определяем, какая кнопка нажата
    scenario = None
    if btn_tz:
        scenario = "tz"
    elif btn_smeta:
        scenario = "smeta"
    elif btn_rd:
        scenario = "rd"
    elif btn_zayavka:
        scenario = "zayavka"
    
    if scenario and zones_defined:
        with st.spinner(f"🔄 Генерация {scenario.upper()}..."):
            # Собираем зоны
            zones = {
                "video": st.session_state.video_zones,
                "skud": st.session_state.skud_zones,
                "ohr": st.session_state.ohr_zones,
                "fire": st.session_state.fire_zones,
                "soue": st.session_state.soue_zones,
                "skud_ident": ident_type if 'ident_type' in locals() else "Карта",
                "skud_2fa": two_factor if 'two_factor' in locals() else True,
                "fire_vent_dist": vent_dist if 'vent_dist' in locals() else 1.0,
                "soue_light": light_exit if 'light_exit' in locals() else True
            }
            
            # Агрегация
            total_equip, room_details = aggregate_equipment(st.session_state.rooms, zones)
            
            # SVG (только для РД и Заявки)
            svg_code = None
            if scenario in ["rd", "zayavka"]:
                svg_code = generate_svg(st.session_state.rooms, room_details)
            
            # Генерация документа через GigaChat
            document_text = generate_document(
                scenario,
                st.session_state.rooms,
                zones,
                total_equip,
                room_details,
                svg_code
            )
            
            # Сохраняем результат
            st.session_state.calc_result = {
                "scenario": scenario,
                "document": document_text,
                "svg": svg_code,
                "rooms": st.session_state.rooms,
                "total_equip": total_equip,
                "room_details": room_details
            }
            st.success(f"✅ {scenario.upper()} сгенерирован!")
            st.rerun()

# ------------------------------------------------------------
# 12. ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ
# ------------------------------------------------------------
if st.session_state.calc_result:
    res = st.session_state.calc_result
    st.markdown("---")
    st.subheader(f"📄 Результат: {res['scenario'].upper()}")
    
    # Текст документа
    st.text_area("Документ", res["document"], height=400)
    
    # SVG (если есть)
    if res.get("svg"):
        st.subheader("🖼️ Схема расстановки оборудования")
        st.components.v1.html(res["svg"], height=600)
        # Скачивание SVG (заглушка)
        b64 = base64.b64encode(res["svg"].encode()).decode()
        href = f'<a href="data:image/svg+xml;base64,{b64}" download="scheme.svg">📥 Скачать SVG</a>'
        st.markdown(href, unsafe_allow_html=True)
    
    # Сводка по оборудованию
    st.subheader("📊 Сводка по оборудованию")
    for sys, equip in res["total_equip"].items():
        if equip:
            st.write(f"**{sys.upper()}:**")
            df = pd.DataFrame(list(equip.items()), columns=["Наименование", "Кол-во"])
            st.dataframe(df, use_container_width=True, hide_index=True)

# ------------------------------------------------------------
# 13. ПРИМЕЧАНИЕ ДЛЯ ML-ИНТЕГРАЦИИ
# ------------------------------------------------------------
st.markdown("---")
st.caption("""
**Примечание:** Прототип V3 с расширенной экспликацией и улучшенной SVG-генерацией.
- Данные вводятся вручную или могут быть заполнены автоматически после интеграции ML-распознавания чертежей.
- Экспорт в DOCX/PDF — в следующих версиях.
- Цены в смете — справочные.
""")

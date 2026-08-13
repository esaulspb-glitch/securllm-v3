import streamlit as st
import re
import json
from gigachat import GigaChat

st.set_page_config(page_title="SecurLLM — Проектирование ВСП", layout="wide")

# --- СТИЛИ (SberDesign) ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .main > div { background-color: #f8f9fa; padding-top: 6rem !important; }
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #1a1a1a !important; font-family: 'Inter', sans-serif;
    }
    .stMarkdown, .stText, label { color: #1a1a1a !important; }
    .stTextArea textarea, .stSelectbox div, .stButton button {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #d0d7de !important;
        border-radius: 8px !important;
    }
    .stButton button {
        background-color: #1A991A !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        width: 100%;
    }
    .stButton button:hover { background-color: #0f7a0f !important; }
    .stAlert, .stInfo, .stSuccess {
        background-color: #ffffff !important;
        border: 1px solid #d0d7de !important;
        color: #1a1a1a !important;
        border-radius: 8px !important;
    }
    .stAlert { border-left: 4px solid #1A991A !important; }
    .stSuccess { border-left: 4px solid #1A991A !important; }
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
    <span style="font-size: 24px; font-weight: 700; color: #1A991A;">Сбер</span>
    <span style="font-size: 18px; color: #333F48; font-weight: 300; margin-left: 4px;">| SecurLLM Проектирование ВСП</span>
</div>
""", unsafe_allow_html=True)

# --- ЗАГОЛОВОК ---
st.title("🏦 Автоматизированное проектирование систем безопасности")
st.markdown("*Загрузите экспликацию или введите список помещений — получите полный проект со сметами и ТЗ.*")

# --- ПРОВЕРКА СЕКРЕТА ---
try:
    GIGACHAT_KEY = st.secrets["GIGACHAT_KEY"]
except Exception:
    st.error("❌ Ошибка: не найден секрет GIGACHAT_KEY. Проверьте настройки приложения.")
    st.stop()

# --- ТИПОВЫЕ НАСТРОЙКИ ---
TYPE_MAPPING = {
    "касс": "Кассовый узел",
    "сейф": "Хранилище ценностей",
    "сервер": "Серверная (ЦОД)",
    "ай-ти": "Серверная (ЦОД)",
    "it": "Серверная (ЦОД)",
    "офис": "Офисное помещение",
    "кабинет": "Офисное помещение",
    "отдел": "Офисное помещение",
    "переговор": "Конференц-зал",
    "коридор": "Коридор",
    "холл": "Коридор",
    "подсоб": "Подсобка",
    "инвентар": "Подсобка",
    "архив": "Архив",
    "охрана": "Помещение охраны",
    "безопасн": "Помещение охраны",
    "мониторн": "Помещение охраны",
    "бухгалтер": "Офисное помещение",
    "юрист": "Офисное помещение",
    "директор": "Офисное помещение",
}

DEFAULT_GEOMETRY = {
    "Кассовый узел": {"length": 6.0, "width": 4.0, "height": 3.0, "doors": 2, "windows": 1},
    "Хранилище ценностей": {"length": 4.0, "width": 3.0, "height": 3.0, "doors": 1, "windows": 0},
    "Серверная (ЦОД)": {"length": 5.0, "width": 4.0, "height": 3.5, "doors": 1, "windows": 0},
    "Офисное помещение": {"length": 5.0, "width": 4.0, "height": 3.0, "doors": 1, "windows": 1},
    "Конференц-зал": {"length": 8.0, "width": 6.0, "height": 3.5, "doors": 2, "windows": 3},
    "Коридор": {"length": 10.0, "width": 2.5, "height": 3.0, "doors": 1, "windows": 0},
    "Подсобка": {"length": 2.0, "width": 2.0, "height": 3.0, "doors": 1, "windows": 0},
    "Архив": {"length": 4.0, "width": 3.0, "height": 3.0, "doors": 1, "windows": 0},
    "Помещение охраны": {"length": 4.0, "width": 3.0, "height": 3.0, "doors": 1, "windows": 1},
}

# --- ФУНКЦИЯ КЛАССИФИКАЦИИ ПОМЕЩЕНИЙ ---
def classify_rooms(explication_list):
    """Классифицирует список названий помещений по типам."""
    classified = []
    for name in explication_list:
        name_lower = name.lower()
        room_type = None
        for key, value in TYPE_MAPPING.items():
            if key in name_lower:
                room_type = value
                break
        if not room_type:
            room_type = "Офисное помещение"  # По умолчанию
        geom = DEFAULT_GEOMETRY.get(room_type, {"length": 5.0, "width": 4.0, "height": 3.0, "doors": 1, "windows": 1})
        classified.append({
            "name": name,
            "type": room_type,
            "length": geom["length"],
            "width": geom["width"],
            "height": geom["height"],
            "doors": geom["doors"],
            "windows": geom["windows"],
            "suspended_ceiling": False,
            "beams": False,
            "beam_height": 0,
            "sun_side": False,
            "cable_protection": False,
            "gypsum_walls": False,
            "through_walls": False,
        })
    return classified

# --- ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ТЕКСТА ОТ GIGACHAT ---
def generate_document(room, scenario, legal_check=False):
    """Генерирует ТЗ, смету, проект или заявку для одного помещения."""
    area = room["length"] * room["width"]
    perimeter = 2 * (room["length"] + room["width"])
    
    base_prompt = f"""
Ты — эксперт по оснащению банков системами безопасности и противопожарной защиты.

Нормативная база: Сборник № 4461, РД 78.36.003-2002, 123-ФЗ, СП 484.1311500.2020, ГОСТ Р 21.110-2013, ГОСТ Р 51558-2014.

Целевой перечень оборудования (предпочтительные производители):
- САПС/СОУЭ: АО НВП «Болид» (ППКУП «Сириус», С2000-КДЛ, С2000Р-ДИП, С2000Р-ИПР, «Рупор»).
- СКУД: ГК «ТвинПро» (NG-1000, MB-NET II), ГК «ЦРТ» (FS6/FS8), считыватели ER 1402, Esmart Reader.
- СОТ: LTV (LTV-3CND40-M2714, LTV-3CNB40-F28, LTV-3RN6481-R).
- СОТС: АО НВП «Болид» (С2000-СМК, «Фотон-9», «Стекло-3»).

Помещение: {room["name"]} (тип: {room["type"]})
Длина: {room["length"]} м, Ширина: {room["width"]} м, Высота: {room["height"]} м
Площадь: {area:.1f} м², Периметр: {perimeter:.1f} м
Двери: {room["doors"]} шт., Окна: {room["windows"]} шт.
Особенности: подвесной потолок - {'Да' if room["suspended_ceiling"] else 'Нет'}, балки - {'Да' if room["beams"] else 'Нет'}, солнечная сторона - {'Да' if room["sun_side"] else 'Нет'}.

Правила расчёта:
- Видеокамеры: 1 на 20 м² (мин. 2). Расчёт: max(2, ceil({area}/20)).
- Дымовые извещатели: 1 на 30 м² (мин. 2). Расчёт: max(2, ceil({area}/30)).
- Ручные извещатели: 1 на выход (если дверей > 0).
- Датчики движения: 1 на 20 м² (мин. 1).
- СКУД: 1 считыватель на дверь, 1 контроллер на помещение.
- Длина кабеля: периметр × 1.5.
При подвесном потолке — извещатели за потолком. При балках — в каждом отсеке. При солнечной стороне — камеры с WDR.
При выборе оборудования строго придерживайся целевого перечня.
В обосновании ссылайся на конкретные пункты нормативных документов.
"""

    if scenario == "Техническое задание":
        prompt = base_prompt + """
Сформируй **Техническое задание** на проектирование систем безопасности для помещения.

Структура:
1. Общие положения (объект, площадь, высота).
2. Нормативная база.
3. Требования к системам (САПС, СОУЭ, СКУД, СОТС, СОТ) с перечнем оборудования из целевого перечня, количеством и обоснованием.
4. Интеграция со смежными системами.
5. Состав рабочей документации.
6. Смета (примерная).
"""
    elif scenario == "Смета":
        prompt = base_prompt + """
Сформируй **Смету** на оснащение помещения.
Включи таблицу: Наименование (модель из целевого перечня), Кол-во, Цена за ед., Сумма.
Добавь итог (оборудование + монтаж 30% + накладные 15%).
Покажи расчёт количества (например, площадь / 20 = X → минимум Y).
"""
    elif scenario == "Проект":
        prompt = base_prompt + """
Сформируй **Проект**:
1. Пояснительная записка.
2. Схема расстановки (текстовое описание).
3. Спецификация по ГОСТ 21.110-2013 с моделями из целевого перечня.
4. Смета.
В конце выведи список оборудования.
"""
    else:  # Заявка
        prompt = base_prompt + """
Сформируй **Проект** и добавь: «Заявка сформирована и направлена исполнителям. Исполнитель назначен автоматически. Статус: принята в работу.»
1. Пояснительная записка...
2. Схема расстановки...
3. Спецификация...
4. Смета...
5. Заявка...
В конце выведи список оборудования.
"""
    if legal_check:
        prompt += "\nДополнительно: проверен аттестат МЧС — действителен (заглушка)."
    
    try:
        with GigaChat(credentials=GIGACHAT_KEY, model="GigaChat-3-Ultra", verify_ssl_certs=False) as client:
            response = client.chat(prompt)
            return response.choices[0].message.content
    except Exception as e:
        return f"❌ Ошибка при генерации: {e}"

# --- ИНТЕРФЕЙС ---
st.markdown("### 📋 Ввод данных")

input_method = st.radio("Способ ввода", ["Вставить список помещений вручную", "Загрузить текстовый файл"], horizontal=True)

rooms_text = ""
if input_method == "Вставить список помещений вручную":
    rooms_text = st.text_area(
        "Введите список помещений (по одному на строку):",
        height=200,
        placeholder="1. Отдел по работе с юридическими лицами\n2. Предкассовый холл\n3. Сейфовая комната..."
    )
else:
    uploaded_file = st.file_uploader("Загрузите файл с экспликацией (TXT, CSV)", type=["txt", "csv"])
    if uploaded_file:
        try:
            content = uploaded_file.read().decode("utf-8")
            rooms_text = content
        except Exception:
            st.error("Не удалось прочитать файл. Проверьте кодировку (UTF-8).")

# --- ПАРСИНГ И КЛАССИФИКАЦИЯ ---
if st.button("🔍 Распознать и классифицировать помещения"):
    if not rooms_text.strip():
        st.warning("Введите список помещений.")
    else:
        lines = [line.strip() for line in rooms_text.split("\n") if line.strip()]
        # Удаляем номера в начале строки (например, "1. " или "1) ")
        cleaned = []
        for line in lines:
            # Убираем "1. ", "1) ", "1- " и т.п.
            cleaned_line = re.sub(r"^\d+[\.\)\-]\s*", "", line)
            cleaned.append(cleaned_line)
        # Классифицируем
        rooms = classify_rooms(cleaned)
        st.session_state["rooms"] = rooms
        st.success(f"✅ Распознано {len(rooms)} помещений.")
        st.dataframe(
            [
                {
                    "№": i+1,
                    "Наименование": r["name"],
                    "Тип": r["type"],
                    "Длина (м)": r["length"],
                    "Ширина (м)": r["width"],
                    "Высота (м)": r["height"],
                    "Двери": r["doors"],
                    "Окна": r["windows"],
                }
                for i, r in enumerate(rooms)
            ],
            use_container_width=True
        )

# --- РЕДАКТИРОВАНИЕ ПАРАМЕТРОВ ---
if "rooms" in st.session_state and st.session_state["rooms"]:
    st.markdown("### ✏️ Редактирование параметров помещений")
    st.warning("Здесь вы можете изменить размеры, количество дверей/окон и отметить особенности для каждого помещения.")
    # Для каждого помещения — небольшой блок
    for i, room in enumerate(st.session_state["rooms"]):
        with st.expander(f"Помещение {i+1}: {room['name']} ({room['type']})", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_length = st.number_input(f"Длина (м) {i}", min_value=1.0, max_value=50.0, value=room["length"], step=0.5, key=f"len_{i}")
                new_doors = st.number_input(f"Двери {i}", min_value=0, max_value=10, value=room["doors"], step=1, key=f"doors_{i}")
            with col2:
                new_width = st.number_input(f"Ширина (м) {i}", min_value=1.0, max_value=50.0, value=room["width"], step=0.5, key=f"wid_{i}")
                new_windows = st.number_input(f"Окна {i}", min_value=0, max_value=10, value=room["windows"], step=1, key=f"win_{i}")
            with col3:
                new_height = st.number_input(f"Высота (м) {i}", min_value=2.0, max_value=10.0, value=room["height"], step=0.5, key=f"hei_{i}")
                suspended = st.checkbox("Подвесной потолок", value=room["suspended_ceiling"], key=f"sus_{i}")
                beams = st.checkbox("Балки", value=room["beams"], key=f"beams_{i}")
                if beams:
                    beam_h = st.number_input("Высота балок (мм)", min_value=0, max_value=1000, value=room.get("beam_height", 400), step=50, key=f"beam_h_{i}")
                else:
                    beam_h = 0
                sun_side = st.checkbox("Солнечная сторона", value=room.get("sun_side", False), key=f"sun_{i}")
                cable_prot = st.checkbox("Защита кабеля", value=room.get("cable_protection", False), key=f"cable_{i}")
                gypsum = st.checkbox("Гипсокартон", value=room.get("gypsum_walls", False), key=f"gypsum_{i}")
                through = st.checkbox("Проход через стены", value=room.get("through_walls", False), key=f"through_{i}")
            # Сохраняем изменения
            st.session_state["rooms"][i]["length"] = new_length
            st.session_state["rooms"][i]["width"] = new_width
            st.session_state["rooms"][i]["height"] = new_height
            st.session_state["rooms"][i]["doors"] = new_doors
            st.session_state["rooms"][i]["windows"] = new_windows
            st.session_state["rooms"][i]["suspended_ceiling"] = suspended
            st.session_state["rooms"][i]["beams"] = beams
            st.session_state["rooms"][i]["beam_height"] = beam_h
            st.session_state["rooms"][i]["sun_side"] = sun_side
            st.session_state["rooms"][i]["cable_protection"] = cable_prot
            st.session_state["rooms"][i]["gypsum_walls"] = gypsum
            st.session_state["rooms"][i]["through_walls"] = through

# --- ВЫБОР СЦЕНАРИЯ И ГЕНЕРАЦИЯ ---
if "rooms" in st.session_state and st.session_state["rooms"]:
    st.markdown("---")
    st.markdown("### 🚀 Генерация документов")
    
    col_scenario, col_legal = st.columns([2, 1])
    with col_scenario:
        scenario = st.radio(
            "Выберите сценарий для всех помещений:",
            ["Техническое задание", "Смета", "Проект", "Заявка"],
            index=0,
            horizontal=True
        )
    with col_legal:
        legal_check = st.checkbox("Проверить аттестат МЧС (заглушка)")
    
    if st.button("📄 Сформировать документы для всех помещений", type="primary", use_container_width=True):
        with st.spinner("Генерация документов..."):
            results = []
            total_smeta = 0.0
            for room in st.session_state["rooms"]:
                doc = generate_document(room, scenario, legal_check)
                results.append((room["name"], doc))
                # Попытка извлечь итоговую сумму из сметы (упрощённо)
                if "Смета" in scenario or "Проект" in scenario:
                    match = re.search(r"ИТОГО[:]?\s*([\d\s,]+)\s*[₽руб]", doc)
                    if match:
                        try:
                            val = float(match.group(1).replace(" ", "").replace(",", ""))
                            total_smeta += val
                        except:
                            pass
            # Вывод результатов
            for i, (name, doc) in enumerate(results):
                with st.expander(f"📄 {name}", expanded=False):
                    st.markdown(doc)
                    st.download_button(
                        f"Скачать документ для {name}",
                        data=doc,
                        file_name=f"{name}_{scenario}.txt",
                        mime="text/plain",
                        key=f"download_{i}"
                    )
            if total_smeta > 0:
                st.success(f"💰 Примерная общая стоимость по всем помещениям: {total_smeta:,.0f} ₽")
            st.success("✅ Все документы сгенерированы.")

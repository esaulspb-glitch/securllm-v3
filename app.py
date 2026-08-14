import streamlit as st
import re
from gigachat import GigaChat

st.set_page_config(page_title="SecurLLM — прототип", layout="centered")

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

# --- ПРОВЕРКА СЕКРЕТА ---
try:
    GIGACHAT_KEY = st.secrets["GIGACHAT_KEY"]
except Exception:
    st.error("❌ Ошибка: не найден секрет GIGACHAT_KEY. Проверьте настройки приложения.")
    st.stop()

# --- СПИСОК ТИПОВЫХ ПОМЕЩЕНИЙ ---
room_options = {
    "": "— Выберите типовое помещение —",
    "Кабинет генерального директора": "Кабинет руководителя, сейф для документов.",
    "Операционный зал": "Зал обслуживания клиентов, 4 кассы.",
    "Кассовый узел": "Кассовая комната, 2 кассы, сейф.",
    "Серверная (ЦОД)": "Серверная стойка, 5 серверов, охлаждение.",
    "Хранилище ценностей": "Сейфовая комната, металлические сейфы.",
    "ИТ-отдел": "Рабочие места программистов, сетевое оборудование.",
    "Туалет / подсобка": "Подсобное помещение.",
    "Архив": "Хранение документов.",
    "Конференц-зал": "Зал для совещаний, до 30 человек.",
    "Помещение охраны": "Пост охраны, мониторы.",
    "Электрощитовая": "Распределительный щит.",
    "Столовая": "Помещение для приёма пищи.",
    "Коридор": "Проходная зона."
}

# --- ИНТЕРФЕЙС ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Выберите типовое помещение**")
    selected_key = st.selectbox(
        "",
        options=list(room_options.keys()),
        format_func=lambda x: room_options[x] if x else "",
        index=0,
        label_visibility="collapsed"
    )

with col2:
    st.markdown("**Или введите своё описание**")
    manual_input = st.text_area(
        "",
        height=68,
        placeholder="Например: комната отдыха сотрудников",
        label_visibility="collapsed"
    )

# --- ГЕОМЕТРИЯ ---
st.markdown("**📐 Размеры помещения (для расчёта количества оборудования)**")
col_geom1, col_geom2, col_geom3, col_geom4, col_geom5 = st.columns(5)

with col_geom1:
    length = st.number_input("Длина (м)", min_value=1.0, max_value=50.0, value=6.0, step=0.5)
with col_geom2:
    width = st.number_input("Ширина (м)", min_value=1.0, max_value=50.0, value=4.0, step=0.5)
with col_geom3:
    height = st.number_input("Высота (м)", min_value=2.0, max_value=10.0, value=3.0, step=0.5)
with col_geom4:
    doors = st.number_input("Двери (шт.)", min_value=0, max_value=10, value=1, step=1)
with col_geom5:
    windows = st.number_input("Окна (шт.)", min_value=0, max_value=10, value=1, step=1)

area = length * width
perimeter = 2 * (length + width)
st.caption(f"📏 Площадь: {area:.1f} м² · Периметр: {perimeter:.1f} м")

# --- КРИТИЧЕСКИЕ ЗОНЫ ДЛЯ ВИДЕОНАБЛЮДЕНИЯ ---
st.markdown("**🎥 Критические зоны для видеоконтроля**")
st.caption("Выберите зоны, которые должны быть перекрыты камерами (для помещений, где требуется видеонаблюдение)")

col_zone1, col_zone2, col_zone3 = st.columns(3)

with col_zone1:
    zone_entrance = st.checkbox("🚪 Входная группа (дверь)", value=True)
    zone_cash = st.checkbox("💵 Кассовый узел (каждое рабочее место)", value=False)
    zone_atm = st.checkbox("🏧 Банкоматы", value=False)

with col_zone2:
    zone_hall = st.checkbox("🛋️ Операционный зал (общий обзор)", value=False)
    zone_storage = st.checkbox("🏛️ Хранилище / сейфовая (вход)", value=False)
    zone_corridor = st.checkbox("🚶 Коридоры / проходы", value=False)

with col_zone3:
    zone_office = st.checkbox("🏢 Кабинеты / офисы", value=False)
    zone_tech = st.checkbox("🛠️ Технические помещения", value=False)
    zone_perimeter = st.checkbox("🔲 Периметр (окна, двери)", value=False)

# Собираем выбранные зоны
selected_zones = []
if zone_entrance: selected_zones.append("Входная группа")
if zone_cash: selected_zones.append("Кассовый узел")
if zone_atm: selected_zones.append("Банкоматы")
if zone_hall: selected_zones.append("Операционный зал")
if zone_storage: selected_zones.append("Хранилище")
if zone_corridor: selected_zones.append("Коридоры")
if zone_office: selected_zones.append("Кабинеты")
if zone_tech: selected_zones.append("Технические помещения")
if zone_perimeter: selected_zones.append("Периметр")

if not selected_zones:
    selected_zones = ["Общий обзор (по умолчанию)"]

# --- НЮАНСЫ ---
st.markdown("**🔧 Особенности помещения**")
col_nuance1, col_nuance2, col_nuance3 = st.columns(3)

with col_nuance1:
    suspended_ceiling = st.checkbox("Подвесной потолок")
    beams = st.checkbox("Балки на потолке")
    if beams:
        beam_height = st.number_input("Высота балок (мм)", min_value=0, max_value=1000, value=400, step=50)

with col_nuance2:
    sun_side = st.checkbox("Окна на солнечную сторону")
    wdr_cameras = st.checkbox("Требуются камеры с WDR")
    cable_protection = st.checkbox("Защита кабеля (гофра)")

with col_nuance3:
    gypsum_walls = st.checkbox("Гипсокартонные стены")
    through_walls = st.checkbox("Проход кабеля через стены")

# --- ВЫБОР СЦЕНАРИЯ ---
st.markdown("**Выберите сценарий:**")
scenario = st.radio(
    "",
    options=["Техническое задание", "Смета", "Проект", "Заявка"],
    index=0,
    horizontal=True,
    label_visibility="collapsed"
)

legal_check = st.checkbox("✅ Проверить аттестат МЧС (заглушка)")

# --- ФУНКЦИЯ ГЕНЕРАЦИИ СХЕМЫ (обновлена для зональной расстановки) ---
def generate_blueprint(room_desc, equipment_list, length, width, doors, windows, selected_zones):
    scale = 40
    margin = 60
    svg_w = length * scale + 2 * margin
    svg_h = width * scale + 2 * margin + 140

    room_x = margin
    room_y = margin
    room_w = length * scale
    room_h = width * scale

    svg = f'<svg width="{svg_w}" height="{svg_h}" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff; border-radius: 8px; font-family: Inter, sans-serif; border: 1px solid #ccc;">'

    # Стены
    svg += f'<rect x="{room_x}" y="{room_y}" width="{room_w}" height="{room_h}" fill="none" stroke="#333" stroke-width="2" />'
    svg += f'<text x="{room_x + 10}" y="{room_y + 20}" fill="#333" font-size="12" font-weight="bold">{room_desc[:30]}</text>'

    # Двери
    door_w = 30
    door_h = 15
    if doors >= 1:
        dx = room_x + 10
        dy = room_y + room_h - door_h
        svg += f'<rect x="{dx}" y="{dy}" width="{door_w}" height="{door_h}" fill="#e67e22" rx="2" />'
        svg += f'<text x="{dx + 5}" y="{dy + 25}" fill="#333" font-size="8">Дверь</text>'
    if doors >= 2:
        dx = room_x + room_w - 10 - door_w
        dy = room_y + room_h - door_h
        svg += f'<rect x="{dx}" y="{dy}" width="{door_w}" height="{door_h}" fill="#e67e22" rx="2" />'
        svg += f'<text x="{dx + 5}" y="{dy + 25}" fill="#333" font-size="8">Дверь</text>'

    # Окна
    win_w = 40
    win_h = 15
    if windows >= 1:
        wx = room_x + 10
        wy = room_y + 10
        svg += f'<rect x="{wx}" y="{wy}" width="{win_w}" height="{win_h}" fill="#3498db" rx="2" />'
        svg += f'<text x="{wx + 5}" y="{wy + 25}" fill="#333" font-size="8">Окно</text>'

    # --- РАССТАНОВКА КАМЕР ПО ЗОНАМ ---
    positions = {}

    # Обрабатываем только камеры (элементы с "Видео" в названии), которые придут из equipment_list
    camera_count = 0
    for zone in selected_zones:
        if zone == "Входная группа":
            positions["Видео (вход)"] = {"x": room_x + 10, "y": room_y + room_h - 50, "sym": "V", "color": "#e74c3c"}
            camera_count += 1
        elif zone == "Кассовый узел":
            # Предположим, что в кассовом узле 2 кассы (можно сделать параметризуемым)
            positions["Видео (касса 1)"] = {"x": room_x + room_w * 0.3, "y": room_y + 20, "sym": "V", "color": "#e74c3c"}
            positions["Видео (касса 2)"] = {"x": room_x + room_w * 0.7, "y": room_y + 20, "sym": "V", "color": "#e74c3c"}
            camera_count += 2
        elif zone == "Операционный зал":
            positions["Видео (общий обзор)"] = {"x": room_x + room_w - 30, "y": room_y + 30, "sym": "V", "color": "#e74c3c"}
            camera_count += 1
        elif zone == "Хранилище":
            positions["Видео (хранилище)"] = {"x": room_x + room_w // 2, "y": room_y + room_h // 2, "sym": "V", "color": "#e74c3c"}
            camera_count += 1
        elif zone == "Коридоры":
            # Камера в начале коридора
            positions["Видео (коридор)"] = {"x": room_x + 10, "y": room_y + 20, "sym": "V", "color": "#e74c3c"}
            camera_count += 1
        elif zone == "Кабинеты":
            positions["Видео (кабинет)"] = {"x": room_x + room_w - 30, "y": room_y + room_h - 30, "sym": "V", "color": "#e74c3c"}
            camera_count += 1
        elif zone == "Технические помещения":
            positions["Видео (техническое)"] = {"x": room_x + room_w // 2, "y": room_y + 20, "sym": "V", "color": "#e74c3c"}
            camera_count += 1
        elif zone == "Периметр":
            # по одной камере на окно/дверь (упрощённо)
            positions["Видео (периметр)"] = {"x": room_x + room_w - 30, "y": room_y + room_h - 30, "sym": "V", "color": "#e74c3c"}
            camera_count += 1
        elif zone == "Банкоматы":
            positions["Видео (банкомат)"] = {"x": room_x + room_w * 0.5, "y": room_y + 20, "sym": "V", "color": "#e74c3c"}
            camera_count += 1
        elif zone == "Общий обзор (по умолчанию)":
            positions["Видео (общий обзор)"] = {"x": room_x + room_w - 30, "y": room_y + 30, "sym": "V", "color": "#e74c3c"}
            camera_count += 1

    # Если камер нет, но в equipment_list есть "Видео", добавим одну для общего обзора
    if camera_count == 0 and any("Видео" in eq for eq in equipment_list):
        positions["Видео (общий обзор)"] = {"x": room_x + room_w - 30, "y": room_y + 30, "sym": "V", "color": "#e74c3c"}

    # Остальное оборудование (не камеры) расставляем по старым правилам (условно)
    other_positions = {
        "СКУД": {"x": room_x + 20, "y": room_y + room_h - 50, "sym": "C", "color": "#2980b9"},
        "Движение": {"x": room_x + room_w // 2, "y": room_y + 20, "sym": "Д", "color": "#f39c12"},
        "Дым": {"x": room_x + 40, "y": room_y + 30, "sym": "И", "color": "#8e44ad"},
        "Ручной": {"x": room_x + room_w - 40, "y": room_y + room_h - 30, "sym": "Р", "color": "#e84393"},
        "Газ": {"x": room_x + room_w // 2, "y": room_y + room_h // 2, "sym": "Г", "color": "#00b894"},
        "Контроллер": {"x": room_x + 20, "y": room_y + 60, "sym": "K", "color": "#6c5ce7"},
    }

    # Рисуем все позиции
    for label, pos in positions.items():
        x, y, sym, color = pos["x"], pos["y"], pos["sym"], pos["color"]
        svg += f'<circle cx="{x}" cy="{y}" r="10" fill="{color}" />'
        svg += f'<text x="{x-4}" y="{y+3}" fill="#fff" font-size="8" font-weight="bold">{sym}</text>'
        svg += f'<text x="{x-15}" y="{y+20}" fill="#333" font-size="7">{label[:6]}</text>'

    for eq, pos in other_positions.items():
        # Рисуем только если это оборудование есть в списке equipment_list
        if any(eq in e for e in equipment_list):
            x, y, sym, color = pos["x"], pos["y"], pos["sym"], pos["color"]
            if eq in ["СКУД", "Контроллер", "Ручной", "Газ"]:
                svg += f'<rect x="{x-10}" y="{y-8}" width="20" height="16" fill="{color}" rx="2" />'
                svg += f'<text x="{x-5}" y="{y+3}" fill="#fff" font-size="8" font-weight="bold">{sym}</text>'
            else:
                svg += f'<circle cx="{x}" cy="{y}" r="10" fill="{color}" />'
                svg += f'<text x="{x-4}" y="{y+3}" fill="#fff" font-size="8" font-weight="bold">{sym}</text>'

    # Легенда
    legend_y = room_y + room_h + 50
    svg += f'<text x="{margin}" y="{legend_y}" fill="#333" font-size="12" font-weight="bold">Условные обозначения:</text>'
    items = [
        ("C", "Считыватель", "#2980b9"),
        ("K", "Контроллер", "#6c5ce7"),
        ("V", "Камера", "#e74c3c"),
        ("Д", "Движение", "#f39c12"),
        ("И", "Дымовой", "#8e44ad"),
        ("Р", "Ручной", "#e84393"),
        ("Г", "Газ", "#00b894"),
    ]
    for i, (code, name, color) in enumerate(items):
        x = margin + 30 + i * 90
        svg += f'<rect x="{x}" y="{legend_y + 10}" width="16" height="12" fill="{color}" rx="2" />'
        svg += f'<text x="{x + 20}" y="{legend_y + 22}" fill="#333" font-size="8">{code} — {name}</text>'

    # Масштаб
    scale_x = room_x + room_w - 80
    scale_y = room_y + room_h + 20
    svg += f'<line x1="{scale_x}" y1="{scale_y}" x2="{scale_x + 40}" y2="{scale_y}" stroke="#333" stroke-width="1" />'
    svg += f'<text x="{scale_x}" y="{scale_y + 12}" fill="#333" font-size="7">1 м</text>'

    svg += '</svg>'
    return svg

# --- КНОПКА ---
if st.button("Получить результат", type="primary", use_container_width=True):
    if manual_input.strip():
        room_desc = manual_input.strip()
    elif selected_key:
        room_desc = room_options[selected_key] + f" (Тип: {selected_key})"
    else:
        room_desc = ""

    if not room_desc.strip():
        st.warning("⚠️ Выберите типовое помещение или введите описание вручную.")
    else:
        with st.spinner("🔄 Анализ..."):
            try:
                with GigaChat(credentials=GIGACHAT_KEY, model="GigaChat-3-Ultra", verify_ssl_certs=False) as client:
                    # --- БАЗОВЫЙ ПРОМПТ С ЗОНАЛЬНЫМ ПОДХОДОМ ---
                    base_prompt = f"""
Ты — эксперт по оснащению банков системами безопасности и противопожарной защиты.

Нормативная база: Сборник № 4461, РД 78.36.003-2002, 123-ФЗ, СП 484.1311500.2020, ГОСТ Р 21.110-2013, ГОСТ Р 51558-2014.

Целевой перечень оборудования (предпочтительные производители):
- САПС/СОУЭ: АО НВП «Болид» (ППКУП «Сириус», С2000-КДЛ, С2000Р-ДИП, С2000Р-ИПР, «Рупор»).
- СКУД: ГК «ТвинПро» (NG-1000, MB-NET II), ГК «ЦРТ» (FS6/FS8), считыватели ER 1402, Esmart Reader.
- СОТ: LTV (LTV-3CND40-M2714, LTV-3CNB40-F28, LTV-3RN6481-R).
- СОТС: АО НВП «Болид» (С2000-СМК, «Фотон-9», «Стекло-3»).

Помещение: {room_desc}
Длина: {length} м, Ширина: {width} м, Высота: {height} м
Площадь: {area:.1f} м², Периметр: {perimeter:.1f} м
Двери: {doors} шт., Окна: {windows} шт.
Критические зоны для видеоконтроля: {', '.join(selected_zones)}.
Особенности: подвесной потолок - {'Да' if suspended_ceiling else 'Нет'}, балки - {'Да' if beams else 'Нет'}, солнечная сторона - {'Да' if sun_side else 'Нет'}.

Правила расчёта:
- Количество видеокамер определяется не площадью, а количеством критических зон. Для каждой зоны требуется минимум одна камера, для касс — по одной на рабочее место. В обосновании укажи, какая камера для какой зоны предназначена.
- Дымовые извещатели: 1 на 30 м² (мин. 2). Расчёт: max(2, ceil({area}/30)).
- Ручные извещатели: 1 на выход (если дверей > 0).
- Датчики движения: 1 на 20 м² (мин. 1).
- СКУД: 1 считыватель на дверь, 1 контроллер на помещение.
- Длина кабеля: периметр × 1.5.
При подвесном потолке — извещатели за потолком. При балках — в каждом отсеке. При солнечной стороне — камеры с WDR.
При выборе оборудования строго придерживайся целевого перечня.
В обосновании ссылайся на конкретные пункты нормативных документов.
"""

                    # --- СЦЕНАРИИ (без изменений) ---
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

                    response = client.chat(prompt)
                    raw = response.choices[0].message.content

                    st.success("✅ Готово")
                    st.markdown(raw)

                    # --- ГЕНЕРАЦИЯ СХЕМЫ (с передачей выбранных зон) ---
                    if scenario in ["Проект", "Заявка"]:
                        equip_list = ["СКУД", "Видео", "Движение", "Дым", "Ручной", "Газ", "Контроллер"]
                        if "Оборудование:" in raw:
                            part = raw.split("Оборудование:")[-1].strip()
                            equip_list = [e.strip() for e in part.split(",") if e.strip()]
                        if equip_list:
                            svg = generate_blueprint(room_desc, equip_list, length, width, doors, windows, selected_zones)
                            st.markdown("### 📐 План расстановки оборудования")
                            st.markdown("_*Размеры указаны согласно введённой геометрии. Камеры расставлены по выбранным зонам._")
                            st.markdown(svg, unsafe_allow_html=True)
                        else:
                            st.info("ℹ️ Список оборудования не найден в ответе, схема не сгенерирована.")

            except Exception as e:
                st.error(f"❌ Ошибка: {e}")

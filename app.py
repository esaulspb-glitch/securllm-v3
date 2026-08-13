import streamlit as st
import re
from gigachat import GigaChat

st.set_page_config(page_title="SecurLLM — Проектировщик", layout="centered")

# --- СТИЛИ (SberDesign) ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .main > div { background-color: #f8f9fa; padding-top: 2rem !important; }
    h1, h2, h3 { color: #1a1a1a !important; font-family: 'Inter', sans-serif; }
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

# --- ШАПКА ---
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem; border-bottom: 1px solid #d0d7de; padding-bottom: 1rem;">
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="36" height="36" rx="8" fill="#1A991A"/>
        <path d="M10 18L14 22L26 10" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <span style="font-size: 24px; font-weight: 700; color: #1A991A;">Сбер</span>
    <span style="font-size: 18px; color: #333F48; font-weight: 300; margin-left: 4px;">| SecurLLM Проектировщик</span>
</div>
""", unsafe_allow_html=True)

# --- ЗАГОЛОВОК ---
st.title("🏗️ Проектирование по геометрии помещения")
st.markdown("*Введите размеры и параметры помещения — получите готовый проект оснащения.*")

# --- ПРОВЕРКА СЕКРЕТА ---
try:
    GIGACHAT_KEY = st.secrets["GIGACHAT_KEY"]
except Exception:
    st.error("❌ Ошибка: не найден секрет GIGACHAT_KEY. Проверьте настройки приложения.")
    st.stop()

# --- ВВОД ДАННЫХ ---
st.markdown("### 📐 Размеры помещения")
col1, col2 = st.columns(2)
with col1:
    room_name = st.text_input("Название помещения", value="Кассовый узел")
    length = st.number_input("Длина (м)", min_value=1.0, max_value=50.0, value=6.0, step=0.5)
    height = st.number_input("Высота (м)", min_value=2.0, max_value=10.0, value=3.0, step=0.5)
with col2:
    room_type = st.selectbox("Тип помещения", ["Кассовый узел", "Хранилище ценностей", "Серверная (ЦОД)", "Офисное помещение", "Коридор", "Подсобка"])
    width = st.number_input("Ширина (м)", min_value=1.0, max_value=50.0, value=4.0, step=0.5)
    doors = st.number_input("Количество дверей", min_value=0, max_value=10, value=1, step=1)
    windows = st.number_input("Количество окон", min_value=0, max_value=10, value=1, step=1)

area = length * width
perimeter = 2 * (length + width)
st.caption(f"📏 Площадь: {area:.1f} м² · Периметр: {perimeter:.1f} м")

# --- КНОПКА ---
if st.button("🚀 Спроектировать", type="primary", use_container_width=True):
    with st.spinner("🔄 Генерация проекта..."):
        try:
            with GigaChat(credentials=GIGACHAT_KEY, model="GigaChat-3-Ultra", verify_ssl_certs=False) as client:
                prompt = f"""
Ты — эксперт по оснащению банков системами безопасности и противопожарной защиты.

Нормативная база: Сборник № 4461, РД 78.36.003-2002, 123-ФЗ, СП 484, ГОСТ Р 21.110-2013.

Помещение: {room_name} (тип: {room_type})
Длина: {length} м, Ширина: {width} м, Высота: {height} м
Площадь: {area:.1f} м², Периметр: {perimeter:.1f} м
Двери: {doors} шт., Окна: {windows} шт.

Классификация зон:
- Зона 0 (подсобка): ничего не требуется.
- Зона 1 (клиентская): видеонаблюдение, пожарная сигнализация.
- Зона 2 (офисная): СКУД, тревожная кнопка, видео, пожарная сигнализация.
- Зона 3A (серверная): СКУД двухфакторная, многорубежная сигнализация, видео высокого разрешения, пожарная сигнализация, газовое пожаротушение.
- Зона 3B (хранилище): СКУД карта+биометрия, многорубежная сигнализация, видео с распознаванием лиц, газовое пожаротушение, вывод на Росгвардию.
- Зона 3C (касса): СКУД карта+PIN, сигнализация, видео над каждым рабочим местом, пожарная сигнализация.

Расчёт количества оборудования:
- Видеокамеры: 1 камера на 20 м² (минимум 2).
- Дымовые извещатели: 1 на 30 м².
- Ручные извещатели: 1 на выход (если дверей > 0).
- Длина кабеля: периметр × 1.5.
- СКУД: 1 считыватель на дверь + 1 контроллер на помещение.
- Датчики движения: 1 на 20 м².

Сформируй полный проект оснащения помещения:

1. Пояснительная записка (объект, нормативная база).
2. Схема расстановки оборудования (текстовое описание с привязкой к геометрии).
3. Спецификация оборудования (таблица: Поз., Наименование, Тип, Марка, Кол-во, Ед. изм.).
4. Смета (таблица: Наименование, Кол-во, Цена за ед., Сумма). Цены — примерные рыночные.

В конце выведи список оборудования в формате:
Оборудование: СКУД, Видео, Движение, Дым, Ручной, Газ, Контроллер
"""
                response = client.chat(prompt)
                raw = response.choices[0].message.content

                st.success("✅ Проект готов")
                st.markdown(raw)

                # --- ГЕНЕРАЦИЯ СХЕМЫ ---
                equip_list = ["СКУД", "Видео", "Движение", "Дым", "Ручной", "Газ", "Контроллер"]
                if "Оборудование:" in raw:
                    part = raw.split("Оборудование:")[-1].strip()
                    equip_list = [e.strip() for e in part.split(",") if e.strip()]

                # --- SVG-схема ---
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
                svg += f'<text x="{room_x + 10}" y="{room_y + 20}" fill="#333" font-size="12" font-weight="bold">{room_name} ({area:.1f} м²)</text>'

                # Двери
                door_width = 30
                door_height = 15
                if doors >= 1:
                    door_x = room_x + 10
                    door_y = room_y + room_h - door_height
                    svg += f'<rect x="{door_x}" y="{door_y}" width="{door_width}" height="{door_height}" fill="#e67e22" rx="2" />'
                    svg += f'<text x="{door_x + 5}" y="{door_y + 25}" fill="#333" font-size="8">Дверь</text>'
                if doors >= 2:
                    door_x = room_x + room_w - 10 - door_width
                    door_y = room_y + room_h - door_height
                    svg += f'<rect x="{door_x}" y="{door_y}" width="{door_width}" height="{door_height}" fill="#e67e22" rx="2" />'
                    svg += f'<text x="{door_x + 5}" y="{door_y + 25}" fill="#333" font-size="8">Дверь</text>'

                # Окна
                win_width = 40
                win_height = 15
                if windows >= 1:
                    win_x = room_x + 10
                    win_y = room_y + 10
                    svg += f'<rect x="{win_x}" y="{win_y}" width="{win_width}" height="{win_height}" fill="#3498db" rx="2" />'
                    svg += f'<text x="{win_x + 5}" y="{win_y + 25}" fill="#333" font-size="8">Окно</text>'

                # Оборудование
                positions = {
                    "СКУД": {"x": room_x + 20, "y": room_y + room_h - 50, "sym": "C", "color": "#2980b9"},
                    "Видео": {"x": room_x + room_w - 30, "y": room_y + 30, "sym": "V", "color": "#e74c3c"},
                    "Движение": {"x": room_x + room_w // 2, "y": room_y + 20, "sym": "Д", "color": "#f39c12"},
                    "Дым": {"x": room_x + 40, "y": room_y + 30, "sym": "И", "color": "#8e44ad"},
                    "Ручной": {"x": room_x + room_w - 40, "y": room_y + room_h - 30, "sym": "Р", "color": "#e84393"},
                    "Газ": {"x": room_x + room_w // 2, "y": room_y + room_h // 2, "sym": "Г", "color": "#00b894"},
                    "Контроллер": {"x": room_x + 20, "y": room_y + 60, "sym": "K", "color": "#6c5ce7"},
                }

                for eq in equip_list:
                    if eq in positions:
                        pos = positions[eq]
                        x, y, sym, color = pos["x"], pos["y"], pos["sym"], pos["color"]
                        if eq in ["СКУД", "Контроллер", "Ручной", "Газ"]:
                            svg += f'<rect x="{x-10}" y="{y-8}" width="20" height="16" fill="{color}" rx="2" />'
                            svg += f'<text x="{x-5}" y="{y+3}" fill="#fff" font-size="8" font-weight="bold">{sym}</text>'
                        elif eq in ["Видео", "Движение", "Дым"]:
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

                st.markdown("### 📐 План расстановки оборудования")
                st.markdown(svg, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Ошибка: {e}")
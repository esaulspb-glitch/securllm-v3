import streamlit as st
import pandas as pd
import json
import requests
import io
import base64
from datetime import datetime
import math

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
# 2. БОКОВАЯ ПАНЕЛЬ — КЛЮЧИ И НАСТРОЙКИ (оставляем как было)
# ------------------------------------------------------------
with st.sidebar:
    st.header("🔐 Настройки")
    gigachat_key = st.text_input("GigaChat API Key", type="password", value=st.secrets.get("GIGACHAT_KEY", ""))
    st.markdown("---")
    st.caption("Прототип V2 • зональный подход • поддержка нескольких помещений")

# ------------------------------------------------------------
# 3. ЭКСПЛИКАЦИЯ ПОМЕЩЕНИЙ
# ------------------------------------------------------------
st.subheader("📐 Экспликация помещений")

col_left, col_right = st.columns([2, 1])

with col_left:
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
            # Быстрое заполнение типовым набором (для теста)
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

with col_right:
    st.markdown("#### 📌 Выбор зон для систем")
    # Здесь мы оставляем существующие expander-ы для зон (они были в прототипе)
    # Их код приведён ниже в секции "ВЫБОР ЗОН"

# ------------------------------------------------------------
# 4. ВЫБОР ЗОН (сохраняем оригинальный интерфейс)
# ------------------------------------------------------------
st.subheader("🎯 Выбор зон для систем безопасности")

# Инициализация состояний для зон (если их нет)
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
    )
    st.session_state.soue_zones = selected_soue
    floors = st.number_input("Количество этажей", min_value=1, value=1, step=1)
    light_exit = st.checkbox("Световые оповещатели «Выход»", value=True)

# ------------------------------------------------------------
# 5. РАСЧЁТ (основная кнопка)
# ------------------------------------------------------------
st.markdown("---")
calc_btn = st.button("🚀 Рассчитать для всех помещений", type="primary", disabled=not st.session_state.rooms)

if calc_btn and gigachat_key:
    with st.spinner("Выполняется расчёт для всех помещений..."):
        # Собираем выбранные зоны в словарь
        zones = {
            "video": st.session_state.video_zones,
            "skud": st.session_state.skud_zones,
            "ohr": st.session_state.ohr_zones,
            "fire": st.session_state.fire_zones,
            "soue": st.session_state.soue_zones,
            "skud_ident": ident_type,
            "skud_2fa": two_factor,
            "fire_suspended": suspended,
            "fire_beams": beams,
            "fire_vent_dist": vent_dist,
            "soue_floors": floors,
            "soue_light": light_exit,
        }

        # --- 5.1 Функции расчёта для одного помещения ---
        def calc_video(room, video_zones):
            equip = {}
            if "Входная группа" in video_zones:
                equip["Купол LTV-3CND40-M2714"] = equip.get("Купол LTV-3CND40-M2714", 0) + 1
                if room["windows"] > 0:
                    equip["Уличная LTV-3RN6481-R"] = equip.get("Уличная LTV-3RN6481-R", 0) + 1
            if "Кассовый узел (каждое место)" in video_zones:
                # здесь можно уточнить количество по числу рабочих мест (пока 1)
                equip["Купол LTV-3CND40-M2714"] = equip.get("Купол LTV-3CND40-M2714", 0) + 1
            if "Операционный зал" in video_zones:
                # по площади: 1 камера на 20 кв.м
                area = room["length"] * room["width"]
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
            # Убираем нулевые
            return {k: v for k, v in equip.items() if v > 0}

        def calc_skud(room, skud_zones, ident_type, two_factor):
            equip = {}
            if "Главный вход" in skud_zones:
                equip["Считыватель ER 1402"] = equip.get("Считыватель ER 1402", 0) + 1
                equip["Контроллер NG-1000"] = equip.get("Контроллер NG-1000", 0) + 1
            if "Внутренние двери" in skud_zones:
                equip["Считыватель Esmart Reader"] = equip.get("Считыватель Esmart Reader", 0) + 1
                equip["Контроллер MB-NET II"] = equip.get("Контроллер MB-NET II", 0) + 1
            if "Кассовый узел/хранилище" in skud_zones:
                equip["Считыватель ER 1402"] = equip.get("Считыватель ER 1402", 0) + 1
                equip["Контроллер NG-1000"] = equip.get("Контроллер NG-1000", 0) + 1
                if two_factor:
                    equip["Считыватель биометрический FS6/FS8"] = equip.get("Считыватель биометрический FS6/FS8", 0) + 1
            if "Серверная" in skud_zones:
                equip["Считыватель ER 1402"] = equip.get("Считыватель ER 1402", 0) + 1
                equip["Контроллер NG-1000"] = equip.get("Контроллер NG-1000", 0) + 1
            if "Кабинеты руководства" in skud_zones:
                equip["Считыватель Esmart Reader"] = equip.get("Считыватель Esmart Reader", 0) + 1
                equip["Контроллер MB-NET II"] = equip.get("Контроллер MB-NET II", 0) + 1
            return {k: v for k, v in equip.items() if v > 0}

        def calc_ohr(room, ohr_zones):
            equip = {}
            if "Периметр (двери/окна)" in ohr_zones:
                # на каждую дверь/окно
                cnt = room["doors"] + room["windows"]
                equip["Извещатель «Стекло-3»"] = equip.get("Извещатель «Стекло-3»", 0) + cnt
            if "Объём (движение)" in ohr_zones:
                area = room["length"] * room["width"]
                cnt = max(1, math.ceil(area / 30))
                equip["Извещатель «Фотон-9»"] = equip.get("Извещатель «Фотон-9»", 0) + cnt
            if "Предметный (сейфы)" in ohr_zones:
                equip["Извещатель С2000-СМК"] = equip.get("Извещатель С2000-СМК", 0) + 1
            if "Усиленная охрана кассы/хранилища" in ohr_zones:
                equip["Извещатель «Фотон-9»"] = equip.get("Извещатель «Фотон-9»", 0) + 2
                equip["Извещатель «Стекло-3»"] = equip.get("Извещатель «Стекло-3»", 0) + 2
            return {k: v for k, v in equip.items() if v > 0}

        def calc_fire(room, fire_types, suspended, beams, vent_dist):
            equip = {}
            area = room["length"] * room["width"]
            # Норматив: 1 извещатель на ~20 кв.м (с учётом коэффициентов)
            coeff = 1.0
            if suspended:
                coeff *= 1.2
            if beams:
                coeff *= 1.3
            base_cnt = max(1, math.ceil(area / 20 * coeff))
            # Распределяем по типам
            if "Дымовые извещатели" in fire_types:
                equip["Дымовой ИП 212-141"] = equip.get("Дымовой ИП 212-141", 0) + base_cnt
            if "Тепловые извещатели" in fire_types:
                equip["Тепловой ИП 101-3А"] = equip.get("Тепловой ИП 101-3А", 0) + base_cnt
            if "Комбинированные извещатели" in fire_types:
                equip["Комбинированный ИП 212/101"] = equip.get("Комбинированный ИП 212/101", 0) + base_cnt
            # Приборы управления
            equip["ППКУП «Сириус»"] = equip.get("ППКУП «Сириус»", 0) + 1
            equip["С2000-КДЛ"] = equip.get("С2000-КДЛ", 0) + 1
            return {k: v for k, v in equip.items() if v > 0}

        def calc_soue(room, soue_types, floors, light_exit):
            equip = {}
            area = room["length"] * room["width"]
            # Оповещатели: 1 на 30 кв.м
            cnt = max(1, math.ceil(area / 30))
            if "Звуковое оповещение" in soue_types:
                equip["Оповещатель «Рупор»"] = equip.get("Оповещатель «Рупор»", 0) + cnt
            if "Речевое оповещение" in soue_types:
                equip["Оповещатель речевой «Рупор-Р»"] = equip.get("Оповещатель речевой «Рупор-Р»", 0) + cnt
            if light_exit:
                equip["Световой оповещатель «Выход»"] = equip.get("Световой оповещатель «Выход»", 0) + max(1, floors)
            return {k: v for k, v in equip.items() if v > 0}

        # --- 5.2 Агрегация по всем помещениям ---
        total_equip = {
            "video": {},
            "skud": {},
            "ohr": {},
            "fire": {},
            "soue": {}
        }
        room_details = []  # для детализации по каждой комнате

        for idx, room in enumerate(st.session_state.rooms):
            # Видео
            v = calc_video(room, zones["video"])
            for k, cnt in v.items():
                total_equip["video"][k] = total_equip["video"].get(k, 0) + cnt
            # СКУД
            s = calc_skud(room, zones["skud"], zones["skud_ident"], zones["skud_2fa"])
            for k, cnt in s.items():
                total_equip["skud"][k] = total_equip["skud"].get(k, 0) + cnt
            # Охранка
            o = calc_ohr(room, zones["ohr"])
            for k, cnt in o.items():
                total_equip["ohr"][k] = total_equip["ohr"].get(k, 0) + cnt
            # Пожар
            f = calc_fire(room, zones["fire"], zones["fire_suspended"], zones["fire_beams"], zones["fire_vent_dist"])
            for k, cnt in f.items():
                total_equip["fire"][k] = total_equip["fire"].get(k, 0) + cnt
            # СОУЭ
            se = calc_soue(room, zones["soue"], zones["soue_floors"], zones["soue_light"])
            for k, cnt in se.items():
                total_equip["soue"][k] = total_equip["soue"].get(k, 0) + cnt

            # Сохраняем детали по комнате (для SVG)
            room_details.append({
                "name": room["name"],
                "video": v,
                "skud": s,
                "ohr": o,
                "fire": f,
                "soue": se
            })

        # --- 5.3 Генерация SVG-схемы этажа ---
        def generate_svg(rooms, details):
            # Простая раскладка комнат в ряд, масштаб 1:20 (1 м = 20 пикселей)
            scale = 20
            margin = 30
            x_offset = margin
            y_offset = margin
            max_y = 0

            svg_parts = []
            svg_parts.append(f'<svg width="{len(rooms)*200+margin*2}" height="400" xmlns="http://www.w3.org/2000/svg">')
            svg_parts.append('<rect width="100%" height="100%" fill="#f0f4f8" />')
            svg_parts.append('<style>text { font-family: Arial; font-size: 12px; fill: #333; }</style>')

            for idx, (room, det) in enumerate(zip(rooms, details)):
                w = room["length"] * scale
                h = room["width"] * scale
                x = x_offset
                y = y_offset + (idx % 2) * (h + 10)  # чередование рядов
                if idx % 2 == 0:
                    x_offset += w + 20
                else:
                    x_offset = margin
                # Комната
                svg_parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#ffffff" stroke="#2c3e50" stroke-width="2" />')
                svg_parts.append(f'<text x="{x+10}" y="{y+20}" font-weight="bold">{room["name"]}</text>')
                svg_parts.append(f'<text x="{x+10}" y="{y+40}">{room["length"]}×{room["width"]} м</text>')
                # Оборудование (иконки)
                icon_x = x + 10
                icon_y = y + 60
                for sys, equip_list in det.items():
                    if equip_list:
                        for eq_name, cnt in equip_list.items():
                            # Упрощённо: рисуем кружок с первой буквой системы
                            color = {"video": "#3498db", "skud": "#2ecc71", "ohr": "#e67e22", "fire": "#e74c3c", "soue": "#9b59b6"}.get(sys, "#95a5a6")
                            svg_parts.append(f'<circle cx="{icon_x}" cy="{icon_y}" r="6" fill="{color}" />')
                            svg_parts.append(f'<text x="{icon_x+10}" y="{icon_y+4}" font-size="10">{eq_name[:3]} {cnt}</text>')
                            icon_y += 20
                # Отметки дверей/окон
                if room["doors"]:
                    svg_parts.append(f'<rect x="{x}" y="{y}" width="10" height="10" fill="#f1c40f" stroke="#333" />')
                if room["windows"]:
                    svg_parts.append(f'<rect x="{x+w-10}" y="{y}" width="10" height="10" fill="#3498db" stroke="#333" />')
                max_y = max(max_y, y + h)

            svg_parts.append('</svg>')
            return "\n".join(svg_parts)

        svg_code = generate_svg(st.session_state.rooms, room_details)

        # --- 5.4 Генерация ТЗ, сметы, проекта через GigaChat ---
        def call_gigachat(prompt, key):
            # Заглушка — реальный вызов API GigaChat
            # Здесь нужно вставить ваш код вызова
            # Ответим просто текстом-заглушкой для демонстрации
            return f"Сгенерированный текст на основе запроса: {prompt[:100]}..."

        # Формируем общее описание объекта
        total_area = sum(r["length"]*r["width"] for r in st.session_state.rooms)
        rooms_desc = ", ".join([f"{r['name']} ({r['length']}×{r['width']})" for r in st.session_state.rooms])

        # ТЗ
        tz_prompt = f"Составь техническое задание на систему безопасности для ВСП банка. Помещения: {rooms_desc}. Оборудование: {total_equip}. Нормативы: СП 484, Р 102-2024 и др."
        tz_text = call_gigachat(tz_prompt, gigachat_key)

        # Смета
        smeta_prompt = f"Составь смету на оборудование для объекта: {total_equip}. Укажи примерные цены."
        smeta_text = call_gigachat(smeta_prompt, gigachat_key)

        # Проект
        proj_prompt = f"Напиши пояснительную записку к проекту системы безопасности для ВСП с перечнем работ и оборудования."
        proj_text = call_gigachat(proj_prompt, gigachat_key)

        # Заявка
        zayavka_prompt = f"Сформируй заявку на выполнение работ по установке системы безопасности на объекте."
        zayavka_text = call_gigachat(zayavka_prompt, gigachat_key)

        # Сохраняем результат
        st.session_state.calc_result = {
            "total_equip": total_equip,
            "tz": tz_text,
            "smeta": smeta_text,
            "project": proj_text,
            "zayavka": zayavka_text,
            "svg": svg_code,
            "rooms": st.session_state.rooms,
            "room_details": room_details
        }

        st.success("Расчёт выполнен!")

# ------------------------------------------------------------
# 6. ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ
# ------------------------------------------------------------
if st.session_state.calc_result:
    res = st.session_state.calc_result

    # Вкладки
    tabs = st.tabs(["📊 Сводка", "📹 Видео", "🚪 СКУД", "🔔 Охранка", "🔥 Пожар", "📢 СОУЭ", "📄 ТЗ", "💰 Смета", "📐 Проект", "📋 Заявка", "🖼️ SVG-схема"])

    with tabs[0]:
        st.subheader("Сводная информация")
        st.write(f"**Количество помещений:** {len(res['rooms'])}")
        st.write(f"**Общая площадь:** {sum(r['length']*r['width'] for r in res['rooms'])} м²")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Оборудование по системам:**")
            for sys, equip in res["total_equip"].items():
                st.write(f"- {sys.upper()}: {sum(equip.values())} шт.")
        with col2:
            st.dataframe(pd.DataFrame(res["rooms"]), use_container_width=True)

    # Табы для каждой системы показывают детали оборудования
    sys_tabs = {
        "📹 Видео": "video",
        "🚪 СКУД": "skud",
        "🔔 Охранка": "ohr",
        "🔥 Пожар": "fire",
        "📢 СОУЭ": "soue"
    }
    for tab_name, sys_key in sys_tabs.items():
        with tabs[list(sys_tabs.keys()).index(tab_name)+1]:  # +1 потому что первый таб - сводка
            equip_dict = res["total_equip"].get(sys_key, {})
            if equip_dict:
                df = pd.DataFrame(list(equip_dict.items()), columns=["Тип", "Количество"])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Оборудование для этой системы не выбрано.")

    with tabs[6]:  # ТЗ
        st.subheader("Техническое задание")
        st.text_area("ТЗ", res["tz"], height=300)

    with tabs[7]:  # Смета
        st.subheader("Смета")
        st.text_area("Смета", res["smeta"], height=300)

    with tabs[8]:  # Проект
        st.subheader("Пояснительная записка")
        st.text_area("Проект", res["project"], height=300)

    with tabs[9]:  # Заявка
        st.subheader("Заявка на исполнение")
        st.text_area("Заявка", res["zayavka"], height=300)

    with tabs[10]:  # SVG
        st.subheader("План расстановки оборудования (SVG)")
        st.components.v1.html(res["svg"], height=500)
        # Кнопка скачать SVG
        b64 = base64.b64encode(res["svg"].encode()).decode()
        href = f'<a href="data:image/svg+xml;base64,{b64}" download="plan.svg">Скачать SVG</a>'
        st.markdown(href, unsafe_allow_html=True)

    # Кнопка экспорта ZIP (заглушка)
    st.download_button(
        label="📦 Скачать все документы (ZIP)",
        data=b"заглушка",  # здесь должен быть реальный ZIP
        file_name="securllm_package.zip",
        mime="application/zip",
        disabled=True
    )

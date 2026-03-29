# views/supplier_view.py
import flet as ft
from colors_apple import colors
from datetime import datetime, timedelta
import sys
import os
import threading
import time
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from login_screen import show_login


def show_supplier_view(page, dm, supplier, from_senior=False):
    """Экран Снабженца: упрощённый (без вкладок)"""
    page.clean()
    objects = dm.get_all_objects()
    
    # === НАВИГАЦИЯ ===
    def go_back(e):
        from views.senior_view import show_senior_menu
        for senior in dm.users.get("senior_masters", []):
            if senior["name"] == supplier["name"]:
                show_senior_menu(page, dm, senior)
                return
        from login_screen import show_login
        show_login(page, dm)
    
    # === ВЫДЕЛИТЬ ВСЁ ПРИ ФОКУСЕ (ТОЛЬКО ДЛЯ КОЛИЧЕСТВА!) ===
    def select_all(e):
        e.control.focus()
        e.control.select_all()
    
    # === ДАТА: МАСКА ВВОДА DD.MM.YYYY ===
    def format_date_mask(e):
        """Форматирует дату с фиксированными точками, курсор прыгает сам"""
        value = e.control.value
        cursor_pos = e.control.cursor_position if e.control.cursor_position else 0
        
        # Убираем всё кроме цифр
        digits = re.sub(r'\D', '', value)
        
        # Ограничиваем 8 цифрами
        digits = digits[:8]
        
        # Форматируем с точками
        if len(digits) >= 6:
            formatted = f"{digits[0:2]}.{digits[2:4]}.{digits[4:6]}"
        elif len(digits) >= 4:
            formatted = f"{digits[0:2]}.{digits[2:4]}."
        elif len(digits) >= 2:
            formatted = f"{digits[0:2]}."
        else:
            formatted = digits
        
        # Обновляем значение ТОЛЬКО если изменилось
        if formatted != value:
            e.control.value = formatted
            # ✅ Ставим курсор в конец (не выделяем!)
            e.control.cursor_position = len(formatted)
        
        e.control.update()
    
    # === ЗАПЛАНИРОВАТЬ ===
    def plan_delivery(e, obj_id, oxygen_input, propane_input, date_field, complete_btn):
        try:
            o_new = int(oxygen_input.value) if oxygen_input.value else 0
            p_new = int(propane_input.value) if propane_input.value else 0
            new_date = date_field.value
            
            # Валидация даты (не раньше сегодня)
            try:
                date_obj = datetime.strptime(new_date, "%d.%m.%Y")
                if date_obj.date() < datetime.now().date():
                    date_field.bgcolor = colors["danger_light"]
                    page.update()
                    return
            except:
                date_field.bgcolor = colors["danger_light"]
                page.update()
                return
            
            # Валидация количества
            requests = dm.get_active_requests(obj_id)
            max_o = next((r["quantity"] for r in requests if r["gas_type"] == "КИСЛОРОД"), 0)
            max_p = next((r["quantity"] for r in requests if r["gas_type"] == "ПРОПАН"), 0)
            
            if o_new > max_o or p_new > max_p or o_new < 0 or p_new < 0:
                oxygen_input.bgcolor = colors["danger_light"]
                propane_input.bgcolor = colors["danger_light"]
                page.update()
                return
            
            # Сохраняем план
            dm.data["deliveries"] = [d for d in dm.data["deliveries"] if d["object_id"] != obj_id]
            
            if o_new > 0:
                dm.add_delivery(obj_id, "КИСЛОРОД", o_new, new_date, "Склад")
            if p_new > 0:
                dm.add_delivery(obj_id, "ПРОПАН", p_new, new_date, "Склад")
            
            dm.save_data()
            
            # Подсветка успеха
            oxygen_input.bgcolor = colors["success_light"]
            propane_input.bgcolor = colors["success_light"]
            
            # ✅ АКТИВИРУЕМ кнопку "Выполнить" (без refresh!)
            complete_btn.disabled = False
            complete_btn.opacity = 1
            
            page.update()
            
            # Убираем подсветку через 2 сек
            def reset():
                time.sleep(2)
                oxygen_input.bgcolor = colors["surface"]
                propane_input.bgcolor = colors["surface"]
                page.update()
            
            threading.Thread(target=reset, daemon=True).start()
            
        except Exception as ex:
            print(f"Ошибка планирования: {ex}")
    
    # === ВЫПОЛНИТЬ ===
    def complete_delivery(e, obj_id):
        try:
            object_deliveries = [d for d in dm.get_planned_deliveries() if d["object_id"] == obj_id]
            if not object_deliveries:
                return
            
            o_planned = next((d["quantity"] for d in object_deliveries if d["gas_type"] == "КИСЛОРОД"), 0)
            p_planned = next((d["quantity"] for d in object_deliveries if d["gas_type"] == "ПРОПАН"), 0)
            
            # Удаляем поставки
            for d in object_deliveries:
                dm.data["deliveries"] = [del_item for del_item in dm.data["deliveries"] if del_item["id"] != d["id"]]
            
            # Добавляем на склад
            for obj_item in dm.data["objects"]:
                if obj_item["id"] == obj_id:
                    obj_item["oxygen"] += o_planned
                    obj_item["propane"] += p_planned
                    break
            
            # Удаляем заявки
            for req in dm.data["requests"]:
                if req["object_id"] == obj_id and req["status"] == "active":
                    if req["gas_type"] == "КИСЛОРОД":
                        req["quantity"] -= o_planned
                    elif req["gas_type"] == "ПРОПАН":
                        req["quantity"] -= p_planned
            
            dm.data["requests"] = [r for r in dm.data["requests"] 
                                  if not (r["object_id"] == obj_id and r["quantity"] <= 0)]
            
            dm.save_data()
            
            # Перезагружаем экран (после выполнения — можно)
            show_supplier_view(page, dm, supplier, from_senior)
            
        except Exception as ex:
            print(f"Ошибка выполнения: {ex}")
    
    # === КАРТОЧКА ОБЪЕКТА ===
    def create_object_card(obj):
        requests = dm.get_active_requests(obj["id"])
        oxygen_req = next((r["quantity"] for r in requests if r["gas_type"] == "КИСЛОРОД"), 0)
        propane_req = next((r["quantity"] for r in requests if r["gas_type"] == "ПРОПАН"), 0)
        
        if oxygen_req == 0 and propane_req == 0:
            return None
        
        # Проверяем есть ли план
        obj_deliveries = [d for d in dm.get_planned_deliveries() if d["object_id"] == obj["id"]]
        has_plan = len(obj_deliveries) > 0
        
        # Если есть план — показываем запланированное количество
        if has_plan:
            plan_o = next((d["quantity"] for d in obj_deliveries if d["gas_type"] == "КИСЛОРОД"), 0)
            plan_p = next((d["quantity"] for d in obj_deliveries if d["gas_type"] == "ПРОПАН"), 0)
            plan_date = obj_deliveries[0]["planned_date"]
        else:
            plan_o = oxygen_req
            plan_p = propane_req
            plan_date = datetime.now().strftime("%d.%m.%Y")
        
        # ✅ Поля количества (с выделением при клике)
        oxygen_input = ft.TextField(
            value=str(plan_o),
            width=100,
            height=60,
            text_align="center",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=colors["border"],
            bgcolor=colors["surface"],
            text_size=24,
            content_padding=10,
            on_focus=select_all,  # ✅ Выделять для количества
        )
        
        propane_input = ft.TextField(
            value=str(plan_p),
            width=100,
            height=60,
            text_align="center",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=colors["border"],
            bgcolor=colors["surface"],
            text_size=24,
            content_padding=10,
            on_focus=select_all,  # ✅ Выделять для количества
        )
        
        # ✅ ПОЛЕ ДАТЫ: DECIMAL_NUMBER (цифры + точка)
        date_field = ft.TextField(
            value=plan_date,
            width=140,
            height=50,
            text_align="center",
            text_size=16,
            border_color=colors["border"],
            bgcolor=colors["surface"],
            content_padding=10,
            keyboard_type=ft.KeyboardType.DECIMAL_NUMBER,  # ✅ ЦИФРЫ + ТОЧКА!
            on_change=format_date_mask,
        )
        
        # ✅ complete_btn ПЕРЕД plan_btn
        complete_btn = ft.ElevatedButton(
            "ВЫПОЛНИТЬ",
            on_click=lambda e, oid=obj["id"]: complete_delivery(e, oid),
            width=350,
            height=45,
            style=ft.ButtonStyle(
                color="white",
                bgcolor=colors["success"],
                shape=ft.RoundedRectangleBorder(radius=6)
            ),
            disabled=not has_plan,
            opacity=1 if has_plan else 0.5
        )
        
        # ✅ plan_btn ПОСЛЕ complete_btn
        plan_btn = ft.ElevatedButton(
            "ЗАПЛАНИРОВАТЬ",
            on_click=lambda e, oid=obj["id"], oi=oxygen_input, pi=propane_input, df=date_field, cb=complete_btn: 
                plan_delivery(e, oid, oi, pi, df, cb),
            width=350,
            height=45,
            style=ft.ButtonStyle(
                color="white",
                bgcolor=colors["primary"],
                shape=ft.RoundedRectangleBorder(radius=6)
            )
        )
        
        # Карточка (отступы по 4px)
        return ft.Container(
            content=ft.Column([
                # Название объекта и остаток
                ft.Row([
                    ft.Text(obj["name"], size=16, weight=ft.FontWeight.BOLD, color=colors["text"], expand=True),
                    ft.Container(
                        content=ft.Row([
                            ft.Text(str(obj["oxygen"]), size=12, color=colors["oxygen"], weight="bold"),
                            ft.Text(" | ", size=10, color=colors["text_secondary"]),
                            ft.Text(str(obj["propane"]), size=12, color=colors["propane"], weight="bold"),
                        ], spacing=4),
                        padding=4,
                        bgcolor=colors["background"],
                        border_radius=4
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=15),
                
                # Поля ввода (с цветным фоном)
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("КИСЛОРОД", size=14, weight=ft.FontWeight.W_600, color=colors["oxygen"]),
                            oxygen_input,
                            ft.Text(f"макс: {oxygen_req}", size=10, color=colors["text_secondary"]),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                        padding=12,
                        bgcolor=colors["oxygen_light"],
                        border_radius=8,
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("ПРОПАН", size=14, weight=ft.FontWeight.W_600, color=colors["propane"]),
                            propane_input,
                            ft.Text(f"макс: {propane_req}", size=10, color=colors["text_secondary"]),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                        padding=12,
                        bgcolor=colors["propane_light"],
                        border_radius=8,
                        expand=True
                    ),
                ], spacing=10),
                
                ft.Container(height=4),
                
                # Дата (без смайлика)
                ft.Row([
                    date_field,
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Container(height=4),
                
                # Кнопки
                plan_btn,
                ft.Container(height=4),
                complete_btn,
                
            ]),
            padding=15,
            margin=ft.margin.only(bottom=10),
            bgcolor=colors["surface"],
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=4, color="#D0D0D0"),
            width=page.width * 0.95 if page.width else 400,
        )
    
    # Собираем карточки
    object_cards = []
    for obj in objects:
        card = create_object_card(obj)
        if card:
            object_cards.append(card)
    
    if not object_cards:
        object_cards = [ft.Container(
            content=ft.Text("Нет активных заявок", color=colors["text_secondary"], size=14),
            padding=30,
            alignment=ft.alignment.center
        )]
    
    # Основной экран
    page.add(
        ft.Column([
            # Хедер
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        icon_color=colors["text_secondary"],
                        tooltip="Назад",
                        on_click=go_back
                    ) if from_senior or supplier.get("is_senior", False) else ft.Container(width=40),
                    
                    ft.Text("НГДУ «Нижнесортымскнефть»", size=16, weight=ft.FontWeight.BOLD, color=colors["primary"], expand=True, text_align=ft.TextAlign.CENTER),
                    
                    ft.IconButton(
                        icon=ft.icons.LOGOUT,
                        icon_color=colors["text_secondary"],
                        tooltip="Выход",
                        on_click=lambda e: show_login(page, dm)
                    )
                ]),
                padding=15,
                bgcolor=colors["surface"],
                border=ft.border.only(bottom=ft.BorderSide(1, colors["border"]))
            ),
            
            # Список объектов
            ft.Container(
                content=ft.Column([
                    ft.Text("ПОСТАВКИ", size=14, weight=ft.FontWeight.W_600, color=colors["secondary"]),
                    ft.Container(height=10),
                    ft.Column(object_cards, spacing=0)
                ]),
                padding=15,
                expand=True
            )
        ], spacing=0)
    )
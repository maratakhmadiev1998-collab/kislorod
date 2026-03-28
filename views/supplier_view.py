# views/supplier_view.py
import flet as ft
from colors_apple import colors
from datetime import datetime
import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from login_screen import show_login


def show_supplier_view(page, dm, supplier, from_senior=False):
    """Экран Снабженца: 1 экран, карточки как у мастера, 2 кнопки"""
    page.clean()
    objects = dm.get_all_objects()
    
    # === НАВИГАЦИЯ ===
    def go_back(e):
        from views.senior_view import show_senior_menu
        for senior in dm.users.get("senior_masters", []):
            if senior["name"] == supplier["name"]:
                show_senior_menu(page, dm, senior)
                return
        show_login(page, dm)
    
    def on_refresh():
        show_supplier_view(page, dm, supplier, from_senior)
    
    # === КАРТОЧКА ОБЪЕКТА ===
    def create_object_card(obj):
        # Получаем активные заявки
        requests = dm.get_active_requests(obj["id"])
        max_oxygen = next((r["quantity"] for r in requests if r["gas_type"] == "КИСЛОРОД"), 0)
        max_propane = next((r["quantity"] for r in requests if r["gas_type"] == "ПРОПАН"), 0)
        
        # Если нет заявок — не показываем карточку
        if max_oxygen == 0 and max_propane == 0:
            return None
        
        # Получаем запланированную поставку
        planned = dm.get_planned_deliveries(obj["id"])
        planned_o = next((d["quantity"] for d in planned if d["gas_type"] == "КИСЛОРОД"), 0)
        planned_p = next((d["quantity"] for d in planned if d["gas_type"] == "ПРОПАН"), 0)
        planned_date = planned[0]["planned_date"] if planned else datetime.now().strftime("%d.%m.%Y")
        has_planned = len(planned) > 0
        
        # Поля ввода (авто-заполнение: заявка или план)
        oxygen_input = ft.TextField(
            value=str(planned_o if has_planned else max_oxygen),
            width=90,
            height=60,
            text_align="center",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=colors["border"],
            bgcolor=colors["surface"],
            text_size=24,
            content_padding=10
        )
        
        propane_input = ft.TextField(
            value=str(planned_p if has_planned else max_propane),
            width=90,
            height=60,
            text_align="center",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=colors["border"],
            bgcolor=colors["surface"],
            text_size=24,
            content_padding=10
        )
        
        # Поле даты (авто-сегодня)
        date_input = ft.TextField(
            value=planned_date,
            width=120,
            height=45,
            text_align="center",
            text_size=16,
            border_color=colors["border"],
            bgcolor=colors["surface"]
        )
        
        # === ВАЛИДАЦИЯ ===
        def validate_oxygen(e):
            try:
                val = int(e.control.value) if e.control.value else 0
                if val < 0:
                    e.control.value = "0"
                elif val > max_oxygen:
                    e.control.value = str(max_oxygen)
                e.control.update()
            except:
                e.control.value = "0"
                e.control.update()
        
        def validate_propane(e):
            try:
                val = int(e.control.value) if e.control.value else 0
                if val < 0:
                    e.control.value = "0"
                elif val > max_propane:
                    e.control.value = str(max_propane)
                e.control.update()
            except:
                e.control.value = "0"
                e.control.update()
        
        def validate_date(e):
            try:
                input_date = datetime.strptime(e.control.value, "%d.%m.%Y")
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                if input_date < today:
                    e.control.value = today.strftime("%d.%m.%Y")
                e.control.update()
            except:
                e.control.value = datetime.now().strftime("%d.%m.%Y")
                e.control.update()
        
        oxygen_input.on_blur = validate_oxygen
        propane_input.on_blur = validate_propane
        date_input.on_blur = validate_date
        
        # === КНОПКИ ===
        def plan_delivery(e):
            try:
                o_new = int(oxygen_input.value) if oxygen_input.value else 0
                p_new = int(propane_input.value) if propane_input.value else 0
                new_date = date_input.value
                
                # Проверка даты
                try:
                    input_date = datetime.strptime(new_date, "%d.%m.%Y")
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    if input_date < today:
                        show_error(page, "Нельзя запланировать дату раньше сегодня")
                        return
                except:
                    show_error(page, "Неверный формат даты. Используйте ДД.ММ.ГГГГ")
                    return
                
                # Проверка количества
                if o_new > max_oxygen:
                    show_error(page, f"Максимум {max_oxygen} кислорода (по заявке)")
                    return
                if p_new > max_propane:
                    show_error(page, f"Максимум {max_propane} пропана (по заявке)")
                    return
                
                # Удаляем старый план
                dm.data["deliveries"] = [d for d in dm.data["deliveries"] if d["object_id"] != obj["id"]]
                
                # Создаём новый план
                if o_new > 0:
                    dm.add_delivery(obj["id"], "КИСЛОРОД", o_new, new_date, "Склад")
                if p_new > 0:
                    dm.add_delivery(obj["id"], "ПРОПАН", p_new, new_date, "Склад")
                
                dm.save_data()
                
                # Зелёная подсветка
                plan_button.bgcolor = colors["success"]
                plan_button.text = "✓ ЗАПЛАНИРОВАНО"
                page.update()
                
                def reset():
                    time.sleep(2)
                    plan_button.bgcolor = colors["accent"]
                    plan_button.text = "ЗАПЛАНИРОВАТЬ"
                    page.update()
                
                threading.Thread(target=reset, daemon=True).start()
                on_refresh()
                
            except Exception as ex:
                show_error(page, f"Ошибка: {ex}")
        
        def complete_delivery(e):
            try:
                planned = dm.get_planned_deliveries(obj["id"])
                if not planned:
                    show_error(page, "Сначала запланируйте поставку")
                    return
                
                o_planned = next((d["quantity"] for d in planned if d["gas_type"] == "КИСЛОРОД"), 0)
                p_planned = next((d["quantity"] for d in planned if d["gas_type"] == "ПРОПАН"), 0)
                
                # Удаляем план
                dm.data["deliveries"] = [d for d in dm.data["deliveries"] if d["object_id"] != obj["id"]]
                
                # Добавляем на склад
                for obj_item in dm.data["objects"]:
                    if obj_item["id"] == obj["id"]:
                        obj_item["oxygen"] += o_planned
                        obj_item["propane"] += p_planned
                        break
                
                # Уменьшаем заявки
                for req in dm.data["requests"]:
                    if req["object_id"] == obj["id"] and req["status"] == "active":
                        if req["gas_type"] == "КИСЛОРОД":
                            req["quantity"] -= o_planned
                        elif req["gas_type"] == "ПРОПАН":
                            req["quantity"] -= p_planned
                
                # Удаляем закрытые заявки
                dm.data["requests"] = [r for r in dm.data["requests"] 
                                      if not (r["object_id"] == obj["id"] and r["quantity"] <= 0)]
                
                dm.save_data()
                
                # Зелёная подсветка
                complete_button.bgcolor = colors["success"]
                complete_button.text = "✓ ВЫПОЛНЕНО"
                page.update()
                
                def reset():
                    time.sleep(2)
                    on_refresh()
                
                threading.Thread(target=reset, daemon=True).start()
                
            except Exception as ex:
                show_error(page, f"Ошибка: {ex}")
        
        # Кнопка ЗАПЛАНИРОВАТЬ
        plan_button = ft.ElevatedButton(
            "ЗАПЛАНИРОВАТЬ",
            on_click=plan_delivery,
            width=page.width * 0.9 if page.width else 350,
            height=45,
            style=ft.ButtonStyle(
                color="white",
                bgcolor=colors["accent"],
                shape=ft.RoundedRectangleBorder(radius=8)
            )
        )
        
        # Кнопка ВЫПОЛНИТЬ (активна только если есть план)
        complete_button = ft.ElevatedButton(
            "ВЫПОЛНИТЬ",
            on_click=complete_delivery,
            width=page.width * 0.9 if page.width else 350,
            height=45,
            style=ft.ButtonStyle(
                color="white",
                bgcolor=colors["success"] if has_planned else colors["text_secondary"],
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            disabled=not has_planned
        )
        
        return ft.Container(
            content=ft.Column([
                # Название объекта + остатки
                ft.Row([
                    ft.Text(obj["name"], size=16, weight=ft.FontWeight.BOLD, color=colors["text"], expand=True),
                    ft.Container(
                        content=ft.Row([
                            ft.Text(str(obj["oxygen"]), size=12, color=colors["oxygen"], weight="bold"),
                            ft.Text(" | ", size=12, color=colors["text_secondary"]),
                            ft.Text(str(obj["propane"]), size=12, color=colors["propane"], weight="bold"),
                        ], spacing=4),
                        padding=4,
                        bgcolor=colors["background"],
                        border_radius=4
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=15),
                
                # Поля ввода
                ft.Row([
                    ft.Column([
                        ft.Text("КИСЛОРОД", size=14, weight=ft.FontWeight.W_600, color=colors["oxygen"]),
                        ft.Text(f"макс: {max_oxygen}", size=10, color=colors["text_secondary"]),
                        oxygen_input,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                    ft.Column([
                        ft.Text("ПРОПАН", size=14, weight=ft.FontWeight.W_600, color=colors["propane"]),
                        ft.Text(f"макс: {max_propane}", size=10, color=colors["text_secondary"]),
                        propane_input,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ], spacing=10),
                
                ft.Container(height=10),
                
                # Дата
                ft.Row([
                    ft.Text("📅", size=16),
                    date_input,
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Container(height=15),
                
                # Кнопки
                plan_button,
                ft.Container(height=8),
                complete_button,
                
            ]),
            padding=15,
            margin=ft.margin.only(bottom=10, left=16, right=16),
            bgcolor=colors["surface"],
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, color="#10000000", offset=ft.Offset(0, 2))
        )
    
    # === СБОРКА КАРТОЧЕК ===
    object_cards = [card for obj in objects if (card := create_object_card(obj))]
    
    if not object_cards:
        object_cards = [ft.Container(
            content=ft.Text("Нет активных заявок", size=16, color=colors["text_secondary"]),
            padding=30,
            alignment=ft.alignment.center
        )]
    
    # === ЭКРАН ===
    page.add(
        ft.Column([
            # Хедер
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.IconButton(icon=ft.icons.ARROW_BACK, icon_size=20, icon_color=colors["text_secondary"],
                                    tooltip="Назад", on_click=go_back)
                    ]) if from_senior or supplier.get("is_senior", False) else ft.Container(),
                    ft.Row([
                        ft.Text("НГДУ «Нижнесортымскнефть»", size=14, weight=ft.FontWeight.W_600,
                               color=colors["text"], expand=True),
                        ft.Row([
                            ft.IconButton(icon=ft.icons.REFRESH, icon_size=20, icon_color=colors["text_secondary"],
                                        tooltip="Обновить", on_click=lambda e: on_refresh()),
                            ft.IconButton(icon=ft.icons.LOGOUT, icon_size=20, icon_color=colors["text_secondary"],
                                        tooltip="Выйти", on_click=lambda e: show_login(page, dm))
                        ], spacing=0)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ]),
                padding=ft.padding.only(top=10, bottom=10, left=10, right=10),
                bgcolor=colors["surface"],
                border=ft.border.only(bottom=ft.BorderSide(1, colors["separator"]))
            ),
            
            # Список объектов
            ft.Container(
                content=ft.Column([
                    ft.Container(height=10),
                    ft.Text(f"ОБЪЕКТОВ: {len(object_cards)}", size=12, color=colors["text_secondary"], weight=ft.FontWeight.W_600),
                    ft.Container(height=10),
                ] + object_cards),
                padding=16,
                expand=True
            )
        ], spacing=0)
    )


def show_error(page, message):
    """Диалог ошибки"""
    def close_error(e):
        if page.dialog:
            page.dialog.open = False
            page.dialog = None
            page.update()
    
    if page.dialog:
        page.dialog.open = False
        page.dialog = None
    
    page.dialog = ft.AlertDialog(
        title=ft.Text("Ошибка", color=colors["danger"], size=18, weight=ft.FontWeight.W_600),
        content=ft.Text(message, size=14),
        actions=[ft.TextButton("OK", on_click=close_error, style=ft.ButtonStyle(color=colors["accent"]))],
        shape=ft.RoundedRectangleBorder(radius=12)
    )
    page.dialog.open = True
    page.update()
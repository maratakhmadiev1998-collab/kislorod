# views/supplier_view.py
import flet as ft
from colors_apple import colors
from datetime import datetime, timedelta
import sys
import os

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from login_screen import show_login

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def card(content):
    """Парящая карточка в стиле iOS"""
    return ft.Container(
        content=content,
        bgcolor=colors["surface"],
        border_radius=12,
        shadow=ft.BoxShadow(blur_radius=8, color="#10000000", offset=ft.Offset(0, 2)),
        padding=16,
        margin=ft.margin.only(bottom=8, left=16, right=16)
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


def plan_delivery(page, dm, obj, on_refresh):
    """Диалог планирования поставки"""
    existing = dm.get_planned_deliveries(obj["id"])
    
    requests = dm.get_active_requests(obj["id"])
    max_o = next((r["quantity"] for r in requests if r["gas_type"] == "КИСЛОРОД"), 0)
    max_p = next((r["quantity"] for r in requests if r["gas_type"] == "ПРОПАН"), 0)
    
    o_val = 0
    p_val = 0
    date_val = datetime.now().strftime("%d.%m.%Y")
    
    if existing:
        o_delivery = next((d for d in existing if d["gas_type"] == "КИСЛОРОД"), None)
        p_delivery = next((d for d in existing if d["gas_type"] == "ПРОПАН"), None)
        o_val = o_delivery["quantity"] if o_delivery else 0
        p_val = p_delivery["quantity"] if p_delivery else 0
        date_val = existing[0]["planned_date"]
    else:
        o_val = max_o
        p_val = max_p
    
    o_qty = ft.TextField(value=str(o_val), width=70, height=45, text_align="center",
                         keyboard_type=ft.KeyboardType.NUMBER, border_color=colors["separator"],
                         focused_border_color=colors["accent"], text_size=20)
    
    p_qty = ft.TextField(value=str(p_val), width=70, height=45, text_align="center",
                         keyboard_type=ft.KeyboardType.NUMBER, border_color=colors["separator"],
                         focused_border_color=colors["accent"], text_size=20)
    
    date_field = ft.TextField(value=date_val, width=120, height=40, text_align="center",
                              text_size=14, border_color=colors["separator"])
    
    def save_plan(e):
        try:
            o_new = int(o_qty.value) if o_qty.value else 0
            p_new = int(p_qty.value) if p_qty.value else 0
            new_date = date_field.value
            
            try:
                datetime.strptime(new_date, "%d.%m.%Y")
            except:
                show_error(page, "Неверный формат даты. Используйте ДД.ММ.ГГГГ")
                return
            
            if o_new > max_o:
                show_error(page, f"Максимум {max_o} кислорода")
                return
            if p_new > max_p:
                show_error(page, f"Максимум {max_p} пропана")
                return
            if o_new < 0 or p_new < 0:
                show_error(page, "Количество не может быть отрицательным")
                return
            
            dm.data["deliveries"] = [d for d in dm.data["deliveries"] if d["object_id"] != obj["id"]]
            
            if o_new > 0:
                dm.add_delivery(obj["id"], "КИСЛОРОД", o_new, new_date, "Склад")
            if p_new > 0:
                dm.add_delivery(obj["id"], "ПРОПАН", p_new, new_date, "Склад")
            
            page.stay_on_deliveries = False
            on_refresh()
            
        except Exception as ex:
            show_error(page, f"Ошибка: {ex}")
    
    def close_plan(e):
        if page.dialog:
            page.dialog.open = False
            page.dialog = None
            page.update()
    
    content = ft.Column([
        ft.Text(obj["name"], size=18, weight=ft.FontWeight.W_600),
        ft.Container(height=15),
        ft.Row([
            ft.Column([ft.Text("КИСЛОРОД", size=12, color=colors["oxygen"]), o_qty,
                      ft.Text(f"макс:{max_o}", size=10, color=colors["text_secondary"])],
                     horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([ft.Text("ПРОПАН", size=12, color=colors["propane"]), p_qty,
                      ft.Text(f"макс:{max_p}", size=10, color=colors["text_secondary"])],
                     horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
        ft.Container(height=10),
        ft.Row([date_field], alignment=ft.MainAxisAlignment.CENTER)
    ])
    
    page.dialog = ft.AlertDialog(
        title=ft.Text("Планирование поставки", size=18, weight=ft.FontWeight.W_600),
        content=ft.Container(content=content, padding=10, width=320),
        actions=[
            ft.TextButton("Отмена", on_click=close_plan),
            ft.ElevatedButton("Сохранить", on_click=save_plan,
                            style=ft.ButtonStyle(color="white", bgcolor=colors["accent"]))
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=12)
    )
    page.dialog.open = True
    page.update()


def complete_delivery(page, dm, obj_id, on_refresh):
    """Выполнить поставку"""
    try:
        object_deliveries = [d for d in dm.get_planned_deliveries() if d["object_id"] == obj_id]
        if not object_deliveries:
            return
        
        o_planned = next((d["quantity"] for d in object_deliveries if d["gas_type"] == "КИСЛОРОД"), 0)
        p_planned = next((d["quantity"] for d in object_deliveries if d["gas_type"] == "ПРОПАН"), 0)
        
        for d in object_deliveries:
            dm.data["deliveries"] = [del_item for del_item in dm.data["deliveries"] if del_item["id"] != d["id"]]
        
        for obj_item in dm.data["objects"]:
            if obj_item["id"] == obj_id:
                obj_item["oxygen"] += o_planned
                obj_item["propane"] += p_planned
                break
        
        for req in dm.data["requests"]:
            if req["object_id"] == obj_id and req["status"] == "active":
                if req["gas_type"] == "КИСЛОРОД":
                    req["quantity"] -= o_planned
                elif req["gas_type"] == "ПРОПАН":
                    req["quantity"] -= p_planned
        
        dm.data["requests"] = [r for r in dm.data["requests"] 
                              if not (r["object_id"] == obj_id and r["quantity"] <= 0)]
        
        dm.save_data()
        page.stay_on_deliveries = True
        on_refresh()
        
    except Exception as ex:
        show_error(page, f"Ошибка выполнения: {ex}")


# === ОСНОВНАЯ ФУНКЦИЯ ===

def show_supplier_view(page, dm, supplier, from_senior=False):
    """Экран Снабженца: Заявки → Поставки"""
    if page.dialog:
        page.dialog.open = False
        page.dialog = None
        page.update()
    
    page.clean()
    objects = dm.get_all_objects()
    
    # Хранилище черновиков
    if not hasattr(page, 'request_drafts'):
        page.request_drafts = {}
    
    # === НАВИГАЦИЯ ===
    def go_back(e):
        from views.senior_view import show_senior_menu
        for senior in dm.users.get("senior_masters", []):
            if senior["name"] == supplier["name"]:
                show_senior_menu(page, dm, senior)
                return
        from login_screen import show_login
        show_login(page, dm)
    
    def on_refresh():
        show_supplier_view(page, dm, supplier, from_senior)
    
    # === ЧЕРНОВИКИ ===
    def create_or_update_draft(obj_id):
        obj = next((o for o in objects if o["id"] == obj_id), None)
        if obj:
            requests = dm.get_active_requests(obj_id)
            oxygen_req = next((r["quantity"] for r in requests if r["gas_type"] == "КИСЛОРОД"), 0)
            propane_req = next((r["quantity"] for r in requests if r["gas_type"] == "ПРОПАН"), 0)
            has_planned = len(dm.get_planned_deliveries(obj_id)) > 0
            
            if obj_id not in page.request_drafts:
                page.request_drafts[obj_id] = {
                    "object_id": obj_id,
                    "oxygen": oxygen_req,
                    "propane": propane_req,
                    "date": datetime.now().strftime("%d.%m.%Y"),
                    "has_planned": has_planned
                }
            else:
                page.request_drafts[obj_id]["has_planned"] = has_planned
                page.request_drafts[obj_id]["oxygen"] = oxygen_req
                page.request_drafts[obj_id]["propane"] = propane_req
    
    def update_draft(obj_id, gas_type, delta):
        if obj_id in page.request_drafts:
            requests = dm.get_active_requests(obj_id)
            if gas_type == "КИСЛОРОД":
                current = page.request_drafts[obj_id]["oxygen"]
                max_val = next((r["quantity"] for r in requests if r["gas_type"] == "КИСЛОРОД"), 0)
                new_val = current + delta
                if 0 <= new_val <= max_val:
                    page.request_drafts[obj_id]["oxygen"] = new_val
            else:
                current = page.request_drafts[obj_id]["propane"]
                max_val = next((r["quantity"] for r in requests if r["gas_type"] == "ПРОПАН"), 0)
                new_val = current + delta
                if 0 <= new_val <= max_val:
                    page.request_drafts[obj_id]["propane"] = new_val
            on_refresh()
    
    def change_date(obj_id, delta):
        if obj_id in page.request_drafts:
            try:
                current = datetime.strptime(page.request_drafts[obj_id]["date"], "%d.%m.%Y")
                new_date = current + timedelta(days=delta)
                if new_date.date() >= datetime.now().date():
                    page.request_drafts[obj_id]["date"] = new_date.strftime("%d.%m.%Y")
                    on_refresh()
            except:
                pass
    
    def send_to_deliveries(obj_id):
        if obj_id in page.request_drafts:
            draft = page.request_drafts[obj_id]
            dm.data["deliveries"] = [d for d in dm.data["deliveries"] if d["object_id"] != obj_id]
            if draft["oxygen"] > 0:
                dm.add_delivery(obj_id, "КИСЛОРОД", draft["oxygen"], draft["date"], "Склад")
            if draft["propane"] > 0:
                dm.add_delivery(obj_id, "ПРОПАН", draft["propane"], draft["date"], "Склад")
            draft["has_planned"] = True
            dm.save_data()
            on_refresh()
    
    # === КАРТОЧКА ЗАЯВКИ ===
    def create_request_row(obj):
        requests = dm.get_active_requests(obj["id"])
        oxygen_req = next((r["quantity"] for r in requests if r["gas_type"] == "КИСЛОРОД"), 0)
        propane_req = next((r["quantity"] for r in requests if r["gas_type"] == "ПРОПАН"), 0)
        
        if oxygen_req == 0 and propane_req == 0:
            return None
        
        create_or_update_draft(obj["id"])
        draft = page.request_drafts.get(obj["id"])
        if not draft:
            return None
        
        def on_plan(e):
            plan_delivery(page, dm, obj, on_refresh)
        
        return card(
            ft.Column([
                ft.Row([
                    ft.Text(obj["name"], size=16, weight=ft.FontWeight.W_600, color=colors["text"], expand=True),
                    ft.Row([
                        ft.Text(str(obj["oxygen"]), size=13, color=colors["oxygen"], weight=ft.FontWeight.W_600),
                        ft.Text(str(obj["propane"]), size=13, color=colors["propane"], weight=ft.FontWeight.W_600),
                    ], spacing=8)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=8),
                ft.Row([
                    ft.Column([
                        ft.Text("КИСЛОРОД", size=11, color=colors["text_secondary"]),
                        ft.Text(str(draft["oxygen"]), size=24, weight=ft.FontWeight.W_600, color=colors["oxygen"]),
                        ft.Text(f"макс:{oxygen_req}", size=9, color=colors["text_secondary"]),
                        ft.Row([
                            ft.IconButton(icon=ft.icons.REMOVE_CIRCLE, icon_size=24, icon_color=colors["accent"],
                                        on_click=lambda e: update_draft(obj["id"], "КИСЛОРОД", -1)),
                            ft.IconButton(icon=ft.icons.ADD_CIRCLE, icon_size=24, icon_color=colors["accent"],
                                        on_click=lambda e: update_draft(obj["id"], "КИСЛОРОД", 1)),
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                    ft.Column([
                        ft.Text("ПРОПАН", size=11, color=colors["text_secondary"]),
                        ft.Text(str(draft["propane"]), size=24, weight=ft.FontWeight.W_600, color=colors["propane"]),
                        ft.Text(f"макс:{propane_req}", size=9, color=colors["text_secondary"]),
                        ft.Row([
                            ft.IconButton(icon=ft.icons.REMOVE_CIRCLE, icon_size=24, icon_color=colors["accent"],
                                        on_click=lambda e: update_draft(obj["id"], "ПРОПАН", -1)),
                            ft.IconButton(icon=ft.icons.ADD_CIRCLE, icon_size=24, icon_color=colors["accent"],
                                        on_click=lambda e: update_draft(obj["id"], "ПРОПАН", 1)),
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Container(height=10),
                ft.Row([
                    ft.IconButton(icon=ft.icons.ARROW_LEFT, icon_size=24, icon_color=colors["accent"],
                                on_click=lambda e: change_date(obj["id"], -1)),
                    ft.Container(
                        content=ft.Text(draft["date"], size=16, weight=ft.FontWeight.W_500),
                        padding=8, bgcolor=colors["surface"], border=ft.border.all(1, colors["separator"]), border_radius=8
                    ),
                    ft.IconButton(icon=ft.icons.ARROW_RIGHT, icon_size=24, icon_color=colors["accent"],
                                on_click=lambda e: change_date(obj["id"], 1)),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),
                ft.Container(
                    content=ft.ElevatedButton("ЗАПЛАНИРОВАТЬ", on_click=on_plan,
                                            width=page.width * 0.9 if page.width else 350, height=45,
                                            style=ft.ButtonStyle(color="white", bgcolor=colors["accent"],
                                                                shape=ft.RoundedRectangleBorder(radius=8))),
                    alignment=ft.alignment.center
                )
            ])
        )
    
    # === КАРТОЧКА ПОСТАВКИ ===
    def create_delivery_row(obj_id):
        obj = next((o for o in objects if o["id"] == obj_id), None)
        if not obj:
            return None
        
        obj_deliveries = [d for d in dm.get_planned_deliveries() if d["object_id"] == obj_id]
        if not obj_deliveries:
            return None
        
        o_planned = next((d["quantity"] for d in obj_deliveries if d["gas_type"] == "КИСЛОРОД"), 0)
        p_planned = next((d["quantity"] for d in obj_deliveries if d["gas_type"] == "ПРОПАН"), 0)
        
        def on_complete(e):
            complete_delivery(page, dm, obj_id, on_refresh)
        
        return card(
            ft.Column([
                ft.Row([
                    ft.Text(obj["name"], size=16, weight=ft.FontWeight.W_600, color=colors["text"], expand=True),
                    ft.Row([
                        ft.Text(str(obj["oxygen"]), size=13, color=colors["oxygen"], weight=ft.FontWeight.W_600),
                        ft.Text(str(obj["propane"]), size=13, color=colors["propane"], weight=ft.FontWeight.W_600),
                    ], spacing=8)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=8),
                ft.Row([
                    ft.Column([
                        ft.Text("КИСЛОРОД", size=11, color=colors["text_secondary"]),
                        ft.Text(str(o_planned), size=24, weight=ft.FontWeight.W_600, color=colors["oxygen"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                    ft.Column([
                        ft.Text("ПРОПАН", size=11, color=colors["text_secondary"]),
                        ft.Text(str(p_planned), size=24, weight=ft.FontWeight.W_600, color=colors["propane"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Container(height=10),
                ft.Container(
                    content=ft.ElevatedButton("ВЫПОЛНИТЬ", on_click=on_complete,
                                            width=page.width * 0.9 if page.width else 350, height=45,
                                            style=ft.ButtonStyle(color="white", bgcolor=colors["success"],
                                                                shape=ft.RoundedRectangleBorder(radius=8))),
                    alignment=ft.alignment.center
                )
            ])
        )
    
    # === СБОРКА КОНТЕНТА ===
    requests_content = [row for obj in objects if (row := create_request_row(obj))]
    
    all_planned = dm.get_planned_deliveries()
    unique_objects = set(d["object_id"] for d in all_planned)
    deliveries_content = [row for obj_id in unique_objects if (row := create_delivery_row(obj_id))]
    
    if not deliveries_content:
        deliveries_content = [ft.Container(content=ft.Text("Нет активных поставок", color=colors["text_secondary"]),
                                          padding=30, alignment=ft.alignment.center)]
    
    selected_index = 1 if hasattr(page, 'stay_on_deliveries') and page.stay_on_deliveries else 0
    
    tabs = ft.Tabs(
        selected_index=selected_index,
        tabs=[
            ft.Tab(text=f"ЗАЯВКИ ({len(requests_content)})",
                  content=ft.Container(content=ft.Column([ft.Container(height=10), ft.Column(requests_content)]),
                                      padding=0, bgcolor=colors["background"])),
            ft.Tab(text=f"ПОСТАВКИ ({len(unique_objects)})",
                  content=ft.Container(content=ft.Column([ft.Container(height=10), ft.Column(deliveries_content)]),
                                      padding=0, bgcolor=colors["background"]))
        ],
        expand=1
    )
    
    # === ЭКРАН ===
    page.add(
        ft.Column([
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
                            ft.TextButton(  # ✅ ИСПРАВЛЕНО: LOGOUT → TextButton
                                "Выход",
                                color=colors["text_secondary"],
                                on_click=lambda e: show_login(page, dm)
                            )
                        ], spacing=0)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ]),
                padding=ft.padding.only(top=10, bottom=10, left=10, right=10),
                bgcolor=colors["surface"],
                border=ft.border.only(bottom=ft.BorderSide(1, colors["separator"]))
            ),
            tabs
        ], spacing=0)
    )
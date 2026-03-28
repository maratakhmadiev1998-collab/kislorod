# views/master_view.py
import flet as ft
from colors_apple import colors
import sys
import os
import threading
import time

# Добавляем корень проекта в путь (чтобы работали импорты из views/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def show_master_view(page, dm, master, from_senior=False):
    """Экран Мастера: объекты, заявки, отправка"""
    page.clean()
    
    # Если зашел через старшего мастера - показываем все объекты
    if from_senior or master.get("is_senior", False):
        objects = dm.get_all_objects()
    else:
        objects = dm.get_objects_for_master(master["id"])
    
    if not objects:
        page.add(ft.Text("Нет доступных объектов", color=colors["danger"]))
        return
    
    # === НАВИГАЦИЯ ===
    def go_back(e):
        from views.senior_view import show_senior_menu
        for senior in dm.users.get("senior_masters", []):
            if senior["name"] == master["name"]:
                show_senior_menu(page, dm, senior)
                return
        from login_screen import show_login
        show_login(page, dm)
    
    def go_home(e):
        from login_screen import show_login
        show_login(page, dm)
    
    # === ОТПРАВКА ЗАЯВКИ ===
    def send_all_requests(obj, oxygen_input, propane_input, oxygen_text, propane_text):
        try:
            o_new = int(oxygen_input.value) if oxygen_input.value and oxygen_input.value.strip() else 0
            p_new = int(propane_input.value) if propane_input.value and propane_input.value.strip() else 0
            
            # Находим все активные заявки для этого объекта
            all_active = [r for r in dm.data["requests"] if r["status"] == "active"]
            obj_requests = [r for r in all_active if r["object_id"] == obj["id"]]
            
            # Определяем создателя заявки (бригада)
            if obj_requests:
                creator_name = obj_requests[0]["created_by"]
            else:
                creator_name = master["name"]
            
            # Получаем СТАРЫЕ заявки этой бригады для этого объекта
            old_requests = [r for r in dm.data["requests"] 
                           if r["created_by"] == creator_name 
                           and r["object_id"] == obj["id"] 
                           and r["status"] == "active"]
            
            old_o = 0
            old_p = 0
            
            for req in old_requests:
                if req["gas_type"] == "КИСЛОРОД":
                    old_o = req["quantity"]
                elif req["gas_type"] == "ПРОПАН":
                    old_p = req["quantity"]
            
            # ВЫЧИСЛЯЕМ доступное количество (факт + старая заявка)
            available_oxygen = obj["oxygen"] + old_o
            available_propane = obj["propane"] + old_p
            
            # ПРОВЕРКА: нельзя заказать больше чем доступно
            if o_new > available_oxygen or p_new > available_propane or o_new < 0 or p_new < 0:
                oxygen_input.bgcolor = colors["danger_light"]
                propane_input.bgcolor = colors["danger_light"]
                page.update()
                
                def reset():
                    time.sleep(2)
                    oxygen_input.bgcolor = colors["surface"]
                    propane_input.bgcolor = colors["surface"]
                    page.update()
                threading.Thread(target=reset, daemon=True).start()
                return
            
            # ВОЗВРАЩАЕМ старые значения в остаток
            obj["oxygen"] = available_oxygen
            obj["propane"] = available_propane
            
            # ВЫЧИТАЕМ новые значения
            obj["oxygen"] = obj["oxygen"] - o_new
            obj["propane"] = obj["propane"] - p_new
            
            # Удаляем ТОЛЬКО заявки этой бригады для этого объекта
            dm.data["requests"] = [r for r in dm.data["requests"] 
                                  if not (r["created_by"] == creator_name 
                                         and r["object_id"] == obj["id"] 
                                         and r["status"] == "active")]
            
            # Создаем новые заявки от имени бригады
            if o_new > 0:
                dm.add_request(obj["id"], "КИСЛОРОД", o_new, creator_name)
            if p_new > 0:
                dm.add_request(obj["id"], "ПРОПАН", p_new, creator_name)
            
            # Обновляем отображение
            oxygen_text.value = str(obj["oxygen"])
            propane_text.value = str(obj["propane"])
            
            # Подсветка успеха
            oxygen_input.bgcolor = colors["success_light"]
            propane_input.bgcolor = colors["success_light"]
            
            dm.save_data()
            page.update()
            
            def reset():
                time.sleep(2)
                oxygen_input.bgcolor = colors["surface"]
                propane_input.bgcolor = colors["surface"]
                page.update()
            
            threading.Thread(target=reset, daemon=True).start()
            
        except Exception as e:
            print(f"Ошибка: {e}")
            import traceback
            traceback.print_exc()
    
    # === ВАЛИДАЦИЯ КИСЛОРОДА ===
    def validate_oxygen(e, obj):
        try:
            val = int(e.control.value) if e.control.value and e.control.value.strip() else 0
            all_active = [r for r in dm.data["requests"] if r["status"] == "active"]
            obj_requests = [r for r in all_active if r["object_id"] == obj["id"]]
            
            old_o = 0
            for req in obj_requests:
                if req["gas_type"] == "КИСЛОРОД":
                    old_o = req["quantity"]
            
            available = obj["oxygen"] + old_o
            if val > available:
                e.control.value = str(available)
            elif val < 0:
                e.control.value = "0"
            e.control.update()
        except:
            e.control.value = "0"
            e.control.update()
    
    # === ВАЛИДАЦИЯ ПРОПАНА ===
    def validate_propane(e, obj):
        try:
            val = int(e.control.value) if e.control.value and e.control.value.strip() else 0
            all_active = [r for r in dm.data["requests"] if r["status"] == "active"]
            obj_requests = [r for r in all_active if r["object_id"] == obj["id"]]
            
            old_p = 0
            for req in obj_requests:
                if req["gas_type"] == "ПРОПАН":
                    old_p = req["quantity"]
            
            available = obj["propane"] + old_p
            if val > available:
                e.control.value = str(available)
            elif val < 0:
                e.control.value = "0"
            e.control.update()
        except:
            e.control.value = "0"
            e.control.update()
    
    # === КАРТОЧКА ОБЪЕКТА ===
    def create_object_card(obj):
        # ✅ ПОКАЗЫВАЕМ ВСЕ активные заявки ЭТОГО ОБЪЕКТА (не фильтруем по мастеру)
        # Чтобы мастер видел заявку старшего
        active_requests = [r for r in dm.data["requests"] 
                          if r["object_id"] == obj["id"] and r["status"] == "active"]
        
        # Берём ПЕРВУЮ заявку каждого типа (не суммируем!)
        oxygen_req = 0
        propane_req = 0
        
        for req in active_requests:
            if req["gas_type"] == "КИСЛОРОД" and oxygen_req == 0:  # ✅ Берём первую, не суммируем
                oxygen_req = req["quantity"]
            elif req["gas_type"] == "ПРОПАН" and propane_req == 0:  # ✅ Берём первую, не суммируем
                propane_req = req["quantity"]
        
        # Текст для отображения физического остатка
        oxygen_text = ft.Text(str(obj["oxygen"]), size=12, color=colors["oxygen"], weight="bold")
        propane_text = ft.Text(str(obj["propane"]), size=12, color=colors["propane"], weight="bold")
        
        # Поля ввода
        oxygen_input = ft.TextField(
            value=str(oxygen_req),
            width=90,
            height=60,
            text_align="center",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=colors["border"],
            bgcolor=colors["surface"],
            text_size=24,
            content_padding=10,
            on_blur=lambda e, o=obj: validate_oxygen(e, o)
        )
        
        propane_input = ft.TextField(
            value=str(propane_req),
            width=90,
            height=60,
            text_align="center",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=colors["border"],
            bgcolor=colors["surface"],
            text_size=24,
            content_padding=10,
            on_blur=lambda e, o=obj: validate_propane(e, o)
        )
        
        # Контейнеры с полями
        oxygen_field = ft.Container(
            content=ft.Column([
                ft.Text("КИСЛОРОД", size=14, weight=ft.FontWeight.W_600, color=colors["oxygen"]),
                oxygen_input
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=12,
            bgcolor=colors["oxygen_light"],
            border_radius=8,
            expand=True
        )
        
        propane_field = ft.Container(
            content=ft.Column([
                ft.Text("ПРОПАН", size=14, weight=ft.FontWeight.W_600, color=colors["propane"]),
                propane_input
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=12,
            bgcolor=colors["propane_light"],
            border_radius=8,
            expand=True
        )
        
        # Планируемые поставки
        planned = dm.get_planned_deliveries(obj["id"])
        planned_info = []
        for p in planned:
            planned_info.append(
                ft.Container(
                    content=ft.Text(f"План: {p['gas_type']} {p['quantity']} балл. на {p['planned_date']}", 
                                   size=12, color=colors["warning"]),
                    padding=5,
                    bgcolor=colors["warning_light"],
                    border_radius=4,
                    margin=ft.margin.only(bottom=3)
                )
            )
        
        return ft.Container(
            content=ft.Column([
                # Название объекта и физический остаток
                ft.Row([
                    ft.Text(obj["name"], size=16, weight=ft.FontWeight.BOLD, color=colors["text"], expand=True),
                    # ✅ Убрал "Факт:" — только цифры
                    ft.Container(
                        content=ft.Row([
                            oxygen_text,
                            ft.Text(" | ", size=10, color=colors["text_secondary"]),
                            propane_text,
                        ], spacing=4),
                        padding=4,
                        bgcolor=colors["background"],
                        border_radius=4
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=15),
                
                # Поля ввода
                ft.Row([
                    oxygen_field,
                    propane_field
                ], spacing=10),
                
                # Планируемые поставки
                ft.Column(planned_info) if planned_info else ft.Container(),
                
                ft.Container(height=10),
                
                # Кнопка на всю ширину
                ft.Container(
                    content=ft.ElevatedButton(
                        "ОТПРАВИТЬ ЗАЯВКУ",
                        on_click=lambda e, o=obj, 
                                       oi=oxygen_input, 
                                       pi=propane_input,
                                       ot=oxygen_text,
                                       pt=propane_text: 
                            send_all_requests(o, oi, pi, ot, pt),
                        width=page.width * 0.9 if page.width else 350,
                        height=45,
                        style=ft.ButtonStyle(
                            color="white",
                            bgcolor=colors["primary"],
                            shape=ft.RoundedRectangleBorder(radius=6)
                        )
                    ),
                    alignment=ft.alignment.center
                ),
                ft.Divider(height=20, color=colors["border"])
            ]),
            padding=15,
            margin=ft.margin.only(bottom=10),
            bgcolor=colors["surface"],
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=4, color="#D0D0D0")
        )
    
    # Собираем карточки
    object_cards = []
    for obj in objects:
        object_cards.append(create_object_card(obj))
    
    # Основной экран
    page.add(
        ft.Column([
            # Хедер
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        icon_color=colors["text_secondary"],
                        tooltip="Назад в меню",
                        on_click=go_back
                    ) if from_senior or master.get("is_senior", False) else ft.Container(width=40),
                    
                    ft.Text("НГДУ «Нижнесортымскнефть»", size=16, weight=ft.FontWeight.BOLD, color=colors["primary"], expand=True, text_align=ft.TextAlign.CENTER),
                    
                    ft.IconButton(icon=ft.icons.LOGOUT, icon_color=colors["text_secondary"], tooltip="Выход", on_click=go_home)
                ]),
                padding=15,
                bgcolor=colors["surface"],
                border=ft.border.only(bottom=ft.BorderSide(1, colors["border"]))
            ),
            # Список объектов
            ft.Container(
                content=ft.Column([
                    ft.Text("ОБЪЕКТЫ", size=14, weight=ft.FontWeight.W_600, color=colors["secondary"]),
                    ft.Container(height=10),
                    ft.Column(object_cards, spacing=0)
                ]),
                padding=15,
                expand=True
            )
        ], spacing=0)
    )
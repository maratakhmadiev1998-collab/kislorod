# views/senior_view.py
import flet as ft
from colors_apple import colors
import sys
import os

# Добавляем корень проекта в путь (чтобы работали импорты)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def show_senior_menu(page, dm, senior):
    """Меню Старшего мастера: Заявки / Поставки"""
    page.clean()
    
    # === НАВИГАЦИЯ ===
    def go_to_master(e):
        # Создаем временного мастера с доступом ко ВСЕМ объектам
        temp_master = {
            "id": 999,
            "name": senior["name"],
            "objects": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
            "is_senior": True  # Флаг что зашел через старшего
        }
        from views.master_view import show_master_view  # ← ИСПРАВЛЕНО
        show_master_view(page, dm, temp_master, from_senior=True)
    
    def go_to_supplier(e):
        # Создаем временного снабженца
        temp_supplier = {
            "id": 999,
            "name": senior["name"],
            "is_senior": True  # Флаг что зашел через старшего
        }
        from views.supplier_view import show_supplier_view  # ← ИСПРАВЛЕНО
        show_supplier_view(page, dm, temp_supplier, from_senior=True)
    
    def go_back(e):
        from login_screen import show_login  # ← ИСПРАВЛЕНО
        show_login(page, dm)
    
    # === КАРТОЧКА МЕНЮ ===
    def create_menu_card(icon, title, subtitle, on_click, icon_color):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=40, color=icon_color),
                ft.Container(height=10),
                ft.Text(title, size=20, weight=ft.FontWeight.W_600),
                ft.Text(subtitle, size=12, color=colors["text_secondary"]),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            width=280,
            padding=25,
            bgcolor=colors["surface"],
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, color="#10000000", offset=ft.Offset(0, 2)),
            on_click=on_click,
            ink=True
        )
    
    # === ОСНОВНОЙ ЭКРАН ===
    page.add(
        ft.Column([
            # Хедер
            ft.Container(
                content=ft.Row([
                    ft.Text("НГДУ «Нижнесортымскнефть»", size=18, weight=ft.FontWeight.W_600, color=colors["text"], expand=True),
                    ft.IconButton(icon=ft.icons.LOGOUT, icon_color=colors["text_secondary"], tooltip="Выйти из системы", on_click=go_back)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=20,
                bgcolor=colors["surface"],
                border=ft.border.only(bottom=ft.BorderSide(1, colors["separator"]))
            ),
            
            # Меню
            ft.Container(
                content=ft.Column([
                    ft.Container(height=40),
                    
                    # Кнопка ЗАЯВКИ (как мастер, все объекты)
                    create_menu_card(
                        ft.icons.FACT_CHECK,
                        "ЗАЯВКИ",
                        "все объекты",
                        go_to_master,
                        colors["primary"]
                    ),
                    
                    ft.Container(height=20),
                    
                    # Кнопка ПОСТАВКИ (как склад)
                    create_menu_card(
                        ft.icons.LOCAL_SHIPPING,
                        "ПОСТАВКИ",
                        "планирование и выполнение",
                        go_to_supplier,
                        colors["accent"]
                    ),
                    
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True
            )
        ])
    )
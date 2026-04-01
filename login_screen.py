# login_screen.py - Flet версия (ИСПРАВЛЕННАЯ)
import flet as ft
from colors_apple import colors

def show_login(page, dm):
    """Экран входа в систему"""
    page.clean()
    
    login_field = ft.TextField(label="Логин", width=280, border_color=colors["border"])
    password_field = ft.TextField(label="Пароль", width=280, password=True, border_color=colors["border"])
    error_text = ft.Text("", color=colors["danger"], size=14)
    
    def try_login(e):
        login = login_field.value
        password = password_field.value
        
        # === ПРОВЕРЯЕМ МАСТЕРОВ ===
        for master in dm.users.get("masters", []):
            if master["login"] == login and master["password"] == password:
                from views.master_view import show_master_view
                show_master_view(page, dm, master)
                return
        
        # === ПРОВЕРЯЕМ СНАБЖЕНЦЕВ ===
        for supplier in dm.users.get("suppliers", []):
            if supplier["login"] == login and supplier["password"] == password:
                from views.supplier_view import show_supplier_view
                show_supplier_view(page, dm, supplier)
                return
        
        # === ПРОВЕРЯЕМ СТАРШИХ МАСТЕРОВ ===
        for senior in dm.users.get("senior_masters", []):
            if senior["login"] == login and senior["password"] == password:
                from views.senior_view import show_senior_menu
                show_senior_menu(page, dm, senior)
                return
        
        # === ПРОВЕРЯЕМ НАЧАЛЬНИКОВ (вместо диспетчеров) ===
        for chief in dm.users.get("chiefs", []):
            if chief["login"] == login and chief["password"] == password:
                from views.chief_view import show_chief_menu
                show_chief_menu(page, dm, chief)
                return
        
        # === ЕСЛИ НИКТО НЕ НАЙДЕН ===
        error_text.value = "Неверный логин или пароль"
        page.update()
    
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Container(height=50),
                # Название организации
                ft.Text("НГДУ", size=28, weight=ft.FontWeight.BOLD, color=colors["primary"]),
                ft.Text("«Нижнесортымскнефть»", size=20, weight=ft.FontWeight.W_600, color=colors["primary"]),
                ft.Container(height=40),
                # Форма входа
                ft.Container(
                    content=ft.Column([
                        ft.Text("Вход в систему", size=18, weight=ft.FontWeight.W_500),
                        ft.Container(height=20),
                        login_field,
                        ft.Container(height=10),
                        password_field,
                        ft.Container(height=20),
                        ft.ElevatedButton(
                            "ВОЙТИ",
                            on_click=try_login,
                            width=280,
                            height=45,
                            style=ft.ButtonStyle(
                                color="white",
                                bgcolor=colors["primary"],
                                shape=ft.RoundedRectangleBorder(radius=8)
                            )
                        ),
                        error_text
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                    bgcolor=colors["surface"],
                    border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=10, color="#C0C0C0")
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True
        )
    )
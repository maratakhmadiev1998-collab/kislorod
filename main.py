# main.py - Flet версия (РАБОЧАЯ для 0.24.0)
import flet as ft
import os
import traceback
import sys
from data_manager import DataManager
from login_screen import show_login

# === НАСТРОЙКИ ===
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

def log(msg):
    """Логирование: всегда локально, на сервере только если DEBUG"""
    if DEBUG or "PORT" not in os.environ:
        print(f"[APP] {msg}")

def main(page: ft.Page):
    """Главная точка входа приложения"""
    try:
        log("Инициализация страницы...")
        
        # === БАЗОВЫЕ НАСТРОЙКИ СТРАНИЦЫ ===
        page.title = "Кислород"  # ✅ Это работает!
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.scroll = ft.ScrollMode.AUTO
        page.prevent_close = True
        
        # === МОБИЛЬНЫЕ НАСТРОЙКИ ===
        page.window_min_width = 320
        page.window_min_height = 500
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # ❌ УБРАЛ: page.run_javascript() не работает в 0.24.0
        # Оставил только client_storage (он работает)
        if page.web:
            page.client_storage.set("viewport_meta", 
                "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no")
        
        log("Создание DataManager...")
        dm = DataManager()
        
        # Лог статистики
        objects_count = len(dm.get_all_objects())
        masters_count = len(dm.users.get("masters", []))
        suppliers_count = len(dm.users.get("suppliers", []))
        seniors_count = len(dm.users.get("senior_masters", []))
        log(f"Загружено: {objects_count} объектов, {masters_count} мастеров, {suppliers_count} снабженцев, {seniors_count} старших")
        
        log("Показ экрана входа...")
        show_login(page, dm)
        log("Приложение запущено")
        
    except Exception as e:
        log(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        if DEBUG:
            traceback.print_exc()
        
        # ❌ УБРАЛ: Кнопка "Обновить" через page.reload() не работает
        # Просто показываем ошибку без кнопки
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.ERROR_OUTLINE, color="red", size=40),
                    ft.Text("Произошла ошибка при загрузке", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(str(e), size=12, color="grey", selectable=True),
                    ft.Text("Перезагрузите страницу вручную (F5)", color="grey", size=12)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=30,
                alignment=ft.alignment.center,
                expand=True
            )
        )


# === НАВИГАЦИЯ ===
# Все переходы через прямые импорты в view-файлах


# === ТОЧКА ЗАПУСКА ===
if __name__ == "__main__":
    print(">>> Запуск Flet приложения...")
    try:
        # Определяем режим запуска
        use_web_mode = "--web" in sys.argv or sys.platform == "android" or "PORT" in os.environ
        
        if use_web_mode:
            log("Запуск в веб-режиме (сервер / Android)")
            ft.app(
                target=main,
                view=ft.AppView.WEB_BROWSER,
                assets_dir=None,  # Отключаем assets для веба (если нет папки assets)
                port=int(os.environ.get("PORT", 8551)),  # ← Flet на порту 8551
                host="0.0.0.0",
                # ❌ УДАЛЕНО: upload_route (нет в 0.24.0)
                web_renderer="canvaskit"  # Более быстрый рендеринг
            )
        else:
            log("Запуск в десктоп-режиме")
            ft.app(
                target=main,
                view=ft.AppView.FLET_APP,
                assets_dir="assets",
                port=int(os.environ.get("PORT", 8551)),
                host="0.0.0.0"
            )
            
    except KeyboardInterrupt:
        print("\n>>> Приложение остановлено пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске: {e}")
        traceback.print_exc()
    print(">>> Завершение" )
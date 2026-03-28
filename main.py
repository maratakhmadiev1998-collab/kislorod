import flet as ft
import os
import traceback
import sys
from data_manager import DataManager
from login_screen import show_login

# Включаем подробное логирование для отладки на сервере
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

def log(msg):
    if DEBUG or "PORT" not in os.environ:  # Печатаем всегда локально
        print(f"[APP] {msg}")

def main(page: ft.Page):
    try:
        log("Инициализация страницы...")
        
        # Настройки страницы
        page.title = "НГДУ Нижнесортымскнефть"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.scroll = ft.ScrollMode.AUTO
        page.prevent_close = True  # Предотвращаем случайное закрытие
        
        # Адаптивный дизайн
        page.window_min_width = 320
        page.window_min_height = 500
        
        log("Создание DataManager...")
        dm = DataManager()
        
        objects_count = len(dm.get_all_objects())
        masters_count = len(dm.users.get("masters", []))
        log(f"Загружено: {objects_count} объектов, {masters_count} мастеров")
        
        log("Показ экрана входа...")
        show_login(page, dm)
        log("Приложение запущено")
        
    except Exception as e:
        log(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        if DEBUG:
            traceback.print_exc()
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.ERROR_OUTLINE, color="red", size=40),
                    ft.Text("Произошла ошибка при загрузке", weight=ft.FontWeight.BOLD),
                    ft.Text(str(e), size=12, color="grey"),
                    ft.ElevatedButton("Обновить", on_click=lambda e: page.reload())
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=30,
                alignment=ft.alignment.center
            )
        )


if __name__ == "__main__":
    print(">>> Запуск приложения...")
    try:
        # ✅ Определяем, нужно ли использовать веб-режим
        # -- флаг --web ИЛИ платформа Android
        use_web_mode = "--web" in sys.argv or sys.platform == "android"
        
        if use_web_mode:
            log("Запуск в веб-режиме (Android / --web флаг)")
            # Для веба: отключаем assets и нативный просмотрщик
            ft.app(
                target=main,
                view=ft.AppView.WEB_BROWSER,
                assets_dir=None,
                port=int(os.environ.get("PORT", 8550)),
                host="0.0.0.0"
            )
        else:
            log("Запуск в стандартном режиме (ПК)")
            # Для ПК: можно использовать стандартные настройки
            ft.app(
                target=main,
                view=ft.AppView.FLET_APP,  # Или WEB_BROWSER, если предпочитаете браузер
                assets_dir="assets",       # Папка с ресурсами (если есть)
                port=int(os.environ.get("PORT", 8550)),
                host="0.0.0.0"
            )
            
    except Exception as e:
        print(f"\n❌ Ошибка при запуске ft.app: {e}")
        traceback.print_exc()
    print(">>> Завершение")
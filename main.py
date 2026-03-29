# main.py - Flet версия (ПОЛНАЯ, ФИНАЛЬНАЯ + PWA для 0.24.0)
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
        page.title = "Кислород"  # ✅ ИЗМЕНИЛ: название для вкладки и PWA
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.scroll = ft.ScrollMode.AUTO
        page.prevent_close = True
        
        # === МОБИЛЬНЫЕ НАСТРОЙКИ ===
        page.window_min_width = 320
        page.window_min_height = 500
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # ✅ ИСПРАВЛЕНИЕ 1: PWA МЕТА-ТЕГИ ЧЕРЕЗ ft.Html (вместо page.meta_tags и run_javascript которые не работают в 0.24.0)
        page.add(
            ft.Html('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">'),
            ft.Html('<meta name="apple-mobile-web-app-capable" content="yes">'),
            ft.Html('<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'),
            ft.Html('<meta name="apple-mobile-web-app-title" content="Кислород">'),
            ft.Html('<meta name="theme-color" content="#007AFF">'),
            ft.Html('<meta name="format-detection" content="telephone=no">'),
        )
        
        # ✅ ИСПРАВЛЕНИЕ 2: АБСОЛЮТНЫЕ URL ДЛЯ СТАТИКИ (порт 8080 через nginx) + Service Worker через ft.Html
        page.add(
            ft.Html('<link rel="manifest" href="http://45.146.165.37:8080/static/manifest.json">'),
            ft.Html('<link rel="apple-touch-icon" href="http://45.146.165.37:8080/static/icon-192.png">'),
            ft.Html('''
            <script>
            if ("serviceWorker" in navigator) {
                navigator.serviceWorker.register("http://45.146.165.37:8080/static/sw.js")
                .then((reg) => console.log("✅ SW registered:", reg))
                .catch((err) => console.log("❌ SW error:", err));
            }
            </script>
            '''),
            ft.Html('''
            <style>
                html, body { -webkit-user-zoom: fixed !important; -webkit-text-size-adjust: 100% !important; }
                * { touch-action: manipulation !important; user-select: none !important; -webkit-tap-highlight-color: transparent !important; }
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; overscroll-behavior: none !important; margin: 0; padding: 0; width: 100vw; overflow-x: hidden; }
                button, .button, button[role="button"] { touch-action: manipulation !important; cursor: pointer !important; }
                input, textarea, [contenteditable] { user-select: text !important; touch-action: auto !important; font-size: 16px !important; }
            </style>
            ''')
        )
        
        # Запрет зума через JS (инъекция в веб-режиме) — ✅ ИСПРАВЛЕНИЕ 3: через ft.Html вместо run_javascript
        if page.web:
            page.client_storage.set("viewport_meta", 
                "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no")
            page.add(
                ft.Html('''
                <script>
                    document.querySelector('meta[name="viewport"]')?.setAttribute('content', 
                        'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
                    document.addEventListener('touchend', function(e) {
                        if (Date.now() - (window._lastTouchEnd || 0) <= 300) e.preventDefault();
                        window._lastTouchEnd = Date.now();
                    }, {passive: false});
                    document.addEventListener('gesturestart', function(e) { e.preventDefault(); }, {passive: false});
                </script>
                ''')
            )
        
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
        
        # ✅ ИСПРАВЛЕНИЕ 4: Кнопка "Обновить" через ft.Html + onclick (вместо page.reload() который не работает)
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.ERROR_OUTLINE, color="red", size=40),
                    ft.Text("Произошла ошибка при загрузке", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(str(e), size=12, color="grey", selectable=True),
                    ft.Html('<button onclick="location.reload()" style="background:#007AFF;color:white;border:none;padding:10px 20px;border-radius:8px;cursor:pointer">Обновить</button>')
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=30,
                alignment=ft.alignment.center,
                expand=True
            )
        )


# === НАВИГАЦИЯ: ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (если нужно) ===
# В Flet навигация работает через прямые вызовы функций, не через URL-роутинг.
# Все переходы реализованы внутри view-файлов через прямые импорты:
#   from views.master_view import show_master_view
#   show_master_view(page, dm, master)
# Это проще и надёжнее чем @ft.route() декораторы.


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
                assets_dir=None,  # ✅ Flet 0.24.0: None для веба
                port=int(os.environ.get("PORT", 8551)),
                host="0.0.0.0",
                web_renderer="canvaskit"
                # ❌ upload_route удалён (нет в 0.24.0)
            )
        else:
            log("Запуск в десктоп-режиме")
            ft.app(
                target=main,
                view=ft.AppView.FLET_APP,
                assets_dir=None,
                port=int(os.environ.get("PORT", 8551)),
                host="0.0.0.0"
            )
            
    except KeyboardInterrupt:
        print("\n>>> Приложение остановлено пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске: {e}")
        traceback.print_exc()
    print(">>> Завершение")
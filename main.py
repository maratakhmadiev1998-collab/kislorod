# main.py - Flet версия (АВТОВХОД + ФИКС ЗАГРУЗКИ для 0.24.0)
import flet as ft
import os
import traceback
import sys
from data_manager import DataManager
from login_screen import show_login

DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

def log(msg):
    if DEBUG or "PORT" not in os.environ:
        print(f"[APP] {msg}")

def main(page: ft.Page):
    try:
        log("Инициализация...")
        
        page.title = "Кислород"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.scroll = ft.ScrollMode.AUTO
        page.prevent_close = True
        page.window_min_width = 320
        page.window_min_height = 500
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # ✅ АВТОВХОД: проверяем токен (ДО загрузки DataManager)
        auth_token = page.client_storage.get("auth_token")
        user_id = page.client_storage.get("user_id")
        user_role = page.client_storage.get("user_role")
        
        # Если есть токен — сразу загружаем DataManager и перенаправляем
        if auth_token and user_id and user_role:
            log(f"Автовход: {user_role} {user_id}")
            dm = DataManager()
            
            if user_role == "master":
                for m in dm.users.get("masters", []):
                    if str(m.get("id")) == user_id:
                        from views.master_view import show_master_view
                        show_master_view(page, dm, m)
                        return
            elif user_role == "supplier":
                for s in dm.users.get("suppliers", []):
                    if str(s.get("id")) == user_id:
                        from views.supplier_view import show_supplier_view
                        show_supplier_view(page, dm, s)
                        return
            elif user_role == "senior":
                for s in dm.users.get("senior_masters", []):
                    if str(s.get("id")) == user_id:
                        from views.senior_view import show_senior_menu
                        show_senior_menu(page, dm, s)
                        return
            elif user_role == "chief":
                for c in dm.users.get("chiefs", []):
                    if str(c.get("id")) == user_id:
                        from views.chief_view import show_chief_menu
                        show_chief_menu(page, dm, c)
                        return
            
            # Токен есть, но пользователь не найден — сброс
            page.client_storage.delete("auth_token")
            page.client_storage.delete("user_id")
            page.client_storage.delete("user_role")
        
        # ✅ JS-ФИКСЫ ЧЕРЕЗ ft.Html (единственный способ в 0.24.0)
        if page.web:
            page.client_storage.set("viewport_meta", 
                "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no")
            
            # Добавляем скрипты через ft.Html
            page.add(
                # Service Worker
                ft.Html('''<script>
                if("serviceWorker" in navigator) {
                    navigator.serviceWorker.register("http://45.146.165.37:8080/static/sw.js")
                    .then(r=>console.log("SW OK:",r))
                    .catch(e=>console.log("SW ERR:",e));
                }
                </script>'''),
                
                # Авто-перезагрузка если загрузка > 10 сек
                ft.Html('''<script>
                window.addEventListener('load', function() {
                    setTimeout(function() {
                        var el = document.querySelector('.flet-app-loading, [class*="loading"]');
                        if(el) { console.log("⚠️ Reload >10s"); location.reload(); }
                    }, 10000);
                });
                </script>'''),
                
                # Перезагрузка при возврате в приложение
                ft.Html('''<script>
                document.addEventListener('visibilitychange', function() {
                    if(document.visibilityState === 'visible') {
                        console.log("✅ Visible — reload");
                        setTimeout(function(){ location.reload(); }, 500);
                    }
                });
                </script>'''),
                
                # Перезагрузка при восстановлении сети
                ft.Html('''<script>
                window.addEventListener('online', function() {
                    console.log("📡 Online — reload");
                    setTimeout(function(){ location.reload(); }, 500);
                });
                </script>''')
            )
        
        # Нет токена — обычная загрузка
        log("Создание DataManager...")
        dm = DataManager()
        
        objects_count = len(dm.get_all_objects())
        masters_count = len(dm.users.get("masters", []))
        suppliers_count = len(dm.users.get("suppliers", []))
        seniors_count = len(dm.users.get("senior_masters", []))
        log(f"Загружено: {objects_count} объектов, {masters_count} мастеров, {suppliers_count} снабженцев, {seniors_count} старших")
        
        log("Показ экрана входа...")
        show_login(page, dm)
        
    except Exception as e:
        log(f"❌ ОШИБКА: {e}")
        if DEBUG: traceback.print_exc()
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.ERROR_OUTLINE, color="red", size=40),
                    ft.Text("Ошибка загрузки", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(str(e), size=12, color="grey", selectable=True),
                    ft.Text("Перезагрузите страницу вручную", color="grey", size=12)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=30, alignment=ft.alignment.center, expand=True
            )
        )

if __name__ == "__main__":
    print(">>> Запуск...")
    try:
        use_web = "--web" in sys.argv or sys.platform == "android" or "PORT" in os.environ
        ft.app(
            target=main,
            view=ft.AppView.WEB_BROWSER if use_web else ft.AppView.FLET_APP,
            assets_dir=None,
            port=int(os.environ.get("PORT", 8551)),
            host="0.0.0.0",
            web_renderer="canvaskit"
        )
    except KeyboardInterrupt:
        print("\n>>> Остановлено")
    except Exception as e:
        print(f"\n❌ {e}")
        traceback.print_exc()
    print(">>> Завершение")
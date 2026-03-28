# views/chief_view.py - Экраны Начальника
import flet as ft

# === ЦВЕТА ===
C = {
    "primary": "#007AFF",
    "surface": "#FFFFFF",
    "background": "#F2F2F7",
    "text": "#000000",
    "text_secondary": "#666666",
    "border": "#C6C6C8",
    "success": "#34C759",
    "warning": "#FF9500",
    "danger": "#FF3B30",
    "oxygen": "#007AFF",
    "propane": "#FF9500",
}


def show_chief_menu(page: ft.Page, dm, chief):
    """Меню Начальника: Объекты / Архив"""
    page.title = "Начальник - НГДУ"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = C["background"]
    
    def go_to_objects(e):
        page.go("/chief/objects")
    
    def go_to_archive(e):
        page.go("/chief/archive")
    
    def go_back(e):
        page.go("/")
    
    # Карточка меню
    def create_menu_card(icon, title, subtitle, on_click, icon_color):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=40, color=icon_color),
                ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                ft.Text(subtitle, size=12, color=C["text_secondary"])
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            padding=24,
            bgcolor=C["surface"],
            border_radius=12,
            width=280,
            on_click=on_click,
            ink=True,
            border=ft.border.all(1, C["border"])
        )
    
    page.add(
        # Хедер
        ft.Container(
            content=ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back, icon_color="grey"),
                ft.Text("НГДУ «Нижнесортымскнефть»", weight=ft.FontWeight.BOLD, size=18, expand=True, text_align=ft.TextAlign.CENTER),
                ft.TextButton("Выход", color="grey", on_click=lambda e: page.go("/"))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=C["surface"],
            border=ft.border.only(bottom=ft.BorderSide(1, C["border"]))
        ),
        
        # Меню
        ft.Container(
            content=ft.Column([
                ft.Text("МЕНЮ НАЧАЛЬНИКА", size=14, color=C["text_secondary"], weight=ft.FontWeight.BOLD),
                ft.Container(height=20),  # отступ
                create_menu_card(ft.icons.FACTORY, "ОБЪЕКТЫ", "просмотр всех заявок", go_to_objects, C["primary"]),
                ft.Container(height=12),  # отступ
                create_menu_card(ft.icons.ARCHIVE, "АРХИВ", "история заявок", go_to_archive, C["warning"]),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=24,
            expand=True
        )
    )


def show_chief_objects(page: ft.Page, dm, chief):
    """Начальник: Просмотр всех объектов и заявок"""
    page.title = "Объекты - Начальник"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = C["background"]
    
    objects = dm.get_all_objects()
    
    def go_back(e):
        page.go("/chief")
    
    def create_object_row(obj):
        """Строка объекта с заявками"""
        # Получаем активные заявки для этого объекта
        requests = [r for r in dm.data.get("requests", []) if r["object_id"] == obj["id"] and r["status"] == "active"]
        
        # Собираем элементы колонок
        col_controls = [
            ft.Row([
                ft.Text(obj["name"], weight=ft.FontWeight.BOLD, size=14, expand=True),
                ft.Row([
                    ft.Text(str(obj["oxygen"]), color=C["oxygen"], weight=ft.FontWeight.BOLD, size=12),
                    ft.Text(str(obj["propane"]), color=C["propane"], weight=ft.FontWeight.BOLD, size=12),
                ], spacing=8)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ]
        
        # Добавляем заявки если есть
        if requests:
            for r in requests:
                col_controls.append(
                    ft.Container(
                        content=ft.Text(f"🔹 {r['gas_type']}: {r['quantity']} балл. ({r['created_by']})", 
                                      size=11, color=C["text_secondary"]),
                        padding=ft.padding.only(left=8),
                        bgcolor=C["background"],
                        border_radius=4,
                        margin=ft.margin.only(top=4)
                    )
                )
        else:
            col_controls.append(
                ft.Text("Нет активных заявок", size=11, color="grey", italic=True)
            )
        
        return ft.Container(
            content=ft.Column(col_controls, spacing=4),
            padding=12,
            bgcolor=C["surface"],
            border_radius=8,
            border=ft.border.all(1, C["border"])
        )
    
    # Собираем список объектов
    object_rows = []
    for obj in objects:
        object_rows.append(create_object_row(obj))
    
    page.add(
        # Хедер
        ft.Container(
            content=ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back, icon_color="grey"),
                ft.Text("Объекты", weight=ft.FontWeight.BOLD, size=18, expand=True, text_align=ft.TextAlign.CENTER),
                ft.IconButton(ft.icons.HOME, on_click=lambda e: page.go("/chief"), icon_color="grey")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=C["surface"],
            border=ft.border.only(bottom=ft.BorderSide(1, C["border"]))
        ),
        
        # Список объектов
        ft.Container(
            content=ft.Column([
                ft.Text(f"ВСЕГО ОБЪЕКТОВ: {len(objects)}", size=12, color=C["text_secondary"], weight=ft.FontWeight.BOLD),
            ] + object_rows, spacing=8),
            padding=16,
            bgcolor=C["background"],
            expand=True
        )
    )


def show_chief_archive(page: ft.Page, dm, chief):
    """Начальник: Архив выполненных заявок"""
    page.title = "Архив - Начальник"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = C["background"]
    
    # Получаем все выполненные заявки (статус != active)
    archive_requests = [r for r in dm.data.get("requests", []) if r["status"] != "active"]
    
    def go_back(e):
        page.go("/chief")
    
    def create_archive_row(req):
        """Строка архивной заявки"""
        obj = next((o for o in dm.get_all_objects() if o["id"] == req["object_id"]), None)
        obj_name = obj["name"] if obj else f"ID:{req['object_id']}"
        
        gas_color = C["oxygen"] if req["gas_type"] == "КИСЛОРОД" else C["propane"]
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(obj_name, weight=ft.FontWeight.BOLD, size=13, expand=True),
                    ft.Text(req.get("completed_date", "—"), size=11, color="grey")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text(f"{req['gas_type']}", color=gas_color, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text(f"{req['quantity']} балл.", size=12),
                    ft.Text(f"• {req['created_by']}", size=11, color=C["text_secondary"], expand=True)
                ]),
            ], spacing=2),
            padding=10,
            bgcolor=C["surface"],
            border_radius=6,
            border=ft.border.all(1, C["border"])
        )
    
    # Собираем список архива (последние 50, в обратном порядке)
    archive_rows = []
    for req in reversed(archive_requests[-50:]):
        archive_rows.append(create_archive_row(req))
    
    page.add(
        # Хедер
        ft.Container(
            content=ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK, on_click=go_back, icon_color="grey"),
                ft.Text("Архив", weight=ft.FontWeight.BOLD, size=18, expand=True, text_align=ft.TextAlign.CENTER),
                ft.IconButton(ft.icons.HOME, on_click=lambda e: page.go("/chief"), icon_color="grey")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=C["surface"],
            border=ft.border.only(bottom=ft.BorderSide(1, C["border"]))
        ),
        
        # Список архива
        ft.Container(
            content=ft.Column([
                ft.Text(f"ВЫПОЛНЕНО ЗАЯВОК: {len(archive_requests)}", size=12, color=C["text_secondary"], weight=ft.FontWeight.BOLD),
            ] + archive_rows, spacing=6),
            padding=16,
            bgcolor=C["background"],
            expand=True
        )
    )
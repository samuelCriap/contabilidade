"""
Toast Notifications - Sistema de Honorários Contábeis
Notificações rápidas para feedback do usuário
"""
import flet as ft


def _show_toast(page: ft.Page, message: str, bg_color: str, icon: str, duration: int = 3000):
    """Exibe uma notificação toast"""
    snack = ft.SnackBar(
        content=ft.Row([
            ft.Text(icon, size=18),
            ft.Text(message, color="#FFFFFF", size=14, weight=ft.FontWeight.W_500),
        ], spacing=10),
        bgcolor=bg_color,
        duration=duration,
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()


def toast_success(page: ft.Page, message: str, duration: int = 3000):
    """Toast de sucesso (verde)"""
    _show_toast(page, message, "#10B981", "✅", duration)


def toast_error(page: ft.Page, message: str, duration: int = 4000):
    """Toast de erro (vermelho)"""
    _show_toast(page, message, "#EF4444", "❌", duration)


def toast_warning(page: ft.Page, message: str, duration: int = 3500):
    """Toast de aviso (amarelo/laranja)"""
    _show_toast(page, message, "#F59E0B", "⚠️", duration)


def toast_info(page: ft.Page, message: str, duration: int = 3000):
    """Toast informativo (azul)"""
    _show_toast(page, message, "#3B82F6", "ℹ️", duration)

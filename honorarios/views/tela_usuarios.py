"""
Tela de Gerenciamento de Usuários e Logs - Apenas Admin
"""
import flet as ft

from database import (
    listar_usuarios, atualizar_cargo_usuario, excluir_usuario, 
    aprovar_usuario, bloquear_usuario, atualizar_status_usuario, get_connection
)
from utils.theme import CORES
from utils.toast import toast_success, toast_error


def criar_tela_usuarios(page: ft.Page, theme):
    """Tela de gerenciamento de usuários e logs (apenas admin)"""
    
    # Cores dinâmicas
    BG = theme.get_bg()
    SURFACE = theme.get_surface()
    SURFACE_HOVER = theme.get_surface_hover()
    INPUT_BG = theme.get_input_bg()
    INPUT_BORDER = theme.get_input_border()
    TEXT_PRIMARY = theme.get_text_color()
    TEXT_SECONDARY = theme.get_text_secondary()
    ACCENT = CORES["accent"]
    SUCCESS = CORES["success"]
    WARNING = CORES["warning"]
    DANGER = CORES["danger"]
    PURPLE = "#8B5CF6"
    
    lista_usuarios = ft.Column([], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    lista_logs = ft.Column([], spacing=4, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def carregar_usuarios():
        lista_usuarios.controls.clear()
        usuarios = listar_usuarios()
        
        if not usuarios:
            lista_usuarios.controls.append(
                ft.Text("Nenhum usuário cadastrado", color=TEXT_SECONDARY)
            )
        else:
            for user in usuarios:
                is_admin_user = user.get('cargo') == 'admin'
                status = user.get('status', 'ativo')
                is_pendente = status == 'pendente'
                is_bloqueado = status == 'bloqueado'
                
                # Cor do badge de status
                if is_pendente:
                    status_cor = WARNING
                    status_texto = "PENDENTE"
                elif is_bloqueado:
                    status_cor = DANGER
                    status_texto = "BLOQUEADO"
                else:
                    status_cor = SUCCESS
                    status_texto = "ATIVO"
                
                # Ícone do usuário
                if is_admin_user:
                    icone = ft.Icons.ADMIN_PANEL_SETTINGS
                    icone_cor = WARNING
                elif is_pendente:
                    icone = ft.Icons.HOURGLASS_EMPTY
                    icone_cor = WARNING
                elif is_bloqueado:
                    icone = ft.Icons.BLOCK
                    icone_cor = DANGER
                else:
                    icone = ft.Icons.PERSON
                    icone_cor = ACCENT
                
                row = ft.Container(
                    content=ft.Row([
                        # Ícone
                        ft.Container(
                            content=ft.Icon(icone, size=18, color=icone_cor),
                            bgcolor=ft.Colors.with_opacity(0.15, icone_cor),
                            border_radius=6, padding=6,
                        ),
                        # Info do usuário
                        ft.Column([
                            ft.Row([
                                ft.Text(user.get('nome') or user['usuario'], size=12, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
                                ft.Container(
                                    content=ft.Text(status_texto, size=8, color="#FFFFFF"),
                                    bgcolor=status_cor, border_radius=4, padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                ),
                            ], spacing=8),
                            ft.Text(f"@{user['usuario']} • {user.get('cargo', 'usuario').upper()}", size=9, color=TEXT_SECONDARY),
                        ], spacing=2, expand=True),
                        # Email
                        ft.Text(user.get('email', '') or '-', size=9, color=TEXT_SECONDARY, width=100),
                        # Dropdown cargo
                        ft.Dropdown(
                            value=user.get('cargo', 'usuario'),
                            options=[
                                ft.dropdown.Option("usuario", "Usuário"),
                                ft.dropdown.Option("admin", "Admin"),
                            ],
                            width=85,
                            bgcolor=INPUT_BG,
                            border_color=INPUT_BORDER,
                            on_change=lambda e, uid=user['id']: alterar_cargo(uid, e.control.value),
                            disabled=user['usuario'] == 'admin',
                        ),
                        # Botão aprovar (só para pendentes)
                        ft.IconButton(
                            ft.Icons.CHECK_CIRCLE,
                            icon_color=SUCCESS,
                            icon_size=18,
                            tooltip="Aprovar",
                            on_click=lambda e, uid=user['id'], uname=user['usuario']: aprovar(uid, uname),
                            visible=is_pendente,
                        ),
                        # Botão bloquear/desbloquear
                        ft.IconButton(
                            ft.Icons.LOCK_OPEN if is_bloqueado else ft.Icons.BLOCK,
                            icon_color=SUCCESS if is_bloqueado else WARNING,
                            icon_size=18,
                            tooltip="Desbloquear" if is_bloqueado else "Bloquear",
                            on_click=lambda e, uid=user['id'], uname=user['usuario'], bloq=is_bloqueado: toggle_bloqueio(uid, uname, bloq),
                            visible=user['usuario'] != 'admin' and not is_pendente,
                        ),
                        # Botão excluir
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE,
                            icon_color=DANGER,
                            icon_size=18,
                            tooltip="Excluir",
                            on_click=lambda e, uid=user['id'], uname=user['usuario']: confirmar_exclusao(uid, uname),
                            visible=user['usuario'] != 'admin',
                        ),
                    ], spacing=8),
                    padding=12,
                    bgcolor=SURFACE,
                    border_radius=10,
                    border=ft.border.all(1, status_cor) if is_pendente else ft.border.all(1, theme.get_border()),
                )
                lista_usuarios.controls.append(row)
        
        page.update()
    
    def carregar_logs():
        lista_logs.controls.clear()
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM logs_auditoria 
            ORDER BY data_hora DESC 
            LIMIT 100
        """)
        logs = cursor.fetchall()
        conn.close()
        
        if not logs:
            lista_logs.controls.append(
                ft.Text("Nenhuma atividade registrada", color=TEXT_SECONDARY)
            )
        else:
            for log in logs:
                acao = log['acao'].lower()
                if 'login' in acao:
                    icone, cor = ft.Icons.LOGIN, SUCCESS
                elif 'logout' in acao:
                    icone, cor = ft.Icons.LOGOUT, WARNING
                elif 'cadastr' in acao or 'criar' in acao:
                    icone, cor = ft.Icons.ADD_CIRCLE_OUTLINE, SUCCESS
                elif 'exclu' in acao or 'delet' in acao:
                    icone, cor = ft.Icons.DELETE_OUTLINE, DANGER
                elif 'aprov' in acao:
                    icone, cor = ft.Icons.CHECK_CIRCLE, SUCCESS
                elif 'bloqu' in acao:
                    icone, cor = ft.Icons.BLOCK, DANGER
                elif 'alter' in acao or 'edita' in acao:
                    icone, cor = ft.Icons.EDIT_OUTLINED, ACCENT
                elif 'recibo' in acao or 'pdf' in acao:
                    icone, cor = ft.Icons.PICTURE_AS_PDF_OUTLINED, PURPLE
                elif 'pago' in acao:
                    icone, cor = ft.Icons.PAID_OUTLINED, SUCCESS
                else:
                    icone, cor = ft.Icons.INFO_OUTLINE, TEXT_SECONDARY
                
                data_hora = log['data_hora'][:16] if log['data_hora'] else ""
                
                def mostrar_detalhe_log(e, log_data=log):
                    dialog = ft.AlertDialog(
                        title=ft.Row([
                            ft.Icon(icone, size=24, color=cor),
                            ft.Text("Detalhes da Atividade", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ], spacing=10),
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text("📅 Data/Hora:", size=11, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, width=100),
                                    ft.Text(log_data['data_hora'] or '-', size=11, color=TEXT_SECONDARY),
                                ]),
                                ft.Divider(height=1, color=SURFACE_HOVER),
                                ft.Row([
                                    ft.Text("👤 Usuário:", size=11, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, width=100),
                                    ft.Text(log_data['usuario'], size=11, color=ACCENT),
                                ]),
                                ft.Divider(height=1, color=SURFACE_HOVER),
                                ft.Row([
                                    ft.Text("📋 Ação:", size=11, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, width=100),
                                    ft.Text(log_data['acao'], size=11, color=TEXT_PRIMARY),
                                ]),
                                ft.Divider(height=1, color=SURFACE_HOVER),
                                ft.Row([
                                    ft.Text("📂 Tabela:", size=11, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, width=100),
                                    ft.Text(log_data['tabela'] or '-', size=11, color=TEXT_SECONDARY),
                                ]),
                                ft.Divider(height=1, color=SURFACE_HOVER),
                                ft.Row([
                                    ft.Text("🔢 ID Registro:", size=11, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, width=100),
                                    ft.Text(str(log_data['registro_id']) if log_data['registro_id'] else '-', size=11, color=TEXT_SECONDARY),
                                ]),
                                ft.Divider(height=1, color=SURFACE_HOVER),
                                ft.Row([
                                    ft.Text("📝 Detalhes:", size=11, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, width=100),
                                    ft.Text(log_data['detalhes'] or '-', size=11, color=TEXT_SECONDARY, expand=True),
                                ]),
                            ], spacing=8, width=350),
                            padding=15,
                        ),
                        actions=[
                            ft.TextButton("Fechar", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                        ],
                    )
                    page.overlay.append(dialog)
                    dialog.open = True
                    page.update()
                
                row = ft.Container(
                    content=ft.Row([
                        ft.Icon(icone, size=14, color=cor),
                        ft.Text(data_hora, size=9, color=TEXT_SECONDARY, width=95),
                        ft.Text(log['usuario'], size=9, weight=ft.FontWeight.W_500, color=ACCENT, width=70),
                        ft.Text(log['acao'], size=10, color=TEXT_PRIMARY, expand=True),
                        ft.Text(log['detalhes'] or '', size=9, color=TEXT_SECONDARY, width=130),
                    ], spacing=6),
                    padding=8,
                    bgcolor=SURFACE,
                    border_radius=6,
                    border=ft.border.all(1, theme.get_border()),
                    on_click=mostrar_detalhe_log,
                    ink=True,
                )
                lista_logs.controls.append(row)
        
        page.update()
    
    def alterar_cargo(user_id, novo_cargo):
        atualizar_cargo_usuario(user_id, novo_cargo)
        toast_success(page, f"Cargo atualizado para {novo_cargo.upper()}")
        carregar_usuarios()
    
    def aprovar(user_id, username):
        aprovar_usuario(user_id)
        toast_success(page, f"✅ {username} aprovado!")
        carregar_usuarios()
    
    def toggle_bloqueio(user_id, username, esta_bloqueado):
        if esta_bloqueado:
            atualizar_status_usuario(user_id, 'ativo')
            toast_success(page, f"🔓 {username} desbloqueado")
        else:
            bloquear_usuario(user_id)
            toast_success(page, f"🔒 {username} bloqueado")
        carregar_usuarios()
    
    def confirmar_exclusao(user_id, username):
        def fechar_dialog(e):
            dialog.open = False
            page.update()
        
        def excluir(e):
            if excluir_usuario(user_id):
                toast_success(page, f"Usuário {username} excluído")
                carregar_usuarios()
            else:
                toast_error(page, "Não foi possível excluir")
            dialog.open = False
            page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f"Deseja excluir o usuário '{username}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_dialog),
                ft.ElevatedButton("Excluir", bgcolor=DANGER, color="#FFFFFF", on_click=excluir),
            ],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()
    
    # Carregar dados iniciais
    carregar_usuarios()
    carregar_logs()
    
    # Tabs
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(
                text="Usuários",
                icon=ft.Icons.PEOPLE_OUTLINE,
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text("● PENDENTE = aguardando aprovação", size=9, color=WARNING),
                            ),
                            ft.Container(
                                content=ft.Text("● BLOQUEADO = sem acesso", size=9, color=DANGER),
                            ),
                            ft.Container(
                                content=ft.Text("● ATIVO = acesso liberado", size=9, color=SUCCESS),
                            ),
                        ], spacing=15),
                        ft.Container(height=10),
                        lista_usuarios,
                    ]),
                    padding=10,
                ),
            ),
            ft.Tab(
                text="Log de Atividades",
                icon=ft.Icons.HISTORY,
                content=ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Row([
                                ft.Text("", width=14),
                                ft.Text("Data/Hora", size=9, width=95, color=TEXT_SECONDARY),
                                ft.Text("Usuário", size=9, width=70, color=TEXT_SECONDARY),
                                ft.Text("Ação", size=9, expand=True, color=TEXT_SECONDARY),
                                ft.Text("Detalhes", size=9, width=130, color=TEXT_SECONDARY),
                            ], spacing=6),
                            padding=ft.padding.only(left=8),
                        ),
                        lista_logs,
                    ]),
                    padding=10,
                ),
            ),
        ],
        expand=True,
    )
    
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=26, color=ACCENT),
                ft.Text("Painel Admin", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Atualizar", icon=ft.Icons.REFRESH,
                    bgcolor=ACCENT, color=TEXT_PRIMARY,
                    on_click=lambda e: (carregar_usuarios(), carregar_logs()),
                ),
            ], spacing=12),
            ft.Container(height=10),
            tabs,
        ]),
        expand=True,
        padding=20,
        bgcolor=BG,
    )

"""
Sistema de Honorários Contábeis - Flet App
VERSÃO OTIMIZADA: Menu animado fluido, visual moderno, sem travamentos
"""
import flet as ft
import os
import sys
import asyncio
import ssl

# Patch para erros de SSL em redes corporativas/PCs antigos
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import create_tables, criar_usuario_inicial, get_config, get_resource_path
from utils.theme import ThemeManager, CORES
from utils.toast import toast_success, toast_error, toast_warning
from utils.updater import GitHubUpdater

VERSION = "1.1.0"


def main(page: ft.Page):
    page.title = "Sistema de Honorários Contábeis"
    page.padding = 0
    page.spacing = 0
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0F172A"
    page.window.width = 1100
    page.window.height = 750
    page.window.center()
    page.fonts = {"Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"}
    page.theme = ft.Theme(font_family="Inter")
    
    # Inicializa
    create_tables()
    criar_usuario_inicial()
    
    theme = ThemeManager()
    page.theme_mode = ft.ThemeMode.DARK if theme.is_dark[0] else ft.ThemeMode.LIGHT
    usuario_logado = [None]
    pagina_atual = [0]
    menu_expandido = [False]
    
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    
    # ══════════════════════════════════════════════════════════════════
    # CORES E ESTILOS MODERNOS
    # ══════════════════════════════════════════════════════════════════
    DARK_BG = "#0F172A"
    DARK_SURFACE = "#1E293B"
    DARK_CARD = "#334155"
    ACCENT = "#3B82F6"
    ACCENT_LIGHT = "#60A5FA"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    TEXT_PRIMARY = "#F8FAFC"
    TEXT_SECONDARY = "#94A3B8"
    
    # ══════════════════════════════════════════════════════════════════
    # TELA DE LOGIN MODERNA COM ABAS
    # ══════════════════════════════════════════════════════════════════
    def criar_login():
        # === ABA LOGIN ===
        login_usuario = ft.TextField(
            label="Usuário", prefix_icon=ft.Icons.PERSON_OUTLINE,
            border_radius=12, bgcolor=DARK_SURFACE, border_color=DARK_CARD,
            focused_border_color=ACCENT, color=TEXT_PRIMARY,
            label_style=ft.TextStyle(color=TEXT_SECONDARY),
            width=300, text_size=14,
        )
        
        login_senha = ft.TextField(
            label="Senha", prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True, can_reveal_password=True,
            border_radius=12, bgcolor=DARK_SURFACE, border_color=DARK_CARD,
            focused_border_color=ACCENT, color=TEXT_PRIMARY,
            label_style=ft.TextStyle(color=TEXT_SECONDARY),
            width=300, text_size=14,
        )
        
        login_erro = ft.Text("", color=DANGER, size=12)
        login_loading = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False, color=ACCENT)
        
        def fazer_login(e):
            if not login_usuario.value or not login_senha.value:
                login_erro.value = "Preencha todos os campos"
                page.update()
                return
            
            login_loading.visible = True
            login_erro.value = ""
            page.update()
            
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND senha = ?", 
                          (login_usuario.value.strip(), login_senha.value))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                status = user['status'] if 'status' in user.keys() else 'ativo'
                
                # Verificar se usuário está aprovado
                if status == 'pendente':
                    login_loading.visible = False
                    login_erro.value = "⏳ Aguardando aprovação do admin"
                    page.update()
                    return
                
                if status == 'bloqueado':
                    login_loading.visible = False
                    login_erro.value = "🚫 Usuário bloqueado"
                    page.update()
                    return
                
                cargo = user['cargo'] if 'cargo' in user.keys() else 'usuario'
                usuario_logado[0] = {
                    "username": login_usuario.value.strip(),
                    "cargo": cargo or 'usuario',
                    "is_admin": cargo == 'admin'
                }
                # Registrar log de login
                from database import registrar_log, gerar_honorarios_mes_atual
                registrar_log(login_usuario.value.strip(), "Login realizado", detalhes=f"Cargo: {cargo}")
                
                # Gerar automaticamente honorários do mês atual para clientes ativos
                try:
                    criados = gerar_honorarios_mes_atual()
                    if criados > 0:
                        print(f"[AUTO] Gerados {criados} honorários para o mês atual")
                except Exception as ex:
                    print(f"[AVISO] Erro ao gerar honorários automáticos: {ex}")
                
                # Verificar update antes de abrir app
                verificar_atualizacao(mostrar_splash)
            else:
                login_loading.visible = False
                login_erro.value = "Usuário ou senha incorretos"
                page.update()

        def verificar_atualizacao(callback_sucesso):
            """Verifica atualização e exibe modal se necessário"""
            updater = GitHubUpdater("samuelCriap", "contabilidade", VERSION)
            
            # Dialog de progresso
            prog_bar = ft.ProgressBar(width=300, value=0)
            prog_text = ft.Text("Baixando atualização...", size=12, color=TEXT_SECONDARY)
            
            dlg_prog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Atualizando", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                bgcolor=DARK_BG,
                content=ft.Column([
                    ft.Text("Por favor, aguarde o download.", size=14, color=TEXT_SECONDARY),
                    ft.Container(height=10),
                    prog_bar,
                    ft.Container(height=5),
                    prog_text,
                ], height=100, width=320),
            )
            
            def iniciar_atualizacao(asset_url):
                page.overlay.append(dlg_prog)
                dlg_prog.open = True
                
                # Fechar dialogo de confirmação
                dlg_confirm.open = False
                page.update()
                
                def on_progress(p):
                    prog_bar.value = p
                    prog_text.value = f"{int(p*100)}%"
                    page.update()
                
                # Executar download em thread separada para não travar UI
                import threading
                def download_thread():
                    file_path = updater.download_update(asset_url, on_progress)
                    if file_path:
                        prog_text.value = "Instalando..."
                        page.update()
                        updater.apply_update(file_path)
                    else:
                        dlg_prog.open = False
                        toast_error(page, "Falha ao baixar atualização")
                        page.update()
                        callback_sucesso()
                
                threading.Thread(target=download_thread, daemon=True).start()
            
            # Verificar atualização (async ou thread)
            login_loading.visible = True
            login_erro.value = "Verificando atualizações..."
            page.update()
            
            import threading
            def check_thread():
                try:
                    update_info = updater.check_for_updates()
                except:
                    update_info = None
                
                login_loading.visible = False
                login_erro.value = ""
                
                if update_info:
                    # Encontrar asset do executável windows
                    asset_url = None
                    for asset in update_info['assets']:
                        if asset['name'].endswith('.exe'):
                            asset_url = asset['browser_download_url']
                            break
                    
                    if asset_url:
                        # Modal de confirmação
                        dlg_confirm.content.controls[0].value = f"Nova versão {update_info['version']} disponível!\nDeseja atualizar agora?"
                        dlg_confirm.actions[1].on_click = lambda e: iniciar_atualizacao(asset_url)
                        page.overlay.append(dlg_confirm)
                        dlg_confirm.open = True
                        page.update()
                        return

                # Se não tiver update ou falhar, segue o fluxo normal
                callback_sucesso()
                
            dlg_confirm = ft.AlertDialog(
                modal=True,
                title=ft.Text("🚀 Atualização Disponível", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                bgcolor=DARK_BG,
                content=ft.Column([
                    ft.Text("", size=14, color=TEXT_SECONDARY),
                ], width=320, height=60),
                actions=[
                    ft.TextButton("Mais tarde", on_click=lambda e: (setattr(dlg_confirm, 'open', False), callback_sucesso(), page.update())),
                    ft.ElevatedButton("Atualizar Agora", bgcolor=ACCENT, color=TEXT_PRIMARY),
                ],
            )
            
            threading.Thread(target=check_thread, daemon=True).start()

        
        login_usuario.on_submit = lambda e: fazer_login(None)
        login_senha.on_submit = lambda e: fazer_login(None)
        
        aba_login = ft.Column([
            ft.Text("Bem-vindo", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Faça login para continuar", size=12, color=TEXT_SECONDARY),
            ft.Container(height=20),
            login_usuario,
            ft.Container(height=10),
            login_senha,
            ft.Container(height=8),
            login_erro,
            ft.Container(height=15),
            login_loading,
            ft.ElevatedButton(
                "Entrar", icon=ft.Icons.LOGIN,
                width=300, height=45, bgcolor=ACCENT, color=TEXT_PRIMARY,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                on_click=fazer_login,
            ),
            ft.Container(height=20),
            ft.Text(f"Versão {VERSION}", size=11, color=TEXT_SECONDARY),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        
        # === ABA CADASTRO ===
        cad_nome = ft.TextField(
            label="Nome completo", prefix_icon=ft.Icons.BADGE_OUTLINED,
            border_radius=12, bgcolor=DARK_SURFACE, border_color=DARK_CARD,
            focused_border_color=ACCENT, color=TEXT_PRIMARY,
            label_style=ft.TextStyle(color=TEXT_SECONDARY),
            width=300, text_size=14,
        )
        
        cad_usuario = ft.TextField(
            label="Usuário", prefix_icon=ft.Icons.PERSON_OUTLINE,
            border_radius=12, bgcolor=DARK_SURFACE, border_color=DARK_CARD,
            focused_border_color=ACCENT, color=TEXT_PRIMARY,
            label_style=ft.TextStyle(color=TEXT_SECONDARY),
            width=300, text_size=14,
        )
        
        cad_email = ft.TextField(
            label="Email", prefix_icon=ft.Icons.EMAIL_OUTLINED,
            border_radius=12, bgcolor=DARK_SURFACE, border_color=DARK_CARD,
            focused_border_color=ACCENT, color=TEXT_PRIMARY,
            label_style=ft.TextStyle(color=TEXT_SECONDARY),
            width=300, text_size=14,
        )
        
        cad_senha = ft.TextField(
            label="Senha", prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True, can_reveal_password=True,
            border_radius=12, bgcolor=DARK_SURFACE, border_color=DARK_CARD,
            focused_border_color=ACCENT, color=TEXT_PRIMARY,
            label_style=ft.TextStyle(color=TEXT_SECONDARY),
            width=300, text_size=14,
        )
        
        cad_msg = ft.Text("", size=12)
        cad_loading = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False, color=ACCENT)
        
        def fazer_cadastro(e):
            if not cad_usuario.value or not cad_senha.value:
                cad_msg.value = "Usuário e senha são obrigatórios"
                cad_msg.color = DANGER
                page.update()
                return
            
            if len(cad_senha.value) < 4:
                cad_msg.value = "Senha deve ter pelo menos 4 caracteres"
                cad_msg.color = DANGER
                page.update()
                return
            
            cad_loading.visible = True
            cad_msg.value = ""
            page.update()
            
            from database import cadastrar_usuario
            result = cadastrar_usuario(
                usuario=cad_usuario.value.strip(),
                senha=cad_senha.value,
                nome=cad_nome.value.strip() or None,
                email=cad_email.value.strip() or None,
                cargo='usuario',
                status='pendente'  # Aguarda aprovação do admin
            )
            
            cad_loading.visible = False
            if result:
                cad_msg.value = "✅ Cadastro enviado! Aguarde aprovação do admin."
                cad_msg.color = SUCCESS
                cad_nome.value = ""
                cad_usuario.value = ""
                cad_email.value = ""
                cad_senha.value = ""
            else:
                cad_msg.value = "Usuário já existe"
                cad_msg.color = DANGER
            page.update()
        
        aba_cadastro = ft.Column([
            ft.Text("Criar Conta", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Preencha os dados abaixo", size=12, color=TEXT_SECONDARY),
            ft.Container(height=15),
            cad_nome,
            ft.Container(height=8),
            cad_usuario,
            ft.Container(height=8),
            cad_email,
            ft.Container(height=8),
            cad_senha,
            ft.Container(height=8),
            cad_msg,
            ft.Container(height=10),
            cad_loading,
            ft.ElevatedButton(
                "Cadastrar", icon=ft.Icons.PERSON_ADD,
                width=300, height=45, bgcolor=SUCCESS, color=TEXT_PRIMARY,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                on_click=fazer_cadastro,
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        
        # Tabs
        tabs = ft.Tabs(
            selected_index=0,
            label_color=TEXT_PRIMARY,
            unselected_label_color=TEXT_SECONDARY,
            indicator_color=ACCENT,
            tabs=[
                ft.Tab(text="Login", content=ft.Container(content=aba_login, padding=20)),
                ft.Tab(text="Cadastrar", content=ft.Container(content=aba_cadastro, padding=20)),
            ],
            expand=True,
        )
        
        # Layout split-screen
        left_panel = ft.Container(
            content=ft.Column([
                ft.Image(src=get_resource_path("logo.png"), width=500, height=500, fit=ft.ImageFit.CONTAIN),
                ft.Container(height=15),
                ft.Text("Sistema de Gestão Contábil", size=20, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY, font_family="Poppins"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[DARK_BG, "#1E3A5F", DARK_BG],
            ),
        )
        
        right_panel = ft.Container(
            content=tabs,
            expand=True,
            bgcolor=DARK_BG,
            padding=30,
        )
        
        return ft.Row([left_panel, right_panel], expand=True, spacing=0)
    
    # ══════════════════════════════════════════════════════════════════
    # SPLASH SCREEN
    # ══════════════════════════════════════════════════════════════════
    def mostrar_splash():
        page.clean()
        
        splash = ft.Container(
            content=ft.Column([
                ft.Image(src=get_resource_path("logo.png"), width=450, height=450, fit=ft.ImageFit.CONTAIN),
                ft.Container(height=20),
                ft.ProgressRing(width=40, height=40, stroke_width=3, color=ACCENT),
                ft.Container(height=15),
                ft.Text("Carregando...", size=16, color=TEXT_SECONDARY, font_family="Poppins"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            expand=True,
            bgcolor=DARK_BG,
        )
        
        page.add(splash)
        page.update()
        
        import time
        time.sleep(1)
        abrir_app()
    
    # ══════════════════════════════════════════════════════════════════
    # APP PRINCIPAL - MENU ANIMADO FLUIDO
    # ══════════════════════════════════════════════════════════════════
    def abrir_app():
        page.window.maximized = True
        page.clean()
        page.bgcolor = DARK_BG
        
        conteudo = ft.Container(expand=True, bgcolor=DARK_BG)
        
        # ═══ ITENS DO MENU (pré-criados, só atualizam propriedades) ═══
        is_admin_user = usuario_logado[0].get('is_admin', False) if usuario_logado[0] else False
        
        menu_items_data = [
            (ft.Icons.HOME_OUTLINED, ft.Icons.HOME, "Início", 0),
            (ft.Icons.RECEIPT_LONG_OUTLINED, ft.Icons.RECEIPT_LONG, "Recibos", 1),
            (ft.Icons.BAR_CHART_OUTLINED, ft.Icons.BAR_CHART, "Relatórios", 2),
            (ft.Icons.CALENDAR_MONTH_OUTLINED, ft.Icons.CALENDAR_MONTH, "Agenda", 3),
            (ft.Icons.VERIFIED_USER_OUTLINED, ft.Icons.VERIFIED_USER, "Certificados", 4),
            (ft.Icons.SETTINGS_OUTLINED, ft.Icons.SETTINGS, "Configurações", 5),
        ]
        
        # Adicionar item Usuários só para admin
        if is_admin_user:
            menu_items_data.append((ft.Icons.PEOPLE_OUTLINED, ft.Icons.PEOPLE, "Usuários", 6))
        
        # Criar referências para os itens (para atualização sem recriação)
        menu_icons = []
        menu_texts = []
        menu_containers = []
        
        def navegar(idx):
            pagina_atual[0] = idx
            atualizar_indicador_menu()
            carregar_pagina(idx)
        
        def carregar_pagina(idx):
            is_admin = usuario_logado[0].get('is_admin', False) if usuario_logado[0] else False
            
            if idx == 0:
                from views.tela_inicio import criar_tela_inicio
                conteudo.content = criar_tela_inicio(page, theme, navegar_para_ano, is_admin)
            elif idx == 1:
                from views.tela_gerar_recibo import criar_tela_gerar_recibo
                conteudo.content = criar_tela_gerar_recibo(page, file_picker, theme, usuario_logado)
            elif idx == 2:
                from views.tela_relatorios import criar_tela_relatorios
                conteudo.content = criar_tela_relatorios(page, theme, is_admin)
            elif idx == 3:
                from views.tela_agenda import criar_tela_agenda
                conteudo.content = criar_tela_agenda(page, theme, usuario_logado)
            elif idx == 4:
                from views.tela_certificados import criar_tela_certificados
                conteudo.content = criar_tela_certificados(page, theme, usuario_logado)
            elif idx == 5:
                from views.tela_configuracoes import criar_tela_configuracoes
                conteudo.content = criar_tela_configuracoes(page, usuario_logado, theme, VERSION)
            elif idx == 6:  # Usuários (só admin)
                from views.tela_usuarios import criar_tela_usuarios
                conteudo.content = criar_tela_usuarios(page, theme)
            page.update()
        
        def navegar_para_ano(ano, mes_filtro=None):
            from views.tela_honorarios_ano import criar_tela_honorarios_ano
            conteudo.content = criar_tela_honorarios_ano(page, ano, mes_filtro, theme, lambda: navegar(0), usuario_logado)
            page.update()
        
        def atualizar_indicador_menu():
            """Atualiza apenas as cores/ícones dos itens (sem recriar)"""
            # Cores dinâmicas baseadas no tema
            menu_text_color = theme.get_text_color()
            menu_text_secondary = theme.get_text_secondary()
            
            for i, (icon_ref, text_ref, container_ref) in enumerate(zip(menu_icons, menu_texts, menu_containers)):
                ativo = pagina_atual[0] == i
                icon_inactive, icon_active, _, _ = menu_items_data[i]
                
                icon_ref.name = icon_active if ativo else icon_inactive
                icon_ref.color = ACCENT if ativo else menu_text_secondary
                text_ref.color = menu_text_color if ativo else menu_text_secondary
                text_ref.weight = ft.FontWeight.W_600 if ativo else ft.FontWeight.NORMAL
                container_ref.bgcolor = ft.Colors.with_opacity(0.15, ACCENT) if ativo else ft.Colors.TRANSPARENT
        
        # Criar itens do menu
        for icon_inactive, icon_active, texto, idx in menu_items_data:
            icon = ft.Icon(icon_inactive, size=22, color=theme.get_text_secondary())
            text = ft.Text(texto, size=13, color=theme.get_text_secondary(), 
                          animate_opacity=ft.Animation(150, ft.AnimationCurve.EASE_OUT))
            
            container = ft.Container(
                content=ft.Row([icon, text], spacing=12),
                padding=ft.padding.symmetric(vertical=12, horizontal=15),
                border_radius=10,
                on_click=lambda e, i=idx: navegar(i),
                ink=True,
                animate=ft.Animation(100, ft.AnimationCurve.EASE_OUT),
            )
            
            menu_icons.append(icon)
            menu_texts.append(text)
            menu_containers.append(container)
        
        # Logo e botões extras
        logo = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.BUSINESS, size=32, color=ACCENT),
                ft.Text("HC", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY,
                       animate_opacity=ft.Animation(150, ft.AnimationCurve.EASE_OUT)),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=20,
        )
        
        btn_tema = ft.IconButton(
            ft.Icons.BRIGHTNESS_6, 
            icon_color=TEXT_SECONDARY, 
            icon_size=20,
            tooltip="Alternar tema",
            on_click=lambda e: alternar_tema(),
        )
        
        btn_sair = ft.IconButton(
            ft.Icons.LOGOUT, 
            icon_color=DANGER, 
            icon_size=20,
            tooltip="Sair",
            on_click=lambda e: page.window.close(),
        )
        
        def alternar_tema():
            theme.toggle()
            is_dark = theme.is_dark[0]
            page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
            
            # Atualizar cores - usando cores do tema com melhor contraste no modo claro
            new_bg = theme.get_bg()
            new_surface = theme.get_surface()
            new_text = theme.get_text_color()
            new_text_sec = theme.get_text_secondary()
            new_border = theme.get_border()
            
            page.bgcolor = new_bg
            conteudo.bgcolor = new_bg
            menu_container.bgcolor = new_surface
            menu_container.border = ft.border.only(right=ft.BorderSide(1, new_border))
            
            # Atualizar menu
            for icon_ref, text_ref, container_ref in zip(menu_icons, menu_texts, menu_containers):
                text_ref.color = new_text_sec
                icon_ref.color = new_text_sec
            
            logo.content.controls[0].color = ACCENT
            logo.content.controls[1].color = new_text
            btn_tema.icon_color = new_text_sec
            
            atualizar_indicador_menu()
            carregar_pagina(pagina_atual[0])
        
        # Coluna do menu
        menu_col = ft.Column([
            logo,
            ft.Container(height=20),
            *menu_containers,
            ft.Container(expand=True),
            ft.Column([btn_tema, btn_sair], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=15),
        ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.START)
        
        # Container do menu com animação
        menu_container = ft.Container(
            content=menu_col,
            width=70,
            bgcolor=theme.get_surface(),
            padding=ft.padding.symmetric(horizontal=10),
            border=ft.border.only(right=ft.BorderSide(1, theme.get_border())),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        )
        
        def on_menu_hover(e):
            expandir = e.data == "true"
            menu_expandido[0] = expandir
            menu_container.width = 200 if expandir else 70
            
            # Atualizar visibilidade dos textos
            for text in menu_texts:
                text.opacity = 1 if expandir else 0
            
            # Logo text
            logo.content.controls[1].opacity = 1 if expandir else 0
            
            page.update()
        
        menu_container.on_hover = on_menu_hover
        
        # Inicializar
        atualizar_indicador_menu()
        carregar_pagina(0)
        
        # Esconder textos inicialmente
        for text in menu_texts:
            text.opacity = 0
        logo.content.controls[1].opacity = 0
        
        page.add(ft.Row([
            menu_container,
            ft.Container(content=conteudo, expand=True, bgcolor=DARK_BG),
        ], expand=True, spacing=0))
    
    # Inicia com login
    page.add(criar_login())


if __name__ == "__main__":
    ft.app(target=main)

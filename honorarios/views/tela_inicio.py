"""
Tela Início - Dashboard Moderno
OTIMIZADO: Visual dinâmico (light/dark), queries agregadas
"""
import flet as ft
from datetime import datetime

from database import get_connection
from utils.theme import CORES


def criar_tela_inicio(page: ft.Page, theme, nav_para_ano, is_admin=True):
    """Dashboard moderno e otimizado"""
    
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month
    
    # Cores dinâmicas do tema
    BG = theme.get_bg()
    SURFACE = theme.get_surface()
    TEXT_PRIMARY = theme.get_text_color()
    TEXT_SECONDARY = theme.get_text_secondary()
    ACCENT = CORES["accent"]
    SUCCESS = CORES["success"]
    WARNING = CORES["warning"]
    DANGER = CORES["danger"]
    PURPLE = CORES["purple"]
    
    # ═══ CARREGAR DADOS COM QUERY ÚNICA ═══
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total de clientes
    cursor.execute("SELECT COUNT(*) as total FROM clientes")
    total_clientes = cursor.fetchone()['total']
    
    # Resumo por ano
    cursor.execute("""
        SELECT 
            ano,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'PAGO' THEN 1 ELSE 0 END) as pagos,
            SUM(valor) as valor_total,
            SUM(CASE WHEN status = 'PAGO' THEN valor ELSE 0 END) as valor_recebido
        FROM honorarios
        GROUP BY ano
        ORDER BY ano DESC
    """)
    resumo_anos = {row['ano']: dict(row) for row in cursor.fetchall()}
    
    # Meses do ano atual
    cursor.execute("""
        SELECT mes, 
               COUNT(*) as total,
               SUM(CASE WHEN status = 'PAGO' THEN 1 ELSE 0 END) as pagos
        FROM honorarios 
        WHERE ano = ?
        GROUP BY mes
    """, (ano_atual,))
    meses_data = {row['mes']: dict(row) for row in cursor.fetchall()}
    
    conn.close()
    
    # Calcular totais
    total_valor = sum(r.get('valor_total', 0) or 0 for r in resumo_anos.values())
    total_recebido = sum(r.get('valor_recebido', 0) or 0 for r in resumo_anos.values())
    total_pendente = total_valor - total_recebido
    
    def formatar_moeda(valor, ocultar=False):
        if ocultar:
            return "R$ *****"
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # ═══ CARDS DE RESUMO ═══
    def criar_card(titulo, valor, cor, icone, subtitulo=""):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icone, size=20, color=cor),
                        bgcolor=ft.Colors.with_opacity(0.15, cor),
                        border_radius=8,
                        padding=8,
                    ),
                    ft.Column([
                        ft.Text(titulo, size=11, color=TEXT_SECONDARY),
                        ft.Text(valor, size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ], spacing=2, expand=True),
                ], spacing=12),
                ft.Text(subtitulo, size=10, color=TEXT_SECONDARY) if subtitulo else ft.Container(),
            ], spacing=8),
            padding=20,
            bgcolor=SURFACE,
            border_radius=16,
            border=ft.border.all(1, theme.get_border()),
            expand=True,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.15, "#000000")),
        )
    
    # Ocultar valores para não-admin
    ocultar = not is_admin
    
    cards = ft.Row([
        criar_card("Clientes Ativos", str(total_clientes), ACCENT, ft.Icons.PEOPLE_ALT),
        criar_card("Total Gerado", formatar_moeda(total_valor, ocultar), PURPLE, ft.Icons.ACCOUNT_BALANCE_WALLET),
        criar_card("Recebido", formatar_moeda(total_recebido, ocultar), SUCCESS, ft.Icons.CHECK_CIRCLE, f"{(total_recebido/total_valor*100):.0f}% do total" if total_valor > 0 and is_admin else ""),
        criar_card("Pendente", formatar_moeda(total_pendente, ocultar), WARNING, ft.Icons.PENDING, f"{(total_pendente/total_valor*100):.0f}% do total" if total_valor > 0 and is_admin else ""),
    ], spacing=15)
    
    # ═══ GRID DE MESES ═══
    MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez", "13º"]
    
    meses_grid = []
    for mes in range(1, 14):
        dados = meses_data.get(mes, {'total': 0, 'pagos': 0})
        total_mes = dados['total']
        pagos_mes = dados['pagos']
        pendentes = total_mes - pagos_mes
        
        # Cor baseada no status
        if total_mes == 0:
            cor = theme.get_surface_hover()
        elif pagos_mes == total_mes:
            cor = SUCCESS
        elif pendentes > pagos_mes:
            cor = WARNING
        else:
            cor = ACCENT
        
        is_atual = mes == mes_atual
        
        meses_grid.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(MESES[mes-1], size=12, weight=ft.FontWeight.W_600 if is_atual else ft.FontWeight.NORMAL, color=TEXT_PRIMARY),
                    ft.Text(f"{pagos_mes}/{total_mes}" if total_mes > 0 else "-", size=10, color=TEXT_SECONDARY),
                    ft.Container(
                        width=40,
                        height=4,
                        border_radius=2,
                        bgcolor=cor,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=12,
                bgcolor=SURFACE if not is_atual else ft.Colors.with_opacity(0.2, ACCENT),
                border_radius=12,
                border=ft.border.all(2, cor) if is_atual else ft.border.all(1, theme.get_border()),
                on_click=lambda e, m=mes: nav_para_ano(ano_atual, m),
                ink=True,
                width=75,
            )
        )
    
    grid_meses = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text(f"📅 {ano_atual}", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Clique para filtrar por mês", size=12, color=TEXT_SECONDARY),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=10),
            ft.Row(meses_grid, spacing=8, wrap=True, run_spacing=8),
        ]),
        padding=20,
        bgcolor=SURFACE,
        border_radius=16,
        border=ft.border.all(1, theme.get_border()),
    )
    
    # ═══ CARDS DE ANOS ═══
    anos_disponiveis = list(range(2019, ano_atual + 1))
    
    def criar_card_ano(ano):
        dados = resumo_anos.get(ano, {})
        total = dados.get('total', 0) or 0
        pagos = dados.get('pagos', 0) or 0
        pendentes = total - pagos
        valor = dados.get('valor_total', 0) or 0
        
        # Cor
        if total == 0:
            cor = theme.get_surface_hover()
        elif pagos == total:
            cor = SUCCESS
        elif pendentes > pagos:
            cor = WARNING
        else:
            cor = ACCENT
        
        pct = (pagos / total * 100) if total > 0 else 0
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(str(ano), size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Container(
                        content=ft.Text(f"{pct:.0f}%", size=10, color=TEXT_PRIMARY),
                        bgcolor=cor,
                        border_radius=10,
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                ft.Row([
                    ft.Column([
                        ft.Text(str(total), size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text("Total", size=9, color=TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([
                        ft.Text(str(pagos), size=16, weight=ft.FontWeight.BOLD, color=SUCCESS),
                        ft.Text("Pagos", size=9, color=TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([
                        ft.Text(str(pendentes), size=16, weight=ft.FontWeight.BOLD, color=WARNING),
                        ft.Text("Pend.", size=9, color=TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Container(height=10),
                ft.Text(formatar_moeda(valor, ocultar), size=14, weight=ft.FontWeight.W_600, color=cor),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Row([
                        ft.Text("Abrir", size=12, color=TEXT_PRIMARY),
                        ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color=TEXT_PRIMARY),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
                    bgcolor=cor,
                    border_radius=10,
                    padding=ft.padding.symmetric(vertical=10, horizontal=15),
                    on_click=lambda e, a=ano: nav_para_ano(a),
                    ink=True,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            bgcolor=SURFACE,
            border_radius=16,
            border=ft.border.all(1, theme.get_border()),
            width=200,
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.15, "#000000")),
        )
    
    anos_row = ft.Row(
        [criar_card_ano(ano) for ano in reversed(anos_disponiveis)],
        spacing=15,
        wrap=True,
        run_spacing=15,
    )
    
    # ═══ LAYOUT PRINCIPAL ═══
    return ft.Container(
        content=ft.Column([
            # Header
            ft.Row([
                ft.Column([
                    ft.Text("Dashboard", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text("Visão geral dos honorários", size=14, color=TEXT_SECONDARY),
                ], spacing=2),
            ]),
            ft.Container(height=25),
            
            # Cards
            cards,
            ft.Container(height=25),
            
            # Meses
            grid_meses,
            ft.Container(height=25),
            
            # Anos
            ft.Text("📆 Anos", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Container(height=10),
            anos_row,
        ], scroll=ft.ScrollMode.AUTO),
        expand=True,
        padding=30,
        bgcolor=BG,
    )

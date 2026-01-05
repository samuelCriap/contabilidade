"""
Tela de Agenda - Visual Moderno
Calendário de cobranças com suporte light/dark
"""
import flet as ft
from datetime import datetime
import calendar

from database import listar_honorarios, marcar_como_pago, get_connection, registrar_log
from utils.theme import CORES
from utils.toast import toast_success


MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


def criar_tela_agenda(page: ft.Page, theme, usuario_logado=None):
    """Tela de agenda moderna"""
    
    # Cores dinâmicas
    BG = theme.get_bg()
    SURFACE = theme.get_surface()
    SURFACE_HOVER = theme.get_surface_hover()
    TEXT_PRIMARY = theme.get_text_color()
    TEXT_SECONDARY = theme.get_text_secondary()
    ACCENT = CORES["accent"]
    SUCCESS = CORES["success"]
    WARNING = CORES["warning"]
    DANGER = CORES["danger"]
    
    hoje = datetime.now()
    mes_atual = [hoje.month]
    ano_atual = [hoje.year]
    
    calendario_container = ft.Container()
    detalhes_container = ft.Column([], scroll=ft.ScrollMode.AUTO)
    titulo_mes = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
    
    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def get_honorarios_dia(dia, mes, ano):
        """Honorários que vencem no dia 10 do mês seguinte"""
        if dia != 10:
            return []
        
        mes_ref = mes - 1 if mes > 1 else 12
        ano_ref = ano if mes > 1 else ano - 1
        
        honorarios = listar_honorarios(ano=ano_ref)
        return [h for h in honorarios if h['mes'] == mes_ref]
    
    def criar_celula(dia, mes, ano):
        if dia == 0:
            return ft.Container(width=45, height=45)
        
        is_hoje = (dia == hoje.day and mes == hoje.month and ano == hoje.year)
        honorarios_dia = get_honorarios_dia(dia, mes, ano)
        
        pendentes = sum(1 for h in honorarios_dia if h['status'] != 'PAGO')
        pagos = sum(1 for h in honorarios_dia if h['status'] == 'PAGO')
        
        if pendentes > 0:
            cor = WARNING
            badge = f"{pendentes}"
        elif pagos > 0:
            cor = SUCCESS
            badge = f"{pagos}"
        else:
            cor = None
            badge = None
        
        return ft.Container(
            content=ft.Column([
                ft.Text(str(dia), size=12, weight=ft.FontWeight.BOLD if is_hoje else ft.FontWeight.NORMAL,
                       color=TEXT_PRIMARY if is_hoje else TEXT_SECONDARY),
                ft.Container(
                    content=ft.Text(badge, size=8, color=TEXT_PRIMARY) if badge else None,
                    bgcolor=cor,
                    border_radius=8,
                    padding=2,
                    visible=badge is not None,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            width=45,
            height=45,
            bgcolor=ACCENT if is_hoje else (ft.Colors.with_opacity(0.2, cor) if cor else SURFACE),
            border_radius=8,
            alignment=ft.alignment.center,
            on_click=lambda e, d=dia: mostrar_detalhes(d, mes, ano),
            ink=True,
        )
    
    def mostrar_detalhes(dia, mes, ano):
        honorarios = get_honorarios_dia(dia, mes, ano)
        detalhes_container.controls.clear()
        
        if not honorarios:
            detalhes_container.controls.append(
                ft.Text(f"Nenhum vencimento em {dia:02d}/{mes:02d}", size=12, color=TEXT_SECONDARY)
            )
        else:
            mes_ref = mes - 1 if mes > 1 else 12
            ano_ref = ano if mes > 1 else ano - 1
            
            detalhes_container.controls.append(
                ft.Text(f"📅 Vencimentos {dia:02d}/{mes:02d}", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
            )
            detalhes_container.controls.append(
                ft.Text(f"Ref: {MESES[mes_ref-1]}/{ano_ref}", size=11, color=TEXT_SECONDARY)
            )
            detalhes_container.controls.append(ft.Container(height=10))
            
            for h in honorarios:
                cor = SUCCESS if h['status'] == 'PAGO' else WARNING
                detalhes_container.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(h['cliente_nome'][:20], size=11, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                ft.Text(formatar_moeda(h['valor']), size=10, color=TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Text(h['status'][:4], size=9, color=TEXT_PRIMARY),
                                bgcolor=cor,
                                border_radius=4,
                                padding=5,
                            ),
                            ft.IconButton(
                                ft.Icons.CHECK_CIRCLE,
                                icon_color=SUCCESS,
                                icon_size=18,
                                visible=h['status'] != 'PAGO',
                                on_click=lambda e, hid=h['id']: marcar_e_atualizar(hid, dia, mes, ano),
                            ) if h['status'] != 'PAGO' else ft.Container(),
                        ]),
                        padding=10,
                        bgcolor=SURFACE,
                        border_radius=8,
                        border=ft.border.all(1, cor),
                    )
                )
        
        page.update()
    
    def marcar_e_atualizar(hid, dia, mes, ano):
        # Buscar dados do honorário para log detalhado
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT h.*, c.nome as cliente_nome 
            FROM honorarios h 
            JOIN clientes c ON h.cliente_id = c.id
            WHERE h.id = ?
        """, (hid,))
        hon = cursor.fetchone()
        conn.close()
        
        marcar_como_pago(hid)
        
        # Log detalhado
        username = usuario_logado[0].get('username', 'desconhecido') if usuario_logado and usuario_logado[0] else 'desconhecido'
        if hon:
            detalhes = f"Cliente: {hon['cliente_nome']} | Venc: {dia:02d}/{mes:02d}/{ano} | R$ {hon['valor']:.2f}"
        else:
            detalhes = f"ID: {hid}"
        registrar_log(username, "Baixa em honorário (PAGO)", tabela="honorarios", registro_id=hid, detalhes=detalhes)
        toast_success(page, "Marcado como pago!")
        atualizar_calendario()
        mostrar_detalhes(dia, mes, ano)
    
    def atualizar_calendario():
        mes = mes_atual[0]
        ano = ano_atual[0]
        titulo_mes.value = f"{MESES[mes-1]} {ano}"
        
        dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        header = ft.Row([
            ft.Container(
                content=ft.Text(d, size=10, color=TEXT_SECONDARY),
                width=45,
                alignment=ft.alignment.center,
            ) for d in dias_semana
        ], spacing=5)
        
        cal = calendar.Calendar(firstweekday=0)
        dias = list(cal.itermonthdays(ano, mes))
        
        semanas = []
        semana = []
        
        for dia in dias:
            semana.append(criar_celula(dia, mes, ano))
            if len(semana) == 7:
                semanas.append(ft.Row(semana, spacing=5))
                semana = []
        
        if semana:
            while len(semana) < 7:
                semana.append(ft.Container(width=45, height=45))
            semanas.append(ft.Row(semana, spacing=5))
        
        calendario_container.content = ft.Column([header, *semanas], spacing=5)
        page.update()
    
    def mudar_mes(delta):
        mes_atual[0] += delta
        if mes_atual[0] > 12:
            mes_atual[0] = 1
            ano_atual[0] += 1
        elif mes_atual[0] < 1:
            mes_atual[0] = 12
            ano_atual[0] -= 1
        atualizar_calendario()
    
    # Resumo
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status = 'PAGO' THEN 1 ELSE 0 END) as pagos,
               SUM(CASE WHEN status != 'PAGO' THEN valor ELSE 0 END) as valor_pendente
        FROM honorarios WHERE ano = ?
    """, (ano_atual[0],))
    resumo = cursor.fetchone()
    conn.close()
    
    total = resumo['total'] or 0
    pagos = resumo['pagos'] or 0
    pendentes = total - pagos
    valor_pendente = resumo['valor_pendente'] or 0
    
    resumo_row = ft.Container(
        content=ft.Row([
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
                ft.Text("Pendentes", size=9, color=TEXT_SECONDARY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([
                ft.Text(formatar_moeda(valor_pendente), size=14, weight=ft.FontWeight.BOLD, color=DANGER),
                ft.Text("A Receber", size=9, color=TEXT_SECONDARY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
        padding=15,
        bgcolor=SURFACE,
        border_radius=12,
    )
    
    atualizar_calendario()
    
    return ft.Container(
        content=ft.Column([
            ft.Text("📅 Agenda de Cobranças", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Container(height=15),
            resumo_row,
            ft.Container(height=20),
            
            # Navegação
            ft.Row([
                ft.IconButton(ft.Icons.CHEVRON_LEFT, icon_color=ACCENT, on_click=lambda e: mudar_mes(-1)),
                titulo_mes,
                ft.IconButton(ft.Icons.CHEVRON_RIGHT, icon_color=ACCENT, on_click=lambda e: mudar_mes(1)),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=10),
            
            # Layout
            ft.Row([
                ft.Container(
                    content=calendario_container,
                    padding=15,
                    bgcolor=SURFACE,
                    border_radius=12,
                    expand=True,
                ),
                ft.Container(
                    content=detalhes_container,
                    width=300,
                    padding=15,
                    bgcolor=SURFACE,
                    border_radius=12,
                ),
            ], spacing=15, expand=True),
        ]),
        expand=True,
        padding=30,
        bgcolor=BG,
    )

"""
Tela de Honorários por Ano - Gerenciamento completo
OTIMIZADO: Query única, suporte light/dark
"""
import flet as ft
from datetime import datetime
import csv
import os

from database import (
    listar_honorarios, listar_clientes, adicionar_honorario,
    marcar_como_pago, atualizar_honorario, get_connection, registrar_log
)
from utils.theme import CORES
from utils.toast import toast_success, toast_error, toast_warning


MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez", "13º"]


def criar_tela_honorarios_ano(page: ft.Page, ano: int, mes_filtro, theme, voltar_callback, usuario_logado=None):
    """Tela de honorários do ano OTIMIZADA"""
    
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
    
    filtro_mes = [mes_filtro]
    filtro_cliente = [""]
    dados_tabela = []
    
    # Cache de códigos internos (carrega uma única vez)
    codigos_cache = {}
    
    # Container para linhas (não usa DataTable que é pesado)
    lista_honorarios = ft.Column([], spacing=4, scroll=ft.ScrollMode.AUTO)
    
    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def carregar_codigos():
        """Carrega todos os códigos internos em uma única query"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, codigo_interno FROM clientes")
        for row in cursor.fetchall():
            codigos_cache[row['id']] = row['codigo_interno'] or str(row['id'])
        conn.close()
    
    def criar_linha(h):
        codigo = codigos_cache.get(h['cliente_id'], str(h['cliente_id']))
        status = h['status']
        cor_status = SUCCESS if status == "PAGO" else WARNING if status == "PENDENTE" else DANGER
        
        return ft.Container(
            content=ft.Row([
                ft.Text(codigo, size=10, width=50, color=TEXT_SECONDARY),
                ft.Text(h['cliente_nome'][:25], size=11, width=200, color=TEXT_PRIMARY),
                ft.Text(MESES[h['mes']-1] if h['mes'] <= 13 else str(h['mes']), size=11, width=50, color=TEXT_SECONDARY),
                ft.Text(formatar_moeda(h['valor']), size=11, width=100, color=ACCENT),
                ft.Container(
                    content=ft.Text(status[:4], size=9, color=TEXT_PRIMARY),
                    bgcolor=cor_status,
                    border_radius=4,
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    width=60,
                ),
                ft.Row([
                    ft.IconButton(
                        ft.Icons.CHECK_CIRCLE,
                        icon_color=SUCCESS,
                        icon_size=18,
                        on_click=lambda e, hid=h['id']: marcar_pago(hid),
                        visible=status != "PAGO",
                    ) if status != "PAGO" else ft.Container(width=40),
                    ft.IconButton(
                        ft.Icons.EDIT,
                        icon_color=ACCENT,
                        icon_size=18,
                        on_click=lambda e, hon=h: abrir_modal_editar(hon),
                    ),
        ], spacing=0, width=80),
            ]),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=SURFACE,
            border_radius=8,
            border=ft.border.all(1, theme.get_border()),
        )
    
    # Paginação para performance
    ITEMS_PER_PAGE = 100
    itens_exibidos = [0]
    
    btn_carregar_mais = ft.ElevatedButton(
        "Carregar mais...",
        bgcolor=ACCENT,
        color=TEXT_PRIMARY,
        visible=False,
        on_click=lambda e: carregar_mais(),
    )
    
    info_paginacao = ft.Text("", size=11, color=TEXT_SECONDARY)
    
    def carregar_mais():
        """Carrega mais itens da lista"""
        inicio = itens_exibidos[0]
        fim = min(inicio + ITEMS_PER_PAGE, len(dados_tabela))
        
        for i in range(inicio, fim):
            lista_honorarios.controls.append(criar_linha(dados_tabela[i]))
        
        itens_exibidos[0] = fim
        btn_carregar_mais.visible = fim < len(dados_tabela)
        info_paginacao.value = f"Exibindo {fim} de {len(dados_tabela)}"
        page.update()
    
    def carregar_dados():
        nonlocal dados_tabela
        lista_honorarios.controls.clear()
        itens_exibidos[0] = 0
        
        honorarios = listar_honorarios(ano=ano)
        dados_tabela = []
        
        for h in honorarios:
            if filtro_mes[0] and h['mes'] != filtro_mes[0]:
                continue
            if filtro_cliente[0] and filtro_cliente[0].lower() not in h['cliente_nome'].lower():
                continue
            
            dados_tabela.append(h)
        
        # Carregar só os primeiros itens
        fim = min(ITEMS_PER_PAGE, len(dados_tabela))
        for i in range(fim):
            lista_honorarios.controls.append(criar_linha(dados_tabela[i]))
        
        itens_exibidos[0] = fim
        btn_carregar_mais.visible = fim < len(dados_tabela)
        info_paginacao.value = f"Exibindo {fim} de {len(dados_tabela)}" if len(dados_tabela) > ITEMS_PER_PAGE else f"{len(dados_tabela)} itens"
        
        page.update()
    
    def marcar_pago(honorario_id):
        # Buscar dados do honorário para log detalhado
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT h.*, c.nome as cliente_nome 
            FROM honorarios h 
            JOIN clientes c ON h.cliente_id = c.id
            WHERE h.id = ?
        """, (honorario_id,))
        hon = cursor.fetchone()
        conn.close()
        
        if not hon:
            toast_error(page, "Honorário não encontrado!")
            return
        
        # Formas de pagamento disponíveis
        FORMAS_PAGAMENTO = ["Boleto", "PIX", "Cartão", "Asaas", "Dinheiro", "Cheque"]
        
        # Data atual formatada
        hoje = datetime.now()
        
        forma_dd = ft.Dropdown(
            label="Forma de Pagamento",
            width=300,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            color=TEXT_PRIMARY,
            options=[ft.dropdown.Option(f, f) for f in FORMAS_PAGAMENTO],
            value="PIX",
        )
        
        data_field = ft.TextField(
            label="Data do Pagamento",
            width=300,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            color=TEXT_PRIMARY,
            value=hoje.strftime("%d/%m/%Y"),
            hint_text="DD/MM/AAAA",
        )
        
        def confirmar_pagamento(e):
            forma = forma_dd.value
            data_str = data_field.value
            
            # Converter data para formato do banco
            try:
                if "/" in data_str:
                    partes = data_str.split("/")
                    data_pagamento = f"{partes[2]}-{partes[1]}-{partes[0]}"
                else:
                    data_pagamento = data_str
            except:
                data_pagamento = hoje.strftime("%Y-%m-%d")
            
            marcar_como_pago(honorario_id, forma_pagamento=forma, data_pagamento=data_pagamento)
            
            # Log detalhado
            username = usuario_logado[0].get('username', 'desconhecido') if usuario_logado and usuario_logado[0] else 'desconhecido'
            mes_nome = MESES[hon['mes']-1] if hon['mes'] <= 13 else str(hon['mes'])
            detalhes = f"Cliente: {hon['cliente_nome']} | {mes_nome}/{hon['ano']} | R$ {hon['valor']:.2f} | {forma} | {data_str}"
            registrar_log(username, "Baixa em honorário (PAGO)", tabela="honorarios", registro_id=honorario_id, detalhes=detalhes)
            
            dlg.open = False
            page.update()
            toast_success(page, f"Marcado como pago via {forma}!")
            carregar_dados()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("💰 Registrar Pagamento", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            bgcolor=BG,
            content=ft.Column([
                ft.Text(f"Cliente: {hon['cliente_nome']}", size=13, color=TEXT_SECONDARY),
                ft.Text(f"Referência: {MESES[hon['mes']-1]}/{hon['ano']}", size=12, color=TEXT_SECONDARY),
                ft.Text(f"Valor: {formatar_moeda(hon['valor'])}", size=14, color=ACCENT, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                forma_dd,
                ft.Container(height=10),
                data_field,
            ], spacing=8, width=320),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dlg, 'open', False) or page.update()),
                ft.ElevatedButton("Confirmar", bgcolor=SUCCESS, color=TEXT_PRIMARY, on_click=confirmar_pagamento),
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
    
    def abrir_modal_novo():
        clientes = sorted(listar_clientes(), key=lambda c: int(c['codigo_interno']) if c['codigo_interno'] and c['codigo_interno'].isdigit() else float('inf'))
        if not clientes:
            toast_warning(page, "Cadastre clientes primeiro!")
            return
        
        cliente_dd = ft.Dropdown(
            label="Cliente", width=300, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
            options=[ft.dropdown.Option(str(c['id']), c['nome']) for c in clientes],
        )
        mes_dd = ft.Dropdown(
            label="Mês", width=300, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
            options=[ft.dropdown.Option(str(i+1), MESES[i]) for i in range(13)],
        )
        valor_field = ft.TextField(label="Valor", width=300, prefix_text="R$ ", 
                                  bgcolor=INPUT_BG, border_color=INPUT_BORDER, color=TEXT_PRIMARY)
        
        def salvar(e):
            if not cliente_dd.value or not mes_dd.value or not valor_field.value:
                toast_error(page, "Preencha todos os campos!")
                return
            try:
                adicionar_honorario(
                    cliente_id=int(cliente_dd.value),
                    ano=ano,
                    mes=int(mes_dd.value),
                    valor=float(valor_field.value.replace(",", ".")),
                )
                toast_success(page, "Honorário adicionado!")
                dlg.open = False
                carregar_dados()
            except:
                toast_error(page, "Valor inválido!")
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"➕ Novo - {ano}", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            bgcolor=BG,
            content=ft.Column([cliente_dd, mes_dd, valor_field], spacing=12, width=320),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dlg, 'open', False) or page.update()),
                ft.ElevatedButton("Salvar", bgcolor=SUCCESS, color=TEXT_PRIMARY, on_click=salvar),
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
    
    def abrir_modal_editar(h):
        status_dd = ft.Dropdown(
            label="Status", width=300, value=h['status'], bgcolor=INPUT_BG, border_color=INPUT_BORDER,
            options=[
                ft.dropdown.Option("PENDENTE", "Pendente"),
                ft.dropdown.Option("PAGO", "Pago"),
                ft.dropdown.Option("ATRASADO", "Atrasado"),
            ],
        )
        
        def salvar(e):
            atualizar_honorario(h['id'], status=status_dd.value)
            toast_success(page, "Atualizado!")
            dlg.open = False
            carregar_dados()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("✏️ Editar", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            bgcolor=BG,
            content=ft.Column([
                ft.Text(f"Cliente: {h['cliente_nome']}", size=12, color=TEXT_SECONDARY),
                ft.Text(f"Mês: {MESES[h['mes']-1]}", size=12, color=TEXT_SECONDARY),
                ft.Container(height=10),
                status_dd,
            ], spacing=8, width=320),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dlg, 'open', False) or page.update()),
                ft.ElevatedButton("Salvar", bgcolor=ACCENT, color=TEXT_PRIMARY, on_click=salvar),
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
    
    def exportar_csv(e):
        if not dados_tabela:
            toast_warning(page, "Nenhum dado!")
            return
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filepath = os.path.join(desktop, f"honorarios_{ano}.csv")
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Cliente", "Mês", "Valor", "Status"])
                for h in dados_tabela:
                    writer.writerow([h['cliente_nome'], MESES[h['mes']-1], h['valor'], h['status']])
            toast_success(page, f"Exportado: {filepath}")
        except Exception as ex:
            toast_error(page, str(ex))
    
    def on_filtro_mes_change(e):
        filtro_mes[0] = int(e.control.value) if e.control.value else None
        carregar_dados()
    
    filtro_mes_dd = ft.Dropdown(
        label="Mês", width=130,
        value=str(mes_filtro) if mes_filtro else None,
        bgcolor=INPUT_BG, border_color=INPUT_BORDER,
        color=TEXT_PRIMARY, label_style=ft.TextStyle(color=TEXT_SECONDARY),
        options=[ft.dropdown.Option("", "Todos")] + [ft.dropdown.Option(str(i+1), MESES[i]) for i in range(13)],
        on_change=on_filtro_mes_change,
    )
    
    busca = ft.TextField(
        label="Buscar", width=200, prefix_icon=ft.Icons.SEARCH,
        bgcolor=INPUT_BG, border_color=INPUT_BORDER, color=TEXT_PRIMARY,
        on_change=lambda e: (filtro_cliente.__setitem__(0, e.control.value or ""), carregar_dados())[1],
    )
    
    # Carregar dados
    carregar_codigos()
    carregar_dados()
    
    # Header da lista
    header = ft.Container(
        content=ft.Row([
            ft.Text("Cód", size=9, width=50, color=TEXT_SECONDARY),
            ft.Text("Cliente", size=9, width=200, color=TEXT_SECONDARY),
            ft.Text("Mês", size=9, width=50, color=TEXT_SECONDARY),
            ft.Text("Valor", size=9, width=100, color=TEXT_SECONDARY),
            ft.Text("Status", size=9, width=60, color=TEXT_SECONDARY),
            ft.Text("Ações", size=9, width=80, color=TEXT_SECONDARY),
        ]),
        padding=ft.padding.symmetric(horizontal=12, vertical=5),
    )
    
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ACCENT, on_click=lambda e: voltar_callback()),
                ft.Text(f"📅 {ano}", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(expand=True),
                ft.ElevatedButton("➕ Novo", bgcolor=SUCCESS, color=TEXT_PRIMARY, on_click=lambda e: abrir_modal_novo()),
                ft.ElevatedButton("📤 CSV", bgcolor=ACCENT, color=TEXT_PRIMARY, on_click=exportar_csv),
            ]),
            ft.Container(height=15),
            ft.Row([filtro_mes_dd, busca], spacing=10),
            ft.Container(height=10),
            header,
            ft.Container(
                content=lista_honorarios,
                expand=True,
                border_radius=10,
                padding=5,
            ),
            ft.Row([info_paginacao, ft.Container(expand=True), btn_carregar_mais], spacing=10),
        ]),
        expand=True,
        padding=25,
        bgcolor=BG,
    )

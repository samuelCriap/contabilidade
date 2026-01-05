"""
Tela de Relatórios - Visual Moderno
OTIMIZADO: Gráficos Flet nativos, lazy loading, suporte light/dark
"""
import flet as ft
from datetime import datetime
import os
import csv

from database import get_connection, listar_clientes, get_relatorio_cliente, get_honorarios_vencendo, listar_logs, listar_certificados, get_relatorio_formas_pagamento
from utils.theme import CORES
from utils.toast import toast_success, toast_error, toast_info


MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def criar_tela_relatorios(page: ft.Page, theme, is_admin=True):
    """Tela de relatórios moderna"""
    
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
    PURPLE = CORES["purple"]
    
    ano_atual = datetime.now().year
    ano_selecionado = [ano_atual]
    conteudo_tab = ft.Container(expand=True)
    
    def formatar_moeda(valor, ocultar=False):
        if ocultar:
            return "R$ *****"
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # ═══ TAB 1: DASHBOARD ═══
    def criar_dashboard():
        ano = ano_selecionado[0]
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Resumo do ano
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'PAGO' THEN 1 ELSE 0 END) as pagos,
                SUM(valor) as valor_total,
                SUM(CASE WHEN status = 'PAGO' THEN valor ELSE 0 END) as valor_recebido
            FROM honorarios WHERE ano = ?
        """, (ano,))
        resumo = cursor.fetchone()
        
        # Por mês
        cursor.execute("""
            SELECT mes, SUM(valor) as total_valor,
                   SUM(CASE WHEN status = 'PAGO' THEN valor ELSE 0 END) as valor_pago
            FROM honorarios WHERE ano = ? AND mes <= 12
            GROUP BY mes ORDER BY mes
        """, (ano,))
        dados_meses = {row['mes']: dict(row) for row in cursor.fetchall()}
        conn.close()
        
        total = resumo['total'] or 0
        pagos = resumo['pagos'] or 0
        pendentes = total - pagos
        valor_total = resumo['valor_total'] or 0
        valor_recebido = resumo['valor_recebido'] or 0
        pct = (pagos / total * 100) if total > 0 else 0
        
        # Cards
        def criar_card(titulo, valor, cor, icone):
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icone, size=18, color=cor),
                        bgcolor=ft.Colors.with_opacity(0.15, cor),
                        border_radius=8,
                        padding=8,
                    ),
                    ft.Column([
                        ft.Text(titulo, size=10, color=TEXT_SECONDARY),
                        ft.Text(valor, size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ], spacing=2),
                ], spacing=10),
                padding=15,
                bgcolor=SURFACE,
                border_radius=12,
                expand=True,
            )
        
        # Barras visuais
        max_valor = max([d.get('total_valor', 0) or 0 for d in dados_meses.values()] or [1])
        
        barras = []
        for mes in range(1, 13):
            dados = dados_meses.get(mes, {'total_valor': 0, 'valor_pago': 0})
            total_v = dados.get('total_valor', 0) or 0
            pago_v = dados.get('valor_pago', 0) or 0
            
            altura = int((total_v / max_valor) * 100) if max_valor > 0 else 0
            altura_pago = int((pago_v / max_valor) * 100) if max_valor > 0 else 0
            
            barras.append(
                ft.Column([
                    ft.Container(height=100 - altura),
                    ft.Container(
                        content=ft.Column([
                            ft.Container(width=24, height=altura - altura_pago, bgcolor=ft.Colors.with_opacity(0.3, ACCENT)),
                            ft.Container(width=24, height=altura_pago, bgcolor=SUCCESS),
                        ], spacing=0),
                    ),
                    ft.Text(MESES[mes-1], size=8, color=TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
            )
        
        grafico_barras = ft.Container(
            content=ft.Column([
                ft.Text(f"Receita Mensal - {ano}", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=10),
                ft.Row(barras, spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),
                ft.Row([
                    ft.Container(width=12, height=12, bgcolor=ft.Colors.with_opacity(0.3, ACCENT)),
                    ft.Text("Total", size=10, color=TEXT_SECONDARY),
                    ft.Container(width=20),
                    ft.Container(width=12, height=12, bgcolor=SUCCESS),
                    ft.Text("Recebido", size=10, color=TEXT_SECONDARY),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ]),
            padding=20,
            bgcolor=SURFACE,
            border_radius=16,
            expand=2,
        )
        
        # Pizza visual
        pizza = ft.Container(
            content=ft.Column([
                ft.Text("Status", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=15),
                ft.Stack([
                    ft.Container(
                        width=100, height=100,
                        border_radius=50,
                        bgcolor=WARNING,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"{pct:.0f}%", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Text("pagos", size=10, color=TEXT_SECONDARY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                        width=100, height=100,
                        border_radius=50,
                        gradient=ft.SweepGradient(
                            colors=[SUCCESS, SUCCESS, WARNING, WARNING],
                            stops=[0, pct/100, pct/100, 1],
                            center=ft.alignment.center,
                        ),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        width=70, height=70,
                        border_radius=35,
                        bgcolor=SURFACE,
                        left=15, top=15,
                    ),
                ]),
                ft.Container(height=15),
                ft.Row([
                    ft.Text(f"✅ {pagos}", size=12, color=SUCCESS),
                    ft.Text(f"⏳ {pendentes}", size=12, color=WARNING),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            bgcolor=SURFACE,
            border_radius=16,
            expand=1,
        )
        
        return ft.Column([
            ft.Row([
                criar_card("Total", str(total), ACCENT, ft.Icons.FOLDER),
                criar_card("Pagos", str(pagos), SUCCESS, ft.Icons.CHECK_CIRCLE),
                criar_card("Pendentes", str(pendentes), WARNING, ft.Icons.PENDING),
                criar_card("Valor", formatar_moeda(valor_total, not is_admin), PURPLE, ft.Icons.ATTACH_MONEY),
            ], spacing=12),
            ft.Container(height=20),
            ft.Row([grafico_barras, pizza], spacing=15),
        ], scroll=ft.ScrollMode.AUTO)
    
    # ═══ TAB 2: POR CLIENTE ═══
    def criar_por_cliente():
        clientes = sorted(listar_clientes(), key=lambda c: int(c['codigo_interno']) if c['codigo_interno'] and c['codigo_interno'].isdigit() else float('inf'))
        cliente_dd = ft.Dropdown(
            label="Cliente", width=350, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
            options=[ft.dropdown.Option(str(c['id']), f"{c['codigo_interno'] or c['id']} - {c['nome'][:25]}") for c in clientes],
        )
        resultado = ft.Column([], scroll=ft.ScrollMode.AUTO)
        dados_cliente_atual = [None]  # Lista para permitir modificação dentro de nested functions
        
        # Botões de exportação (inicialmente desabilitados)
        btn_pdf = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.PICTURE_AS_PDF, size=16),
                ft.Text("PDF", size=12),
            ], spacing=5),
            bgcolor=DANGER, color=TEXT_PRIMARY, disabled=True,
        )
        btn_excel = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.TABLE_CHART, size=16),
                ft.Text("Excel", size=12),
            ], spacing=5),
            bgcolor=SUCCESS, color=TEXT_PRIMARY, disabled=True,
        )
        
        def carregar(e):
            if not cliente_dd.value:
                return
            dados = get_relatorio_cliente(int(cliente_dd.value))
            if not dados:
                return
            
            dados_cliente_atual[0] = dados  # Guardar para exportação
            resultado.controls.clear()
            c = dados['cliente']
            
            resultado.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(c['nome'], size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text(f"Código: {c['codigo_interno'] or c['id']}", size=11, color=TEXT_SECONDARY),
                    ]),
                    padding=15, bgcolor=SURFACE, border_radius=12,
                )
            )
            
            resultado.controls.append(ft.Container(height=10))
            resultado.controls.append(
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Total", size=10, color=TEXT_SECONDARY),
                            ft.Text(formatar_moeda(dados['total_geral']), size=16, weight=ft.FontWeight.BOLD, color=ACCENT),
                        ]), padding=12, bgcolor=SURFACE, border_radius=10, expand=True,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Pago", size=10, color=TEXT_SECONDARY),
                            ft.Text(formatar_moeda(dados['total_pago']), size=16, weight=ft.FontWeight.BOLD, color=SUCCESS),
                        ]), padding=12, bgcolor=SURFACE, border_radius=10, expand=True,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("DEVEDOR", size=10, color=DANGER),
                            ft.Text(formatar_moeda(dados['saldo_devedor']), size=16, weight=ft.FontWeight.BOLD, color=DANGER),
                        ]), padding=12, bgcolor=SURFACE, border_radius=10, border=ft.border.all(2, DANGER), expand=True,
                    ),
                ], spacing=10)
            )
            
            pendentes = [h for h in dados['honorarios'] if h['status'] != 'PAGO'][:10]
            if pendentes:
                resultado.controls.append(ft.Container(height=15))
                resultado.controls.append(ft.Text("⚠️ Pendentes", size=14, weight=ft.FontWeight.BOLD, color=WARNING))
                for h in pendentes:
                    mes = MESES[h['mes']-1] if h['mes'] <= 12 else "13º"
                    resultado.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(f"{mes}/{h['ano']}", size=11, width=70, color=TEXT_PRIMARY),
                                ft.Text(formatar_moeda(h['valor']), size=11, color=WARNING),
                            ]),
                            padding=8, bgcolor=ft.Colors.with_opacity(0.1, WARNING), border_radius=6,
                        )
                    )
            
            # Habilitar botões de exportação
            btn_pdf.disabled = False
            btn_excel.disabled = False
            page.update()
        
        # FilePicker para exportação
        def criar_file_picker():
            fp = ft.FilePicker()
            page.overlay.append(fp)
            return fp
        
        file_picker_export = criar_file_picker()
        
        def exportar_pdf(e):
            if not dados_cliente_atual[0]:
                toast_error(page, "Carregue um cliente primeiro!")
                return
            
            def on_result_pdf(ev):
                if not ev.path:
                    return
                try:
                    from utils.pdf_relatorio_cliente import gerar_pdf_relatorio_cliente
                    from database import get_config
                    
                    dados_empresa = {
                        'nome': get_config('empresa_nome', 'Escritório Contábil'),
                        'cnpj': get_config('empresa_cnpj', ''),
                        'endereco': get_config('empresa_endereco', ''),
                        'cidade': get_config('empresa_cidade', ''),
                        'telefone': get_config('empresa_telefone', ''),
                    }
                    
                    caminho = gerar_pdf_relatorio_cliente(
                        dados_relatorio=dados_cliente_atual[0],
                        pasta_destino=ev.path,
                        dados_empresa=dados_empresa
                    )
                    toast_success(page, f"PDF gerado com sucesso!")
                except Exception as ex:
                    toast_error(page, f"Erro: {str(ex)}")
            
            file_picker_export.on_result = on_result_pdf
            file_picker_export.get_directory_path(dialog_title="Pasta para salvar PDF")
        
        def exportar_excel(e):
            if not dados_cliente_atual[0]:
                toast_error(page, "Carregue um cliente primeiro!")
                return
            
            def on_result_excel(ev):
                if not ev.path:
                    return
                try:
                    from utils.excel_export import exportar_excel_cliente
                    
                    sucesso, resultado_exp = exportar_excel_cliente(
                        dados_relatorio=dados_cliente_atual[0],
                        pasta_destino=ev.path
                    )
                    
                    if sucesso:
                        toast_success(page, f"Excel gerado com sucesso!")
                    else:
                        toast_error(page, f"Erro: {resultado_exp}")
                except Exception as ex:
                    toast_error(page, f"Erro: {str(ex)}")
            
            file_picker_export.on_result = on_result_excel
            file_picker_export.get_directory_path(dialog_title="Pasta para salvar Excel")
        
        btn_pdf.on_click = exportar_pdf
        btn_excel.on_click = exportar_excel
        
        return ft.Column([
            ft.Row([
                cliente_dd,
                ft.ElevatedButton("Carregar", bgcolor=ACCENT, color=TEXT_PRIMARY, on_click=carregar),
                ft.Container(width=20),
                btn_pdf,
                btn_excel,
            ], spacing=10),
            ft.Container(height=15),
            resultado,
        ])
    
    # ═══ TAB 3: VENCIMENTOS ═══
    def criar_vencimentos():
        vencendo = get_honorarios_vencendo(dias=30)[:15]
        lista = ft.Column([], spacing=6)
        
        if not vencendo:
            lista.controls.append(ft.Text("✅ Nenhum vencimento próximo!", color=SUCCESS))
        else:
            for h in vencendo:
                mes = MESES[h['mes']-1] if h['mes'] <= 12 else "13º"
                lista.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.NOTIFICATIONS, color=WARNING, size=18),
                            ft.Text(h['cliente_nome'][:25], size=12, color=TEXT_PRIMARY, expand=True),
                            ft.Text(f"{mes}/{h['ano']}", size=11, color=TEXT_SECONDARY),
                            ft.Text(formatar_moeda(h['valor']), size=11, weight=ft.FontWeight.BOLD, color=WARNING),
                        ]),
                        padding=12, bgcolor=SURFACE, border_radius=10,
                    )
                )
        
        return ft.Column([
            ft.Text(f"🔔 {len(vencendo)} vencimentos", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Container(height=10),
            lista,
        ])
    
    # ═══ TAB 4: HISTÓRICO ═══
    def criar_historico():
        logs = listar_logs(limite=20)
        lista = ft.Column([], spacing=4)
        
        if not logs:
            lista.controls.append(ft.Text("Nenhum registro", color=TEXT_SECONDARY))
        else:
            for log in logs:
                lista.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(log['data_hora'][:16] if log['data_hora'] else "", size=10, color=TEXT_SECONDARY, width=110),
                            ft.Text(log['acao'], size=10, color=TEXT_PRIMARY, expand=True),
                        ]),
                        padding=8, bgcolor=SURFACE, border_radius=6,
                    )
                )
        
        return ft.Column([
            ft.Text("📋 Histórico", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Container(height=10),
            lista,
        ])
    
    # ═══ TAB 5: CERTIFICADOS ═══
    def criar_relatorio_certificados():
        from datetime import datetime, timedelta
        
        certs = listar_certificados()
        hoje = datetime.now()
        
        # Estatísticas
        total = len(certs)
        ativos = sum(1 for c in certs if c['status'] == 'ATIVO')
        vencidos = sum(1 for c in certs if c['status'] == 'VENCIDO')
        vencendo_30 = 0
        valor_total = sum(c['valor'] for c in certs)
        
        for cert in certs:
            try:
                data_venc = datetime.strptime(cert['data_vencimento'], "%Y-%m-%d")
                dias = (data_venc - hoje).days
                if 0 <= dias <= 30 and cert['status'] == 'ATIVO':
                    vencendo_30 += 1
            except:
                pass
        
        # Cards de resumo
        def card_stat(titulo, valor, cor, icone):
            return ft.Container(
                content=ft.Row([
                    ft.Icon(icone, size=24, color=cor),
                    ft.Column([
                        ft.Text(titulo, size=10, color=TEXT_SECONDARY),
                        ft.Text(str(valor), size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ], spacing=2)
                ], spacing=10),
                padding=15, bgcolor=SURFACE, border_radius=12, border=ft.border.all(1, theme.get_border()),
                expand=True,
            )
        
        cards = ft.Row([
            card_stat("Total", total, ACCENT, ft.Icons.VERIFIED_USER),
            card_stat("Ativos", ativos, SUCCESS, ft.Icons.CHECK_CIRCLE_OUTLINE),
            card_stat("Vencidos", vencidos, DANGER, ft.Icons.ERROR_OUTLINE),
            card_stat("Vencendo 30d", vencendo_30, WARNING, ft.Icons.WARNING_AMBER_OUTLINED),
        ], spacing=10)
        
        # Lista de certificados
        lista = ft.Column([], spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)
        
        for cert in certs:
            nome = cert.get('cliente_nome') or cert.get('nome_avulso') or 'Avulso'
            try:
                data_venc = datetime.strptime(cert['data_vencimento'], "%Y-%m-%d")
                dias = (data_venc - hoje).days
            except:
                dias = 0
            
            if cert['status'] == 'VENCIDO' or dias < 0:
                status_cor = DANGER
            elif dias <= 30:
                status_cor = WARNING
            else:
                status_cor = SUCCESS
            
            lista.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.VERIFIED_USER, size=16, color=status_cor),
                        ft.Text(nome[:25], size=11, color=TEXT_PRIMARY, width=150),
                        ft.Text(cert['tipo'], size=10, color=ACCENT, width=120),
                        ft.Text(cert['cpf_cnpj'] or '-', size=9, color=TEXT_SECONDARY, width=100),
                        ft.Text(data_venc.strftime("%d/%m/%Y") if dias else "-", size=10, color=status_cor, width=80),
                        ft.Text(f"{dias}d" if dias >= 0 else "VENC", size=10, color=status_cor, width=50),
                        ft.Text(formatar_moeda(cert['valor'], not is_admin), size=10, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, width=90),
                    ], spacing=8),
                    padding=10, bgcolor=SURFACE, border_radius=8, border=ft.border.all(1, theme.get_border()),
                )
            )
        
        return ft.Column([
            ft.Text("🔐 Certificados Digitais", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Container(height=10),
            cards,
            ft.Container(height=15),
            ft.Text(f"Total: {formatar_moeda(valor_total, not is_admin)}", size=12, color=ACCENT) if is_admin else ft.Container(),
            ft.Container(height=10),
            lista,
        ], expand=True)
    
    # ═══ TAB 6: PAGAMENTOS ═══
    def criar_relatorio_pagamentos():
        dados = get_relatorio_formas_pagamento(ano_selecionado[0])
        total_pago = sum(d['total'] for d in dados)
        
        lista = ft.Column([], spacing=10, scroll=ft.ScrollMode.AUTO)
        
        if not dados:
            lista.controls.append(ft.Text("Nenhum pagamento registrado neste ano.", color=TEXT_SECONDARY))
        
        cores_metodos = [ACCENT, SUCCESS, WARNING, PURPLE, DANGER, ft.Colors.TEAL, ft.Colors.INDIGO]
        
        for i, d in enumerate(dados):
            metodo = d['metodo']
            qtd = d['qtd']
            valor = d['total']
            percentual = (valor / total_pago * 100) if total_pago > 0 else 0
            cor = cores_metodos[i % len(cores_metodos)]
            
            # Icone baseado no nome
            icone = ft.Icons.PAYMENT
            if "pix" in metodo.lower(): icone = ft.Icons.PIX
            elif "dinheiro" in metodo.lower(): icone = ft.Icons.ATTACH_MONEY
            elif "boleto" in metodo.lower(): icone = ft.Icons.RECEIPT_LONG
            elif "asaas" in metodo.lower(): icone = ft.Icons.CLOUD_DONE
            elif "cart" in metodo.lower(): icone = ft.Icons.CREDIT_CARD
            
            lista.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(content=ft.Icon(icone, color=cor), padding=8, bgcolor=ft.Colors.with_opacity(0.1, cor), border_radius=8),
                            ft.Column([
                                ft.Text(metodo, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                ft.Text(f"{qtd} pagamentos", size=10, color=TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            ft.Column([
                                ft.Text(formatar_moeda(valor), weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, text_align=ft.TextAlign.RIGHT),
                                ft.Text(f"{percentual:.1f}%", size=10, color=TEXT_SECONDARY, text_align=ft.TextAlign.RIGHT),
                            ], spacing=2),
                        ]),
                        ft.ProgressBar(value=percentual/100, color=cor, bgcolor=ft.Colors.with_opacity(0.1, cor), height=6),
                    ], spacing=10),
                    padding=15, bgcolor=SURFACE, border_radius=12,
                )
            )
            
        return ft.Column([
            ft.Text(f"💰 Formas de Pagamento ({ano_selecionado[0]})", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Container(height=10),
            ft.Container(
                content=ft.Row([
                    ft.Text("Total Recebido:", color=TEXT_SECONDARY),
                    ft.Text(formatar_moeda(total_pago), weight=ft.FontWeight.BOLD, color=SUCCESS, size=16),
                ], alignment=ft.MainAxisAlignment.END),
                padding=10,
            ),
            lista,
        ], expand=True)

    # Navegação
    def mudar_tab(e):
        idx = e.control.selected_index
        if idx == 0:
            conteudo_tab.content = criar_dashboard()
        elif idx == 1:
            conteudo_tab.content = criar_por_cliente()
        elif idx == 2:
            conteudo_tab.content = criar_vencimentos()
        elif idx == 3:
            conteudo_tab.content = criar_historico()
        elif idx == 4:
            conteudo_tab.content = criar_relatorio_certificados()
        elif idx == 5:
            conteudo_tab.content = criar_relatorio_pagamentos()
        page.update()
    
    def mudar_ano(e):
        ano_selecionado[0] = int(e.control.value)
        conteudo_tab.content = criar_dashboard()
        page.update()
    
    ano_dd = ft.Dropdown(
        label="Ano", width=110, value=str(ano_atual), bgcolor=INPUT_BG, border_color=INPUT_BORDER,
        color=TEXT_PRIMARY, label_style=ft.TextStyle(color=TEXT_SECONDARY),
        options=[ft.dropdown.Option(str(a), str(a)) for a in range(2019, ano_atual + 1)],
        on_change=mudar_ano,
    )
    
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=150,
        on_change=mudar_tab,
        indicator_color=ACCENT,
        label_color=TEXT_PRIMARY,
        unselected_label_color=TEXT_SECONDARY,
        tabs=[
            ft.Tab(text="Dashboard"),
            ft.Tab(text="Por Cliente"),
            ft.Tab(text="Vencimentos"),
            ft.Tab(text="Histórico"),
            ft.Tab(text="Certificados"),
            ft.Tab(text="Pagamentos"),
        ],
    )
    
    conteudo_tab.content = criar_dashboard()
    
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("📊 Relatórios", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(expand=True),
                ano_dd,
            ]),
            ft.Container(height=10),
            tabs,
            ft.Container(height=15),
            conteudo_tab,
        ]),
        expand=True,
        padding=30,
        bgcolor=BG,
    )

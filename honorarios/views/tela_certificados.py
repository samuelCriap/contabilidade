"""
Tela de Certificados Digitais - Gerenciamento Completo
"""
import flet as ft
from datetime import datetime, timedelta

from database import (
    listar_clientes, listar_certificados, adicionar_certificado,
    buscar_certificado, atualizar_certificado, excluir_certificado,
    get_certificados_vencendo, registrar_log, get_connection
)
from utils.theme import CORES
from utils.toast import toast_success, toast_error, toast_warning


# Tipos de certificados
TIPOS_CERT = {
    "A1 PF": {"validade": 1, "categoria": "PF", "midia": None},
    "A1 PJ": {"validade": 1, "categoria": "PJ", "midia": None},
    "A3 PF Token 2 anos": {"validade": 2, "categoria": "PF", "midia": "Token"},
    "A3 PJ Token 2 anos": {"validade": 2, "categoria": "PJ", "midia": "Token"},
    "A3 PF Cartão 2 anos": {"validade": 2, "categoria": "PF", "midia": "Cartão"},
    "A3 PJ Cartão 2 anos": {"validade": 2, "categoria": "PJ", "midia": "Cartão"},
    "A3 PF Token 3 anos": {"validade": 3, "categoria": "PF", "midia": "Token"},
    "A3 PJ Token 3 anos": {"validade": 3, "categoria": "PJ", "midia": "Token"},
    "A3 PF Cartão 3 anos": {"validade": 3, "categoria": "PF", "midia": "Cartão"},
    "A3 PJ Cartão 3 anos": {"validade": 3, "categoria": "PJ", "midia": "Cartão"},
}


def criar_tela_certificados(page: ft.Page, theme, usuario_logado=None):
    """Tela de gerenciamento de certificados digitais"""
    
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
    
    lista_certificados = ft.Column([], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    filtro_status = ["TODOS"]
    
    from datetime import datetime
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month
    filtro_mes = [0]  # 0 = todos
    filtro_ano = [ano_atual]
    
    MESES = ["Todos", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    
    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def carregar_certificados():
        lista_certificados.controls.clear()
        
        status_filtro = filtro_status[0] if filtro_status[0] != "TODOS" else None
        certs = listar_certificados(status=status_filtro)
        
        # Filtrar por mês/ano da emissão
        if filtro_mes[0] > 0 or filtro_ano[0]:
            certs_filtrados = []
            for c in certs:
                try:
                    dt = datetime.strptime(c['data_emissao'], "%Y-%m-%d")
                    if filtro_ano[0] and dt.year != filtro_ano[0]:
                        continue
                    if filtro_mes[0] > 0 and dt.month != filtro_mes[0]:
                        continue
                    certs_filtrados.append(c)
                except:
                    certs_filtrados.append(c)
            certs = certs_filtrados
        
        if not certs:
            lista_certificados.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.VERIFIED_USER_OUTLINED, size=48, color=TEXT_SECONDARY),
                        ft.Text("Nenhum certificado cadastrado", color=TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    alignment=ft.alignment.center,
                    padding=40,
                )
            )
        else:
            for cert in certs:
                # Determinar status visual
                data_venc = datetime.strptime(cert['data_vencimento'], "%Y-%m-%d")
                dias_restantes = (data_venc - datetime.now()).days
                
                if cert['status'] == 'VENCIDO' or dias_restantes < 0:
                    status_cor = DANGER
                    status_icon = ft.Icons.ERROR_OUTLINE
                elif dias_restantes <= 30:
                    status_cor = WARNING
                    status_icon = ft.Icons.WARNING_AMBER_OUTLINED
                else:
                    status_cor = SUCCESS
                    status_icon = ft.Icons.VERIFIED_USER
                
                # Nome do titular
                nome = cert.get('cliente_nome') or cert.get('nome_avulso') or 'Avulso'
                
                # Status de pagamento
                pag_status = cert.get('pagamento_status', 'PENDENTE')
                if pag_status == 'PAGO':
                    pag_cor = SUCCESS
                    pag_icon = ft.Icons.PAID
                elif pag_status == 'PENDENTE':
                    pag_cor = TEXT_SECONDARY
                    pag_icon = ft.Icons.HOURGLASS_EMPTY
                else:
                    pag_cor = DANGER
                    pag_icon = ft.Icons.MONEY_OFF
                
                def toggle_pagamento(e, cid=cert['id'], status=pag_status):
                    novo_status = 'PAGO' if status != 'PAGO' else 'PENDENTE'
                    atualizar_certificado(cid, pagamento_status=novo_status)
                    # Log
                    username = usuario_logado[0].get('username', 'desconhecido') if usuario_logado and usuario_logado[0] else 'desconhecido'
                    registrar_log(username, f"Certificado {novo_status.lower()}", tabela="certificados", registro_id=cid)
                    carregar_certificados()
                
                row = ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(status_icon, size=20, color=status_cor),
                            bgcolor=ft.Colors.with_opacity(0.15, status_cor),
                            border_radius=8, padding=8,
                        ),
                        ft.Column([
                            ft.Text(nome[:30], size=12, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
                            ft.Text(f"{cert['tipo']} • {cert['cpf_cnpj'] or '-'}", size=9, color=TEXT_SECONDARY),
                        ], spacing=2, expand=True),
                        # Badge de pagamento
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(pag_icon, size=12, color="#FFFFFF"),
                                ft.Text(pag_status, size=8, color="#FFFFFF"),
                            ], spacing=4),
                            bgcolor=pag_cor,
                            border_radius=4, padding=ft.padding.symmetric(horizontal=6, vertical=3),
                            on_click=toggle_pagamento,
                            ink=True,
                            tooltip="Clique para alternar pago/pendente",
                        ),
                        ft.Column([
                            ft.Text(f"Vence: {data_venc.strftime('%d/%m/%Y')}", size=10, color=TEXT_PRIMARY),
                            ft.Text(f"{dias_restantes} dias" if dias_restantes > 0 else "VENCIDO", 
                                   size=9, color=status_cor, weight=ft.FontWeight.BOLD),
                        ], spacing=2, width=100),
                        ft.Text(formatar_moeda(cert['valor']), size=11, weight=ft.FontWeight.BOLD, color=ACCENT, width=90),
                        ft.Row([
                            ft.IconButton(
                                ft.Icons.EDIT_OUTLINED, icon_color=ACCENT, icon_size=16,
                                tooltip="Editar",
                                on_click=lambda e, c=cert: abrir_modal_editar(c),
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE, icon_color=DANGER, icon_size=16,
                                tooltip="Excluir",
                                on_click=lambda e, c=cert: confirmar_exclusao(c),
                            ),
                        ], spacing=0, width=70),
                    ], spacing=12),
                    padding=12,
                    bgcolor=SURFACE if pag_status != 'PENDENTE' else ft.Colors.with_opacity(0.5, SURFACE),
                    border_radius=10,
                    border=ft.border.all(1, pag_cor if pag_status == 'PAGO' else (status_cor if dias_restantes <= 30 else theme.get_border())),
                )
                lista_certificados.controls.append(row)
        
        page.update()
    
    def abrir_modal_novo():
        clientes = sorted(listar_clientes(), key=lambda c: int(c['codigo_interno']) if c['codigo_interno'] and c['codigo_interno'].isdigit() else float('inf'))
        hoje = datetime.now()
        
        tipo_cliente = ft.RadioGroup(
            value="cliente",
            content=ft.Row([
                ft.Radio(value="cliente", label="Cliente Cadastrado"),
                ft.Radio(value="avulso", label="Avulso"),
            ]),
        )
        
        cliente_dd = ft.Dropdown(
            label="Cliente", width=350, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
            options=[ft.dropdown.Option(str(c['id']), c['nome']) for c in clientes],
            visible=True,
        )
        
        nome_avulso = ft.TextField(
            label="Nome Completo", width=350, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
            visible=False,
        )
        
        cpf_cnpj = ft.TextField(
            label="CPF/CNPJ", width=350, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
        )
        
        tipo_cert = ft.Dropdown(
            label="Tipo de Certificado", width=350, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
            options=[ft.dropdown.Option(t, t) for t in TIPOS_CERT.keys()],
        )
        
        valor = ft.TextField(
            label="Valor (R$)", width=170, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        data_emissao = ft.TextField(
            label="Data Emissão", width=170, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
            value=hoje.strftime("%d/%m/%Y"),
        )
        
        vincular_honorario = ft.Checkbox(label="Vincular ao honorário do mês", value=False)
        
        def on_tipo_cliente_change(e):
            cliente_dd.visible = tipo_cliente.value == "cliente"
            nome_avulso.visible = tipo_cliente.value == "avulso"
            if tipo_cliente.value == "avulso":
                cpf_cnpj.value = ""
            page.update()
        
        def on_cliente_change(e):
            # Preencher CPF/CNPJ automaticamente
            if cliente_dd.value:
                cliente_selecionado = next((c for c in clientes if str(c['id']) == cliente_dd.value), None)
                if cliente_selecionado:
                    # Acessar de forma segura
                    try:
                        cpf_val = cliente_selecionado['cpf'] or ''
                    except:
                        cpf_val = ''
                    try:
                        cnpj_val = cliente_selecionado['cnpj'] or ''
                    except:
                        cnpj_val = ''
                    cpf_cnpj.value = cnpj_val or cpf_val
                    page.update()
        
        tipo_cliente.on_change = on_tipo_cliente_change
        cliente_dd.on_change = on_cliente_change
        
        def salvar(e):
            if not tipo_cert.value:
                toast_warning(page, "Selecione o tipo de certificado!")
                return
            
            if tipo_cliente.value == "cliente" and not cliente_dd.value:
                toast_warning(page, "Selecione o cliente!")
                return
            
            if tipo_cliente.value == "avulso" and not nome_avulso.value:
                toast_warning(page, "Informe o nome!")
                return
            
            try:
                valor_float = float(valor.value.replace(",", ".")) if valor.value else 0
            except:
                toast_error(page, "Valor inválido!")
                return
            
            # Calcular data de vencimento
            tipo_info = TIPOS_CERT.get(tipo_cert.value, {})
            validade_anos = tipo_info.get('validade', 1)
            
            try:
                dt_emissao = datetime.strptime(data_emissao.value, "%d/%m/%Y")
            except:
                toast_error(page, "Data inválida! Use DD/MM/AAAA")
                return
            
            dt_vencimento = dt_emissao.replace(year=dt_emissao.year + validade_anos)
            
            cert_id = adicionar_certificado(
                cliente_id=int(cliente_dd.value) if tipo_cliente.value == "cliente" else None,
                nome_avulso=nome_avulso.value if tipo_cliente.value == "avulso" else None,
                cpf_cnpj=cpf_cnpj.value,
                tipo=tipo_cert.value,
                categoria=tipo_info.get('categoria', 'PF'),
                midia=tipo_info.get('midia'),
                validade_anos=validade_anos,
                data_emissao=dt_emissao.strftime("%Y-%m-%d"),
                data_vencimento=dt_vencimento.strftime("%Y-%m-%d"),
                valor=valor_float,
                vinculado_honorario=vincular_honorario.value,
                mes_honorario=hoje.month if vincular_honorario.value else None,
                ano_honorario=hoje.year if vincular_honorario.value else None,
            )
            
            # Log
            username = usuario_logado[0].get('username', 'desconhecido') if usuario_logado and usuario_logado[0] else 'desconhecido'
            nome_titular = nome_avulso.value if tipo_cliente.value == "avulso" else [c['nome'] for c in clientes if str(c['id']) == cliente_dd.value][0] if cliente_dd.value else "?"
            registrar_log(username, "Certificado cadastrado", tabela="certificados", registro_id=cert_id, 
                         detalhes=f"{tipo_cert.value} | {nome_titular} | {formatar_moeda(valor_float)}")
            
            # Se vincular ao honorário, adicionar acréscimo
            if vincular_honorario.value and tipo_cliente.value == "cliente":
                conn = get_connection()
                cursor = conn.cursor()
                descricao_cert = f" [+{tipo_cert.value}: {formatar_moeda(valor_float)}]"
                cursor.execute("""
                    UPDATE honorarios SET valor = valor + ?, observacao = COALESCE(observacao, '') || ?
                    WHERE cliente_id = ? AND mes = ? AND ano = ?
                """, (valor_float, descricao_cert, int(cliente_dd.value), hoje.month, hoje.year))
                conn.commit()
                conn.close()
                toast_success(page, f"Certificado cadastrado e {formatar_moeda(valor_float)} adicionado ao honorário!")
            else:
                toast_success(page, "Certificado cadastrado!")
            
            dlg.open = False
            page.update()
            carregar_certificados()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("➕ Novo Certificado Digital", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            bgcolor=BG,
            content=ft.Container(
                content=ft.Column([
                    tipo_cliente,
                    cliente_dd,
                    nome_avulso,
                    cpf_cnpj,
                    tipo_cert,
                    ft.Row([valor, data_emissao], spacing=10),
                    vincular_honorario,
                ], spacing=12, width=380, scroll=ft.ScrollMode.AUTO),
                height=350,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dlg, 'open', False), page.update())),
                ft.ElevatedButton("Salvar", bgcolor=SUCCESS, color=TEXT_PRIMARY, on_click=salvar),
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
    
    def abrir_modal_editar(cert):
        cpf_cnpj = ft.TextField(
            label="CPF/CNPJ", width=350, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
            value=cert.get('cpf_cnpj', ''),
        )
        valor = ft.TextField(
            label="Valor (R$)", width=170, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
            value=str(cert['valor']),
        )
        status_dd = ft.Dropdown(
            label="Status", width=170, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
            value=cert['status'],
            options=[
                ft.dropdown.Option("ATIVO", "Ativo"),
                ft.dropdown.Option("VENCIDO", "Vencido"),
                ft.dropdown.Option("CANCELADO", "Cancelado"),
            ],
        )
        observacao = ft.TextField(
            label="Observação", width=350, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
            value=cert.get('observacao', ''),
            multiline=True, min_lines=2,
        )
        
        def salvar(e):
            try:
                valor_float = float(valor.value.replace(",", "."))
            except:
                toast_error(page, "Valor inválido!")
                return
            
            atualizar_certificado(
                cert['id'],
                cpf_cnpj=cpf_cnpj.value,
                valor=valor_float,
                status=status_dd.value,
                observacao=observacao.value,
            )
            
            username = usuario_logado[0].get('username', 'desconhecido') if usuario_logado and usuario_logado[0] else 'desconhecido'
            registrar_log(username, "Certificado atualizado", tabela="certificados", registro_id=cert['id'], 
                         detalhes=f"{cert['tipo']} | Status: {status_dd.value}")
            
            toast_success(page, "Certificado atualizado!")
            dlg.open = False
            page.update()
            carregar_certificados()
        
        nome = cert.get('cliente_nome') or cert.get('nome_avulso') or 'Avulso'
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"✏️ {nome[:25]}", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            bgcolor=BG,
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Tipo: {cert['tipo']}", size=11, color=TEXT_SECONDARY),
                    ft.Text(f"Validade: {cert['validade_anos']} ano(s)", size=11, color=TEXT_SECONDARY),
                    ft.Divider(height=10),
                    cpf_cnpj,
                    ft.Row([valor, status_dd], spacing=10),
                    observacao,
                ], spacing=12, width=380),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dlg, 'open', False), page.update())),
                ft.ElevatedButton("Salvar", bgcolor=SUCCESS, color=TEXT_PRIMARY, on_click=salvar),
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
    
    def confirmar_exclusao(cert):
        def excluir(e):
            excluir_certificado(cert['id'])
            
            username = usuario_logado[0].get('username', 'desconhecido') if usuario_logado and usuario_logado[0] else 'desconhecido'
            nome = cert.get('cliente_nome') or cert.get('nome_avulso') or 'Avulso'
            registrar_log(username, "Certificado excluído", tabela="certificados", registro_id=cert['id'], 
                         detalhes=f"{cert['tipo']} | {nome}")
            
            toast_success(page, "Certificado excluído!")
            dlg.open = False
            page.update()
            carregar_certificados()
        
        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f"Deseja excluir este certificado?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dlg, 'open', False), page.update())),
                ft.ElevatedButton("Excluir", bgcolor=DANGER, color="#FFFFFF", on_click=excluir),
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
    
    def on_filtro_change(e):
        filtro_status[0] = e.control.value
        carregar_certificados()
    
    # Carregar dados iniciais
    carregar_certificados()
    
    # Alertas de vencimento
    vencendo = get_certificados_vencendo(dias=30)
    alerta = None
    if vencendo:
        alerta = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.WARNING_AMBER, color=WARNING, size=20),
                ft.Text(f"⚠️ {len(vencendo)} certificado(s) vencendo nos próximos 30 dias!", 
                       size=12, color=WARNING, weight=ft.FontWeight.W_500),
            ], spacing=10),
            padding=12,
            bgcolor=ft.Colors.with_opacity(0.1, WARNING),
            border_radius=8,
        )
    
    def on_mes_change(e):
        filtro_mes[0] = int(e.control.value)
        carregar_certificados()
    
    def on_ano_change(e):
        filtro_ano[0] = int(e.control.value)
        carregar_certificados()
    
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.VERIFIED_USER, size=26, color=ACCENT),
                ft.Text("Certificados Digitais", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(expand=True),
                ft.Dropdown(
                    value="0", width=110, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
                    color=TEXT_PRIMARY, label_style=ft.TextStyle(color=TEXT_SECONDARY),
                    options=[ft.dropdown.Option(str(i), MESES[i]) for i in range(13)],
                    on_change=on_mes_change,
                    label="Mês",
                ),
                ft.Dropdown(
                    value=str(ano_atual), width=100, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
                    color=TEXT_PRIMARY, label_style=ft.TextStyle(color=TEXT_SECONDARY),
                    options=[ft.dropdown.Option(str(a), str(a)) for a in range(2020, ano_atual + 1)],
                    on_change=on_ano_change,
                    label="Ano",
                ),
                ft.Dropdown(
                    value="TODOS", width=120, bgcolor=INPUT_BG, border_color=INPUT_BORDER,
                    color=TEXT_PRIMARY, label_style=ft.TextStyle(color=TEXT_SECONDARY),
                    options=[
                        ft.dropdown.Option("TODOS", "Todos"),
                        ft.dropdown.Option("ATIVO", "Ativos"),
                        ft.dropdown.Option("VENCIDO", "Vencidos"),
                    ],
                    on_change=on_filtro_change,
                    label="Status",
                ),
                ft.ElevatedButton(
                    "Novo", icon=ft.Icons.ADD,
                    bgcolor=SUCCESS, color=TEXT_PRIMARY,
                    on_click=lambda e: abrir_modal_novo(),
                ),
            ], spacing=10),
            alerta if alerta else ft.Container(),
            ft.Container(height=10),
            lista_certificados,
        ]),
        expand=True,
        padding=20,
        bgcolor=BG,
    )

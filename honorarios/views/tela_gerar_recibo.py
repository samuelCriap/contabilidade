"""
Tela de Gerar Recibos - Visual Moderno
OTIMIZADO: Query única, suporte light/dark
"""
import flet as ft
from datetime import datetime
import os

from database import listar_clientes, criar_recibo, get_config, buscar_cliente, get_connection, registrar_log
from utils.theme import CORES
from utils.toast import toast_success, toast_error, toast_warning
from utils.email_sender import enviar_recibo_email


MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def criar_tela_gerar_recibo(page: ft.Page, file_picker, theme, usuario_logado=None):
    """Tela de recibos moderna e otimizada"""
    
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
    
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month
    
    clientes = sorted(listar_clientes(), key=lambda c: int(c['codigo_interno']) if c['codigo_interno'] and c['codigo_interno'].isdigit() else c['id'])
    valores_cache = {}
    clientes_dados = {}
    
    lista_clientes = ft.Column([], spacing=4, scroll=ft.ScrollMode.AUTO)
    resultado_text = ft.Text("", size=12)
    progresso = ft.ProgressBar(width=250, visible=False, color=ACCENT)
    enviar_email_cb = ft.Checkbox(label="Enviar por email", value=False, active_color=ACCENT, check_color=TEXT_PRIMARY)
    
    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def carregar_valores(mes, ano):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cliente_id, valor FROM honorarios WHERE ano = ? AND mes = ?", (ano, mes))
        valores_cache.clear()
        for row in cursor.fetchall():
            valores_cache[(row['cliente_id'], mes, ano)] = row['valor']
        conn.close()
    
    def criar_linha(cliente, mes, ano):
        cid = cliente['id']
        codigo = cliente['codigo_interno'] or str(cid)
        valor = valores_cache.get((cid, mes, ano), 0)
        
        if cid not in clientes_dados:
            clientes_dados[cid] = {'selecionado': False, 'acrescimo': 0, 'decrescimo': 0, 'descricao': ''}
        
        def on_sel(e, cliente_id=cid):
            clientes_dados[cliente_id]['selecionado'] = e.control.value
        
        def on_acre(e, cliente_id=cid):
            try:
                clientes_dados[cliente_id]['acrescimo'] = float(e.control.value.replace(",", ".")) if e.control.value else 0
            except: pass
        
        def on_decr(e, cliente_id=cid):
            try:
                clientes_dados[cliente_id]['decrescimo'] = float(e.control.value.replace(",", ".")) if e.control.value else 0
            except: pass
        
        def on_desc(e, cliente_id=cid):
            clientes_dados[cliente_id]['descricao'] = e.control.value or ''
        
        return ft.Container(
            content=ft.Row([
                ft.Checkbox(value=clientes_dados[cid]['selecionado'], on_change=on_sel, 
                           active_color=ACCENT, check_color=TEXT_PRIMARY),
                ft.Text(codigo, size=10, width=45, color=TEXT_SECONDARY),
                ft.Text(cliente['nome'][:20], size=11, width=160, color=TEXT_PRIMARY),
                ft.Text(formatar_moeda(valor), size=10, width=85, color=ACCENT),
        ft.TextField(width=75, hint_text="+R$", text_size=10, content_padding=5, 
                            bgcolor=INPUT_BG, border_color=INPUT_BORDER, color=TEXT_PRIMARY, on_change=on_acre),
                ft.TextField(width=75, hint_text="-R$", text_size=10, content_padding=5, 
                            bgcolor=INPUT_BG, border_color=INPUT_BORDER, color=TEXT_PRIMARY, on_change=on_decr),
                ft.TextField(width=120, hint_text="Desc...", text_size=10, content_padding=5, 
                            bgcolor=INPUT_BG, border_color=INPUT_BORDER, color=TEXT_PRIMARY, on_change=on_desc),
            ], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            bgcolor=SURFACE,
            border_radius=8,
            border=ft.border.all(1, theme.get_border()),
        )
    
    def atualizar_lista():
        mes = int(mes_dd.value) if mes_dd.value else mes_atual
        ano = int(ano_dd.value) if ano_dd.value else ano_atual
        carregar_valores(mes, ano)
        lista_clientes.controls.clear()
        for cliente in clientes:
            lista_clientes.controls.append(criar_linha(cliente, mes, ano))
        page.update()
    
    def selecionar_todos(e):
        for c in clientes:
            if c['id'] not in clientes_dados:
                clientes_dados[c['id']] = {'selecionado': True, 'acrescimo': 0, 'decrescimo': 0, 'descricao': ''}
            else:
                clientes_dados[c['id']]['selecionado'] = True
        atualizar_lista()
    
    def desmarcar_todos(e):
        for cid in clientes_dados:
            clientes_dados[cid]['selecionado'] = False
        atualizar_lista()
    
    mes_dd = ft.Dropdown(
        label="Mês", width=130, value=str(mes_atual),
        bgcolor=INPUT_BG, border_color=INPUT_BORDER,
        color=TEXT_PRIMARY, label_style=ft.TextStyle(color=TEXT_SECONDARY),
        options=[ft.dropdown.Option(str(i+1), MESES[i]) for i in range(12)],
        on_change=lambda e: atualizar_lista(),
    )
    
    ano_dd = ft.Dropdown(
        label="Ano", width=100, value=str(ano_atual),
        bgcolor=INPUT_BG, border_color=INPUT_BORDER,
        color=TEXT_PRIMARY, label_style=ft.TextStyle(color=TEXT_SECONDARY),
        options=[ft.dropdown.Option(str(a), str(a)) for a in range(2019, ano_atual + 1)],
        on_change=lambda e: atualizar_lista(),
    )
    
    def gerar_recibos(e):
        selecionados = [cid for cid, d in clientes_dados.items() if d.get('selecionado')]
        
        if not selecionados:
            toast_warning(page, "Selecione pelo menos um cliente!")
            return
        
        mes = int(mes_dd.value)
        ano = int(ano_dd.value)
        
        def on_result(ev):
            if not ev.path:
                return
            
            pasta = ev.path
            progresso.visible = True
            resultado_text.value = "Gerando..."
            resultado_text.color = TEXT_SECONDARY
            page.update()
            
            gerados = 0
            erros = 0
            
            try:
                from utils.pdf_recibo import gerar_pdf_recibo
                
                dados_empresa = {
                    'nome': get_config('empresa_nome', 'Escritório'),
                    'cnpj': get_config('empresa_cnpj', ''),
                    'endereco': get_config('empresa_endereco', ''),
                    'cidade': get_config('empresa_cidade', ''),
                    'telefone': get_config('empresa_telefone', ''),
                    'email': get_config('empresa_email', ''),
                    'chave_pix': get_config('empresa_pix', ''),
                }
                
                for cid in selecionados:
                    cliente = buscar_cliente(cid)
                    if not cliente:
                        erros += 1
                        continue
                    
                    dados = clientes_dados.get(cid, {})
                    valor_base = valores_cache.get((cid, mes, ano), 0)
                    valor = valor_base + dados.get('acrescimo', 0) - dados.get('decrescimo', 0)
                    
                    mes_nome = MESES[mes-1] if mes <= 12 else "13º"
                    descricao = f"Honorários ref. {mes_nome}/{ano}"
                    
                    # Lista de extras (acréscimos/decréscimos) para o PDF
                    extras = []
                    if dados.get('acrescimo', 0) > 0:
                        desc_extra = dados.get('descricao', '').strip() or "Acréscimo"
                        extras.append({'descricao': desc_extra, 'valor': dados['acrescimo']})
                    if dados.get('decrescimo', 0) > 0:
                        desc_extra = dados.get('descricao', '').strip() or "Desconto"
                        extras.append({'descricao': desc_extra, 'valor': -dados['decrescimo']})
                    
                    # Buscar certificados vinculados ao honorário deste mês
                    certificados_mes = []
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT tipo, valor FROM certificados 
                            WHERE cliente_id = ? AND mes_honorario = ? AND ano_honorario = ? 
                            AND vinculado_honorario = 1
                        """, (cid, mes, ano))
                        for row in cursor.fetchall():
                            certificados_mes.append({'tipo': row['tipo'], 'valor': row['valor'] or 0})
                        conn.close()
                    except:
                        pass
                    
                    recibo_id, numero = criar_recibo(
                        cliente_id=cid, valor=valor, descricao=descricao,
                        referencia_mes=mes, referencia_ano=ano,
                    )
                    
                    try:
                        # Gerar nome do arquivo para o PDF
                        codigo = cliente['codigo_interno'] or str(cid)
                        nome_arquivo = f"recibo_{numero}_{codigo}_{mes:02d}_{ano}.pdf"
                        caminho_pdf = os.path.join(pasta, nome_arquivo)
                        
                        gerar_pdf_recibo(
                            cliente=dict(cliente), valor=valor, mes=mes, ano=ano,
                            numero_recibo=numero, pasta_destino=pasta, dados_empresa=dados_empresa,
                            certificados=certificados_mes, extras=extras,
                        )
                        gerados += 1
                        
                        # Enviar por email se marcado
                        if enviar_email_cb.value and cliente['email']:
                            try:
                                sucesso, msg = enviar_recibo_email(
                                    cliente_email=cliente['email'],
                                    cliente_nome=cliente['nome'],
                                    recibo_path=caminho_pdf,
                                    mes=mes,
                                    ano=ano,
                                    valor=valor
                                )
                                if not sucesso:
                                    toast_warning(page, f"{cliente['nome'][:15]}: {msg}")
                            except Exception as email_err:
                                pass  # Ignora erro de email, PDF já foi gerado
                    except:
                        erros += 1
                
                progresso.visible = False
                resultado_text.value = f"✅ {gerados} gerados | ❌ {erros} erros"
                resultado_text.color = SUCCESS if erros == 0 else WARNING
                page.update()
                
                if gerados > 0:
                    # Log da geração
                    username = usuario_logado[0].get('username', 'desconhecido') if usuario_logado and usuario_logado[0] else 'desconhecido'
                    registrar_log(username, "Recibos PDF gerados", detalhes=f"{gerados} recibos ref. {mes}/{ano}")
                    toast_success(page, f"{gerados} recibos gerados!")
                
            except Exception as ex:
                progresso.visible = False
                resultado_text.value = f"Erro: {str(ex)}"
                resultado_text.color = DANGER
                page.update()
        
        file_picker.on_result = on_result
        file_picker.get_directory_path(dialog_title="Pasta para recibos")
    
    # Inicializar
    carregar_valores(mes_atual, ano_atual)
    for cliente in clientes:
        lista_clientes.controls.append(criar_linha(cliente, mes_atual, ano_atual))
    
    return ft.Container(
        content=ft.Column([
            ft.Text("📄 Gerar Recibos", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Ajuste valores individualmente para cada cliente", size=12, color=TEXT_SECONDARY),
            ft.Container(height=15),
            
            ft.Row([
                mes_dd,
                ano_dd,
                ft.Container(width=20),
                ft.ElevatedButton("✅ Todos", bgcolor=ACCENT, color=TEXT_PRIMARY, on_click=selecionar_todos),
                ft.ElevatedButton("❌ Nenhum", bgcolor=SURFACE_HOVER, color=TEXT_PRIMARY, on_click=desmarcar_todos),
                ft.Container(width=20),
                enviar_email_cb,
            ], spacing=10),
            ft.Container(height=10),
            
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Text("", width=35),
                    ft.Text("Cód", size=9, width=45, color=TEXT_SECONDARY),
                    ft.Text("Cliente", size=9, width=160, color=TEXT_SECONDARY),
                    ft.Text("Valor Base", size=9, width=85, color=TEXT_SECONDARY),
                    ft.Text("+R$", size=9, width=75, color=SUCCESS),
                    ft.Text("-R$", size=9, width=75, color=DANGER),
                    ft.Text("Descrição", size=9, width=120, color=TEXT_SECONDARY),
                ], spacing=5),
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
            ),
            
            ft.Container(
                content=lista_clientes,
                height=350,
                border_radius=12,
                border=ft.border.all(1, SURFACE_HOVER),
                padding=5,
                bgcolor=BG,
            ),
            ft.Container(height=15),
            
            ft.Row([
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PICTURE_AS_PDF, size=18),
                        ft.Text("Gerar PDFs", size=14),
                    ], spacing=8),
                    bgcolor=SUCCESS, color=TEXT_PRIMARY, height=48, width=180,
                    on_click=gerar_recibos,
                ),
                progresso,
            ], spacing=15),
            ft.Container(height=8),
            resultado_text,
        ]),
        expand=True,
        padding=30,
        bgcolor=BG,
    )

"""
Gerador de PDF de Relatório Individual por Cliente
Design premium com cabeçalho, cards visuais e tabelas coloridas
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Table, TableStyle
import os
from datetime import datetime


MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

MESES_CURTO = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez", "13º"]


def formatar_moeda(valor):
    """Formata valor como moeda brasileira"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_pdf_relatorio_cliente(dados_relatorio, pasta_destino, dados_empresa=None):
    """
    Gera um PDF premium com relatório completo do cliente
    
    Args:
        dados_relatorio: Dict retornado por get_relatorio_cliente()
        pasta_destino: Pasta onde salvar o PDF
        dados_empresa: Dict com dados da empresa (opcional)
    
    Returns:
        Caminho completo do arquivo gerado
    """
    dados_empresa = dados_empresa or {}
    cliente = dados_relatorio['cliente']
    honorarios = dados_relatorio['honorarios']
    resumo_anos = dados_relatorio['resumo_anos']
    total_geral = dados_relatorio['total_geral']
    total_pago = dados_relatorio['total_pago']
    saldo_devedor = dados_relatorio['saldo_devedor']
    
    # Cores premium
    AZUL_ESCURO = HexColor('#1A2957')
    AZUL_MEDIO = HexColor('#2D4A8C')
    DOURADO = HexColor('#C4A962')
    VERDE = HexColor('#10B981')
    VERMELHO = HexColor('#EF4444')
    LARANJA = HexColor('#F59E0B')
    CINZA_CLARO = HexColor('#F3F4F6')
    CINZA = HexColor('#6B7280')
    PRETO = HexColor('#1F2937')
    BRANCO = HexColor('#FFFFFF')
    
    # Nome do arquivo
    codigo = cliente.get('codigo_interno') or str(cliente.get('id', ''))
    nome_limpo = "".join(c for c in cliente['nome'] if c.isalnum() or c in " -_").strip()[:30]
    nome_arquivo = f"relatorio_{codigo}_{nome_limpo}.pdf"
    caminho_completo = os.path.join(pasta_destino, nome_arquivo)
    
    # Criar canvas
    c = canvas.Canvas(caminho_completo, pagesize=A4)
    width, height = A4
    margin = 40
    
    # ═══════════════════════════════════════════════════════════════
    # CABEÇALHO - Faixa azul com nome da empresa
    # ═══════════════════════════════════════════════════════════════
    header_height = 70
    c.setFillColor(AZUL_ESCURO)
    c.rect(0, height - header_height, width, header_height, fill=True, stroke=False)
    
    # Linha dourada decorativa
    c.setFillColor(DOURADO)
    c.rect(0, height - header_height - 4, width, 4, fill=True, stroke=False)
    
    # Nome da empresa
    empresa_nome = dados_empresa.get('nome', 'Sistema de Honorários')
    c.setFillColor(BRANCO)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, height - 35, empresa_nome.upper())
    
    # Subtítulo
    c.setFont("Helvetica", 10)
    c.drawString(margin, height - 52, "RELATÓRIO INDIVIDUAL DO CLIENTE")
    
    # Data de geração
    c.setFont("Helvetica", 9)
    data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")
    c.drawRightString(width - margin, height - 35, f"Gerado em: {data_geracao}")
    
    y = height - header_height - 30
    
    # ═══════════════════════════════════════════════════════════════
    # SEÇÃO DO CLIENTE
    # ═══════════════════════════════════════════════════════════════
    c.setFillColor(PRETO)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, cliente['nome'])
    y -= 18
    
    c.setFont("Helvetica", 10)
    c.setFillColor(CINZA)
    c.drawString(margin, y, f"Código: {codigo}")
    
    if cliente.get('cnpj'):
        c.drawString(margin + 120, y, f"CNPJ/CPF: {cliente['cnpj']}")
    
    y -= 35
    
    # ═══════════════════════════════════════════════════════════════
    # CARDS DE RESUMO
    # ═══════════════════════════════════════════════════════════════
    card_width = (width - 2*margin - 30) / 3
    card_height = 55
    card_radius = 8
    
    cards = [
        ("TOTAL GERAL", formatar_moeda(total_geral), AZUL_MEDIO),
        ("TOTAL PAGO", formatar_moeda(total_pago), VERDE),
        ("SALDO DEVEDOR", formatar_moeda(saldo_devedor), VERMELHO),
    ]
    
    for i, (titulo, valor, cor) in enumerate(cards):
        x = margin + i * (card_width + 15)
        
        # Fundo do card
        c.setFillColor(CINZA_CLARO)
        c.roundRect(x, y - card_height, card_width, card_height, card_radius, fill=True, stroke=False)
        
        # Barra lateral colorida
        c.setFillColor(cor)
        c.rect(x, y - card_height, 5, card_height, fill=True, stroke=False)
        
        # Título
        c.setFillColor(CINZA)
        c.setFont("Helvetica", 8)
        c.drawString(x + 15, y - 18, titulo)
        
        # Valor
        c.setFillColor(cor)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x + 15, y - 38, valor)
    
    y -= card_height + 25
    
    # ═══════════════════════════════════════════════════════════════
    # RESUMO POR ANO
    # ═══════════════════════════════════════════════════════════════
    if resumo_anos:
        c.setFillColor(PRETO)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "📊 RESUMO POR ANO")
        y -= 20
        
        # Cabeçalho da tabela
        header = ["Ano", "Total", "Pagos", "Pendentes", "Valor Total", "Valor Pago", "Valor Pendente"]
        data = [header]
        
        for r in resumo_anos[:8]:  # Limitar a 8 anos
            data.append([
                str(r['ano']),
                str(r['total']),
                str(r['pagos']),
                str(r['pendentes']),
                formatar_moeda(r['valor_total'] or 0),
                formatar_moeda(r['valor_pago'] or 0),
                formatar_moeda(r['valor_pendente'] or 0),
            ])
        
        col_widths = [50, 45, 45, 55, 85, 85, 95]
        row_height = 22
        table = Table(data, colWidths=col_widths, rowHeights=[row_height] * len(data))
        
        table.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), AZUL_ESCURO),
            ('TEXTCOLOR', (0, 0), (-1, 0), BRANCO),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Corpo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (3, -1), 'CENTER'),
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
            
            # Cores alternadas
            ('BACKGROUND', (0, 1), (-1, -1), BRANCO),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, CINZA_CLARO]),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E5E7EB')),
            ('BOX', (0, 0), (-1, -1), 1, AZUL_ESCURO),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        # Calcular altura real da tabela
        table_width_calc, table_height = table.wrap(width - 2*margin, height)
        table.drawOn(c, margin, y - table_height)
        
        y -= table_height + 30  # Espaçamento extra após a tabela
    
    # ═══════════════════════════════════════════════════════════════
    # ÚLTIMOS HONORÁRIOS
    # ═══════════════════════════════════════════════════════════════
    if honorarios and y > 150:
        c.setFillColor(PRETO)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "📋 ÚLTIMOS HONORÁRIOS")
        y -= 20
        
        # Limitar quantidade baseado no espaço disponível
        max_items = min(15, int((y - 80) / 18))
        
        header = ["Mês/Ano", "Valor", "Status", "Observação"]
        data = [header]
        
        for h in honorarios[:max_items]:
            mes_nome = MESES_CURTO[h['mes']-1] if h['mes'] <= 13 else str(h['mes'])
            status = h['status']
            obs = (h.get('observacao') or '')[:30]
            
            data.append([
                f"{mes_nome}/{h['ano']}",
                formatar_moeda(h['valor']),
                status,
                obs,
            ])
        
        col_widths = [70, 90, 80, 220]
        row_height = 20
        table = Table(data, colWidths=col_widths, rowHeights=[row_height] * len(data))
        
        # Definir cores por status
        table.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), AZUL_ESCURO),
            ('TEXTCOLOR', (0, 0), (-1, 0), BRANCO),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Corpo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            
            # Cores alternadas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, CINZA_CLARO]),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E5E7EB')),
            ('BOX', (0, 0), (-1, -1), 1, AZUL_ESCURO),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        # Colorir status individualmente
        for i, h in enumerate(honorarios[:max_items], start=1):
            if h['status'] == 'PAGO':
                table.setStyle(TableStyle([
                    ('BACKGROUND', (2, i), (2, i), VERDE),
                    ('TEXTCOLOR', (2, i), (2, i), BRANCO),
                ]))
            elif h['status'] == 'PENDENTE':
                table.setStyle(TableStyle([
                    ('BACKGROUND', (2, i), (2, i), LARANJA),
                    ('TEXTCOLOR', (2, i), (2, i), BRANCO),
                ]))
        
        # Calcular altura real da tabela
        table_width_calc, table_height = table.wrap(width - 2*margin, height)
        table.drawOn(c, margin, y - table_height)
        
        y -= table_height + 25
    
    # ═══════════════════════════════════════════════════════════════
    # RODAPÉ
    # ═══════════════════════════════════════════════════════════════
    footer_y = 30
    
    # Linha separadora
    c.setStrokeColor(DOURADO)
    c.setLineWidth(2)
    c.line(margin, footer_y + 15, width - margin, footer_y + 15)
    
    # Texto do rodapé
    c.setFillColor(CINZA)
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, footer_y, "Sistema de Honorários Contábeis | Relatório gerado automaticamente")
    
    # Salvar
    c.save()
    
    return caminho_completo

"""
Gerador de PDF de Recibos - Sistema de Honorários Contábeis
Layout conforme modelo de referência
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import os
from datetime import datetime


def numero_por_extenso(valor):
    """Converte número para texto por extenso"""
    unidades = ['', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove',
                'dez', 'onze', 'doze', 'treze', 'quatorze', 'quinze', 'dezesseis', 'dezessete', 'dezoito', 'dezenove']
    dezenas = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa']
    centenas = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 
                'seiscentos', 'setecentos', 'oitocentos', 'novecentos']
    
    def extenso_centena(n):
        if n == 0:
            return ''
        if n == 100:
            return 'cem'
        if n < 20:
            return unidades[n]
        if n < 100:
            d, u = divmod(n, 10)
            if u == 0:
                return dezenas[d]
            return f"{dezenas[d]} e {unidades[u]}"
        c, resto = divmod(n, 100)
        if resto == 0:
            return centenas[c] if c != 1 else 'cem'
        return f"{centenas[c]} e {extenso_centena(resto)}"
    
    def extenso_milhar(n):
        if n == 0:
            return 'zero'
        if n < 1000:
            return extenso_centena(n)
        m, resto = divmod(n, 1000)
        if m == 1:
            milhares = 'mil'
        else:
            milhares = f"{extenso_centena(m)} mil"
        if resto == 0:
            return milhares
        if resto < 100:
            return f"{milhares} e {extenso_centena(resto)}"
        return f"{milhares}, {extenso_centena(resto)}"
    
    inteiro = int(valor)
    centavos = round((valor - inteiro) * 100)
    
    resultado = extenso_milhar(inteiro)
    
    if inteiro == 1:
        resultado += " real"
    else:
        resultado += " reais"
    
    if centavos > 0:
        if centavos == 1:
            resultado += f" e {extenso_centena(centavos)} centavo"
        else:
            resultado += f" e {extenso_centena(centavos)} centavos"
    
    return resultado


MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


def gerar_pdf_recibo(cliente, valor, mes, ano, numero_recibo, pasta_destino, dados_empresa, certificados=None, extras=None):
    """Gera um PDF de recibo conforme modelo de referência"""
    
    certificados = certificados or []
    extras = extras or []
    
    # Nome do arquivo: código do cliente + nome
    codigo_cliente = cliente.get('codigo_interno') or str(cliente.get('id', ''))
    nome_cliente_limpo = "".join(c for c in cliente['nome'] if c.isalnum() or c in " -_").strip()
    nome_arquivo = f"{codigo_cliente} - {nome_cliente_limpo}.pdf"
    caminho_completo = os.path.join(pasta_destino, nome_arquivo)
    
    # Cores
    AZUL = HexColor('#1E3A5F')
    AZUL_CLARO = HexColor('#3B82F6')
    PRETO = HexColor('#000000')
    BRANCO = HexColor('#FFFFFF')
    CINZA_CLARO = HexColor('#F3F4F6')
    VERDE = HexColor('#22C55E')
    VERMELHO = HexColor('#EF4444')
    
    # Criar canvas
    c = canvas.Canvas(caminho_completo, pagesize=A4)
    width, height = A4  # 595 x 842 points
    
    margin = 50
    
    # Calcular valores separados
    valor_certificados = sum(cert.get('valor', 0) for cert in certificados)
    valor_extras = sum(ext.get('valor', 0) for ext in extras)
    valor_honorario = valor - valor_certificados - valor_extras  # Valor base do honorário
    
    # Formatar valores
    def formatar_moeda(v):
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # ═══════════════════════════════════════════════════════════════
    # CABEÇALHO - Dados da empresa centralizados
    # ═══════════════════════════════════════════════════════════════
    y = height - 60
    
    empresa_nome = dados_empresa.get('nome', 'Escritório Contábil')
    empresa_cnpj = dados_empresa.get('cnpj', '')
    empresa_endereco = dados_empresa.get('endereco', '')
    empresa_cidade = dados_empresa.get('cidade', '')
    empresa_telefone = dados_empresa.get('telefone', '')
    
    # Nome da empresa em destaque
    c.setFillColor(PRETO)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, empresa_nome.upper())
    y -= 16
    
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, y, f"Contabilista: {empresa_nome}")
    y -= 12
    
    if empresa_cnpj:
        c.drawCentredString(width / 2, y, f"CNPJ: {empresa_cnpj}")
        y -= 12
    
    if empresa_endereco:
        c.drawCentredString(width / 2, y, empresa_endereco)
        y -= 12
    
    if empresa_telefone:
        c.drawCentredString(width / 2, y, f"Telefone: {empresa_telefone}")
    
    y -= 30
    
    # ═══════════════════════════════════════════════════════════════
    # TÍTULO - Faixa azul
    # ═══════════════════════════════════════════════════════════════
    titulo_height = 25
    c.setFillColor(AZUL)
    c.rect(margin, y - titulo_height, width - 2*margin, titulo_height, fill=True, stroke=False)
    
    c.setFillColor(BRANCO)
    c.setFont("Helvetica-Bold", 12)
    titulo = f"RECIBO DE HONORÁRIOS CONTÁBEIS nº {numero_recibo:07d}"
    c.drawCentredString(width / 2, y - titulo_height + 8, titulo)
    
    y -= titulo_height + 20
    
    # ═══════════════════════════════════════════════════════════════
    # EMISSÃO E CLIENTE
    # ═══════════════════════════════════════════════════════════════
    data_emissao = datetime.now()
    cidade_emissao = dados_empresa.get('cidade', 'Local').split('-')[0].strip()
    
    c.setFillColor(PRETO)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Emissão:")
    c.setFont("Helvetica", 10)
    c.drawString(margin + 55, y, f"{cidade_emissao}, {data_emissao.day} de {MESES[data_emissao.month - 1]} de {data_emissao.year}.")
    
    y -= 18
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Cliente:")
    c.setFont("Helvetica", 10)
    c.drawString(margin + 55, y, cliente['nome'])
    
    y -= 25
    
    # ═══════════════════════════════════════════════════════════════
    # TABELA DE SERVIÇOS
    # ═══════════════════════════════════════════════════════════════
    mes_nome = MESES[mes - 1] if mes <= 12 else "13º"
    
    # Cabeçalho da tabela
    table_width = width - 2*margin
    col1_width = table_width * 0.7
    col2_width = table_width * 0.3
    
    c.setFillColor(AZUL)
    c.rect(margin, y - 20, table_width, 20, fill=True, stroke=False)
    
    c.setFillColor(BRANCO)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(margin + col1_width/2, y - 14, "Descrição")
    c.drawCentredString(margin + col1_width + col2_width/2, y - 14, "Valor")
    
    y -= 20
    
    # Linha do serviço contábil
    row_height = 20
    c.setStrokeColor(AZUL)
    c.setLineWidth(0.5)
    c.rect(margin, y - row_height, table_width, row_height, fill=False, stroke=True)
    c.line(margin + col1_width, y, margin + col1_width, y - row_height)
    
    c.setFillColor(PRETO)
    c.setFont("Helvetica", 10)
    c.drawString(margin + 5, y - 14, f"Serviços contábeis prestados em {mes_nome}/{ano}")
    c.drawCentredString(margin + col1_width + col2_width/2, y - 14, formatar_moeda(valor_honorario))
    
    y -= row_height
    
    # Linhas dos certificados (se houver)
    for cert in certificados:
        c.rect(margin, y - row_height, table_width, row_height, fill=False, stroke=True)
        c.line(margin + col1_width, y, margin + col1_width, y - row_height)
        
        c.setFillColor(PRETO)
        c.setFont("Helvetica", 10)
        c.drawString(margin + 5, y - 14, f"Certificado Digital ({cert.get('tipo', 'N/A')})")
        c.drawCentredString(margin + col1_width + col2_width/2, y - 14, formatar_moeda(cert.get('valor', 0)))
        
        y -= row_height
    
    # Linhas de extras (acréscimos/decréscimos)
    for ext in extras:
        c.rect(margin, y - row_height, table_width, row_height, fill=False, stroke=True)
        c.line(margin + col1_width, y, margin + col1_width, y - row_height)
        
        ext_valor = ext.get('valor', 0)
        c.setFillColor(PRETO)
        c.setFont("Helvetica", 10)
        c.drawString(margin + 5, y - 14, ext.get('descricao', 'Ajuste'))
        c.drawCentredString(margin + col1_width + col2_width/2, y - 14, formatar_moeda(abs(ext_valor)))
        
        y -= row_height
    
    y -= 15
    
    # ═══════════════════════════════════════════════════════════════
    # TABELA DE TOTAIS
    # ═══════════════════════════════════════════════════════════════
    col_width = table_width / 3
    
    # Cabeçalho
    c.setFillColor(CINZA_CLARO)
    c.rect(margin, y - 18, table_width, 18, fill=True, stroke=False)
    c.setStrokeColor(AZUL)
    c.rect(margin, y - 18, table_width, 18, fill=False, stroke=True)
    
    c.setFillColor(PRETO)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(margin + col_width/2, y - 12, "Total Bruto")
    c.drawCentredString(margin + col_width + col_width/2, y - 12, "Descontos")
    c.drawCentredString(margin + 2*col_width + col_width/2, y - 12, "Total Líquido")
    
    # Linhas verticais
    c.line(margin + col_width, y, margin + col_width, y - 38)
    c.line(margin + 2*col_width, y, margin + 2*col_width, y - 38)
    
    y -= 18
    
    # Valores
    c.rect(margin, y - 20, table_width, 20, fill=False, stroke=True)
    
    valor_total_formatado = formatar_moeda(valor)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(margin + col_width/2, y - 14, valor_total_formatado)
    c.drawCentredString(margin + col_width + col_width/2, y - 14, "R$ 0,00")
    c.drawCentredString(margin + 2*col_width + col_width/2, y - 14, valor_total_formatado)
    
    y -= 35
    
    # ═══════════════════════════════════════════════════════════════
    # VENCIMENTO E VALOR POR EXTENSO
    # ═══════════════════════════════════════════════════════════════
    if mes == 12:
        venc_mes = 1
        venc_ano = ano + 1
    else:
        venc_mes = mes + 1
        venc_ano = ano
    
    c.setFillColor(PRETO)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Vencimento:")
    c.setFont("Helvetica", 10)
    c.drawString(margin + 80, y, f"dia 10/{venc_mes:02d}/{venc_ano} no valor de {valor_total_formatado}")
    
    y -= 16
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Valor por extenso:")
    c.setFont("Helvetica", 10)
    extenso = numero_por_extenso(valor)
    c.drawString(margin + 105, y, extenso)
    
    y -= 25
    
    # ═══════════════════════════════════════════════════════════════
    # CHAVE PIX
    # ═══════════════════════════════════════════════════════════════
    chave_pix = dados_empresa.get('chave_pix', '')
    if chave_pix:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y, "Chave Pix:")
        c.setFont("Helvetica", 10)
        c.setFillColor(AZUL_CLARO)
        c.drawString(margin + 65, y, chave_pix)
    
    y -= 60
    
    # ═══════════════════════════════════════════════════════════════
    # ASSINATURA
    # ═══════════════════════════════════════════════════════════════
    line_width = 200
    line_x = (width - line_width) / 2
    
    c.setStrokeColor(PRETO)
    c.setLineWidth(0.5)
    c.line(line_x, y, line_x + line_width, y)
    
    # ═══════════════════════════════════════════════════════════════
    # RODAPÉ
    # ═══════════════════════════════════════════════════════════════
    y = margin + 20
    c.setFillColor(HexColor('#9CA3AF'))
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, y, "Página 1 de 1 | Gerado pelo Sistema de Honorários")
    
    # Salvar
    c.save()
    
    return caminho_completo

"""
Script para gerar honorários pendentes para todos os clientes
baseado nos valores cadastrados por ano.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'honorarios'))

from datetime import datetime
from honorarios.database import get_connection

def gerar_todos_honorarios():
    """
    Gera honorários PENDENTES para:
    - Anos passados: 12 meses por ano
    - Ano atual: apenas meses até o mês atual
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month
    
    # Buscar todos os valores cadastrados por cliente/ano
    cursor.execute("""
        SELECT vh.cliente_id, vh.ano, vh.valor, c.nome, c.ativo
        FROM valores_honorarios vh
        JOIN clientes c ON c.id = vh.cliente_id
        ORDER BY vh.cliente_id, vh.ano
    """)
    valores = cursor.fetchall()
    
    criados = 0
    pulados = 0
    
    for valor_row in valores:
        cliente_id = valor_row['cliente_id']
        ano = valor_row['ano']
        valor = valor_row['valor']
        nome = valor_row['nome']
        ativo = valor_row['ativo']
        
        # Definir quantos meses criar
        if ano < ano_atual:
            meses = range(1, 13)  # 12 meses completos
        elif ano == ano_atual:
            meses = range(1, mes_atual + 1)  # Apenas até o mês atual
        else:
            meses = []  # Ano futuro, não criar
        
        for mes in meses:
            # Verificar se já existe
            cursor.execute("""
                SELECT id FROM honorarios 
                WHERE cliente_id = ? AND ano = ? AND mes = ?
            """, (cliente_id, ano, mes))
            
            if cursor.fetchone():
                pulados += 1
                continue
            
            # Criar honorário pendente
            cursor.execute("""
                INSERT INTO honorarios (cliente_id, ano, mes, valor, status)
                VALUES (?, ?, ?, ?, 'PENDENTE')
            """, (cliente_id, ano, mes, valor))
            criados += 1
            
            if criados % 100 == 0:
                print(f"  Criados: {criados}...")
    
    conn.commit()
    conn.close()
    
    return criados, pulados

if __name__ == "__main__":
    print("\n" + "="*60)
    print("   GERAÇÃO DE HONORÁRIOS PENDENTES")
    print("="*60)
    
    print("\nGerando honorários baseados nos valores cadastrados...")
    criados, pulados = gerar_todos_honorarios()
    
    print("\n" + "="*60)
    print(f"   CONCLUÍDO!")
    print(f"   Criados: {criados}")
    print(f"   Já existiam (pulados): {pulados}")
    print("="*60)

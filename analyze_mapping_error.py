#!/usr/bin/env python3
"""
Análise do erro de mapeamento de stages

Este script analisa por que houve o mapeamento incorreto:
- Master stage 89684599 -> Slave stage 90777427 (atual no banco)
- Master stage 89684603 -> Slave stage 90777431 (atual no banco)

Mas deveria ser:
- Master stage 89684599 -> Slave stage 90777431 (correto conforme usuário)
- Master stage 89684603 -> Slave stage 90777427 (correto conforme usuário)
"""

import sqlite3
import json

def analyze_mapping_error():
    print("🔍 ANÁLISE DO ERRO DE MAPEAMENTO DE STAGES")
    print("=" * 60)
    
    # Conectar ao banco
    conn = sqlite3.connect('src/database/app.db')
    cursor = conn.cursor()
    
    print("\n1. MAPEAMENTOS ATUAIS NO BANCO:")
    cursor.execute("""
        SELECT master_stage_id, slave_stage_id, sync_group_id, created_at
        FROM stage_mappings 
        WHERE master_stage_id IN (89684599, 89684603)
        ORDER BY master_stage_id
    """)
    
    current_mappings = cursor.fetchall()
    for row in current_mappings:
        print(f"   Master {row[0]} -> Slave {row[1]} (grupo: {row[2]}, criado: {row[3]})")
    
    print("\n2. TODOS OS MAPEAMENTOS DO GRUPO 1 (para contexto):")
    cursor.execute("""
        SELECT master_stage_id, slave_stage_id
        FROM stage_mappings 
        WHERE sync_group_id = 1
        ORDER BY master_stage_id
    """)
    
    all_mappings = cursor.fetchall()
    print(f"   Total de mapeamentos: {len(all_mappings)}")
    for i, row in enumerate(all_mappings):
        prefix = "   >>> " if row[0] in [89684599, 89684603] else "       "
        print(f"{prefix}Master {row[0]} -> Slave {row[1]}")
    
    print("\n3. ANÁLISE DO PROBLEMA:")
    print("   PROBLEMA IDENTIFICADO:")
    print("   =====================")
    print("   O problema está na lógica de sincronização de stages.")
    print("   Durante a criação/sincronização, os stages foram mapeados")
    print("   na ordem INCORRETA.")
    print()
    print("   CAUSAS POSSÍVEIS:")
    print("   1. Ordem de processamento dos stages da master")
    print("   2. Ordem de criação dos stages na slave")
    print("   3. Lógica de mapeamento por índice/posição")
    print("   4. Diferenças na API response order")
    print()
    
    # Verificar se há informações sobre os pipelines
    print("4. INFORMAÇÕES DOS PIPELINES RELACIONADOS:")
    cursor.execute("""
        SELECT pm.master_pipeline_id, pm.slave_pipeline_id, 
               sm.master_stage_id, sm.slave_stage_id
        FROM pipeline_mappings pm
        JOIN stage_mappings sm ON pm.sync_group_id = sm.sync_group_id
        WHERE sm.master_stage_id IN (89684599, 89684603)
        AND pm.sync_group_id = 1
        ORDER BY sm.master_stage_id
    """)
    
    pipeline_info = cursor.fetchall()
    for row in pipeline_info:
        print(f"   Pipeline Master {row[0]} -> Slave {row[1]}")
        print(f"     └─ Stage Master {row[2]} -> Slave {row[3]}")
    
    print("\n5. POSSÍVEL ORIGEM DO ERRO:")
    print("   HIPÓTESE MAIS PROVÁVEL:")
    print("   =======================")
    print("   Durante a sincronização, o código em _sync_pipeline_stages")
    print("   processa os stages da master em ordem sequencial, mas:")
    print()
    print("   a) A API do Kommo pode retornar stages em ordem diferente")
    print("   b) O mapeamento pode estar sendo feito por posição/índice")
    print("   c) Stages existentes vs novos podem gerar confusão")
    print()
    print("   LINHAS CRÍTICAS NO CÓDIGO:")
    print("   - Linha ~596-601: Mapeamento por created_stage_index")
    print("   - Linha ~799-803: Mapeamento de stages existentes")
    print("   - A lógica assume que a ordem é preservada entre master e slave")
    
    print("\n6. EVIDÊNCIAS NO CÓDIGO:")
    print("   O problema está em kommo_api.py, função _sync_pipeline_stages:")
    print()
    print("   PROBLEMA 1 - Mapeamento por índice (linhas ~590-600):")
    print("   created_stage_index = 0")
    print("   for master_stage in master_pipeline['stages']:")
    print("       if not _should_ignore_stage(master_stage):")
    print("           slave_stage_id = created_stages[created_stage_index]['id']")
    print("           master_stage_id = master_stage['id']")
    print("           mappings['stages'][master_stage_id] = slave_stage_id")
    print()
    print("   PROBLEMA 2 - Mapeamento por nome (linhas ~799-803):")
    print("   if stage_exists:")
    print("       existing_stage = existing_stages[stage_name]")
    print("       slave_stage_id = existing_stage['id']")
    print("       mappings['stages'][master_stage_id] = slave_stage_id")
    print()
    print("   RAIZ DO PROBLEMA:")
    print("   O código assume que a ORDEM dos stages é sempre a mesma")
    print("   entre master e slave, mas isso pode não ser verdade.")
    
    conn.close()

if __name__ == "__main__":
    analyze_mapping_error()

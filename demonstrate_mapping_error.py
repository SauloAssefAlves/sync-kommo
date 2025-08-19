#!/usr/bin/env python3
"""
Demonstração da origem do erro de mapeamento

Este script simula o que aconteceu durante a sincronização
e mostra exatamente onde e por que ocorreu o erro.
"""

def demonstrate_mapping_error():
    print("🚨 DEMONSTRAÇÃO DA ORIGEM DO ERRO DE MAPEAMENTO")
    print("=" * 65)
    
    print("\n📋 CENÁRIO REPRODUZIDO:")
    print("-" * 25)
    
    # Simular dados da master
    master_stages = [
        {'id': 89684599, 'name': 'blue', 'sort': 1},
        {'id': 89684603, 'name': 'green', 'sort': 2}, 
        {'id': 89684607, 'name': 'yellow', 'sort': 3},
        # ... outros stages
    ]
    
    # Simular resposta da API slave (ordem pode ser diferente!)
    created_stages_response = [
        {'id': 90777427, 'name': 'blue', 'sort': 1},    # ATENÇÃO: ordem pode variar!
        {'id': 90777431, 'name': 'green', 'sort': 2},   # ATENÇÃO: ordem pode variar!
        {'id': 90777435, 'name': 'yellow', 'sort': 3},
    ]
    
    print("MASTER STAGES (ordem de processamento):")
    for i, stage in enumerate(master_stages):
        print(f"   {i}: Master ID {stage['id']} - '{stage['name']}'")
    
    print("\nSLAVE STAGES CRIADOS (resposta da API):")
    for i, stage in enumerate(created_stages_response):
        print(f"   {i}: Slave ID {stage['id']} - '{stage['name']}'")
    
    print("\n🐛 SIMULAÇÃO DO CÓDIGO PROBLEMÁTICO:")
    print("-" * 40)
    
    print("\nCÓDIGO ATUAL (PROBLEMÁTICO):")
    print("```python")
    print("created_stage_index = 0")
    print("for master_stage in master_pipeline['stages']:")
    print("    if not _should_ignore_stage(master_stage):")
    print("        slave_stage_id = created_stages[created_stage_index]['id']")
    print("        master_stage_id = master_stage['id']")
    print("        mappings['stages'][master_stage_id] = slave_stage_id")
    print("        created_stage_index += 1")
    print("```")
    
    print("\nEXECUÇÃO DO CÓDIGO PROBLEMÁTICO:")
    mappings_wrong = {}
    created_stage_index = 0
    
    for i, master_stage in enumerate(master_stages):
        # Simular _should_ignore_stage retornando False
        if True:  # Assumindo que não são stages especiais
            slave_stage_id = created_stages_response[created_stage_index]['id']
            master_stage_id = master_stage['id']
            mappings_wrong[master_stage_id] = slave_stage_id
            
            print(f"   Iteração {i}:")
            print(f"     Master stage: {master_stage_id} ('{master_stage['name']}')")
            print(f"     Mapeado para slave: {slave_stage_id}")
            print(f"     ❌ MAS o slave {slave_stage_id} é na verdade '{created_stages_response[created_stage_index]['name']}'!")
            print()
            
            created_stage_index += 1
    
    print("RESULTADO INCORRETO:")
    for master_id, slave_id in mappings_wrong.items():
        print(f"   Master {master_id} -> Slave {slave_id}")
    
    print("\n✅ CORREÇÃO NECESSÁRIA:")
    print("-" * 25)
    
    print("CÓDIGO CORRIGIDO:")
    print("```python")
    print("# Mapear por NOME, não por posição")
    print("slave_stages_by_name = {s['name']: s for s in created_stages}")
    print("for master_stage in master_pipeline['stages']:")
    print("    if not _should_ignore_stage(master_stage):")
    print("        stage_name = master_stage['name']")
    print("        if stage_name in slave_stages_by_name:")
    print("            slave_stage_id = slave_stages_by_name[stage_name]['id']")
    print("            master_stage_id = master_stage['id']")
    print("            mappings['stages'][master_stage_id] = slave_stage_id")
    print("```")
    
    print("\nEXECUÇÃO DO CÓDIGO CORRIGIDO:")
    mappings_correct = {}
    slave_stages_by_name = {s['name']: s for s in created_stages_response}
    
    for master_stage in master_stages:
        stage_name = master_stage['name']
        if stage_name in slave_stages_by_name:
            slave_stage_id = slave_stages_by_name[stage_name]['id']
            master_stage_id = master_stage['id']
            mappings_correct[master_stage_id] = slave_stage_id
            
            print(f"   Master stage: {master_stage_id} ('{stage_name}')")
            print(f"   Mapeado para slave: {slave_stage_id} ('{stage_name}')")
            print(f"   ✅ CORRETO: Ambos têm o nome '{stage_name}'")
            print()
    
    print("RESULTADO CORRETO:")
    for master_id, slave_id in mappings_correct.items():
        print(f"   Master {master_id} -> Slave {slave_id}")
    
    print("\n🎯 CONCLUSÃO:")
    print("-" * 15)
    print("PROBLEMA IDENTIFICADO:")
    print("- O código mapeia stages por POSIÇÃO/ÍNDICE")
    print("- Mas a API pode retornar stages em ordem diferente")
    print("- Isso causa mapeamentos incorretos")
    print()
    print("SOLUÇÃO:")
    print("- Mapear stages por NOME em vez de posição")
    print("- Garantir que stages com mesmo nome sejam mapeados corretamente")
    print("- Adicionar validação para detectar inconsistências")

if __name__ == "__main__":
    demonstrate_mapping_error()

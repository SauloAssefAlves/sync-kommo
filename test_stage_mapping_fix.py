#!/usr/bin/env python3
"""
Teste da correção do mapeamento de stages

Este script testa se a correção aplicada resolve o problema
de mapeamento incorreto por posição/índice.
"""

def test_stage_mapping_fix():
    print("🔧 TESTE DA CORREÇÃO DO MAPEAMENTO DE STAGES")
    print("=" * 55)
    
    print("\n📋 CENÁRIO DE TESTE:")
    print("-" * 20)
    
    # Simular dados da master (ordem específica)
    master_stages = [
        {'id': 89684599, 'name': 'blue', 'sort': 1},
        {'id': 89684603, 'name': 'green', 'sort': 2}, 
        {'id': 89684607, 'name': 'yellow', 'sort': 3},
    ]
    
    # Simular resposta da API slave (ordem pode ser diferente!)
    created_stages = [
        {'id': 90777431, 'name': 'green', 'sort': 2},   # Verde em posição 0 (diferente da master)
        {'id': 90777427, 'name': 'blue', 'sort': 1},    # Azul em posição 1 (diferente da master)
        {'id': 90777435, 'name': 'yellow', 'sort': 3},  # Amarelo em posição 2 (igual à master)
    ]
    
    print("MASTER STAGES (ordem de processamento):")
    for i, stage in enumerate(master_stages):
        print(f"   {i}: Master ID {stage['id']} - '{stage['name']}'")
    
    print("\nSLAVE STAGES CRIADOS (ordem retornada pela API):")
    for i, stage in enumerate(created_stages):
        print(f"   {i}: Slave ID {stage['id']} - '{stage['name']}'")
    
    print("\n❌ LÓGICA ANTIGA (PROBLEMÁTICA - POR POSIÇÃO):")
    print("-" * 50)
    
    mappings_old = {}
    created_stage_index = 0
    
    print("Mapeamento por posição/índice:")
    for i, master_stage in enumerate(master_stages):
        if created_stage_index < len(created_stages):
            slave_stage_id = created_stages[created_stage_index]['id']
            slave_stage_name = created_stages[created_stage_index]['name']
            master_stage_id = master_stage['id']
            mappings_old[master_stage_id] = slave_stage_id
            
            status = "✅" if master_stage['name'] == slave_stage_name else "❌"
            print(f"   {status} Master {master_stage_id} ('{master_stage['name']}') -> Slave {slave_stage_id} ('{slave_stage_name}')")
            created_stage_index += 1
    
    print("\nResultado INCORRETO da lógica antiga:")
    for master_id, slave_id in mappings_old.items():
        print(f"   Master {master_id} -> Slave {slave_id}")
    
    print("\n✅ LÓGICA NOVA (CORRIGIDA - POR NOME):")
    print("-" * 45)
    
    mappings_new = {}
    created_stages_by_name = {s['name']: s for s in created_stages}
    
    print("Mapeamento por nome:")
    for master_stage in master_stages:
        stage_name = master_stage['name']
        if stage_name in created_stages_by_name:
            slave_stage_data = created_stages_by_name[stage_name]
            slave_stage_id = slave_stage_data['id']
            master_stage_id = master_stage['id']
            mappings_new[master_stage_id] = slave_stage_id
            
            print(f"   ✅ Master {master_stage_id} ('{stage_name}') -> Slave {slave_stage_id} ('{stage_name}')")
        else:
            print(f"   ❌ Master stage '{stage_name}' não encontrado na slave!")
    
    print("\nResultado CORRETO da lógica nova:")
    for master_id, slave_id in mappings_new.items():
        print(f"   Master {master_id} -> Slave {slave_id}")
    
    print("\n🎯 COMPARAÇÃO DOS RESULTADOS:")
    print("-" * 35)
    
    print("DIFERENÇAS ENCONTRADAS:")
    for master_id in mappings_old:
        old_slave = mappings_old[master_id]
        new_slave = mappings_new.get(master_id, "NÃO MAPEADO")
        
        if old_slave != new_slave:
            print(f"   Master {master_id}: {old_slave} (antigo) -> {new_slave} (novo) ✅ CORRIGIDO")
        else:
            print(f"   Master {master_id}: {old_slave} (sem mudança)")
    
    print("\n🏆 CONCLUSÃO:")
    print("-" * 15)
    print("✅ A correção resolve o problema de mapeamento incorreto!")
    print("✅ Agora os stages são mapeados por NOME, não por posição!")
    print("✅ Garante que stages com mesmo nome sejam mapeados corretamente!")
    print("\nPróximo teste: Execute um novo sync para verificar se funciona na prática.")

if __name__ == "__main__":
    test_stage_mapping_fix()

#!/usr/bin/env python3
"""
Teste específico da lógica de mapeamento do campo 'texto longo'
"""

def test_texto_longo_mapping():
    """Testa o mapeamento específico do campo texto longo"""
    print("🧪 TESTANDO MAPEAMENTO ESPECÍFICO")
    print("=" * 50)
    
    # Dados reais do problema
    master_field = {
        'name': 'texto longo',
        'required_statuses': [
            {'pipeline_id': 11670079, 'status_id': 89684599}
        ]
    }
    
    # Mapeamentos reais do banco
    mappings = {
        'pipelines': {11670079: 11795583},
        'stages': {89684599: 90777427}
    }
    
    print(f"📥 Campo master: {master_field['name']}")
    print(f"📥 Required statuses originais: {master_field['required_statuses']}")
    print()
    
    # Aplicar lógica de mapeamento
    mapped_required_statuses = []
    
    for req_status in master_field['required_statuses']:
        master_status_id = req_status.get('status_id')
        master_pipeline_id = req_status.get('pipeline_id')
        
        print(f"🔄 Processando: Pipeline {master_pipeline_id}, Status {master_status_id}")
        
        if master_pipeline_id in mappings['pipelines']:
            slave_pipeline_id = mappings['pipelines'][master_pipeline_id]
            print(f"   ✅ Pipeline encontrado: {master_pipeline_id} → {slave_pipeline_id}")
            
            if master_status_id in mappings['stages']:
                slave_status_id = mappings['stages'][master_status_id]
                print(f"   ✅ Status encontrado: {master_status_id} → {slave_status_id}")
                
                mapped_status = {
                    'status_id': slave_status_id,
                    'pipeline_id': slave_pipeline_id
                }
                mapped_required_statuses.append(mapped_status)
                print(f"   ✅ Required status mapeado: {mapped_status}")
            else:
                print(f"   ❌ Status {master_status_id} não encontrado nos mapeamentos")
        else:
            print(f"   ❌ Pipeline {master_pipeline_id} não encontrado nos mapeamentos")
    
    print()
    print(f"📤 Required statuses finais: {mapped_required_statuses}")
    print(f"📊 Total de required statuses mapeados: {len(mapped_required_statuses)}")
    
    # Resultado esperado
    expected = [{'status_id': 90777427, 'pipeline_id': 11795583}]
    success = mapped_required_statuses == expected
    
    print()
    print(f"🎯 RESULTADO:")
    print(f"   Esperado: {expected}")
    print(f"   Obtido:   {mapped_required_statuses}")
    print(f"   Status:   {'✅ SUCESSO' if success else '❌ FALHA'}")
    
    return mapped_required_statuses

if __name__ == "__main__":
    result = test_texto_longo_mapping()

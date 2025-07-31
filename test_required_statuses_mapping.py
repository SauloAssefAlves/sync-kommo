#!/usr/bin/env python3
"""
Script para testar o mapeamento de required_statuses
"""

def test_required_statuses_mapping():
    """
    Testa como os required_statuses são mapeados
    """
    print("🧪 Testando mapeamento de required_statuses...")
    
    def _should_ignore_stage(stage):
        """Função igual à do código principal"""
        stage_id = stage.get('id')
        stage_type = stage.get('type', 0)
        stage_name = stage.get('name', '').lower()
        
        if stage_id in [142, 143]:
            print(f"    DEBUG: 🚫 Ignorando estágio por ID especial: {stage_id}")
            return True
            
        if stage_type == 1:
            print(f"    DEBUG: 🚫 Ignorando estágio type=1: {stage_id}")
            return True
            
        special_patterns = [
            'venda ganha', 'fechado - ganho', 'closed - won', 'won',
            'venda perdida', 'fechado - perdido', 'closed - lost', 'lost',
            'incoming leads', 'incoming', 'entrada'
        ]
        
        for pattern in special_patterns:
            if pattern in stage_name:
                print(f"    DEBUG: 🚫 Ignorando estágio por nome: {pattern}")
                return True
                
        return False
    
    # Simular dados do log real
    print("📋 DADOS DO LOG REAL:")
    master_field = {
        'id': 958054,
        'name': 'texto longo',
        'type': 'textarea',
        'required_statuses': [{'pipeline_id': 11670079, 'status_id': 89684599}]
    }
    
    # Simular mapeamentos (baseado nos logs - deveria haver estes mapeamentos)
    mappings = {
        'pipelines': {
            11670079: 11670175  # Master pipeline -> Slave pipeline
        },
        'stages': {
            89684599: 89685559  # Master status -> Slave status
        }
    }
    
    print(f"Master field: {master_field['name']}")
    print(f"Master required_statuses: {master_field['required_statuses']}")
    print(f"Mapeamentos disponíveis:")
    print(f"  Pipelines: {mappings['pipelines']}")
    print(f"  Stages: {mappings['stages']}")
    
    # Simular o processo de mapeamento
    print("\n🔄 PROCESSO DE MAPEAMENTO:")
    
    mapped_required_statuses = []
    for req_status in master_field['required_statuses']:
        master_status_id = req_status.get('status_id')
        master_pipeline_id = req_status.get('pipeline_id')
        
        print(f"\n   🔍 Processando: pipeline={master_pipeline_id}, status={master_status_id}")
        
        # Verificar se é estágio especial
        stage_info = {'id': master_status_id}
        if _should_ignore_stage(stage_info):
            print(f"   🚫 Ignorando required_status com estágio especial {master_status_id}")
            continue
        
        # Mapear pipeline
        if master_pipeline_id in mappings.get('pipelines', {}):
            slave_pipeline_id = mappings['pipelines'][master_pipeline_id]
            print(f"   ✅ Pipeline mapeado: {master_pipeline_id} -> {slave_pipeline_id}")
            
            # Mapear status
            if master_status_id in mappings.get('stages', {}):
                slave_status_id = mappings['stages'][master_status_id]
                print(f"   ✅ Status mapeado: {master_status_id} -> {slave_status_id}")
                
                mapped_status = {
                    'status_id': slave_status_id,
                    'pipeline_id': slave_pipeline_id
                }
                mapped_required_statuses.append(mapped_status)
                print(f"   ✅ Required_status mapeado com sucesso!")
            else:
                print(f"   ❌ Status {master_status_id} não encontrado nos mapeamentos")
        else:
            print(f"   ❌ Pipeline {master_pipeline_id} não encontrado nos mapeamentos")
    
    print(f"\n📊 RESULTADO:")
    print(f"Required_statuses mapeados: {mapped_required_statuses}")
    
    if mapped_required_statuses:
        print("✅ Mapeamento bem-sucedido - campo seria criado com required_statuses")
    else:
        print("❌ Nenhum required_status mapeado - campo seria criado sem restrições específicas")
    
    print("\n🎯 POSSÍVEIS CAUSAS DO ERRO 400:")
    print("1. 🚫 Status especial (142/143) nos required_statuses")
    print("2. ❌ Mapeamento não foi criado corretamente")
    print("3. 🔄 Sincronização de pipelines executada antes dos mapeamentos serem salvos")
    print("4. 📋 IDs de pipeline/status inexistentes na conta slave")
    
    print("\n💡 SOLUÇÕES:")
    print("1. ✅ Ignorar required_statuses com estágios especiais")
    print("2. 🔄 Criar campo sem required_statuses como fallback")
    print("3. 📊 Melhorar logs para debug de mapeamentos")
    print("4. 🔍 Validar se IDs existem na slave antes de enviar")

if __name__ == "__main__":
    test_required_statuses_mapping()

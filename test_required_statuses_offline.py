#!/usr/bin/env python3
"""
Teste offline da lógica de required_statuses para campos de texto longo
"""

import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_required_statuses_mapping():
    """
    Simula o mapeamento de required_statuses sem precisar do banco
    """
    logger.info("🧪 SIMULANDO MAPEAMENTO DE REQUIRED_STATUSES")
    logger.info("=" * 60)
    
    # Simular dados da master
    master_pipelines = [
        {'id': 11670079, 'name': 'cor teste 2'},
        {'id': 11670080, 'name': 'Pipeline Principal'},
    ]
    
    master_stages = {
        11670079: [  # Pipeline 'cor teste 2'
            {'id': 89684599, 'name': 'blue', 'color': '#0000ff'},
            {'id': 89684600, 'name': 'red', 'color': '#ff0000'},
            {'id': 89684601, 'name': 'green', 'color': '#00ff00'},
        ],
        11670080: [  # Pipeline Principal
            {'id': 89684602, 'name': 'Novo', 'color': '#d6eaff'},
            {'id': 89684603, 'name': 'Em andamento', 'color': '#fff000'},
        ]
    }
    
    # Simular dados da slave (após sincronização) - CORRIGIDO com ID real
    slave_pipelines = [
        {'id': 11680487, 'name': 'cor teste 2'},  # ID REAL da slave
        {'id': 11670176, 'name': 'Pipeline Principal'},  # Exemplo
    ]
    
    slave_stages = {
        11680487: [  # Pipeline 'cor teste 2' na slave com ID correto
            {'id': 89685559, 'name': 'blue', 'color': '#d6eaff'},  # Mapeado de 89684599
            {'id': 89685560, 'name': 'red', 'color': '#ffdbdb'},   # Mapeado de 89684600
            {'id': 89685561, 'name': 'green', 'color': '#87f2c0'}, # Mapeado de 89684601
        ],
        11670176: [  # Pipeline Principal na slave
            {'id': 89685562, 'name': 'Novo', 'color': '#d6eaff'},        # Mapeado de 89684602
            {'id': 89685563, 'name': 'Em andamento', 'color': '#fff000'}, # Mapeado de 89684603
        ]
    }
    
    # Simular campo texto longo com required_statuses
    master_field = {
        'name': 'Observações Detalhadas',
        'type': 'textarea',
        'required_statuses': [
            {'pipeline_id': 11670079, 'status_id': 89684599},  # Pipeline 'cor teste 2', status 'blue'
            {'pipeline_id': 11670080, 'status_id': 89684603},  # Pipeline Principal, status 'Em andamento'
        ]
    }
    
    logger.info("📋 DADOS SIMULADOS:")
    logger.info(f"   Campo: {master_field['name']} ({master_field['type']})")
    logger.info(f"   Required statuses: {len(master_field['required_statuses'])}")
    
    for rs in master_field['required_statuses']:
        pipeline_id = rs['pipeline_id']
        status_id = rs['status_id']
        
        # Encontrar nomes
        pipeline_name = next((p['name'] for p in master_pipelines if p['id'] == pipeline_id), 'Desconhecido')
        status_name = next((s['name'] for s in master_stages.get(pipeline_id, []) if s['id'] == status_id), 'Desconhecido')
        
        logger.info(f"      - Pipeline '{pipeline_name}' ({pipeline_id}), Status '{status_name}' ({status_id})")
    
    # Simular processo de mapeamento
    logger.info(f"\n🔄 SIMULANDO PROCESSO DE MAPEAMENTO...")
    
    mapped_required_statuses = []
    
    for rs in master_field['required_statuses']:
        master_pipeline_id = rs['pipeline_id']
        master_status_id = rs['status_id']
        
        logger.info(f"\n   🔍 Processando required_status:")
        logger.info(f"      Master Pipeline: {master_pipeline_id}")
        logger.info(f"      Master Status: {master_status_id}")
        
        # 1. Encontrar pipeline correspondente na slave
        master_pipeline = next((p for p in master_pipelines if p['id'] == master_pipeline_id), None)
        if not master_pipeline:
            logger.error(f"      ❌ Pipeline {master_pipeline_id} não encontrado na master")
            continue
        
        slave_pipeline = next((p for p in slave_pipelines if p['name'] == master_pipeline['name']), None)
        if not slave_pipeline:
            logger.error(f"      ❌ Pipeline '{master_pipeline['name']}' não encontrado na slave")
            continue
        
        logger.info(f"      ✅ Pipeline mapeado: {master_pipeline_id} → {slave_pipeline['id']}")
        
        # 2. Encontrar status correspondente na slave
        master_status = next((s for s in master_stages.get(master_pipeline_id, []) if s['id'] == master_status_id), None)
        if not master_status:
            logger.error(f"      ❌ Status {master_status_id} não encontrado na master")
            continue
        
        slave_status = next((s for s in slave_stages.get(slave_pipeline['id'], []) if s['name'] == master_status['name']), None)
        if not slave_status:
            logger.error(f"      ❌ Status '{master_status['name']}' não encontrado na slave")
            continue
        
        logger.info(f"      ✅ Status mapeado: {master_status_id} → {slave_status['id']}")
        
        # 3. Adicionar à lista de mapeados
        mapped_status = {
            'pipeline_id': slave_pipeline['id'],
            'status_id': slave_status['id']
        }
        mapped_required_statuses.append(mapped_status)
        
        logger.info(f"      📝 Required status mapeado:")
        logger.info(f"         Pipeline: {master_pipeline['name']} ({master_pipeline_id} → {slave_pipeline['id']})")
        logger.info(f"         Status: {master_status['name']} ({master_status_id} → {slave_status['id']})")
    
    # Resultado final
    logger.info(f"\n📊 RESULTADO DO MAPEAMENTO:")
    logger.info(f"   Required statuses originais: {len(master_field['required_statuses'])}")
    logger.info(f"   Required statuses mapeados: {len(mapped_required_statuses)}")
    
    if mapped_required_statuses:
        logger.info(f"   ✅ Mapeamento bem-sucedido!")
        for i, rs in enumerate(mapped_required_statuses, 1):
            logger.info(f"      {i}. Pipeline {rs['pipeline_id']}, Status {rs['status_id']}")
        
        # Simular criação do campo na slave
        slave_field_data = {
            'name': master_field['name'],
            'type': master_field['type'],
            'required_statuses': mapped_required_statuses
        }
        
        logger.info(f"\n📤 DADOS PARA CRIAÇÃO NA SLAVE:")
        logger.info(f"   {slave_field_data}")
        
        # Validar se os IDs existem na slave
        logger.info(f"\n🔍 VALIDANDO IDs NA SLAVE...")
        valid_statuses = []
        
        for rs in mapped_required_statuses:
            slave_pipeline_id = rs['pipeline_id']
            slave_status_id = rs['status_id']
            
            # Verificar se pipeline existe
            pipeline_exists = any(p['id'] == slave_pipeline_id for p in slave_pipelines)
            
            if pipeline_exists:
                # Verificar se status existe
                status_exists = any(s['id'] == slave_status_id for s in slave_stages.get(slave_pipeline_id, []))
                
                if status_exists:
                    valid_statuses.append(rs)
                    logger.info(f"      ✅ Válido: Pipeline {slave_pipeline_id}, Status {slave_status_id}")
                else:
                    logger.warning(f"      ❌ Status {slave_status_id} não existe no pipeline {slave_pipeline_id}")
            else:
                logger.warning(f"      ❌ Pipeline {slave_pipeline_id} não existe")
        
        logger.info(f"\n📈 VALIDAÇÃO FINAL:")
        logger.info(f"   Required statuses válidos: {len(valid_statuses)}")
        
        if valid_statuses:
            logger.info(f"   ✅ Campo pode ser criado com required_statuses")
        else:
            logger.warning(f"   ⚠️ Campo será criado SEM required_statuses (sem restrições)")
            
    else:
        logger.error(f"   ❌ Falha no mapeamento - campo será criado sem required_statuses")

def test_api_validation_error():
    """
    Simula o erro de validação da API que você está enfrentando
    """
    logger.info("\n" + "=" * 60)
    logger.info("🚨 SIMULANDO ERRO DE VALIDAÇÃO DA API")
    logger.info("=" * 60)
    
    # Dados que causariam erro
    problematic_data = {
        'name': 'Observações Detalhadas',
        'type': 'textarea',
        'required_statuses': [
            {'pipeline_id': 89685559, 'status_id': 11670175},  # IDs TROCADOS!
        ]
    }
    
    logger.info("🔍 ANALISANDO DADOS PROBLEMÁTICOS:")
    logger.info(f"   {problematic_data}")
    
    logger.info("\n❌ PROBLEMA IDENTIFICADO:")
    logger.info("   Os IDs estão TROCADOS!")
    logger.info("   pipeline_id deveria ser o ID do pipeline")
    logger.info("   status_id deveria ser o ID do status")
    logger.info("   Mas os valores estão invertidos!")
    
    # Dados corretos com ID real da pipeline
    correct_data = {
        'name': 'Observações Detalhadas',
        'type': 'textarea',
        'required_statuses': [
            {'pipeline_id': 11680487, 'status_id': 89685559},  # CORRETO com ID real
        ]
    }
    
    logger.info("\n✅ DADOS CORRETOS:")
    logger.info(f"   {correct_data}")
    
    logger.info("\n💡 SOLUÇÃO:")
    logger.info("   Verificar se o mapeamento está retornando os IDs na ordem correta")
    logger.info("   pipeline_id = ID do pipeline na slave")
    logger.info("   status_id = ID do status na slave")

if __name__ == "__main__":
    simulate_required_statuses_mapping()
    test_api_validation_error()

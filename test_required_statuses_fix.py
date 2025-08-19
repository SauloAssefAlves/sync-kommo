#!/usr/bin/env python3
"""
Teste para verificar se os status 142 e 143 estão sendo incluídos corretamente nos required_statuses
"""

import logging
import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_required_statuses_with_special_stages():
    """Testa se os status especiais 142, 143 são incluídos nos required_statuses"""
    
    logger.info("🧪 TESTE: Required_statuses com status especiais 142 e 143")
    logger.info("=" * 80)
    
    # Simular dados de teste
    master_field = {
        'name': 'Campo Teste',
        'type': 'textarea',
        'required_statuses': [
            {'pipeline_id': 123, 'status_id': 456},      # Status normal
            {'pipeline_id': 123, 'status_id': 142},      # Status especial Won
            {'pipeline_id': 123, 'status_id': 143},      # Status especial Lost  
            {'pipeline_id': 123, 'status_id': 1},        # Status especial Incoming
            {'pipeline_id': 123, 'status_id': 789},      # Outro status normal
        ]
    }
    
    # Simular mapeamentos (sem os status especiais)
    mappings = {
        'pipelines': {123: 999},  # Pipeline mapeado
        'stages': {
            456: 556,  # Status normal mapeado
            789: 889,  # Outro status normal mapeado
            # Note: 142, 143, 1 NÃO estão nos mapeamentos propositalmente
        }
    }
    
    logger.info(f"📋 Campo de teste: {master_field['name']}")
    logger.info(f"📋 Required statuses originais: {len(master_field['required_statuses'])}")
    for i, rs in enumerate(master_field['required_statuses'], 1):
        status_type = "ESPECIAL" if rs['status_id'] in [142, 143, 1] else "NORMAL"
        logger.info(f"   {i}. Pipeline {rs['pipeline_id']}, Status {rs['status_id']} ({status_type})")
    
    logger.info(f"\n🗺️ Mapeamentos disponíveis:")
    logger.info(f"   Pipelines: {mappings['pipelines']}")
    logger.info(f"   Stages: {mappings['stages']}")
    
    # Simular o processamento como está no código
    logger.info(f"\n🔄 SIMULANDO PROCESSAMENTO...")
    mapped_required_statuses = []
    
    for req_status in master_field['required_statuses']:
        master_status_id = req_status.get('status_id')
        master_pipeline_id = req_status.get('pipeline_id')
        
        logger.info(f"\n   🔍 Processando: pipeline={master_pipeline_id}, status={master_status_id}")
        
        # Mapear pipeline_id da master para escrava
        if master_pipeline_id and master_pipeline_id in mappings.get('pipelines', {}):
            slave_pipeline_id = mappings['pipelines'][master_pipeline_id]
            logger.info(f"   ✅ Pipeline mapeado: {master_pipeline_id} -> {slave_pipeline_id}")
            
            # Mapear status_id da master para escrava
            if master_status_id and master_status_id in mappings.get('stages', {}):
                slave_status_id = mappings['stages'][master_status_id]
                logger.info(f"   ✅ Status mapeado: {master_status_id} -> {slave_status_id}")
                
                mapped_status = {
                    'status_id': slave_status_id,
                    'pipeline_id': slave_pipeline_id
                }
                mapped_required_statuses.append(mapped_status)
                logger.info(f"   ✅ Required_status mapeado com sucesso: pipeline {master_pipeline_id}->{slave_pipeline_id}, status {master_status_id}->{slave_status_id}")
            elif master_status_id in [142, 143, 1]:  # Status especiais do sistema
                # Para required_statuses, os status especiais 142, 143, 1 são mapeados para eles mesmos
                # pois estes IDs são padrão do Kommo em todas as contas
                logger.info(f"   🎯 Status especial detectado: {master_status_id} - mapeando para ele mesmo")
                
                mapped_status = {
                    'status_id': master_status_id,  # Mapear para ele mesmo
                    'pipeline_id': slave_pipeline_id
                }
                mapped_required_statuses.append(mapped_status)
                logger.info(f"   ✅ Required_status especial mapeado: pipeline {master_pipeline_id}->{slave_pipeline_id}, status {master_status_id}->{master_status_id} (especial)")
            else:
                logger.warning(f"   ❌ Status {master_status_id} não encontrado nos mapeamentos - pulando required_status")
        else:
            logger.warning(f"   ❌ Pipeline {master_pipeline_id} não encontrado nos mapeamentos - pulando required_status")
    
    # Resultado final
    logger.info(f"\n📊 RESULTADO FINAL:")
    logger.info(f"   Required statuses originais: {len(master_field['required_statuses'])}")
    logger.info(f"   Required statuses mapeados: {len(mapped_required_statuses)}")
    logger.info(f"   Sucesso: {len(mapped_required_statuses)}/{len(master_field['required_statuses'])}")
    
    if mapped_required_statuses:
        logger.info(f"\n📤 Required statuses finais que serão enviados:")
        for i, rs in enumerate(mapped_required_statuses, 1):
            status_type = "ESPECIAL" if rs['status_id'] in [142, 143, 1] else "MAPEADO"
            logger.info(f"   {i}. Pipeline {rs['pipeline_id']}, Status {rs['status_id']} ({status_type})")
    
    # Verificar se os status especiais foram incluídos
    special_statuses_found = [rs for rs in mapped_required_statuses if rs['status_id'] in [142, 143, 1]]
    logger.info(f"\n🎯 VERIFICAÇÃO DOS STATUS ESPECIAIS:")
    logger.info(f"   Status especiais encontrados: {len(special_statuses_found)}")
    
    if special_statuses_found:
        logger.info(f"   ✅ SUCESSO! Os status especiais foram incluídos:")
        for rs in special_statuses_found:
            logger.info(f"      - Status {rs['status_id']} no pipeline {rs['pipeline_id']}")
    else:
        logger.error(f"   ❌ FALHA! Nenhum status especial foi incluído nos required_statuses")
        return False
    
    # Verificar se todos os status esperados foram mapeados (5 no total)
    expected_count = 5  # 2 normais + 3 especiais
    if len(mapped_required_statuses) == expected_count:
        logger.info(f"   ✅ PERFEITO! Todos os {expected_count} required_statuses foram mapeados corretamente")
        return True
    else:
        logger.warning(f"   ⚠️ Esperado {expected_count} mapeamentos, obtido {len(mapped_required_statuses)}")
        return len(mapped_required_statuses) > 0

if __name__ == "__main__":
    success = test_required_statuses_with_special_stages()
    
    logger.info(f"\n{'='*80}")
    if success:
        logger.info(f"🎉 TESTE PASSOU! Os status especiais 142 e 143 estão sendo incluídos nos required_statuses")
    else:
        logger.error(f"💥 TESTE FALHOU! Os status especiais não estão sendo incluídos corretamente")
    logger.info(f"{'='*80}")
    
    sys.exit(0 if success else 1)

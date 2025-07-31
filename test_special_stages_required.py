#!/usr/bin/env python3
"""
Teste para verificar se estágios especiais (142, 143) são incluídos nos required_statuses
"""

import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_special_stages_in_required_statuses():
    """
    Testa se estágios 142 e 143 são mapeados corretamente nos required_statuses
    """
    logger.info("🔍 TESTANDO ESTÁGIOS ESPECIAIS NOS REQUIRED_STATUSES")
    logger.info("=" * 60)
    
    # Simular campo com required_statuses incluindo estágios especiais
    master_field = {
        'name': 'Campo com Estágios Especiais',
        'type': 'textarea',
        'required_statuses': [
            {'pipeline_id': 11670079, 'status_id': 89684599},  # Status normal: 'blue'
            {'pipeline_id': 11670079, 'status_id': 142},       # ESTÁGIO ESPECIAL 142 ⭐
            {'pipeline_id': 11670079, 'status_id': 143},       # ESTÁGIO ESPECIAL 143 ⭐
        ]
    }
    
    # Simular mapeamentos do banco
    mappings = {
        'pipelines': {
            11670079: 11680487  # master → slave pipeline
        },
        'stages': {
            89684599: 89685559,  # blue: master → slave
            142: 142,           # ESTÁGIO ESPECIAL 142: mesmo ID em ambas ⭐
            143: 143,           # ESTÁGIO ESPECIAL 143: mesmo ID em ambas ⭐
        }
    }
    
    logger.info("📋 DADOS SIMULADOS:")
    logger.info(f"   Campo: {master_field['name']}")
    logger.info(f"   Required statuses: {len(master_field['required_statuses'])}")
    
    for i, rs in enumerate(master_field['required_statuses'], 1):
        status_id = rs['status_id']
        pipeline_id = rs['pipeline_id']
        is_special = status_id in [142, 143]
        logger.info(f"      {i}. Pipeline {pipeline_id}, Status {status_id} {'⭐ ESPECIAL' if is_special else ''}")
    
    # Simular processo de mapeamento
    logger.info(f"\n🔄 SIMULANDO MAPEAMENTO (SEM IGNORE)...")
    
    mapped_required_statuses = []
    
    for req_status in master_field['required_statuses']:
        master_status_id = req_status.get('status_id')
        master_pipeline_id = req_status.get('pipeline_id')
        
        logger.info(f"\n   🔍 Processando: pipeline={master_pipeline_id}, status={master_status_id}")
        
        # NOVA LÓGICA: NÃO ignorar estágios especiais para required_statuses
        is_special_stage = master_status_id in [142, 143]
        if is_special_stage:
            logger.info(f"   ⭐ ESTÁGIO ESPECIAL DETECTADO: {master_status_id} - será INCLUÍDO nos required_statuses")
        
        # Mapear pipeline
        if master_pipeline_id in mappings['pipelines']:
            slave_pipeline_id = mappings['pipelines'][master_pipeline_id]
            logger.info(f"      ✅ Pipeline mapeado: {master_pipeline_id} → {slave_pipeline_id}")
            
            # Mapear status
            if master_status_id in mappings['stages']:
                slave_status_id = mappings['stages'][master_status_id]
                logger.info(f"      ✅ Status mapeado: {master_status_id} → {slave_status_id}")
                
                mapped_status = {
                    'status_id': slave_status_id,
                    'pipeline_id': slave_pipeline_id
                }
                mapped_required_statuses.append(mapped_status)
                
                if is_special_stage:
                    logger.info(f"      ⭐ SUCESSO: Estágio especial {master_status_id} INCLUÍDO nos required_statuses!")
                else:
                    logger.info(f"      ✅ Status normal mapeado com sucesso")
                    
            else:
                logger.error(f"      ❌ Status {master_status_id} não encontrado nos mapeamentos")
        else:
            logger.error(f"      ❌ Pipeline {master_pipeline_id} não encontrado nos mapeamentos")
    
    # Resultado final
    logger.info(f"\n📊 RESULTADO DO MAPEAMENTO:")
    logger.info(f"   Required statuses originais: {len(master_field['required_statuses'])}")
    logger.info(f"   Required statuses mapeados: {len(mapped_required_statuses)}")
    
    if mapped_required_statuses:
        logger.info(f"   ✅ Mapeamento bem-sucedido!")
        
        special_stages_mapped = 0
        for i, rs in enumerate(mapped_required_statuses, 1):
            status_id = rs['status_id']
            pipeline_id = rs['pipeline_id']
            is_special = status_id in [142, 143]
            
            if is_special:
                special_stages_mapped += 1
                logger.info(f"      {i}. Pipeline {pipeline_id}, Status {status_id} ⭐ ESPECIAL MAPEADO!")
            else:
                logger.info(f"      {i}. Pipeline {pipeline_id}, Status {status_id}")
        
        logger.info(f"\n🎯 ESTÁGIOS ESPECIAIS MAPEADOS: {special_stages_mapped}/2")
        
        if special_stages_mapped == 2:
            logger.info(f"   ✅ PERFEITO: Ambos os estágios especiais (142, 143) foram mapeados!")
        elif special_stages_mapped > 0:
            logger.warning(f"   ⚠️ PARCIAL: {special_stages_mapped} estágios especiais mapeados")
        else:
            logger.error(f"   ❌ FALHA: Nenhum estágio especial foi mapeado")
        
        # Dados finais para envio
        field_data = {
            'name': master_field['name'],
            'type': master_field['type'],
            'required_statuses': mapped_required_statuses
        }
        
        logger.info(f"\n📤 DADOS FINAIS PARA ENVIO:")
        logger.info(f"   {field_data}")
        
    else:
        logger.error(f"   ❌ Falha completa no mapeamento")

def compare_before_after():
    """
    Compara comportamento antes e depois da correção
    """
    logger.info("\n" + "=" * 60)
    logger.info("🔄 COMPARAÇÃO: ANTES vs DEPOIS DA CORREÇÃO")
    logger.info("=" * 60)
    
    logger.info("❌ ANTES (comportamento incorreto):")
    logger.info("   - Estágio 142: IGNORADO nos required_statuses")
    logger.info("   - Estágio 143: IGNORADO nos required_statuses")
    logger.info("   - Campo criado SEM required_statuses para estágios especiais")
    logger.info("   - Resultado: Campo não é obrigatório nos estágios que deveria ser")
    
    logger.info("\n✅ DEPOIS (comportamento correto):")
    logger.info("   - Estágio 142: INCLUÍDO nos required_statuses")
    logger.info("   - Estágio 143: INCLUÍDO nos required_statuses")
    logger.info("   - Campo criado COM required_statuses para estágios especiais")
    logger.info("   - Resultado: Campo é obrigatório nos estágios corretos, incluindo especiais")
    
    logger.info("\n💡 IMPORTANTE:")
    logger.info("   - Estágios especiais não devem ser DELETADOS/MODIFICADOS")
    logger.info("   - Mas PODEM e DEVEM ser usados como required_statuses")
    logger.info("   - São estágios válidos do sistema Kommo")

if __name__ == "__main__":
    test_special_stages_in_required_statuses()
    compare_before_after()

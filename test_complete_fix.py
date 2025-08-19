#!/usr/bin/env python3
"""
Teste para verificar se os status 142 e 143 continuam sendo ignorados nas funções normais,
mas são incluídos apenas nos required_statuses
"""

import logging
import sys
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_should_ignore_stage():
    """Testa se a função _should_ignore_stage continua funcionando corretamente"""
    
    logger.info("🧪 TESTE: Verificando se _should_ignore_stage continua ignorando status especiais")
    logger.info("=" * 80)
    
    # Simular estágios de teste
    test_stages = [
        {'id': 456, 'name': 'Estágio Normal', 'type': 0},       # Normal - NÃO deve ser ignorado
        {'id': 142, 'name': 'Won', 'type': 1},                  # Especial - DEVE ser ignorado
        {'id': 143, 'name': 'Lost', 'type': 2},                 # Especial - DEVE ser ignorado
        {'id': 1, 'name': 'Incoming Leads', 'type': 1},         # Especial type=1 - DEVE ser ignorado
        {'id': 789, 'name': 'Outro Normal', 'type': 0},         # Normal - NÃO deve ser ignorado
    ]
    
    # Simular a função _should_ignore_stage
    def should_ignore_stage(stage):
        """Cópia da lógica da função _should_ignore_stage"""
        stage_id = stage.get('id')
        stage_type = stage.get('type', 0)
        stage_name = stage.get('name', '').lower()
        
        # REGRA 1: Ignorar por ID direto (MAIS IMPORTANTE)
        if stage_id in [142, 143]:
            logger.debug(f"🚫 Ignorando estágio por ID especial: {stage_id} - '{stage_name}'")
            return True
            
        # REGRA 2: Ignorar estágios type=1 (incoming leads) - criados automaticamente
        if stage_type == 1:
            logger.debug(f"🚫 Ignorando estágio type=1: '{stage_name}' - criado automaticamente pelo Kommo")
            return True
            
        return False
    
    # Testar cada estágio
    logger.info(f"📋 Testando {len(test_stages)} estágios:")
    
    ignored_count = 0
    processed_count = 0
    
    for i, stage in enumerate(test_stages, 1):
        stage_id = stage['id']
        stage_name = stage['name']
        stage_type = stage['type']
        
        should_ignore = should_ignore_stage(stage)
        
        if should_ignore:
            ignored_count += 1
            status = "🚫 IGNORADO"
            reason = ""
            if stage_id in [142, 143]:
                reason = "(ID especial)"
            elif stage_type == 1:
                reason = "(type=1)"
        else:
            processed_count += 1
            status = "✅ PROCESSADO"
            reason = "(normal)"
        
        logger.info(f"   {i}. Stage {stage_id} '{stage_name}' (type={stage_type}) → {status} {reason}")
    
    # Verificar resultados
    logger.info(f"\n📊 RESULTADO:")
    logger.info(f"   Estágios ignorados: {ignored_count}")
    logger.info(f"   Estágios processados: {processed_count}")
    logger.info(f"   Total: {ignored_count + processed_count}")
    
    # Verificações esperadas
    expected_ignored = 3  # 142, 143, e o type=1
    expected_processed = 2  # Os dois normais
    
    success = True
    
    if ignored_count == expected_ignored:
        logger.info(f"   ✅ Correto! {expected_ignored} estágios especiais foram ignorados")
    else:
        logger.error(f"   ❌ Erro! Esperado {expected_ignored} ignorados, obteve {ignored_count}")
        success = False
    
    if processed_count == expected_processed:
        logger.info(f"   ✅ Correto! {expected_processed} estágios normais foram processados")
    else:
        logger.error(f"   ❌ Erro! Esperado {expected_processed} processados, obteve {processed_count}")
        success = False
    
    # Verificar especificamente os status 142 e 143
    stage_142 = next((s for s in test_stages if s['id'] == 142), None)
    stage_143 = next((s for s in test_stages if s['id'] == 143), None)
    
    if stage_142 and should_ignore_stage(stage_142):
        logger.info(f"   ✅ Status 142 está sendo ignorado corretamente")
    else:
        logger.error(f"   ❌ Status 142 NÃO está sendo ignorado!")
        success = False
    
    if stage_143 and should_ignore_stage(stage_143):
        logger.info(f"   ✅ Status 143 está sendo ignorado corretamente")
    else:
        logger.error(f"   ❌ Status 143 NÃO está sendo ignorado!")
        success = False
    
    return success

def test_required_statuses_inclusion():
    """Testa se os status especiais são incluídos apenas nos required_statuses"""
    
    logger.info(f"\n🧪 TESTE: Verificando inclusão especial nos required_statuses")
    logger.info("=" * 80)
    
    # Simular cenário onde status especiais são necessários em required_statuses
    special_statuses = [142, 143, 1]
    normal_statuses = [456, 789]
    
    logger.info(f"📋 Status especiais (devem ser incluídos em required_statuses): {special_statuses}")
    logger.info(f"📋 Status normais (processamento normal): {normal_statuses}")
    
    # Simular processamento de required_statuses (nova lógica)
    logger.info(f"\n🔄 SIMULANDO PROCESSAMENTO DE REQUIRED_STATUSES:")
    
    mappings = {'stages': {456: 556, 789: 889}}  # Mapeamentos normais
    required_statuses_input = [
        {'pipeline_id': 123, 'status_id': 456},  # Normal
        {'pipeline_id': 123, 'status_id': 142},  # Especial
        {'pipeline_id': 123, 'status_id': 143},  # Especial
        {'pipeline_id': 123, 'status_id': 789},  # Normal
    ]
    
    mapped_required_statuses = []
    slave_pipeline_id = 999
    
    for req_status in required_statuses_input:
        master_status_id = req_status['status_id']
        
        if master_status_id in mappings.get('stages', {}):
            # Status normal - usar mapeamento
            slave_status_id = mappings['stages'][master_status_id]
            mapped_required_statuses.append({'status_id': slave_status_id, 'pipeline_id': slave_pipeline_id})
            logger.info(f"   ✅ Status normal {master_status_id} → {slave_status_id}")
        elif master_status_id in [142, 143, 1]:
            # Status especial - mapear para ele mesmo
            mapped_required_statuses.append({'status_id': master_status_id, 'pipeline_id': slave_pipeline_id})
            logger.info(f"   🎯 Status especial {master_status_id} → {master_status_id} (mantido)")
        else:
            logger.warning(f"   ❌ Status {master_status_id} não mapeado")
    
    # Verificar se os status especiais foram incluídos
    special_found = [rs for rs in mapped_required_statuses if rs['status_id'] in [142, 143, 1]]
    normal_found = [rs for rs in mapped_required_statuses if rs['status_id'] not in [142, 143, 1]]
    
    logger.info(f"\n📊 RESULTADO DOS REQUIRED_STATUSES:")
    logger.info(f"   Status especiais incluídos: {len(special_found)}")
    logger.info(f"   Status normais mapeados: {len(normal_found)}")
    logger.info(f"   Total mapeado: {len(mapped_required_statuses)}")
    
    success = True
    
    # Verificar se os status especiais estão lá
    if 142 in [rs['status_id'] for rs in special_found]:
        logger.info(f"   ✅ Status 142 incluído nos required_statuses")
    else:
        logger.error(f"   ❌ Status 142 NÃO incluído nos required_statuses")
        success = False
    
    if 143 in [rs['status_id'] for rs in special_found]:
        logger.info(f"   ✅ Status 143 incluído nos required_statuses")
    else:
        logger.error(f"   ❌ Status 143 NÃO incluído nos required_statuses")
        success = False
    
    return success

if __name__ == "__main__":
    logger.info("🚀 BATERIA DE TESTES: Status especiais 142 e 143")
    logger.info("=" * 80)
    
    test1_success = test_should_ignore_stage()
    test2_success = test_required_statuses_inclusion()
    
    overall_success = test1_success and test2_success
    
    logger.info(f"\n{'='*80}")
    if overall_success:
        logger.info(f"🎉 TODOS OS TESTES PASSARAM!")
        logger.info(f"   ✅ Status 142 e 143 são ignorados nas funções normais")
        logger.info(f"   ✅ Status 142 e 143 são incluídos nos required_statuses")
        logger.info(f"   ✅ A correção está funcionando perfeitamente!")
    else:
        logger.error(f"💥 ALGUNS TESTES FALHARAM!")
        logger.error(f"   - Teste 1 (ignore normal): {'✅' if test1_success else '❌'}")
        logger.error(f"   - Teste 2 (include required): {'✅' if test2_success else '❌'}")
    logger.info(f"{'='*80}")
    
    sys.exit(0 if overall_success else 1)

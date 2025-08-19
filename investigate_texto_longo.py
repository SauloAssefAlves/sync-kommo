#!/usr/bin/env python3
"""
Investiga por que o campo 'texto longo' com required_statuses não está sendo aplicado na slave
"""

import sqlite3
import logging
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def investigate_required_status_issue():
    """Investiga o problema com o required_status específico"""
    logger.info("🔍 INVESTIGANDO PROBLEMA COM REQUIRED_STATUS")
    logger.info("=" * 60)
    
    # Dados do problema
    field_name = "texto longo"
    master_pipeline_id = 11670079
    master_status_id = 89684599
    
    logger.info(f"📋 Analisando campo: '{field_name}'")
    logger.info(f"📊 Pipeline master: {master_pipeline_id}")
    logger.info(f"🎭 Status master: {master_status_id}")
    
    # Verificar mapeamentos no banco
    db_path = "src/database/app.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Buscar mapeamento do pipeline
    cursor.execute("SELECT slave_pipeline_id FROM pipeline_mappings WHERE sync_group_id = 1 AND master_pipeline_id = ?", (master_pipeline_id,))
    pipeline_row = cursor.fetchone()
    
    if not pipeline_row:
        logger.error(f"❌ Pipeline {master_pipeline_id} não encontrado nos mapeamentos!")
        return
    
    slave_pipeline_id = pipeline_row['slave_pipeline_id']
    logger.info(f"✅ Pipeline mapeado: {master_pipeline_id} → {slave_pipeline_id}")
    
    # Buscar mapeamento do stage
    cursor.execute("SELECT slave_stage_id FROM stage_mappings WHERE sync_group_id = 1 AND master_stage_id = ?", (master_status_id,))
    stage_row = cursor.fetchone()
    
    if not stage_row:
        logger.error(f"❌ Stage {master_status_id} não encontrado nos mapeamentos!")
        return
    
    slave_status_id = stage_row['slave_stage_id']
    logger.info(f"✅ Stage mapeado: {master_status_id} → {slave_status_id}")
    
    conn.close()
    
    # Simular o processo de mapeamento como no código
    logger.info(f"\n🔄 SIMULANDO PROCESSO DE MAPEAMENTO:")
    
    # Dados originais do required_status
    original_required_status = {
        'pipeline_id': master_pipeline_id,
        'status_id': master_status_id
    }
    
    logger.info(f"📥 Required_status original: {original_required_status}")
    
    # Aplicar lógica de mapeamento (como no código real)
    mapped_required_status = {
        'status_id': slave_status_id,
        'pipeline_id': slave_pipeline_id
    }
    
    logger.info(f"📤 Required_status mapeado: {mapped_required_status}")
    
    # Verificar se o mapeamento está correto
    logger.info(f"\n✅ MAPEAMENTO CORRETO:")
    logger.info(f"   Pipeline: {master_pipeline_id} → {slave_pipeline_id}")
    logger.info(f"   Status: {master_status_id} → {slave_status_id}")
    
    # Possíveis causas do problema
    logger.info(f"\n🕵️ POSSÍVEIS CAUSAS DO PROBLEMA:")
    
    logger.info(f"\n1. 🔍 VERIFICAR SE O CAMPO FOI REALMENTE SINCRONIZADO:")
    logger.info(f"   - O campo 'texto longo' existe na conta slave?")
    logger.info(f"   - O required_status pode ter sido removido durante a validação")
    
    logger.info(f"\n2. 🔍 VERIFICAR VALIDAÇÃO NA SLAVE:")
    logger.info(f"   - Pipeline {slave_pipeline_id} existe na slave?")
    logger.info(f"   - Status {slave_status_id} existe no pipeline {slave_pipeline_id} da slave?")
    
    logger.info(f"\n3. 🔍 VERIFICAR LOGS DE SINCRONIZAÇÃO:")
    logger.info(f"   - Buscar por mensagens como 'VÁLIDO' ou 'NÃO existe'")
    logger.info(f"   - Verificar se houve erro na validação real")
    
    logger.info(f"\n4. 🔍 VERIFICAR SE É CAMPO NOVO OU ATUALIZAÇÃO:")
    logger.info(f"   - Se é atualização, o required_status pode ter sido perdido")
    logger.info(f"   - Verificar se o campo já existia na slave antes")
    
    # Script de verificação sugerido
    logger.info(f"\n💡 SCRIPT DE VERIFICAÇÃO SUGERIDO:")
    
    verification_code = f"""
# 1. Verificar se o pipeline existe na slave
GET /leads/pipelines → buscar pipeline ID {slave_pipeline_id}

# 2. Verificar se o status existe no pipeline da slave  
GET /leads/pipelines/{slave_pipeline_id}/statuses → buscar status ID {slave_status_id}

# 3. Verificar o campo na slave
GET /leads/custom_fields → buscar campo 'texto longo' e seus required_statuses

# 4. Verificar logs da última sincronização
grep -r "texto longo" logs/ 
grep -r "{slave_pipeline_id}" logs/
grep -r "{slave_status_id}" logs/
"""
    
    logger.info(f"\n📋 COMANDOS PARA EXECUTAR:")
    logger.info(verification_code)
    
    return {
        'field_name': field_name,
        'master_pipeline_id': master_pipeline_id,
        'master_status_id': master_status_id,
        'slave_pipeline_id': slave_pipeline_id,
        'slave_status_id': slave_status_id,
        'mapped_required_status': mapped_required_status
    }

def create_test_script():
    """Cria script para testar se o mapeamento funcionaria"""
    logger.info(f"\n🧪 CRIANDO SCRIPT DE TESTE:")
    
    test_code = '''
# Teste do mapeamento específico
def test_texto_longo_mapping():
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
    
    # Aplicar lógica de mapeamento
    mapped_required_statuses = []
    
    for req_status in master_field['required_statuses']:
        master_status_id = req_status.get('status_id')
        master_pipeline_id = req_status.get('pipeline_id')
        
        if master_pipeline_id in mappings['pipelines']:
            slave_pipeline_id = mappings['pipelines'][master_pipeline_id]
            
            if master_status_id in mappings['stages']:
                slave_status_id = mappings['stages'][master_status_id]
                
                mapped_status = {
                    'status_id': slave_status_id,
                    'pipeline_id': slave_pipeline_id
                }
                mapped_required_statuses.append(mapped_status)
                print(f"✅ Mapeado: {master_status_id} → {slave_status_id}")
            else:
                print(f"❌ Status {master_status_id} não mapeado")
        else:
            print(f"❌ Pipeline {master_pipeline_id} não mapeado")
    
    print(f"📤 Required statuses finais: {mapped_required_statuses}")
    return mapped_required_statuses

# Executar teste
result = test_texto_longo_mapping()
'''
    
    logger.info(test_code)

if __name__ == "__main__":
    investigation_result = investigate_required_status_issue()
    create_test_script()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🎯 PRÓXIMOS PASSOS RECOMENDADOS:")
    logger.info(f"1. Verificar se o pipeline {investigation_result['slave_pipeline_id']} existe na slave")
    logger.info(f"2. Verificar se o status {investigation_result['slave_status_id']} existe no pipeline da slave")
    logger.info(f"3. Buscar logs da sincronização do campo 'texto longo'")
    logger.info(f"4. Verificar se houve erro na validação real dos IDs")
    logger.info(f"{'='*60}")

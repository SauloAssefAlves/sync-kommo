#!/usr/bin/env python3
"""
Script para testar diretamente as funções de mapeamento de required_statuses
sem depender do Flask
"""

import sys
import os
import sqlite3
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_mappings_from_db():
    """Carrega mapeamentos do banco de dados"""
    logger.info("📊 Carregando mapeamentos do banco...")
    
    db_path = "src/database/app.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Carregar mapeamentos de pipeline
    cursor.execute("SELECT master_pipeline_id, slave_pipeline_id FROM pipeline_mappings WHERE sync_group_id = 1")
    pipeline_rows = cursor.fetchall()
    pipeline_mappings = {row['master_pipeline_id']: row['slave_pipeline_id'] for row in pipeline_rows}
    
    # Carregar mapeamentos de stage
    cursor.execute("SELECT master_stage_id, slave_stage_id FROM stage_mappings WHERE sync_group_id = 1")
    stage_rows = cursor.fetchall()
    stage_mappings = {row['master_stage_id']: row['slave_stage_id'] for row in stage_rows}
    
    conn.close()
    
    logger.info(f"✅ Pipelines mapeados: {len(pipeline_mappings)}")
    logger.info(f"✅ Stages mapeados: {len(stage_mappings)}")
    
    return pipeline_mappings, stage_mappings

def simulate_required_status_mapping():
    """Simula o processo de mapeamento de required_statuses"""
    logger.info("🔄 SIMULANDO MAPEAMENTO DE REQUIRED_STATUSES")
    logger.info("=" * 60)
    
    # Carregar mapeamentos reais do banco
    pipeline_mappings, stage_mappings = load_mappings_from_db()
    
    # Simular campo 'texto longo' da master
    master_field = {
        'id': 123456,
        'name': 'texto longo',
        'type': 'textarea',
        'required_statuses': [
            {
                'pipeline_id': 11670079,
                'status_id': 89684599
            }
        ]
    }
    
    logger.info(f"📥 Campo master: {master_field['name']}")
    logger.info(f"📥 Required statuses originais: {master_field['required_statuses']}")
    
    # Aplicar lógica de mapeamento (copiado do código real)
    mapped_required_statuses = []
    
    for required_status in master_field.get('required_statuses', []):
        master_status_id = required_status.get('status_id')
        master_pipeline_id = required_status.get('pipeline_id')
        
        logger.info(f"\n🔍 Processando required_status:")
        logger.info(f"   Master Pipeline ID: {master_pipeline_id}")
        logger.info(f"   Master Status ID: {master_status_id}")
        
        # Verificar se status é especial (142, 143, 1)
        if master_status_id in [142, 143, 1]:
            logger.info(f"   ⚡ Status especial detectado: {master_status_id}")
            
            # Para statuses especiais, mapear para eles mesmos
            if master_pipeline_id in pipeline_mappings:
                slave_pipeline_id = pipeline_mappings[master_pipeline_id]
                
                mapped_status = {
                    'status_id': master_status_id,  # Status especial mantém mesmo ID
                    'pipeline_id': slave_pipeline_id
                }
                mapped_required_statuses.append(mapped_status)
                logger.info(f"   ✅ Status especial mapeado: {mapped_status}")
            else:
                logger.warning(f"   ❌ Pipeline {master_pipeline_id} não encontrado nos mapeamentos")
                
        else:
            logger.info(f"   📋 Status normal, buscando mapeamento...")
            
            # Para statuses normais, usar mapeamento do banco
            if master_pipeline_id in pipeline_mappings and master_status_id in stage_mappings:
                slave_pipeline_id = pipeline_mappings[master_pipeline_id]
                slave_status_id = stage_mappings[master_status_id]
                
                mapped_status = {
                    'status_id': slave_status_id,
                    'pipeline_id': slave_pipeline_id
                }
                mapped_required_statuses.append(mapped_status)
                logger.info(f"   ✅ Status normal mapeado: {mapped_status}")
                
            elif master_pipeline_id not in pipeline_mappings:
                logger.warning(f"   ❌ Pipeline {master_pipeline_id} não encontrado nos mapeamentos")
                
            elif master_status_id not in stage_mappings:
                logger.warning(f"   ❌ Status {master_status_id} não encontrado nos mapeamentos")
    
    # Resultado final
    logger.info(f"\n📤 RESULTADO FINAL:")
    logger.info(f"   Required statuses mapeados: {len(mapped_required_statuses)}")
    
    for i, rs in enumerate(mapped_required_statuses):
        logger.info(f"   {i+1}. {rs}")
    
    # Comparar com esperado
    expected = [{'status_id': 90777427, 'pipeline_id': 11795583}]
    success = mapped_required_statuses == expected
    
    logger.info(f"\n🎯 VALIDAÇÃO:")
    logger.info(f"   Esperado: {expected}")
    logger.info(f"   Obtido:   {mapped_required_statuses}")
    logger.info(f"   Status:   {'✅ SUCESSO' if success else '❌ DIFERENTE'}")
    
    return mapped_required_statuses

def test_special_statuses():
    """Testa o comportamento com statuses especiais"""
    logger.info(f"\n🧪 TESTE COM STATUSES ESPECIAIS")
    logger.info("=" * 40)
    
    pipeline_mappings, stage_mappings = load_mappings_from_db()
    
    # Testar campos com statuses especiais
    test_cases = [
        {'name': 'campo_142', 'required_statuses': [{'pipeline_id': 11670079, 'status_id': 142}]},
        {'name': 'campo_143', 'required_statuses': [{'pipeline_id': 11670079, 'status_id': 143}]},
        {'name': 'campo_1', 'required_statuses': [{'pipeline_id': 11670079, 'status_id': 1}]},
    ]
    
    for test_field in test_cases:
        logger.info(f"\n🔍 Testando {test_field['name']}:")
        
        for rs in test_field['required_statuses']:
            master_pipeline_id = rs['pipeline_id']
            master_status_id = rs['status_id']
            
            if master_status_id in [142, 143, 1]:
                if master_pipeline_id in pipeline_mappings:
                    slave_pipeline_id = pipeline_mappings[master_pipeline_id]
                    result = {'status_id': master_status_id, 'pipeline_id': slave_pipeline_id}
                    logger.info(f"   ✅ {master_status_id} → {result}")
                else:
                    logger.info(f"   ❌ Pipeline {master_pipeline_id} não mapeado")

if __name__ == "__main__":
    logger.info("🔬 TESTE DE MAPEAMENTO DE REQUIRED_STATUSES")
    logger.info("=" * 70)
    
    try:
        # Teste principal
        simulate_required_status_mapping()
        
        # Teste com statuses especiais
        test_special_statuses()
        
        logger.info(f"\n" + "=" * 70)
        logger.info("✅ TESTE CONCLUÍDO")
        
    except Exception as e:
        logger.error(f"❌ Erro durante teste: {e}")
        import traceback
        logger.error(traceback.format_exc())

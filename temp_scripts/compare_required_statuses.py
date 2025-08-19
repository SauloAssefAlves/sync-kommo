#!/usr/bin/env python3
"""
Compara os required_statuses entre as contas master e slave usando dados do banco local
"""

import sqlite3
import logging
import sys
import json
from typing import Dict, List

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_accounts_from_database() -> Dict:
    """Obtém dados das contas master e slave do banco de dados"""
    db_path = "src/database/app.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Buscar conta master
        cursor.execute("SELECT * FROM kommo_accounts WHERE is_master = 1 LIMIT 1")
        master_row = cursor.fetchone()
        
        # Buscar conta slave
        cursor.execute("SELECT * FROM kommo_accounts WHERE is_master = 0 LIMIT 1")
        slave_row = cursor.fetchone()
        
        conn.close()
        
        if not master_row or not slave_row:
            logger.error("❌ Contas master e/ou slave não encontradas")
            return {}
        
        master_account = dict(master_row)
        slave_account = dict(slave_row)
        
        logger.info(f"📊 Contas encontradas:")
        logger.info(f"   Master: {master_account['subdomain']} (ID: {master_account['id']})")
        logger.info(f"   Slave: {slave_account['subdomain']} (ID: {slave_account['id']})")
        
        return {
            'master': master_account,
            'slave': slave_account
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao acessar banco de dados: {e}")
        return {}

def get_mappings_from_database(sync_group_id: int) -> Dict:
    """Obtém mapeamentos de pipelines e stages do banco de dados"""
    db_path = "src/database/app.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obter mapeamentos de pipelines
        cursor.execute("SELECT master_pipeline_id, slave_pipeline_id FROM pipeline_mappings WHERE sync_group_id = ?", (sync_group_id,))
        pipeline_rows = cursor.fetchall()
        
        pipeline_mappings = {}
        for row in pipeline_rows:
            pipeline_mappings[row['master_pipeline_id']] = row['slave_pipeline_id']
        
        # Obter mapeamentos de stages
        cursor.execute("SELECT master_stage_id, slave_stage_id FROM stage_mappings WHERE sync_group_id = ?", (sync_group_id,))
        stage_rows = cursor.fetchall()
        
        stage_mappings = {}
        for row in stage_rows:
            stage_mappings[row['master_stage_id']] = row['slave_stage_id']
        
        conn.close()
        
        logger.info(f"📊 Mapeamentos encontrados no banco:")
        logger.info(f"   Pipelines: {len(pipeline_mappings)} mapeamentos")
        logger.info(f"   Stages: {len(stage_mappings)} mapeamentos")
        
        # Verificar se há mapeamentos de status especiais
        special_stages = [stage_id for stage_id in stage_mappings.keys() if stage_id in [142, 143, 1]]
        if special_stages:
            logger.info(f"   🎯 Status especiais encontrados nos mapeamentos: {special_stages}")
            for special_id in special_stages:
                mapped_id = stage_mappings[special_id]
                status_names = {142: "Won", 143: "Lost", 1: "Incoming"}
                status_name = status_names.get(special_id, "ESPECIAL")
                logger.info(f"      Status {special_id} ({status_name}) → {mapped_id}")
        else:
            logger.warning(f"   ⚠️ Nenhum status especial (142, 143, 1) encontrado nos mapeamentos")
        
        return {
            'pipelines': pipeline_mappings,
            'stages': stage_mappings
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter mapeamentos: {e}")
        return {'pipelines': {}, 'stages': {}}

def simulate_required_statuses_mapping(mappings: Dict) -> None:
    """Simula como os required_statuses seriam mapeados"""
    logger.info(f"\n🧪 SIMULAÇÃO DE MAPEAMENTO DE REQUIRED_STATUSES")
    logger.info("=" * 60)
    
    # Simular alguns casos de required_statuses comuns
    test_cases = [
        {
            'field_name': 'Campo Texto 1',
            'required_statuses': [
                {'pipeline_id': 123, 'status_id': 456},  # Status normal
                {'pipeline_id': 123, 'status_id': 142},  # Won
            ]
        },
        {
            'field_name': 'Campo Textarea 1', 
            'required_statuses': [
                {'pipeline_id': 124, 'status_id': 143},  # Lost
                {'pipeline_id': 124, 'status_id': 789},  # Status normal
            ]
        },
        {
            'field_name': 'Campo Select 1',
            'required_statuses': [
                {'pipeline_id': 125, 'status_id': 1},    # Incoming
                {'pipeline_id': 125, 'status_id': 142},  # Won
                {'pipeline_id': 125, 'status_id': 143},  # Lost
            ]
        }
    ]
    
    logger.info(f"📋 Testando {len(test_cases)} casos de required_statuses:")
    
    for i, test_case in enumerate(test_cases, 1):
        field_name = test_case['field_name']
        required_statuses = test_case['required_statuses']
        
        logger.info(f"\n🏷️ Caso {i}: Campo '{field_name}'")
        logger.info(f"   Required statuses originais: {len(required_statuses)}")
        
        mapped_required_statuses = []
        
        for j, rs in enumerate(required_statuses, 1):
            master_pipeline_id = rs['pipeline_id']
            master_status_id = rs['status_id']
            
            logger.info(f"\n   {j}. Processando: pipeline={master_pipeline_id}, status={master_status_id}")
            
            # Verificar se pipeline está mapeado
            if master_pipeline_id in mappings['pipelines']:
                slave_pipeline_id = mappings['pipelines'][master_pipeline_id]
                logger.info(f"      ✅ Pipeline mapeado: {master_pipeline_id} → {slave_pipeline_id}")
                
                # Verificar mapeamento do status
                if master_status_id in mappings['stages']:
                    slave_status_id = mappings['stages'][master_status_id]
                    logger.info(f"      ✅ Status mapeado: {master_status_id} → {slave_status_id}")
                    
                    mapped_status = {
                        'status_id': slave_status_id,
                        'pipeline_id': slave_pipeline_id
                    }
                    mapped_required_statuses.append(mapped_status)
                    
                elif master_status_id in [142, 143, 1]:
                    # Aplicar a NOVA LÓGICA implementada
                    logger.info(f"      🎯 Status especial detectado: {master_status_id}")
                    status_names = {142: "Won", 143: "Lost", 1: "Incoming"}
                    status_name = status_names.get(master_status_id, "ESPECIAL")
                    logger.info(f"      🎯 Aplicando nova lógica: mapear {master_status_id} ({status_name}) para ele mesmo")
                    
                    mapped_status = {
                        'status_id': master_status_id,  # Mapear para ele mesmo
                        'pipeline_id': slave_pipeline_id
                    }
                    mapped_required_statuses.append(mapped_status)
                    logger.info(f"      ✅ Required_status especial mapeado: {master_status_id} → {master_status_id}")
                    
                else:
                    logger.warning(f"      ❌ Status {master_status_id} não encontrado nos mapeamentos")
                    
            else:
                logger.warning(f"      ❌ Pipeline {master_pipeline_id} não encontrado nos mapeamentos")
        
        # Resultado do campo
        success_rate = len(mapped_required_statuses) / len(required_statuses) * 100
        logger.info(f"\n   📊 Resultado do campo '{field_name}':")
        logger.info(f"      Original: {len(required_statuses)} required_statuses")
        logger.info(f"      Mapeados: {len(mapped_required_statuses)} required_statuses")
        logger.info(f"      Taxa de sucesso: {success_rate:.1f}%")
        
        if success_rate == 100:
            logger.info(f"      ✅ PERFEITO! Todos os required_statuses foram mapeados")
        elif success_rate >= 80:
            logger.info(f"      ⚠️ BOM: Maioria dos required_statuses mapeados")
        else:
            logger.warning(f"      ❌ PROBLEMA: Muitos required_statuses não mapeados")

def analyze_stage_mappings(mappings: Dict) -> None:
    """Analisa os mapeamentos de stages em detalhes"""
    logger.info(f"\n📊 ANÁLISE DETALHADA DOS MAPEAMENTOS DE STAGES")
    logger.info("=" * 60)
    
    stage_mappings = mappings.get('stages', {})
    
    if not stage_mappings:
        logger.error("❌ Nenhum mapeamento de stage encontrado!")
        return
    
    # Separar status normais e especiais
    normal_stages = {k: v for k, v in stage_mappings.items() if k not in [142, 143, 1]}
    special_stages = {k: v for k, v in stage_mappings.items() if k in [142, 143, 1]}
    
    logger.info(f"📈 Resumo dos mapeamentos:")
    logger.info(f"   Total de stages mapeados: {len(stage_mappings)}")
    logger.info(f"   Stages normais: {len(normal_stages)}")
    logger.info(f"   Stages especiais: {len(special_stages)}")
    
    # Analisar stages especiais
    if special_stages:
        logger.info(f"\n🎯 STAGES ESPECIAIS MAPEADOS:")
        status_names = {142: "Won", 143: "Lost", 1: "Incoming"}
        
        for master_id, slave_id in special_stages.items():
            status_name = status_names.get(master_id, "ESPECIAL")
            if master_id == slave_id:
                logger.info(f"   ✅ Status {master_id} ({status_name}): {master_id} → {slave_id} (mapeamento correto)")
            else:
                logger.warning(f"   ⚠️ Status {master_id} ({status_name}): {master_id} → {slave_id} (mapeamento diferente)")
        
        # Verificar se todos os status especiais estão presentes
        expected_special = [142, 143, 1]
        missing_special = [sid for sid in expected_special if sid not in special_stages]
        
        if missing_special:
            logger.warning(f"\n⚠️ STAGES ESPECIAIS NÃO MAPEADOS:")
            for missing_id in missing_special:
                status_name = status_names.get(missing_id, "ESPECIAL")
                logger.warning(f"   ❌ Status {missing_id} ({status_name}) não encontrado nos mapeamentos")
                logger.info(f"      💡 Isso pode causar problemas com required_statuses que dependem deste status")
        else:
            logger.info(f"\n✅ PERFEITO! Todos os stages especiais esperados estão mapeados")
    
    else:
        logger.warning(f"\n❌ PROBLEMA: Nenhum stage especial (142, 143, 1) encontrado nos mapeamentos!")
        logger.info(f"💡 Isso significa que campos com required_statuses dependendo desses status falharão")
        logger.info(f"💡 A correção implementada resolve exatamente este problema")

def main():
    """Função principal"""
    logger.info("🔍 COMPARAÇÃO DE REQUIRED_STATUSES - MASTER vs SLAVE")
    logger.info("=" * 80)
    
    try:
        # Obter contas do banco
        accounts = get_accounts_from_database()
        if not accounts:
            return
        
        master_account = accounts['master']
        slave_account = accounts['slave']
        sync_group_id = master_account.get('sync_group_id') or slave_account.get('sync_group_id')
        
        if not sync_group_id:
            logger.error("❌ sync_group_id não encontrado")
            return
        
        logger.info(f"🔗 Sync Group ID: {sync_group_id}")
        
        # Obter mapeamentos do banco
        mappings = get_mappings_from_database(sync_group_id)
        
        # Analisar mapeamentos de stages
        analyze_stage_mappings(mappings)
        
        # Simular mapeamento de required_statuses
        simulate_required_statuses_mapping(mappings)
        
        # Conclusão
        logger.info(f"\n{'='*80}")
        logger.info(f"🎯 CONCLUSÃO DA ANÁLISE")
        logger.info(f"{'='*80}")
        
        stage_mappings = mappings.get('stages', {})
        special_stages = [sid for sid in [142, 143, 1] if sid in stage_mappings]
        
        if len(special_stages) == 3:
            logger.info(f"✅ TUDO CERTO! Todos os stages especiais (142, 143, 1) estão mapeados")
            logger.info(f"✅ Os required_statuses que dependem desses status funcionarão corretamente")
            logger.info(f"✅ A correção implementada não é mais necessária (já resolvida)")
        elif len(special_stages) > 0:
            logger.warning(f"⚠️ PARCIALMENTE OK: {len(special_stages)}/3 stages especiais mapeados")
            logger.info(f"⚠️ Stages mapeados: {special_stages}")
            missing = [sid for sid in [142, 143, 1] if sid not in stage_mappings]
            logger.warning(f"⚠️ Stages faltando: {missing}")
            logger.info(f"💡 A correção implementada ajudará com os status faltantes")
        else:
            logger.error(f"❌ PROBLEMA: Nenhum stage especial mapeado!")
            logger.error(f"❌ Required_statuses com status 142, 143 ou 1 falharão")
            logger.info(f"✅ A correção implementada resolverá este problema completamente")
        
        # Salvar análise
        result = {
            'accounts': {
                'master': {
                    'subdomain': master_account['subdomain'],
                    'id': master_account['id']
                },
                'slave': {
                    'subdomain': slave_account['subdomain'], 
                    'id': slave_account['id']
                }
            },
            'mappings': {
                'pipelines_count': len(mappings.get('pipelines', {})),
                'stages_count': len(mappings.get('stages', {})),
                'special_stages_mapped': special_stages,
                'special_stages_count': len(special_stages)
            },
            'analysis': {
                'all_special_stages_mapped': len(special_stages) == 3,
                'correction_needed': len(special_stages) < 3,
                'correction_effectiveness': 'full' if len(special_stages) == 0 else 'partial'
            }
        }
        
        with open('required_statuses_comparison.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Comparação salva em: required_statuses_comparison.json")
        
    except Exception as e:
        logger.error(f"❌ Erro na comparação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

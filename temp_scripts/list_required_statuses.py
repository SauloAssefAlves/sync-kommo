#!/usr/bin/env python3
"""
Lista os required_statuses dos campos customizados das contas master e slave
"""

import logging
import sys
import os
from typing import Dict, List, Optional

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_account_required_statuses(api_service, account_name: str) -> Dict:
    """Obtém todos os required_statuses de uma conta"""
    logger.info(f"🔍 Analisando required_statuses da conta: {account_name}")
    
    try:
        # Obter pipelines para referência
        pipelines = api_service.get_pipelines()
        pipelines_by_id = {p['id']: p for p in pipelines}
        
        logger.info(f"📊 Pipelines encontrados: {len(pipelines)}")
        for pipeline in pipelines:
            logger.info(f"   - {pipeline['name']} (ID: {pipeline['id']})")
        
        # Obter campos customizados de diferentes entidades
        entities = ['leads', 'contacts', 'companies']
        all_required_statuses = {}
        
        for entity in entities:
            logger.info(f"\n🔍 Verificando campos de {entity}...")
            
            try:
                fields = api_service.get_custom_fields(entity)
                logger.info(f"   Campos encontrados: {len(fields)}")
                
                fields_with_required = []
                for field in fields:
                    if field.get('required_statuses'):
                        fields_with_required.append(field)
                        logger.info(f"   📋 Campo '{field['name']}' tem {len(field['required_statuses'])} required_statuses")
                
                all_required_statuses[entity] = fields_with_required
                logger.info(f"   Total com required_statuses: {len(fields_with_required)}")
                
            except Exception as e:
                logger.error(f"   ❌ Erro ao obter campos de {entity}: {e}")
                all_required_statuses[entity] = []
        
        return {
            'account_name': account_name,
            'pipelines': pipelines_by_id,
            'required_statuses': all_required_statuses
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao analisar conta {account_name}: {e}")
        return {
            'account_name': account_name,
            'pipelines': {},
            'required_statuses': {},
            'error': str(e)
        }

def print_required_statuses_analysis(account_data: Dict):
    """Imprime análise detalhada dos required_statuses"""
    account_name = account_data['account_name']
    pipelines = account_data.get('pipelines', {})
    required_statuses = account_data.get('required_statuses', {})
    
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 ANÁLISE DETALHADA - {account_name.upper()}")
    logger.info(f"{'='*80}")
    
    if 'error' in account_data:
        logger.error(f"❌ Erro na conta: {account_data['error']}")
        return
    
    total_fields_with_required = 0
    total_required_statuses = 0
    status_usage = {}  # Para contar quantas vezes cada status é usado
    
    for entity, fields in required_statuses.items():
        if not fields:
            logger.info(f"\n📂 {entity.upper()}: Nenhum campo com required_statuses")
            continue
            
        logger.info(f"\n📂 {entity.upper()}: {len(fields)} campos com required_statuses")
        total_fields_with_required += len(fields)
        
        for field in fields:
            field_name = field['name']
            field_type = field.get('type', 'unknown')
            req_statuses = field.get('required_statuses', [])
            
            logger.info(f"\n   🏷️ Campo: '{field_name}' ({field_type})")
            logger.info(f"      Required statuses: {len(req_statuses)}")
            
            total_required_statuses += len(req_statuses)
            
            for i, rs in enumerate(req_statuses, 1):
                status_id = rs.get('status_id')
                pipeline_id = rs.get('pipeline_id')
                
                # Contar uso do status
                if status_id not in status_usage:
                    status_usage[status_id] = 0
                status_usage[status_id] += 1
                
                # Obter nomes para facilitar leitura
                pipeline_name = "DESCONHECIDA"
                if pipeline_id in pipelines:
                    pipeline_name = pipelines[pipeline_id]['name']
                
                status_name = "DESCONHECIDO"
                if pipeline_id in pipelines:
                    try:
                        # Esta seria uma chamada à API para obter stages
                        # Por agora, apenas mostrar o ID
                        if status_id in [142, 143, 1]:
                            status_names = {142: "Won", 143: "Lost", 1: "Incoming"}
                            status_name = status_names.get(status_id, "ESPECIAL")
                    except:
                        pass
                
                status_type = "ESPECIAL" if status_id in [142, 143, 1] else "NORMAL"
                logger.info(f"         {i}. Pipeline '{pipeline_name}' (ID: {pipeline_id})")
                logger.info(f"            Status ID: {status_id} ({status_name}) [{status_type}]")
    
    # Resumo geral
    logger.info(f"\n📈 RESUMO GERAL:")
    logger.info(f"   Total de campos com required_statuses: {total_fields_with_required}")
    logger.info(f"   Total de required_statuses configurados: {total_required_statuses}")
    logger.info(f"   Status únicos utilizados: {len(status_usage)}")
    
    # Análise de status mais usados
    if status_usage:
        logger.info(f"\n🎯 STATUS MAIS UTILIZADOS:")
        sorted_statuses = sorted(status_usage.items(), key=lambda x: x[1], reverse=True)
        
        for status_id, count in sorted_statuses[:10]:  # Top 10
            status_type = "ESPECIAL" if status_id in [142, 143, 1] else "NORMAL"
            logger.info(f"   Status {status_id}: usado {count}x ({status_type})")
    
    # Verificar se há status especiais
    special_statuses = [sid for sid in status_usage.keys() if sid in [142, 143, 1]]
    if special_statuses:
        logger.info(f"\n⭐ STATUS ESPECIAIS ENCONTRADOS:")
        for status_id in special_statuses:
            status_names = {142: "Won", 143: "Lost", 1: "Incoming"}
            status_name = status_names.get(status_id, "ESPECIAL")
            count = status_usage[status_id]
            logger.info(f"   Status {status_id} ({status_name}): usado {count}x")
    else:
        logger.info(f"\n📝 Nenhum status especial (142, 143, 1) encontrado nos required_statuses")

def main():
    """Função principal"""
    logger.info("🚀 ANALISADOR DE REQUIRED_STATUSES")
    logger.info("=" * 80)
    
    try:
        # Importar as classes necessárias
        from src.services.kommo_api import KommoAPIService
        from src.models.kommo_account import KommoAccount
        from src.database import db
        
        # Obter contas do banco de dados
        logger.info("📊 Obtendo contas do banco de dados...")
        
        accounts = KommoAccount.query.all()
        logger.info(f"Contas encontradas: {len(accounts)}")
        
        if len(accounts) < 2:
            logger.error("❌ Necessário pelo menos 2 contas para comparar master e slave")
            return
        
        # Para este exemplo, vamos usar as duas primeiras contas
        # Você pode modificar esta lógica conforme necessário
        master_account = accounts[0]
        slave_account = accounts[1]
        
        logger.info(f"Master: {master_account.subdomain}")
        logger.info(f"Slave: {slave_account.subdomain}")
        
        # Criar instâncias das APIs
        master_api = KommoAPIService(master_account.subdomain, master_account.access_token)
        slave_api = KommoAPIService(slave_account.subdomain, slave_account.access_token)
        
        # Analisar ambas as contas
        logger.info(f"\n🔍 Iniciando análise das contas...")
        
        master_data = get_account_required_statuses(master_api, f"MASTER ({master_account.subdomain})")
        slave_data = get_account_required_statuses(slave_api, f"SLAVE ({slave_account.subdomain})")
        
        # Imprimir análises
        print_required_statuses_analysis(master_data)
        print_required_statuses_analysis(slave_data)
        
        # Comparação final
        logger.info(f"\n{'='*80}")
        logger.info(f"🔄 COMPARAÇÃO MASTER vs SLAVE")
        logger.info(f"{'='*80}")
        
        master_fields = sum(len(fields) for fields in master_data.get('required_statuses', {}).values())
        slave_fields = sum(len(fields) for fields in slave_data.get('required_statuses', {}).values())
        
        logger.info(f"📊 Campos com required_statuses:")
        logger.info(f"   Master: {master_fields}")
        logger.info(f"   Slave: {slave_fields}")
        logger.info(f"   Diferença: {master_fields - slave_fields}")
        
        if master_fields > slave_fields:
            logger.warning(f"⚠️ Master tem mais campos com required_statuses que a slave")
        elif slave_fields > master_fields:
            logger.warning(f"⚠️ Slave tem mais campos com required_statuses que a master")
        else:
            logger.info(f"✅ Ambas as contas têm o mesmo número de campos com required_statuses")
            
    except Exception as e:
        logger.error(f"❌ Erro na análise: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

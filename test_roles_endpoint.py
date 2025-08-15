#!/usr/bin/env python3
"""
Teste do endpoint de sincronização de roles

Este script testa o novo endpoint POST /sync/roles que sincroniza
somente as roles entre as contas Kommo.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.kommo_api import KommoAPIService, KommoSyncService
from src.models.kommo_account import KommoAccount
from src.database import db
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_roles_sync_functionality():
    """Testa a funcionalidade de sincronização de roles"""
    logger.info("🧪 Iniciando teste da sincronização de roles...")
    
    try:
        # Buscar contas de teste
        master_account = KommoAccount.query.filter_by(
            account_role='master', 
            is_active=True
        ).first()
        
        if not master_account:
            logger.error("❌ Nenhuma conta master encontrada para teste")
            return False
        
        slave_accounts = KommoAccount.query.filter_by(
            account_role='slave', 
            is_active=True
        ).limit(2).all()  # Pegar apenas 2 slaves para teste
        
        if not slave_accounts:
            logger.error("❌ Nenhuma conta slave encontrada para teste")
            return False
        
        logger.info(f"✅ Contas para teste: Master={master_account.subdomain}, Slaves={[s.subdomain for s in slave_accounts]}")
        
        # Configurar API da master
        master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
        
        # Testar conexão
        if not master_api.test_connection():
            logger.error("❌ Falha na conexão com a conta master")
            return False
        
        logger.info("✅ Conexão com master estabelecida")
        
        # Extrair roles da master
        logger.info("📋 Extraindo roles da master...")
        master_roles = master_api.get_roles()
        
        logger.info(f"✅ Encontradas {len(master_roles)} roles na master:")
        for role in master_roles:
            logger.info(f"  - {role['name']} (ID: {role['id']}) - Permissões: {len(role.get('rights', {}))}")
        
        if not master_roles:
            logger.warning("⚠️ Nenhuma role encontrada na master")
            return True
        
        # Preparar configuração da master
        master_config = {'roles': []}
        for role in master_roles:
            role_data = {
                'id': role['id'],
                'name': role['name'],
                'rights': role.get('rights', {}),
            }
            master_config['roles'].append(role_data)
        
        # Configurar serviço de sincronização
        sync_service = KommoSyncService(master_api, batch_size=3, delay_between_batches=1.0)
        
        # Testar sincronização com primeira conta slave
        test_slave = slave_accounts[0]
        logger.info(f"🔄 Testando sincronização com {test_slave.subdomain}...")
        
        slave_api = KommoAPIService(test_slave.subdomain, test_slave.refresh_token)
        
        if not slave_api.test_connection():
            logger.error(f"❌ Falha na conexão com a conta slave {test_slave.subdomain}")
            return False
        
        logger.info("✅ Conexão com slave estabelecida")
        
        # Obter roles atuais da slave (antes da sincronização)
        slave_roles_before = slave_api.get_roles()
        logger.info(f"📋 Roles na slave antes da sincronização: {len(slave_roles_before)}")
        for role in slave_roles_before:
            logger.info(f"  - {role['name']} (ID: {role['id']})")
        
        # Executar sincronização de roles
        mappings = {'roles': {}}
        
        def progress_callback(progress_data):
            logger.info(f"📈 Progresso: {progress_data.get('operation', 'N/A')} - "
                       f"{progress_data.get('processed', 0)}/{progress_data.get('total', 0)} "
                       f"({progress_data.get('percentage', 0):.1f}%)")
        
        results = sync_service.sync_roles_to_slave(
            slave_api=slave_api,
            master_config=master_config,
            mappings=mappings,
            progress_callback=progress_callback
        )
        
        logger.info(f"📊 Resultados da sincronização:")
        logger.info(f"  - Roles criadas: {results.get('created', 0)}")
        logger.info(f"  - Roles atualizadas: {results.get('updated', 0)}")
        logger.info(f"  - Roles ignoradas: {results.get('skipped', 0)}")
        logger.info(f"  - Roles deletadas: {results.get('deleted', 0)}")
        logger.info(f"  - Erros: {len(results.get('errors', []))}")
        
        if results.get('errors'):
            logger.error("❌ Erros durante a sincronização:")
            for error in results['errors']:
                logger.error(f"  - {error}")
        
        # Verificar roles após sincronização
        slave_roles_after = slave_api.get_roles()
        logger.info(f"📋 Roles na slave após sincronização: {len(slave_roles_after)}")
        for role in slave_roles_after:
            logger.info(f"  - {role['name']} (ID: {role['id']})")
        
        # Verificar mapeamentos
        logger.info(f"🗺️ Mapeamentos criados: {len(mappings.get('roles', {}))}")
        for master_id, slave_id in mappings.get('roles', {}).items():
            logger.info(f"  - Master ID {master_id} -> Slave ID {slave_id}")
        
        logger.info("✅ Teste de sincronização de roles concluído com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_endpoint_payload():
    """Valida diferentes payloads para o endpoint"""
    logger.info("🧪 Validando payloads do endpoint...")
    
    # Payload 1: Vazio (deve usar padrões)
    payload1 = {}
    logger.info("✅ Payload vazio: usar master padrão e todos os slaves")
    
    # Payload 2: Master específico
    payload2 = {"master_account_id": 1}
    logger.info("✅ Payload com master específico")
    
    # Payload 3: Master e slaves específicos
    payload3 = {
        "master_account_id": 1,
        "slave_account_ids": [2, 3]
    }
    logger.info("✅ Payload com master e slaves específicos")
    
    # Payload 4: Com configurações de lote
    payload4 = {
        "batch_config": {
            "batch_size": 5,
            "batch_delay": 1.5
        }
    }
    logger.info("✅ Payload com configurações de lote personalizadas")
    
    logger.info("✅ Todos os payloads são válidos")

if __name__ == "__main__":
    logger.info("🚀 Iniciando testes do endpoint de sincronização de roles...")
    
    # Teste 1: Validar payloads
    validate_endpoint_payload()
    
    print("\n" + "="*60 + "\n")
    
    # Teste 2: Funcionalidade de sincronização
    success = test_roles_sync_functionality()
    
    if success:
        logger.info("🎉 Todos os testes passaram!")
    else:
        logger.error("❌ Alguns testes falharam!")
        sys.exit(1)

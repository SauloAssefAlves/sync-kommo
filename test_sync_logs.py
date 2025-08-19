#!/usr/bin/env python3
"""
Script simples para testar sincronização de custom fields e capturar logs
"""

import sys
import os
import logging
from datetime import datetime

# Configurar logging detalhado
log_filename = f"sync_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_sync_custom_fields():
    """Testa sincronização de campos customizados"""
    logger.info("🧪 INICIANDO TESTE DE SINCRONIZAÇÃO")
    logger.info("=" * 60)
    
    try:
        # Tentar importar
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from src.main import app
        from src.database import db
        from src.models.kommo_account import KommoAccount
        from src.services.kommo_api import KommoSyncService
        
        logger.info("✅ Imports realizados com sucesso")
        
        with app.app_context():
            # Buscar contas
            master_account = KommoAccount.query.filter_by(is_master=True).first()
            slave_accounts = KommoAccount.query.filter_by(is_master=False).all()
            
            if not master_account:
                logger.error("❌ Conta master não encontrada")
                return
                
            if not slave_accounts:
                logger.error("❌ Contas slave não encontradas")
                return
                
            logger.info(f"✅ Master: {master_account.subdomain}")
            logger.info(f"✅ Slaves: {[acc.subdomain for acc in slave_accounts]}")
            
            # Criar serviço de sync
            sync_service = KommoSyncService()
            
            # Testar sincronização
            logger.info("🔄 Iniciando sincronização de custom fields...")
            
            result = sync_service.sync_custom_fields(['leads'])
            
            logger.info(f"📊 Resultado: {result}")
            
    except ImportError as e:
        logger.error(f"❌ Erro de import: {e}")
        logger.info("💡 Tentando abordagem alternativa...")
        
        # Abordagem alternativa: usar requests diretamente
        test_direct_api_call()
    
    except Exception as e:
        logger.error(f"❌ Erro geral: {e}")
        import traceback
        logger.error(traceback.format_exc())

def test_direct_api_call():
    """Testa chamada direta à API sem Flask"""
    logger.info("🔧 TESTE DIRETO NA API")
    
    # Buscar dados do banco
    import sqlite3
    
    db_path = "src/database/app.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Buscar master
    cursor.execute("SELECT subdomain, refresh_token FROM kommo_accounts WHERE is_master = 1")
    master = cursor.fetchone()
    
    if not master:
        logger.error("❌ Master não encontrado")
        return
    
    logger.info(f"✅ Master encontrado: {master['subdomain']}")
    
    # Aqui seria onde faríamos a chamada real à API
    # Mas como não temos as credenciais OAuth completas, vamos simular
    
    logger.info("📡 SIMULANDO CHAMADA À API:")
    logger.info(f"GET https://{master['subdomain']}.amocrm.ru/api/v4/leads/custom_fields?with=required_statuses")
    
    # Simular resposta
    logger.info("📋 CAMPO 'texto longo' DEVERIA RETORNAR:")
    logger.info("   name: 'texto longo'")
    logger.info("   type: 'textarea'") 
    logger.info("   required_statuses: [{'pipeline_id': 11670079, 'status_id': 89684599}]")
    
    logger.info("🔄 PROCESSAMENTO ESPERADO:")
    logger.info("   1. Buscar mapeamento pipeline 11670079 → 11795583")
    logger.info("   2. Buscar mapeamento status 89684599 → 90777427")
    logger.info("   3. Criar required_status mapeado: {'pipeline_id': 11795583, 'status_id': 90777427}")
    logger.info("   4. Enviar para slave com required_statuses mapeados")
    
    conn.close()

if __name__ == "__main__":
    print(f"📝 Log será salvo em: {log_filename}")
    test_sync_custom_fields()

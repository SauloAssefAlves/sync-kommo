#!/usr/bin/env python3
"""
Script para deletar todas as roles da slave para testar nova sincronização
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import create_app
from src.database import db
from src.models.kommo_account import KommoAccount
from src.services.kommo_api import KommoAPIService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def delete_slave_roles():
    """Deleta todas as roles da slave"""
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🗑️ Deletando roles da slave...")
            
            # Buscar conta slave
            slave_account = KommoAccount.query.filter_by(subdomain='testedev').first()
            
            if not slave_account:
                logger.error("❌ Conta slave não encontrada!")
                return
            
            # Criar API
            slave_api = KommoAPIService(
                subdomain=slave_account.subdomain,
                refresh_token=slave_account.access_token
            )
            
            # Buscar roles
            roles = slave_api.get_roles()
            logger.info(f"📋 Encontradas {len(roles)} roles para deletar")
            
            for role in roles:
                role_id = role['id']
                role_name = role['name']
                
                try:
                    response = slave_api._make_request('DELETE', f'/roles/{role_id}')
                    logger.info(f"✅ Role '{role_name}' (ID: {role_id}) deletada")
                except Exception as e:
                    logger.error(f"❌ Erro ao deletar role '{role_name}': {e}")
            
            logger.info("🎉 Deleção de roles concluída!")
                
        except Exception as e:
            logger.error(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    delete_slave_roles()

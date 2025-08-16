#!/usr/bin/env python3
"""
Script para debug - analisar a estrutura dos status_rights das roles da master
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import create_app
from src.database import db
from src.models.kommo_account import KommoAccount
from src.services.kommo_api import KommoAPIService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_master_roles():
    """Debug da estrutura das roles da master"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Buscar conta master
            master_account = KommoAccount.query.filter_by(subdomain='evoresultdev').first()
            
            if not master_account:
                logger.error("❌ Conta master não encontrada!")
                return False
            
            # Criar API
            master_api = KommoAPIService(
                subdomain=master_account.subdomain,
                refresh_token=master_account.access_token
            )
            
            # Obter roles
            logger.info("🔍 Obtendo roles da master...")
            master_roles = master_api.get_roles()
            
            logger.info(f"✅ Encontradas {len(master_roles)} roles na master")
            
            for i, role in enumerate(master_roles):
                logger.info(f"\n🔐 ROLE {i+1}: {role['name']} (ID: {role['id']})")
                
                rights = role.get('rights', {})
                status_rights = rights.get('status_rights', [])
                
                logger.info(f"📋 Status rights: {len(status_rights)} itens")
                
                if status_rights:
                    # Mostrar primeiro status_right como exemplo
                    first_sr = status_rights[0]
                    logger.info(f"🔍 EXEMPLO DE STATUS_RIGHT:")
                    logger.info(json.dumps(first_sr, indent=2, ensure_ascii=False))
                    
                    # Mostrar estrutura de todos
                    for j, sr in enumerate(status_rights[:3]):  # Só primeiros 3
                        logger.info(f"   📝 Status Right {j+1}:")
                        logger.info(f"      Pipeline ID: {sr.get('pipeline_id')}")
                        logger.info(f"      Status ID: {sr.get('status_id')}")
                        if 'rights' in sr:
                            rights_detail = sr['rights']
                            logger.info(f"      Rights: {list(rights_detail.keys())}")
                            logger.info(f"      Rights detail: {rights_detail}")
                        else:
                            logger.warning(f"      ⚠️ Sem campo 'rights' neste status_right!")
                
                # Outros tipos de rights
                logger.info(f"📋 Outros rights: {[k for k in rights.keys() if k != 'status_rights']}")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    debug_master_roles()

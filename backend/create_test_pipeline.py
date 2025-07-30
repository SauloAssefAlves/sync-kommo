#!/usr/bin/env python3
"""
Script para criar um pipeline de teste na master para testar sincronização de nomes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.models.kommo_account import KommoAccount
from src.services.kommo_api import KommoAPIService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_pipeline():
    """
    Cria um pipeline de teste na master com nomes corretos dos estágios
    """
    logger.info("🛠️ Criando pipeline de teste na master...")
    
    with app.app_context():
        # Buscar conta master
        master_account = KommoAccount.query.filter_by(is_master=True).first()
        
        if not master_account:
            logger.error("❌ Conta master não encontrada")
            return
        
        logger.info(f"🔍 Master: {master_account.subdomain}")
        
        # Criar instância da API
        master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
        
        # Dados do pipeline de teste
        pipeline_data = {
            'name': 'Pipeline Teste Simples',
            'sort': 1,
            'is_main': False,
            'is_unsorted_on': True,
            '_embedded': {
                'statuses': [
                    {
                        'name': 'Contato inicial',
                        'color': '#fffd7f',
                        'sort': 20
                    },
                    {
                        'name': 'Proposta enviada',
                        'color': '#fff000',
                        'sort': 30
                    }
                ]
            }
        }
        
        try:
            logger.info("📦 Criando pipeline 'Pipeline Teste Nomes' na master...")
            result = master_api.create_pipeline(pipeline_data)
            
            if result:
                logger.info("✅ Pipeline de teste criado com sucesso na master!")
                logger.info("🔄 Agora execute a sincronização para testar os nomes corretos")
            else:
                logger.error("❌ Erro ao criar pipeline de teste")
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar pipeline: {e}")

if __name__ == '__main__':
    create_test_pipeline()

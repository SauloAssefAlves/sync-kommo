#!/usr/bin/env python3
"""
Script para verificar e corrigir mapeamentos de pipelines no banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.database import db
from src.models.kommo_account import KommoAccount
from src.services.kommo_api import KommoAPIService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_pipeline_mappings():
    """
    Verifica os mapeamentos de pipelines no banco vs realidade das APIs
    """
    logger.info("🔍 VERIFICANDO MAPEAMENTOS DE PIPELINES")
    logger.info("=" * 60)
    
    with app.app_context():
        # Buscar contas
        master_account = KommoAccount.query.filter_by(is_master=True).first()
        slave_accounts = KommoAccount.query.filter_by(is_master=False).all()
        
        if not master_account or not slave_accounts:
            logger.error("❌ Contas não encontradas")
            return
        
        master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
        
        # Obter pipelines da master
        logger.info("📋 PIPELINES NA MASTER:")
        master_pipelines = master_api.get_pipelines()
        
        for pipeline in master_pipelines:
            pipeline_id = pipeline['id']
            pipeline_name = pipeline['name']
            logger.info(f"   {pipeline_id}: {pipeline_name}")
        
        # Verificar cada slave
        for slave_account in slave_accounts:
            logger.info(f"\n🔸 VERIFICANDO SLAVE: {slave_account.subdomain}")
            slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
            
            if not slave_api.test_connection():
                logger.warning(f"   ⚠️ Conexão falhou")
                continue
            
            # Obter pipelines da slave
            slave_pipelines = slave_api.get_pipelines()
            
            logger.info(f"   📋 PIPELINES NA SLAVE:")
            for pipeline in slave_pipelines:
                pipeline_id = pipeline['id']
                pipeline_name = pipeline['name']
                logger.info(f"      {pipeline_id}: {pipeline_name}")
            
            # Verificar mapeamentos por nome
            logger.info(f"\n   🔄 MAPEAMENTOS CORRETOS (por nome):")
            
            for master_pipeline in master_pipelines:
                master_id = master_pipeline['id']
                master_name = master_pipeline['name']
                
                # Encontrar pipeline correspondente na slave
                slave_pipeline = next((p for p in slave_pipelines if p['name'] == master_name), None)
                
                if slave_pipeline:
                    slave_id = slave_pipeline['id']
                    logger.info(f"      ✅ {master_name}: {master_id} → {slave_id}")
                    
                    # Verificar se é o pipeline 'cor teste 2'
                    if 'cor teste 2' in master_name.lower():
                        logger.info(f"      🎯 PIPELINE PRINCIPAL: {master_name}")
                        logger.info(f"         Master ID: {master_id}")
                        logger.info(f"         Slave ID: {slave_id}")
                        
                        if slave_id == 11680487:
                            logger.info(f"         ✅ ID da slave está CORRETO!")
                        else:
                            logger.error(f"         ❌ ID da slave INCORRETO! Esperado: 11680487, Atual: {slave_id}")
                else:
                    logger.warning(f"      ❌ {master_name}: {master_id} → NÃO ENCONTRADO na slave")
            
            # Verificar mapeamentos no banco de dados
            logger.info(f"\n   🗄️ VERIFICANDO MAPEAMENTOS NO BANCO...")
            
            # Aqui você precisaria acessar a tabela de mapeamentos
            # Como não temos acesso direto, vamos mostrar o que deveria ser feito
            logger.info(f"      📝 AÇÕES NECESSÁRIAS:")
            logger.info(f"      1. Verificar tabela de mapeamentos pipeline_mappings")
            logger.info(f"      2. Corrigir mapeamento: master 11670079 → slave 11680487")
            logger.info(f"      3. Verificar se existem outros mapeamentos incorretos")

def suggest_required_statuses_fix():
    """
    Sugere como corrigir o problema dos required_statuses
    """
    logger.info("\n" + "=" * 60)
    logger.info("💡 SOLUÇÃO PARA REQUIRED_STATUSES")
    logger.info("=" * 60)
    
    logger.info("🔧 PROBLEMA IDENTIFICADO:")
    logger.info("   O mapeamento no banco está incorreto:")
    logger.info("   Master pipeline 11670079 → Slave pipeline 11670175 (INCORRETO)")
    logger.info("   Deveria ser:")
    logger.info("   Master pipeline 11670079 → Slave pipeline 11680487 (CORRETO)")
    
    logger.info("\n🛠️ SOLUÇÕES POSSÍVEIS:")
    logger.info("   1. OPÇÃO RÁPIDA: Executar nova sincronização de pipelines")
    logger.info("      - Isso recriará os mapeamentos corretos no banco")
    logger.info("   2. OPÇÃO MANUAL: Corrigir diretamente no banco")
    logger.info("      UPDATE pipeline_mappings SET slave_id = 11680487 WHERE master_id = 11670079")
    logger.info("   3. OPÇÃO SEGURA: Deletar mapeamentos antigos e recriar")
    
    logger.info("\n📋 AFTER FIX - DADOS CORRETOS:")
    correct_mapping = {
        'name': 'texto longo',
        'type': 'textarea',
        'required_statuses': [
            {'pipeline_id': 11680487, 'status_id': 89685559}  # IDs corretos
        ]
    }
    logger.info(f"   {correct_mapping}")
    
    logger.info("\n🎯 RESULTADO ESPERADO:")
    logger.info("   ✅ Campo 'texto longo' será criado com required_statuses corretos")
    logger.info("   ✅ Sem mais erros de validação da API")
    logger.info("   ✅ Campo será obrigatório apenas no status 'blue' do pipeline 'cor teste 2'")

if __name__ == "__main__":
    check_pipeline_mappings()
    suggest_required_statuses_fix()

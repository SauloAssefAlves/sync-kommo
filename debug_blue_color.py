#!/usr/bin/env python3
"""
Script para debugar especificamente o problema com a cor do status 'blue' no pipeline 'cor teste 2'
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup
from src.services.kommo_api import KommoAPIService, KommoSyncService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_blue_status():
    """
    Debug específico para o status 'blue' no pipeline 'cor teste 2'
    """
    logger.info("🔍 DEBUG: Investigando problema com status 'blue' no pipeline 'cor teste 2'")
    
    with app.app_context():
        # Buscar contas master e slave
        master_account = KommoAccount.query.filter_by(is_master=True).first()
        slave_accounts = KommoAccount.query.filter_by(is_master=False).all()
        
        if not master_account or not slave_accounts:
            logger.error("❌ Contas não encontradas")
            return
        
        # Criar APIs
        master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
        
        # 1. VERIFICAR PIPELINE NA MASTER
        logger.info("🔍 STEP 1: Verificando pipeline 'cor teste 2' na MASTER...")
        master_pipelines = master_api.get_pipelines()
        
        target_pipeline = None
        for pipeline in master_pipelines:
            if 'cor teste 2' in pipeline['name'].lower():
                target_pipeline = pipeline
                break
        
        if not target_pipeline:
            logger.error("❌ Pipeline 'cor teste 2' não encontrado na master")
            return
        
        logger.info(f"✅ Pipeline encontrado na master: {target_pipeline['name']} (ID: {target_pipeline['id']})")
        
        # Obter estágios do pipeline na master
        master_stages = master_api.get_pipeline_stages(target_pipeline['id'])
        blue_stage_master = None
        
        for stage in master_stages:
            if 'blue' in stage['name'].lower():
                blue_stage_master = stage
                break
        
        if not blue_stage_master:
            logger.error("❌ Status 'blue' não encontrado no pipeline da master")
            return
        
        logger.info(f"✅ Status 'blue' encontrado na master:")
        logger.info(f"   Nome: {blue_stage_master['name']}")
        logger.info(f"   Cor: {blue_stage_master.get('color', 'N/A')}")
        logger.info(f"   ID: {blue_stage_master['id']}")
        logger.info(f"   Type: {blue_stage_master.get('type', 'N/A')}")
        
        # 2. VERIFICAR CORES VÁLIDAS DO KOMMO
        logger.info("\n🎨 STEP 2: Verificando se a cor é válida no Kommo...")
        kommo_colors = [
            '#fffeb2', '#fffd7f', '#fff000', '#ffeab2', '#ffdc7f', '#ffce5a',
            '#ffdbdb', '#ffc8c8', '#ff8f92', '#d6eaff', '#c1e0ff', '#98cbff',
            '#ebffb1', '#deff81', '#87f2c0', '#f9deff', '#f3beff', '#ccc8f9',
            '#eb93ff', '#f2f3f4', '#e6e8ea'
        ]
        
        master_color = blue_stage_master.get('color', '').lower()
        is_valid_color = master_color in [c.lower() for c in kommo_colors]
        
        logger.info(f"   Cor da master: {master_color}")
        logger.info(f"   É válida no Kommo? {is_valid_color}")
        
        if not is_valid_color:
            logger.warning(f"⚠️ Cor '{master_color}' NÃO é válida no Kommo!")
            # Encontrar cor azul mais próxima
            blue_colors = ['#d6eaff', '#c1e0ff', '#98cbff']  # Cores azuis disponíveis
            suggested_color = blue_colors[0]  # Azul claro como padrão
            logger.info(f"   Sugestão: usar {suggested_color} (azul claro)")
        
        # 3. VERIFICAR PIPELINE NAS SLAVES
        logger.info(f"\n🔍 STEP 3: Verificando pipeline nas SLAVES...")
        
        for slave_account in slave_accounts:
            logger.info(f"\n   🔸 Verificando slave: {slave_account.subdomain}")
            slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
            
            if not slave_api.test_connection():
                logger.warning(f"   ⚠️ Conexão falhou com {slave_account.subdomain}")
                continue
            
            # Buscar pipeline correspondente na slave
            slave_pipelines = slave_api.get_pipelines()
            slave_target_pipeline = None
            
            for pipeline in slave_pipelines:
                if pipeline['name'] == target_pipeline['name']:
                    slave_target_pipeline = pipeline
                    break
            
            if not slave_target_pipeline:
                logger.warning(f"   ⚠️ Pipeline '{target_pipeline['name']}' não encontrado na slave")
                continue
            
            # Buscar status 'blue' na slave
            slave_stages = slave_api.get_pipeline_stages(slave_target_pipeline['id'])
            blue_stage_slave = None
            
            for stage in slave_stages:
                if stage['name'] == blue_stage_master['name']:
                    blue_stage_slave = stage
                    break
            
            if not blue_stage_slave:
                logger.warning(f"   ⚠️ Status '{blue_stage_master['name']}' não encontrado na slave")
                continue
            
            logger.info(f"   ✅ Status encontrado na slave:")
            logger.info(f"      Nome: {blue_stage_slave['name']}")
            logger.info(f"      Cor: {blue_stage_slave.get('color', 'N/A')}")
            logger.info(f"      ID: {blue_stage_slave['id']}")
            
            # Comparar cores
            slave_color = blue_stage_slave.get('color', '').lower()
            colors_match = master_color == slave_color
            
            if colors_match:
                logger.info(f"   ✅ Cores coincidem!")
            else:
                logger.error(f"   ❌ PROBLEMA ENCONTRADO!")
                logger.error(f"      Master: {master_color}")
                logger.error(f"      Slave:  {slave_color}")
                
                # Verificar se a cor da slave corresponde a amarelo
                yellow_colors = ['#fff000', '#fffd7f', '#fffeb2', '#ffeab2', '#ffdc7f', '#ffce5a']
                is_yellow = slave_color in [c.lower() for c in yellow_colors]
                
                if is_yellow:
                    logger.error(f"      🟡 A cor da slave É AMARELA!")
                    logger.error(f"      Isso pode indicar uso de fallback por índice")
        
        # 4. TESTAR FUNÇÃO DE VALIDAÇÃO DE COR
        logger.info(f"\n🧪 STEP 4: Testando função get_valid_kommo_color...")
        
        def get_valid_kommo_color(master_color, fallback_index):
            """Função igual à do código principal"""
            if master_color and master_color.lower() in [c.lower() for c in kommo_colors]:
                return master_color
            else:
                return kommo_colors[fallback_index % len(kommo_colors)]
        
        # Simular diferentes índices
        for i in range(5):
            result_color = get_valid_kommo_color(master_color, i)
            logger.info(f"   Índice {i}: {result_color}")
            
            if result_color.lower() in ['#fff000', '#fffd7f', '#fffeb2']:
                logger.warning(f"      ⚠️ Índice {i} resulta em AMARELO!")

if __name__ == "__main__":
    debug_blue_status()

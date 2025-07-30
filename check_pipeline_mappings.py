#!/usr/bin/env python3
"""
Script para verificar mapeamentos de pipelines e stages existentes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup, PipelineMapping, StageMapping
from src.services.kommo_api import KommoAPIService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_mappings():
    """Verifica quais mapeamentos existem atualmente"""
    
    with app.app_context():
        # Verificar contas
        master = KommoAccount.query.filter_by(is_master=True).first()
        slave = KommoAccount.query.filter_by(is_master=False).first()
        
        if not master or not slave:
            logger.error("❌ Contas master ou slave não encontradas")
            return
            
        print(f"🔍 Master: {master.subdomain}")
        print(f"🔍 Slave: {slave.subdomain}")
        
        # Verificar grupo
        group = SyncGroup.query.filter_by(master_account=master).first()
        if not group:
            logger.error("❌ Grupo de sincronização não encontrado")
            return
            
        print(f"🔍 Grupo: {group.name}")
        
        # Obter pipelines das contas
        master_api = KommoAPIService(master.subdomain, master.refresh_token)
        slave_api = KommoAPIService(slave.subdomain, slave.refresh_token)
        
        master_pipelines = master_api.get_pipelines()
        slave_pipelines = slave_api.get_pipelines()
        
        print(f"\n📋 PIPELINES MASTER ({master.subdomain}):")
        for pipeline in master_pipelines:
            print(f"  - {pipeline['name']} (ID: {pipeline['id']})")
        
        print(f"\n📋 PIPELINES SLAVE ({slave.subdomain}):")
        for pipeline in slave_pipelines:
            print(f"  - {pipeline['name']} (ID: {pipeline['id']})")
        
        # Verificar mapeamentos no banco
        pipeline_mappings = PipelineMapping.query.filter_by(sync_group_id=group.id).all()
        print(f"\n🗂️ MAPEAMENTOS DE PIPELINE NO BANCO ({len(pipeline_mappings)}):")
        for mapping in pipeline_mappings:
            print(f"  - Master {mapping.master_pipeline_id} -> Slave {mapping.slave_pipeline_id}")
        
        stage_mappings = StageMapping.query.filter_by(sync_group_id=group.id).all()
        print(f"\n🗂️ MAPEAMENTOS DE STAGE NO BANCO ({len(stage_mappings)}):")
        for mapping in stage_mappings[:10]:  # Só os primeiros 10
            print(f"  - Master {mapping.master_stage_id} -> Slave {mapping.slave_stage_id}")
        if len(stage_mappings) > 10:
            print(f"  ... e mais {len(stage_mappings) - 10} mapeamentos")
        
        # Verificar quais pipelines master estão sem mapeamento
        mapped_master_ids = {m.master_pipeline_id for m in pipeline_mappings}
        unmapped_pipelines = [p for p in master_pipelines if p['id'] not in mapped_master_ids]
        
        if unmapped_pipelines:
            print(f"\n⚠️ PIPELINES MASTER SEM MAPEAMENTO ({len(unmapped_pipelines)}):")
            for pipeline in unmapped_pipelines:
                print(f"  - {pipeline['name']} (ID: {pipeline['id']})")
                
                # Verificar se existe pipeline similar na slave
                for slave_pipeline in slave_pipelines:
                    if slave_pipeline['name'] == pipeline['name']:
                        print(f"    ✅ Encontrado na slave: {slave_pipeline['name']} (ID: {slave_pipeline['id']})")
                        break
                else:
                    print(f"    ❌ NÃO encontrado na slave")
        
        print(f"\n🎯 PROBLEMA IDENTIFICADO:")
        print(f"Os required_statuses fazem referência aos IDs:")
        problem_ids = [11669623, 7829791, 11670079, 11669643, 11669867, 11669895, 11670211]
        for pid in problem_ids:
            if pid in mapped_master_ids:
                mapping = next(m for m in pipeline_mappings if m.master_pipeline_id == pid)
                print(f"  - {pid} ✅ MAPEADO -> {mapping.slave_pipeline_id}")
            else:
                # Verificar se existe na lista master
                master_pipeline = next((p for p in master_pipelines if p['id'] == pid), None)
                if master_pipeline:
                    print(f"  - {pid} ❌ NÃO MAPEADO (Pipeline: {master_pipeline['name']})")
                else:
                    print(f"  - {pid} ❌ NÃO ENCONTRADO nem na master")

if __name__ == "__main__":
    check_mappings()

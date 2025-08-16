#!/usr/bin/env python3
"""
Script para verificar e criar tabelas de mapeamento necessárias
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

def check_and_create_mappings():
    """Verifica e cria tabelas/mapeamentos necessários"""
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🔍 Verificando estrutura do banco de dados...")
            
            # 1. Verificar que tabelas existem
            from sqlalchemy import text, inspect
            
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            logger.info(f"📊 Tabelas existentes no banco: {tables}")
            
            # 2. Verificar se a tabela sync_mappings existe
            if 'sync_mappings' not in tables:
                logger.warning("⚠️ Tabela sync_mappings não existe!")
                logger.info("🔧 Criando tabela sync_mappings...")
                
                # Criar tabela sync_mappings
                create_table_sql = text("""
                CREATE TABLE IF NOT EXISTS sync_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    master_account_id INTEGER NOT NULL,
                    slave_account_id INTEGER NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    master_id INTEGER NOT NULL,
                    slave_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (master_account_id) REFERENCES kommo_account(id),
                    FOREIGN KEY (slave_account_id) REFERENCES kommo_account(id),
                    UNIQUE(master_account_id, slave_account_id, type, master_id)
                )
                """)
                
                db.session.execute(create_table_sql)
                db.session.commit()
                logger.info("✅ Tabela sync_mappings criada!")
            else:
                logger.info("✅ Tabela sync_mappings já existe")
            
            # 3. Buscar contas
            master_account = KommoAccount.query.filter_by(subdomain='evoresultdev').first()
            slave_account = KommoAccount.query.filter_by(subdomain='testedev').first()
            
            if not master_account or not slave_account:
                logger.error("❌ Contas não encontradas!")
                return
                
            logger.info(f"✅ Contas encontradas: {master_account.subdomain} -> {slave_account.subdomain}")
            
            # 4. Verificar mapeamentos existentes
            existing_mappings_query = text("""
            SELECT type, COUNT(*) as count 
            FROM sync_mappings 
            WHERE master_account_id = :master_id 
            AND slave_account_id = :slave_id 
            GROUP BY type
            """)
            
            result = db.session.execute(
                existing_mappings_query, 
                {"master_id": master_account.id, "slave_id": slave_account.id}
            ).fetchall()
            
            logger.info("📊 Mapeamentos existentes:")
            for row in result:
                logger.info(f"   {row[0]}: {row[1]} mapeamentos")
            
            # 5. Se não há mapeamentos, criar
            if not result:
                logger.warning("⚠️ Nenhum mapeamento encontrado! Criando mapeamentos...")
                
                # Criar APIs
                master_api = KommoAPIService(
                    subdomain=master_account.subdomain,
                    refresh_token=master_account.access_token
                )
                
                slave_api = KommoAPIService(
                    subdomain=slave_account.subdomain,
                    refresh_token=slave_account.access_token
                )
                
                # Buscar pipelines
                master_pipelines = master_api.get_pipelines()
                slave_pipelines = slave_api.get_pipelines()
                
                # Criar mapeamentos de pipelines por nome
                logger.info("🔧 Criando mapeamentos de pipelines...")
                pipeline_mappings = {}
                
                for master_pipeline in master_pipelines:
                    master_name = master_pipeline['name']
                    master_id = master_pipeline['id']
                    
                    # Procurar pipeline correspondente na slave
                    slave_pipeline = next((p for p in slave_pipelines if p['name'] == master_name), None)
                    
                    if slave_pipeline:
                        slave_id = slave_pipeline['id']
                        pipeline_mappings[master_id] = slave_id
                        
                        # Inserir no banco
                        insert_mapping_sql = text("""
                        INSERT OR REPLACE INTO sync_mappings 
                        (master_account_id, slave_account_id, type, master_id, slave_id)
                        VALUES (:master_account_id, :slave_account_id, 'pipeline', :master_id, :slave_id)
                        """)
                        
                        db.session.execute(insert_mapping_sql, {
                            "master_account_id": master_account.id,
                            "slave_account_id": slave_account.id,
                            "master_id": master_id,
                            "slave_id": slave_id
                        })
                        
                        logger.info(f"   ✅ Pipeline mapeado: {master_name} ({master_id} -> {slave_id})")
                    else:
                        logger.warning(f"   ⚠️ Pipeline não encontrado na slave: {master_name}")
                
                # Criar mapeamentos de etapas
                logger.info("🔧 Criando mapeamentos de etapas...")
                
                for master_id, slave_id in pipeline_mappings.items():
                    try:
                        # Buscar etapas de cada pipeline
                        master_stages = master_api.get_pipeline_stages(master_id)
                        slave_stages = slave_api.get_pipeline_stages(slave_id)
                        
                        for master_stage in master_stages:
                            master_stage_name = master_stage['name']
                            master_stage_id = master_stage['id']
                            
                            # Procurar etapa correspondente na slave
                            slave_stage = next((s for s in slave_stages if s['name'] == master_stage_name), None)
                            
                            if slave_stage:
                                slave_stage_id = slave_stage['id']
                                
                                # Inserir no banco
                                insert_stage_sql = text("""
                                INSERT OR REPLACE INTO sync_mappings 
                                (master_account_id, slave_account_id, type, master_id, slave_id)
                                VALUES (:master_account_id, :slave_account_id, 'stage', :master_id, :slave_id)
                                """)
                                
                                db.session.execute(insert_stage_sql, {
                                    "master_account_id": master_account.id,
                                    "slave_account_id": slave_account.id,
                                    "master_id": master_stage_id,
                                    "slave_id": slave_stage_id
                                })
                                
                                # Verificar se é etapa de lead
                                is_lead_stage = any(keyword in master_stage_name.lower() for keyword in ['lead', 'entrada', 'incoming', 'novo'])
                                lead_indicator = "🎪 [LEAD]" if is_lead_stage else ""
                                
                                logger.info(f"     ✅ Etapa mapeada: {master_stage_name} ({master_stage_id} -> {slave_stage_id}) {lead_indicator}")
                            else:
                                logger.warning(f"     ⚠️ Etapa não encontrada na slave: {master_stage_name}")
                                
                    except Exception as e:
                        logger.error(f"   ❌ Erro ao mapear etapas da pipeline {master_id}: {e}")
                
                # Commit das mudanças
                db.session.commit()
                logger.info("✅ Mapeamentos criados e salvos!")
                
                # 6. Verificar mapeamentos finais
                final_mappings_query = text("""
                SELECT type, COUNT(*) as count 
                FROM sync_mappings 
                WHERE master_account_id = :master_id 
                AND slave_account_id = :slave_id 
                GROUP BY type
                """)
                
                result = db.session.execute(
                    final_mappings_query, 
                    {"master_id": master_account.id, "slave_id": slave_account.id}
                ).fetchall()
                
                logger.info("📊 Mapeamentos finais criados:")
                for row in result:
                    logger.info(f"   {row[0]}: {row[1]} mapeamentos")
            
            else:
                logger.info("✅ Mapeamentos já existem no banco")
                
        except Exception as e:
            logger.error(f"❌ Erro geral: {e}")
            db.session.rollback()

if __name__ == "__main__":
    check_and_create_mappings()

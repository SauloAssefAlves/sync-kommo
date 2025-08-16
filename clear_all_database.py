#!/usr/bin/env python3
"""
Script para DELETAR TODOS OS DADOS do banco local
Limpa completamente todas as tabelas do banco de dados
"""

import sqlite3
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_all_database():
    """
    Deleta TODOS os dados do banco local
    Remove todos os registros de todas as tabelas
    """
    db_path = 'kommo_sync.db'
    
    if not os.path.exists(db_path):
        logger.info(f"❌ Banco de dados não encontrado: {db_path}")
        return
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🗑️ INICIANDO LIMPEZA COMPLETA DO BANCO DE DADOS...")
        
        # Desabilitar foreign keys temporariamente para evitar problemas de dependência
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Obter lista de todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        if not tables:
            logger.info("ℹ️ Nenhuma tabela encontrada no banco")
            conn.close()
            return
        
        total_deleted = 0
        
        # Deletar dados de cada tabela
        for (table_name,) in tables:
            try:
                # Contar registros antes da exclusão
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count_before = cursor.fetchone()[0]
                
                if count_before > 0:
                    logger.info(f"🗑️ Deletando {count_before} registros da tabela '{table_name}'...")
                    
                    # Deletar todos os registros da tabela
                    cursor.execute(f"DELETE FROM {table_name}")
                    
                    # Resetar auto-increment se a tabela tiver
                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
                    
                    total_deleted += count_before
                    logger.info(f"✅ Tabela '{table_name}' limpa com sucesso")
                else:
                    logger.info(f"ℹ️ Tabela '{table_name}' já estava vazia")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao limpar tabela '{table_name}': {e}")
        
        # Reabilitar foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Commit das mudanças
        conn.commit()
        conn.close()
        
        logger.info(f"✅ LIMPEZA COMPLETA CONCLUÍDA!")
        logger.info(f"📊 Total de registros deletados: {total_deleted}")
        logger.info(f"🎯 Banco de dados está completamente limpo e pronto para novos dados")
        
        # Verificar se realmente está vazio
        verify_empty_database()
        
    except Exception as e:
        logger.error(f"❌ Erro durante a limpeza do banco: {e}")

def verify_empty_database():
    """Verifica se o banco está realmente vazio"""
    try:
        conn = sqlite3.connect('kommo_sync.db')
        cursor = conn.cursor()
        
        # Obter lista de todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        logger.info("🔍 VERIFICAÇÃO FINAL:")
        total_records = 0
        
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_records += count
            logger.info(f"  📋 {table_name}: {count} registros")
        
        if total_records == 0:
            logger.info("✅ CONFIRMADO: Banco de dados está completamente vazio!")
        else:
            logger.warning(f"⚠️ ATENÇÃO: Ainda existem {total_records} registros no banco!")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")

if __name__ == "__main__":
    print("🚨 AVISO: Este script irá DELETAR TODOS OS DADOS do banco local!")
    print("📋 Tabelas que serão limpas:")
    print("   - kommo_accounts (contas)")
    print("   - sync_groups (grupos de sincronização)")
    print("   - pipeline_mappings (mapeamentos de pipelines)")
    print("   - stage_mappings (mapeamentos de estágios)")
    print("   - Todas as outras tabelas existentes")
    print()
    
    confirm = input("❓ Tem certeza que deseja continuar? Digite 'CONFIRMO' para prosseguir: ")
    
    if confirm.upper() == "CONFIRMO":
        clear_all_database()
    else:
        print("❌ Operação cancelada pelo usuário")

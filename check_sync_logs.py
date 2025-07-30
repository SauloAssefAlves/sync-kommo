#!/usr/bin/env python3
"""Script para verificar logs de sincronização"""

from src.main import app
from src.database import db
from src.models.kommo_account import SyncLog

def check_sync_logs():
    with app.app_context():
        print('=== LOGS DE SINCRONIZAÇÃO ===')
        logs = SyncLog.query.order_by(SyncLog.id.desc()).limit(10).all()
        
        if not logs:
            print('Nenhum log encontrado')
        else:
            for log in logs:
                print(f'ID: {log.id}')
                print(f'  Iniciado: {log.started_at}')
                if log.completed_at:
                    print(f'  Concluído: {log.completed_at}')
                print(f'  Tipo: {log.sync_type}')
                print(f'  Status: {log.status}')
                print(f'  Mensagem: {log.message}')
                if log.sync_group_id:
                    print(f'  Grupo ID: {log.sync_group_id}')
                if log.accounts_processed:
                    print(f'  Contas processadas: {log.accounts_processed}')
                if log.accounts_failed:
                    print(f'  Contas com falha: {log.accounts_failed}')
                print()

if __name__ == '__main__':
    check_sync_logs()

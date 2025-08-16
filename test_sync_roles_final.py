"""
🔐 TESTE DE SINCRONIZAÇÃO DE ROLES - VERSÃO FINAL
Usa a função sync_roles_to_slave_new do kommo_api.py
"""

import os
import sys
from datetime import datetime

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_sync_roles_final():
    """Testa sincronização de roles usando a função integrada"""
    print("🔐 TESTE DE SINCRONIZAÇÃO DE ROLES - VERSÃO FINAL")
    print("=" * 60)
    
    try:
        # Importar Flask app para contexto
        from src.main import app
        
        with app.app_context():
            print("⚙️ Contexto Flask inicializado")
            
            # Importar serviços necessários
            from src.services.kommo_api import KommoSyncService
            
            # Dados obtidos do teste anterior
            master_account_id = 1    # evoresultdev
            slave_account_id = 3     # testedev
            sync_group_id = 1        # Grupo Master 1
            
            print(f"📊 Usando dados:")
            print(f"   Master Account ID: {master_account_id} (evoresultdev)")
            print(f"   Slave Account ID: {slave_account_id} (testedev)")
            print(f"   Sync Group ID: {sync_group_id}")
            
            # Criar instância do serviço
            sync_service = KommoSyncService("dummy", "dummy")  # Tokens serão obtidos do banco
            
            # Callback para progresso
            def progress_callback(status):
                operation = status.get('operation', 'Processando')
                percentage = status.get('percentage', 0)
                print(f"   📊 {operation}... ({percentage:.1f}%)")
            
            print(f"\n🚀 Iniciando sincronização de roles...")
            
            # Executar sincronização usando a função integrada
            results = sync_service.sync_roles_to_slave_new(
                master_account_id=master_account_id,
                slave_account_id=slave_account_id,
                sync_group_id=sync_group_id,
                progress_callback=progress_callback
            )
            
            # Mostrar resultados
            print(f"\n📊 RESULTADOS DA SINCRONIZAÇÃO:")
            print(f"   Pipelines mapeados: {results.get('pipelines_mapped', 0)}")
            print(f"   Stages mapeados: {results.get('stages_mapped', 0)}")
            print(f"   Roles criadas: {results.get('roles_created', 0)}")
            print(f"   Roles atualizadas: {results.get('roles_updated', 0)}")
            print(f"   Roles ignoradas: {results.get('roles_skipped', 0)}")
            
            # Mostrar avisos
            warnings = results.get('warnings', [])
            if warnings:
                print(f"\n⚠️ AVISOS ({len(warnings)}):")
                for warning in warnings:
                    print(f"   • {warning}")
            
            # Mostrar erros
            errors = results.get('errors', [])
            if errors:
                print(f"\n❌ ERROS ({len(errors)}):")
                for error in errors:
                    print(f"   • {error}")
            else:
                print(f"\n✅ Sincronização concluída sem erros!")
            
            # Salvar relatório
            report = {
                'timestamp': datetime.now().isoformat(),
                'test_data': {
                    'master_account_id': master_account_id,
                    'slave_account_id': slave_account_id,
                    'sync_group_id': sync_group_id
                },
                'results': results
            }
            
            import json
            with open('sync_roles_final_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 Relatório salvo em: sync_roles_final_report.json")
            
            if errors:
                print(f"\n⚠️ Teste concluído com {len(errors)} erro(s)")
            else:
                print(f"\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
    
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sync_roles_final()

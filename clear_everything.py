#!/usr/bin/env python3
"""
🔥 LIMPAR TUDO DO BANCO

Este script limpa COMPLETAMENTE o banco de dados:
- Todas as contas 
- Todos os mapeamentos
- Todos os logs
- Todos os grupos

USO: python clear_everything.py
"""

import requests
import json

def clear_everything():
    """Limpa tudo do banco de dados"""
    
    print("🔥 LIMPEZA COMPLETA DO BANCO DE DADOS")
    print("=" * 50)
    
    base_url = "http://localhost:5000/api/sync"
    
    print("⚠️ ATENÇÃO: Esta operação irá APAGAR TUDO do banco!")
    print("• Todas as contas")
    print("• Todos os mapeamentos de pipeline/stage")
    print("• Todos os logs de sincronização")  
    print("• Todos os grupos de sincronização")
    print()
    
    # Confirmar operação
    confirmation = input("Digite 'CONFIRMAR' para prosseguir: ")
    if confirmation != 'CONFIRMAR':
        print("❌ Operação cancelada")
        return
    
    try:
        print("\n🔥 Executando limpeza completa...")
        response = requests.delete(f"{base_url}/database/clear-all")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ LIMPEZA COMPLETA EXECUTADA COM SUCESSO!")
            print(f"📊 Detalhes:")
            
            details = result.get('details', {})
            for key, value in details.items():
                if key.endswith('_removed'):
                    item_type = key.replace('_removed', '').replace('_', ' ').title()
                    print(f"   • {item_type}: {value}")
            
            print(f"\n🎯 Próximos passos:")
            for step in result.get('next_steps', []):
                print(f"   1. {step}")
            
            print(f"\n💡 Comandos para recomeçar:")
            print("# 1. Adicionar conta master")
            print('curl -X POST http://localhost:5000/api/sync/accounts \\')
            print('  -H "Content-Type: application/json" \\')
            print('  -d \'{"subdomain": "evoresultdev", "refresh_token": "TOKEN", "is_master": true}\'')
            print()
            print("# 2. Adicionar conta slave")  
            print('curl -X POST http://localhost:5000/api/sync/accounts \\')
            print('  -H "Content-Type: application/json" \\')
            print('  -d \'{"subdomain": "testedev", "refresh_token": "TOKEN", "is_master": false}\'')
            print()
            print("# 3. Sincronizar pipelines")
            print('curl -X POST http://localhost:5000/api/sync/trigger \\')
            print('  -H "Content-Type: application/json" \\')
            print('  -d \'{"sync_type": "pipelines"}\'')
            print()
            print("# 4. Sincronizar roles")
            print('curl -X POST http://localhost:5000/api/sync/roles')
            
        else:
            result = response.json()
            print(f"❌ Erro na limpeza: {result.get('error', 'Erro desconhecido')}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def show_current_database_status():
    """Mostra o status atual do banco"""
    
    print("\n📊 STATUS ATUAL DO BANCO:")
    print("-" * 30)
    
    base_url = "http://localhost:5000/api/sync"
    
    try:
        # Verificar contas
        response = requests.get(f"{base_url}/accounts")
        if response.status_code == 200:
            accounts = response.json()
            print(f"📋 Contas: {accounts['total']}")
            for acc in accounts['accounts']:
                role_emoji = "👑" if acc['is_master'] else "👤"
                print(f"   {role_emoji} {acc['subdomain']} ({acc['account_role']})")
        else:
            print("📋 Contas: Erro ao consultar")
            
    except Exception as e:
        print(f"📋 Contas: Erro na conexão ({e})")

if __name__ == '__main__':
    show_current_database_status()
    print()
    clear_everything()

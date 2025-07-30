#!/usr/bin/env python3
"""
Exemplo de uso do Sistema de Sincronização Kommo
Este script demonstra como usar a API para gerenciar contas e sincronizações.
"""

import requests
import json
from datetime import datetime, timedelta

# Configuração da API
API_BASE = "http://localhost:5000/api/sync"

def adicionar_conta_exemplo():
    """Exemplo de como adicionar uma conta Kommo"""
    
    # Dados da conta (substitua pelos dados reais)
    # conta_data = {
    #     "subdomain": "exemplo",
    #     "access_token": "seu_access_token_aqui",
    #     "refresh_token": "seu_refresh_token_aqui",
    #     "token_expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
    #     "is_master": True  # Primeira conta como mestre
    # }
    
        # Dados da conta (substitua pelos dados reais)
    conta_data = {
        "subdomain": "evoresultdev",
        "access_token":  "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImYwNGZhZjNkMGZjOGYyZTRhZmFkM2Y3ZGUwMzg5NDM0ZTg3MzQ1NGE5NjMzODBlNzZiZGFmODhlNWFjOTI5YTFmOWQwN2MzNThhYWQxNTJmIn0.eyJhdWQiOiJkZTcyMjY1NS1iYWM4LTQ3M2ItYTgzYy0yNzMwOTdmZGRhZGMiLCJqdGkiOiJmMDRmYWYzZDBmYzhmMmU0YWZhZDNmN2RlMDM4OTQzNGU4NzM0NTRhOTYzMzgwZTc2YmRhZjg4ZTVhYzkyOWExZjlkMDdjMzU4YWFkMTUyZiIsImlhdCI6MTc1MzEzNzkyMiwibmJmIjoxNzUzMTM3OTIyLCJleHAiOjE3NTMyMjQzMjIsInN1YiI6IjEwMjgxNTk5IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMyMDg0NDkxLCJiYXNlX2RvbWFpbiI6ImtvbW1vLmNvbSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJwdXNoX25vdGlmaWNhdGlvbnMiLCJmaWxlcyIsImNybSIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiM2NkOWJhODctZWI3OS00NjVlLWEwNWQtNWU2MjgwYWNlZTk5IiwiYXBpX2RvbWFpbiI6ImFwaS1jLmtvbW1vLmNvbSJ9.GnJqd6t9J97DFe4gFjXeu455diizBJ14qUqjLwbUOFV86f5lLEFdXNKw6NvL8pBD5S5IopA7jw3Flvyh3ThYYgd4xHMPU7zE61LlVtj1abirAGt3TKHTka02bTidDnLcUiC-7wN1Ccil88Otyq4eW2gI4WujxOzmYIg0Fu7FZh2IMyX_BB6nY8_0SkYPYq-qlI8OUfw9kKA2GgMYG_qQ6J-boQT6v4eRUeWacwROLeQcAQHxRd4dXYnMqZSrRU-V78gIjmQ5q69tDxcILSBZvB8bbHTYITqC5W5Il75eHz7ZbPKZWr9Qc76E0p-txMWIVjOnwPGTLGZZT4HxM3XVGQ",
        "refresh_token": "def50200605f3cfdc519cabfda582c5f8e384b0fe3ffb09941378b5303c951ec62711a7022c7ebc452b0e63df3d749fc2fa6f767a425fa4954faefa33b572bb3bb2e1e40af9741d00d363e5102a4561dff5f86a57c4a800d663f6fc9e3f9a535fd2b6a306fd78d7bcb30d66183a826f1c2d3dbf3460205c947ddc6d1ae5428c8d083302f1665c9693d7018bd21f64629fcacfd720701b6de9f722502925dca777ffa2ef316bf85063792f416b89e4d55a7694c000e3a0fcb0e1518db81e4f0ba276a61e78c8c5263d6865d2b7153fec012554de09563ec36819c679939bdf0ac77c5f00f8a4daf896801ce313c0f2c765905a06931ddb4161211414c68fa583d09c6b07a4e375cc2ed0f6708a3f6629f0b0a2f914f2a859bffa42f4e882e92bad80bfef0059314a251913f57a254dabfa0aabdcacd9ee0f560a59cbbe9971b928bc2c48eb547ffc6944c7966338f7db1a507a4ef68a85bad356f549862b6af988e11c62a143f8aee9ac1fb9a24356d754edf8dd32fabaf9bfedf1fb73d9f582045e53ce557ad84a3cf6d42b9688698ee8b5e5281ea4c5176dda6d5eb970e59a71191cee4f3dca6b6e336c69531aacb3b55b09a4ca66595ee32581e613e7e0b374709a13364f7ad6e8a44fc716ece58aaaf27a18080f4e4ecd0fb7647abdb8ecc273b0484b55b3188a4d6b9fd3a2e",
        "token_expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
        "is_master": True  # Primeira conta como mestre
    }

    try:
        response = requests.post(f"{API_BASE}/accounts", json=conta_data)
        result = response.json()
        
        if result['success']:
            print(f"✅ Conta adicionada com sucesso! ID: {result['account_id']}")
        else:
            print(f"❌ Erro ao adicionar conta: {result['error']}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def listar_contas():
    """Lista todas as contas cadastradas"""
    
    try:
        response = requests.get(f"{API_BASE}/accounts")
        result = response.json()
        
        if result['success']:
            print(f"\n📋 Total de contas: {result['total']}")
            for conta in result['accounts']:
                tipo = "MESTRE" if conta['is_master'] else "ESCRAVA"
                print(f"  - {conta['subdomain']} ({tipo}) - ID: {conta['id']}")
        else:
            print(f"❌ Erro ao listar contas: {result['error']}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def acionar_sincronizacao(tipo='full'):
    """Aciona uma sincronização"""
    
    tipos_validos = ['full', 'pipelines', 'custom_fields']
    if tipo not in tipos_validos:
        print(f"❌ Tipo inválido. Use: {', '.join(tipos_validos)}")
        return
    
    try:
        response = requests.post(f"{API_BASE}/trigger", json={"sync_type": tipo})
        result = response.json()
        
        if result['success']:
            print(f"✅ Sincronização {tipo} iniciada com sucesso!")
            print(f"📊 Contas processadas: {result['results']['accounts_processed']}")
            print(f"❌ Contas com falha: {result['results']['accounts_failed']}")
            
            # Mostrar detalhes por conta
            for detalhe in result['results']['details']:
                if 'error' in detalhe:
                    print(f"  ❌ {detalhe['subdomain']}: {detalhe['error']}")
                else:
                    print(f"  ✅ {detalhe['subdomain']}: Sincronizada")
        else:
            print(f"❌ Erro na sincronização: {result['error']}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def verificar_status():
    """Verifica o status do sistema"""
    
    try:
        response = requests.get(f"{API_BASE}/status")
        result = response.json()
        
        if result['success']:
            status = result['status']
            print(f"\n📊 Status do Sistema:")
            print(f"  Total de contas: {status['accounts']['total']}")
            print(f"  Contas mestre: {status['accounts']['master']}")
            print(f"  Contas escravas: {status['accounts']['slaves']}")
            
            if status['last_sync']:
                last_sync = status['last_sync']
                print(f"  Última sincronização: {last_sync['status']} ({last_sync['sync_type']})")
                print(f"  Data: {last_sync['started_at']}")
            else:
                print(f"  Última sincronização: Nenhuma")
        else:
            print(f"❌ Erro ao verificar status: {result['error']}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def simular_webhook_salesbot():
    """Simula um webhook do Salesbot"""
    
    # Dados simulados de um webhook do Salesbot
    webhook_data = {
        "leads": {
            "add": [
                {
                    "id": 12345,
                    "name": "Lead de Teste",
                    "status_id": 67890,
                    "pipeline_id": 123
                }
            ]
        }
    }
    
    try:
        response = requests.post(f"{API_BASE}/webhook", json=webhook_data)
        result = response.json()
        
        if result['success']:
            print("✅ Webhook processado com sucesso!")
            print("🔄 Sincronização acionada automaticamente")
        else:
            print(f"❌ Erro no webhook: {result['error']}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def main():
    """Função principal com menu interativo"""
    
    print("🔄 Sistema de Sincronização Kommo - Exemplo de Uso")
    print("=" * 50)
    
    while True:
        print("\nOpções disponíveis:")
        print("1. Verificar status do sistema")
        print("2. Listar contas")
        print("3. Adicionar conta (exemplo)")
        print("4. Sincronização completa")
        print("5. Sincronizar apenas funis")
        print("6. Sincronizar apenas campos personalizados")
        print("7. Simular webhook do Salesbot")
        print("0. Sair")
        
        escolha = input("\nEscolha uma opção: ").strip()
        
        if escolha == "0":
            print("👋 Saindo...")
            break
        elif escolha == "1":
            verificar_status()
        elif escolha == "2":
            listar_contas()
        elif escolha == "3":
            print("\n⚠️  ATENÇÃO: Este é apenas um exemplo!")
            print("Substitua os dados pelos tokens reais da sua conta Kommo.")
            adicionar_conta_exemplo()
        elif escolha == "4":
            acionar_sincronizacao('full')
        elif escolha == "5":
            acionar_sincronizacao('pipelines')
        elif escolha == "6":
            acionar_sincronizacao('custom_fields')
        elif escolha == "7":
            simular_webhook_salesbot()
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    main()


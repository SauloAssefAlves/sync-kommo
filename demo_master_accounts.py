#!/usr/bin/env python3
"""
Script de demonstração: Criação de Conta Mestre e Grupo
"""

import requests
import json

# Configuração do servidor
BASE_URL = "http://localhost:5000"

def test_create_master_account():
    """Testa a criação de uma nova conta mestre"""
    
    print("🧪 Testando criação de nova conta mestre...")
    
    # Dados da conta mestre de exemplo
    account_data = {
        "subdomain": "exemplo-master-2",
        "refresh_token": "exemplo_refresh_token_123456789",
        "is_master": True
    }
    
    print(f"\n1. Criando conta mestre: {account_data['subdomain']}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/sync/accounts", json=account_data)
        
        if response.status_code == 200:
            data = response.json()
            account_id = data['account_id']
            print(f"✅ Conta mestre criada com sucesso!")
            print(f"   - ID: {account_id}")
            print(f"   - Subdomínio: {account_data['subdomain']}")
            
            # Testar a conta criada
            print(f"\n2. Testando conexão da conta criada...")
            test_response = requests.get(f"{BASE_URL}/api/sync/accounts/{account_id}/test")
            
            if test_response.status_code == 200:
                test_data = test_response.json()
                if test_data['success']:
                    print("✅ Teste de conexão bem-sucedido!")
                else:
                    print("⚠️  Teste de conexão falhou (esperado para dados de exemplo)")
            
            return account_id
            
        else:
            error_data = response.json()
            print(f"❌ Erro ao criar conta: {error_data.get('error', 'Erro desconhecido')}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def test_create_group_with_master():
    """Testa a criação de um grupo usando a conta mestre"""
    
    print("\n🧪 Testando criação de grupo com conta mestre...")
    
    # Primeiro criar uma conta mestre
    account_id = test_create_master_account()
    
    if not account_id:
        print("❌ Falha ao criar conta mestre, abortando teste de grupo")
        return
    
    # Dados do grupo
    group_data = {
        "name": "Grupo de Teste Automático",
        "description": "Grupo criado automaticamente via script de demonstração",
        "master_account_id": account_id
    }
    
    print(f"\n3. Criando grupo: {group_data['name']}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/groups", json=group_data)
        
        if response.status_code == 201:
            data = response.json()
            group_id = data['group']['id']
            print(f"✅ Grupo criado com sucesso!")
            print(f"   - ID: {group_id}")
            print(f"   - Nome: {group_data['name']}")
            print(f"   - Conta Mestre: {data['group']['master_account']['subdomain']}")
            
            return group_id
            
        else:
            error_data = response.json()
            print(f"❌ Erro ao criar grupo: {error_data.get('error', 'Erro desconhecido')}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def demo_web_interface():
    """Demonstra como usar a interface web"""
    
    print("\n🌐 Demonstração da Interface Web")
    print("=" * 40)
    
    print(f"\n1. Acesse: {BASE_URL}")
    print("\n2. Na seção 'Gerenciamento de Grupos':")
    print("   📋 Clique em 'Novo Grupo'")
    print("   🔧 Preencha o nome do grupo")
    print("   👑 Clique em 'Nova Conta' para adicionar uma conta mestre")
    print("   💾 Salve o grupo")
    
    print("\n3. Para adicionar conta mestre:")
    print("   🔤 Digite o subdomínio (ex: minhaempresa)")
    print("   🔑 Cole o refresh token do Kommo")
    print("   ✅ Marque 'Testar conexão'")
    print("   💾 Clique em 'Adicionar Conta'")
    
    print("\n4. Depois de criar o grupo:")
    print("   👥 Adicione contas escravas")
    print("   🔄 Execute a sincronização")
    print("   📊 Acompanhe o progresso em tempo real")

def main():
    """Função principal de demonstração"""
    
    print("🚀 Demonstração: Sistema Multi-Master com Grupos")
    print("=" * 60)
    
    print("\n📋 Este script demonstra:")
    print("1. ✨ Criação de conta mestre via API")
    print("2. 🧪 Teste de conexão automático")
    print("3. 📦 Criação de grupo com a nova conta")
    print("4. 🌐 Como usar a interface web")
    
    # Executar testes via API
    group_id = test_create_group_with_master()
    
    if group_id:
        print(f"\n✅ Demonstração via API bem-sucedida!")
        print(f"   📦 Grupo criado: ID {group_id}")
    
    # Demonstrar interface web
    demo_web_interface()
    
    print(f"\n🎯 Funcionalidades Implementadas:")
    print("   ✅ Múltiplas contas mestres")
    print("   ✅ Grupos isolados de sincronização")
    print("   ✅ Interface web intuitiva")
    print("   ✅ Criação de conta via modal")
    print("   ✅ Teste de conexão automático")
    print("   ✅ Validação de dados em tempo real")
    
    print(f"\n🌟 Próximos Passos:")
    print(f"   1. Acesse {BASE_URL}")
    print(f"   2. Explore a seção 'Gerenciamento de Grupos'")
    print(f"   3. Crie suas próprias contas e grupos")
    print(f"   4. Execute sincronizações específicas por grupo")

if __name__ == "__main__":
    main()

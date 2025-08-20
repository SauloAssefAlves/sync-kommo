#!/usr/bin/env python3
"""
Diagnóstico de erros 400 na criação de roles

Este script tenta identificar por que a criação de roles está retornando 400 Bad Request
"""

import sys
import os
sys.path.append('/home/user/sync-kommo')

from src.services.kommo_api import KommoAPIService
import json

def diagnose_role_creation_error():
    print("🔍 DIAGNÓSTICO DE ERROS 400 NA CRIAÇÃO DE ROLES")
    print("=" * 60)
    
    print("\n📋 POSSÍVEIS CAUSAS DO ERRO 400:")
    print("-" * 35)
    print("1. Dados de role inválidos (nome muito longo, caracteres especiais)")
    print("2. Direitos/permissões inválidos (IDs de pipeline/stage inexistentes)")
    print("3. Estrutura de dados incorreta")
    print("4. Role com nome duplicado")
    print("5. Permissões insuficientes na conta slave")
    print("6. Limites da API do Kommo (max roles por conta)")
    
    print("\n🔍 DADOS TÍPICOS DE UMA ROLE PROBLEMÁTICA:")
    print("-" * 45)
    
    # Simular dados de role que podem estar causando problema
    problematic_role = {
        'name': 'Consultor - Vendas',  # Nome com caracteres especiais
        'rights': {
            'leads': {'view': 'D', 'edit': 'D', 'add': 'D', 'delete': 'D', 'export': 'D'},
            'contacts': {'view': 'D', 'edit': 'D', 'add': 'D', 'delete': 'D', 'export': 'D'},
            'companies': {'view': 'D', 'edit': 'D', 'add': 'D', 'delete': 'D', 'export': 'D'},
            'tasks': {'view': 'D', 'edit': 'D', 'add': 'D', 'delete': 'D'},
            'mail_access': True,
            'catalog_access': True,
            'files_access': True,
            'status_rights': [
                {'entity_type': 'leads', 'pipeline_id': 99999999, 'status_id': 88888888}  # IDs podem não existir
            ]
        }
    }
    
    print("Role problemática exemplo:")
    print(json.dumps(problematic_role, indent=2, ensure_ascii=False))
    
    print("\n⚠️ PROBLEMAS IDENTIFICADOS NO EXEMPLO:")
    print("-" * 40)
    print("1. 🚫 Nome com hífen: 'Consultor - Vendas'")
    print("   - Solução: Usar 'Consultor Vendas' ou 'ConsultorVendas'")
    print("")
    print("2. 🚫 IDs de pipeline/status podem não existir na slave:")
    print("   - pipeline_id: 99999999 (provavelmente inexistente)")
    print("   - status_id: 88888888 (provavelmente inexistente)")
    print("")
    print("3. 🚫 Permissões podem estar no formato incorreto:")
    print("   - 'D' pode não ser um valor válido")
    print("   - Valores corretos: 'N' (nenhum), 'W' (próprio), 'D' (departamento), 'A' (todos)")
    
    print("\n✅ SOLUÇÕES RECOMENDADAS:")
    print("-" * 25)
    print("1. VALIDAR NOMES DAS ROLES:")
    print("   - Remover caracteres especiais (-, /, etc)")
    print("   - Usar apenas letras, números e espaços")
    print("   - Limitar a 50 caracteres")
    print("")
    print("2. VALIDAR IDS DE PIPELINE/STATUS:")
    print("   - Verificar se existem na conta slave")
    print("   - Usar apenas IDs mapeados corretamente")
    print("   - Remover status_rights se IDs forem inválidos")
    print("")
    print("3. SIMPLIFICAR DADOS INICIALMENTE:")
    print("   - Criar roles apenas com nome")
    print("   - Adicionar direitos básicos depois")
    print("   - Testar incrementalmente")
    
    print("\n🛠️ CORREÇÃO RECOMENDADA NO CÓDIGO:")
    print("-" * 35)
    print("```python")
    print("def _prepare_role_data_safe(self, master_role: Dict) -> Dict:")
    print("    # Limpar nome da role")
    print("    clean_name = master_role['name']")
    print("    clean_name = clean_name.replace(' - ', ' ')  # Remover hífens")
    print("    clean_name = clean_name.replace('-', '')     # Remover hífens")
    print("    clean_name = clean_name[:50]                 # Limitar tamanho")
    print("    ")
    print("    # Dados mínimos para teste")
    print("    role_data = {")
    print("        'name': clean_name,")
    print("        'rights': {")
    print("            'leads': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'N'},")
    print("            'contacts': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'N'},")
    print("            'companies': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'N'}")
    print("            # Remover status_rights temporariamente")
    print("        }")
    print("    }")
    print("    return role_data")
    print("```")
    
    print("\n🎯 PRÓXIMA AÇÃO:")
    print("-" * 15)
    print("1. Implementar validação de nomes das roles")
    print("2. Simplificar dados das roles temporariamente")
    print("3. Testar criação com dados mínimos")
    print("4. Adicionar complexidade gradualmente")

if __name__ == "__main__":
    diagnose_role_creation_error()

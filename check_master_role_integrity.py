#!/usr/bin/env python3
"""
🔍 VERIFICADOR: Origem dos Status Rights na Role Master

Este script verifica se a role na conta master contém
IDs corretos (da master) ou se tem IDs da slave por engano.

PROBLEMA DETECTADO:
- IDs 89684595, 89686887, 89765891 parecem ser da SLAVE
- Mas estão sendo processados como se fossem da MASTER
- Isso indica que a role master foi contaminada com dados da slave

VERIFICAÇÃO:
1. Conectar na conta master
2. Buscar roles e seus status_rights  
3. Analisar padrões dos IDs
4. Identificar possíveis contaminações
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.services.kommo_api import KommoAPIService
from src.models.kommo_account import KommoAccount
from src.database import db
from src.main import app as flask_app
import json

def check_master_role_integrity():
    """Verifica a integridade dos dados da role master"""
    
    print("🔍 VERIFICADOR: Integridade da Role Master")
    print("=" * 60)
    
    # Usar contexto da aplicação Flask existente
    with flask_app.app_context():
        try:
            # Buscar conta master
            master_account = KommoAccount.query.filter_by(
                account_role='master'
            ).first()
            
            if not master_account:
                print("❌ Nenhuma conta master encontrada!")
                return
                
            print(f"🎯 Conta Master: {master_account.subdomain}")
            
            # Conectar à API
            master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
            
            if not master_api.test_connection():
                print("❌ Falha na conexão com a conta master!")
                return
                
            print("✅ Conexão com conta master estabelecida")
            
            # Buscar roles
            print("\n📋 Analisando roles da conta master...")
            roles = master_api.get_roles()
            
            if not roles:
                print("❌ Nenhuma role encontrada na conta master!")
                return
                
            print(f"📊 Encontradas {len(roles)} roles na conta master")
            
            # Analisar cada role
            for role in roles:
                role_name = role.get('name', 'Unnamed')
                role_id = role.get('id')
                rights = role.get('rights', {})
                status_rights = rights.get('status_rights', [])
                
                print(f"\n🔐 Role: '{role_name}' (ID: {role_id})")
                print(f"   📈 Status Rights: {len(status_rights)}")
                
                if not status_rights:
                    print("   ℹ️ Esta role não tem status_rights específicos")
                    continue
                    
                # Analisar padrões dos IDs
                master_like_ids = []  # IDs que parecem ser da master
                slave_like_ids = []   # IDs que parecem ser da slave
                unknown_ids = []      # IDs de padrão desconhecido
                
                for i, sr in enumerate(status_rights, 1):
                    pipeline_id = sr.get('pipeline_id')
                    status_id = sr.get('status_id') 
                    entity_type = sr.get('entity_type', 'leads')
                    
                    print(f"      {i}. {entity_type}: pipeline={pipeline_id}, status={status_id}")
                    
                    # Classificar IDs por padrão
                    if status_id:
                        status_str = str(status_id)
                        if status_str.startswith('632'):
                            master_like_ids.append(status_id)
                            print(f"         ✅ ID típico de MASTER: {status_id}")
                        elif status_str.startswith(('896', '897', '905')):
                            slave_like_ids.append(status_id)
                            print(f"         🚨 ID típico de SLAVE: {status_id} (SUSPEITO!)")
                        elif status_str.startswith('89'):
                            unknown_ids.append(status_id)
                            print(f"         ⚠️ ID ambíguo: {status_id} (pode ser master ou slave)")
                        else:
                            unknown_ids.append(status_id)
                            print(f"         ❓ ID padrão desconhecido: {status_id}")
                
                # Resumo da análise
                print(f"\n   📊 RESUMO para role '{role_name}':")
                print(f"      ✅ IDs típicos de MASTER: {len(master_like_ids)} - {master_like_ids}")
                print(f"      🚨 IDs típicos de SLAVE: {len(slave_like_ids)} - {slave_like_ids}")
                print(f"      ⚠️ IDs ambíguos: {len(unknown_ids)} - {unknown_ids}")
                
                # Diagnóstico
                if slave_like_ids:
                    print(f"      🚨 PROBLEMA DETECTADO: Role master contém {len(slave_like_ids)} IDs típicos de slave!")
                    print(f"      💡 Possíveis causas:")
                    print(f"         • Role foi copiada de uma conta slave")
                    print(f"         • Houve sincronização reversa (slave -> master)")
                    print(f"         • Esta conta não é a master original")
                    print(f"      🔧 Recomendação: Verificar origem desta role")
                
                if len(master_like_ids) == 0 and len(status_rights) > 0:
                    print(f"      ⚠️ ALERTA: Role não tem nenhum ID típico de master!")
                    print(f"      💭 Esta role pode ter sido importada de outra conta")
            
            print(f"\n" + "=" * 60)
            print("🎯 CONCLUSÕES:")
            print("• Se houver IDs 89xxx na role master, isso explica os erros")
            print("• Estes IDs não podem ser mapeados porque já são da slave")
            print("• A role master precisa ter apenas IDs da própria conta master")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Erro durante verificação: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_master_role_integrity()

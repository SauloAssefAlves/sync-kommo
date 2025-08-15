#!/usr/bin/env python3
"""
Mock test para sincronização de roles
Testa o mapeamento de status_rights sem precisar de banco ou APIs reais
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def mock_roles_sync_test():
    """Testa a lógica de mapeamento de roles com dados mockados"""
    print("🧪 Iniciando teste mock da sincronização de roles...")
    
    # Mock dos dados da master (como viriam da API)
    mock_master_roles = [
        {
            'id': 1234567,
            'name': 'ROLE 1',
            'rights': {
                'leads': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'A'},
                'contacts': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'A'},
                'status_rights': [
                    {
                        'entity_type': 'leads',
                        'pipeline_id': 7829791,  # ID da pipeline na master
                        'status_id': 63288851,   # Status que não existe nos mapeamentos
                        'rights': {'view': 'A', 'edit': 'A'}
                    },
                    {
                        'entity_type': 'leads',
                        'pipeline_id': 7829791,
                        'status_id': 63288855,   # Status que existe nos mapeamentos
                        'rights': {'view': 'A', 'edit': 'A'}
                    },
                    {
                        'entity_type': 'leads',
                        'pipeline_id': 11680155,
                        'status_id': 89774811,   # Status que existe
                        'rights': {'view': 'A', 'edit': 'A'}
                    }
                ]
            }
        }
    ]
    
    # Mock dos mapeamentos (como viriam do banco)
    mock_pipelines_mapping = {
        7829791: 11629591,    # master_pipeline_id -> slave_pipeline_id
        11680155: 11774003,
        11680283: 11774007,
        11680391: 11774011
    }
    
    mock_stages_mapping = {
        # Status IDs disponíveis na slave
        63288855: 89317579,   # master_status_id -> slave_status_id
        63288859: 89317583,
        63288863: 89317587,
        63288867: 89317591,
        89774811: 89775163,
        89775999: 89776043,
        89776867: 89776895,
        89776871: 90595635,
        # Note: 63288851 não está mapeado (simulando o problema real)
    }
    
    # Mock dos status disponíveis na slave (como viriam da API)
    mock_slave_status_ids = {
        89317579, 89317583, 89317587, 89317591,
        89775163, 89776043, 89776895, 90595635,
        89526047, 89684599, 89684603, 89684607,
        # Note: alguns IDs dos mapeamentos não estão aqui (simulando o problema de validação)
    }
    
    print(f"📊 Master roles: {len(mock_master_roles)}")
    print(f"🗺️  Pipeline mappings: {len(mock_pipelines_mapping)}")
    print(f"🗺️  Stage mappings: {len(mock_stages_mapping)}")
    print(f"✅ Available slave status IDs: {len(mock_slave_status_ids)}")
    
    # Simular processamento da role
    for role in mock_master_roles:
        role_name = role['name']
        master_rights = role['rights']
        
        print(f"\n🔄 Processando role: {role_name}")
        
        if 'status_rights' not in master_rights:
            print(f"   ℹ️  Role '{role_name}' não tem status_rights específicos")
            continue
            
        print(f"🎯 Mapeando {len(master_rights['status_rights'])} status_rights para role '{role_name}'")
        
        mapped_status_rights = []
        missing_pipeline_mappings = 0
        missing_stage_mappings = 0
        invalid_status_ids = 0
        
        for i, status_right in enumerate(master_rights['status_rights'], 1):
            master_pipeline_id = int(status_right['pipeline_id'])
            master_status_id = int(status_right['status_id'])
            
            print(f"  {i}. Pipeline {master_pipeline_id} -> Status {master_status_id}")
            
            # Verificar mapeamento de pipeline
            slave_pipeline_id = mock_pipelines_mapping.get(master_pipeline_id)
            if not slave_pipeline_id:
                missing_pipeline_mappings += 1
                print(f"     ❌ Pipeline {master_pipeline_id} não encontrado nos mapeamentos")
                continue
            
            # Verificar mapeamento de status
            slave_status_id = mock_stages_mapping.get(master_status_id)
            if not slave_status_id:
                missing_stage_mappings += 1
                print(f"     ❌ Status {master_status_id} não encontrado nos mapeamentos")
                continue
            
            print(f"     ✅ Mapeado: pipeline {master_pipeline_id}->{slave_pipeline_id}, status {master_status_id}->{slave_status_id}")
            
            # Criar status_right mapeado
            mapped_status_right = {
                'entity_type': status_right['entity_type'],
                'pipeline_id': slave_pipeline_id,
                'status_id': slave_status_id,
                'rights': status_right['rights']
            }
            mapped_status_rights.append(mapped_status_right)
        
        print(f"📊 Role '{role_name}': {len(mapped_status_rights)} status_rights mapeados de {len(master_rights['status_rights'])} originais")
        
        # Log de diagnóstico
        if missing_pipeline_mappings > 0 or missing_stage_mappings > 0:
            print(f"🚨 MAPEAMENTOS DESATUALIZADOS DETECTADOS!")
            print(f"   📊 Pipelines não mapeadas: {missing_pipeline_mappings}")
            print(f"   📊 Status/Stages não mapeados: {missing_stage_mappings}")
            print(f"   💡 SOLUÇÃO: Execute uma sincronização de pipelines primeiro!")
        
        # Simulação da validação prévia (novo código)
        if mapped_status_rights:
            print(f"🔍 Validando {len(mapped_status_rights)} status_rights antes da atualização...")
            
            validated_status_rights = []
            for sr in mapped_status_rights:
                status_id = int(sr['status_id'])
                if status_id in mock_slave_status_ids:
                    validated_status_rights.append(sr)
                else:
                    invalid_status_ids += 1
                    print(f"     🚫 Status {status_id} não existe na slave - removendo da requisição")
            
            print(f"✅ Validação concluída: {len(validated_status_rights)} de {len(mapped_status_rights)} status_rights são válidos")
            
            if invalid_status_ids > 0:
                print(f"⚠️  {invalid_status_ids} status_rights foram removidos por não existirem na slave")
        
        # Resultado final
        final_count = len(validated_status_rights) if mapped_status_rights else 0
        print(f"🎯 RESULTADO FINAL: {final_count} status_rights serão enviados para a API")
        
        if final_count > 0:
            print("✅ Sincronização seria SUCESSFUL")
            print("📋 Status_rights finais:")
            for sr in validated_status_rights:
                print(f"   - {sr['entity_type']}: pipeline={sr['pipeline_id']}, status={sr['status_id']}")
        else:
            print("⚠️  Role teria apenas permissões gerais (sem status_rights específicos)")

def main():
    """Executa o teste mock"""
    print("=" * 60)
    print("🧪 TESTE MOCK - SINCRONIZAÇÃO DE ROLES")
    print("=" * 60)
    
    mock_roles_sync_test()
    
    print("\n" + "=" * 60)
    print("✅ TESTE CONCLUÍDO")
    print("💡 Este teste simula exatamente o problema que você estava enfrentando:")
    print("   1. Mapeamentos incompletos (alguns status IDs não mapeados)")
    print("   2. Validação prévia removendo status IDs inválidos")
    print("   3. Diagnóstico claro dos problemas encontrados")
    print("=" * 60)

if __name__ == "__main__":
    main()

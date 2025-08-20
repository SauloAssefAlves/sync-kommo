#!/usr/bin/env python3
"""
Teste da correção para filtrar catalog_rights e outros direitos problemáticos
"""

def test_rights_filtering():
    print("🔧 TESTE DE FILTRAGEM DE DIREITOS PROBLEMÁTICOS")
    print("=" * 55)
    
    # Simular direitos da master que incluem catalog_rights problemático
    master_rights = {
        'leads': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'N'},
        'contacts': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'N'},
        'companies': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'N'},
        'tasks': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'N'},
        'mail_access': True,
        'catalog_access': True,
        'files_access': True,
        'catalog_rights': [  # PROBLEMÁTICO - IDs específicos da master
            {
                'catalog_id': 12345,  # ID que não existe na slave
                'can_view': True,
                'can_edit': False
            }
        ],
        'source_rights': [  # PROBLEMÁTICO - IDs específicos da master
            {
                'source_id': 67890,  # ID que não existe na slave
                'can_view': True
            }
        ],
        'status_rights': [  # Já tratado separadamente
            {
                'pipeline_id': 11111,
                'status_id': 22222,
                'entity_type': 'leads'
            }
        ]
    }
    
    print("📋 DIREITOS ORIGINAIS DA MASTER:")
    print("-" * 32)
    for right_type, right_value in master_rights.items():
        if isinstance(right_value, list):
            print(f"   {right_type}: {len(right_value)} itens")
        else:
            print(f"   {right_type}: {right_value}")
    
    print(f"\nTotal de tipos de direitos: {len(master_rights)}")
    
    # Simular a nova lógica de filtragem
    def filter_problematic_rights(rights):
        problematic_rights = ['catalog_rights', 'source_rights', 'pipeline_rights']
        filtered_rights = {}
        
        for right_type, right_value in rights.items():
            if right_type == 'status_rights':
                # Processamento especial (simulado como vazio)
                filtered_rights[right_type] = []
                print(f"   🔄 '{right_type}' processado separadamente")
            elif right_type in problematic_rights:
                print(f"   🚫 '{right_type}' filtrado - contém IDs específicos")
            else:
                filtered_rights[right_type] = right_value
                print(f"   ✅ '{right_type}' mantido")
        
        return filtered_rights
    
    print("\n🔍 PROCESSAMENTO DOS DIREITOS:")
    print("-" * 30)
    
    filtered_rights = filter_problematic_rights(master_rights)
    
    print("\n📊 RESULTADO APÓS FILTRAGEM:")
    print("-" * 30)
    for right_type, right_value in filtered_rights.items():
        if isinstance(right_value, list):
            print(f"   {right_type}: {len(right_value)} itens")
        else:
            print(f"   {right_type}: {right_value}")
    
    print(f"\nTotal de tipos mantidos: {len(filtered_rights)}")
    
    # Comparação
    removed_count = len(master_rights) - len(filtered_rights)
    print(f"Tipos removidos: {removed_count}")
    
    print("\n✅ DIREITOS PROBLEMÁTICOS REMOVIDOS:")
    print("-" * 35)
    problematic_rights = ['catalog_rights', 'source_rights', 'pipeline_rights']
    for right_type in problematic_rights:
        if right_type in master_rights:
            print(f"   ❌ {right_type} (removido)")
        else:
            print(f"   ➖ {right_type} (não presente)")
    
    print("\n🎯 BENEFÍCIOS ESPERADOS:")
    print("-" * 25)
    print("✅ Elimina erro 400 'NotSupportedChoice' para catalog_id")
    print("✅ Evita IDs de source/catalog inexistentes na slave")
    print("✅ Mantém direitos básicos funcionais")
    print("✅ Roles podem ser criadas com sucesso")
    print("✅ Direitos específicos podem ser configurados manualmente depois")

if __name__ == "__main__":
    test_rights_filtering()

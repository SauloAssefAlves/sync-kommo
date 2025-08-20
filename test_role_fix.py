#!/usr/bin/env python3
"""
Teste das correções para erro 400 na criação de roles
"""

def test_role_name_sanitization():
    print("🧪 TESTE DE SANITIZAÇÃO DE NOMES DE ROLES")
    print("=" * 50)
    
    # Nomes problemáticos que estavam causando erro 400
    test_names = [
        "Diretor",
        "Gerente", 
        "Consultor - Vendas",  # Contém hífen
        "SDR",
        "Social Media",
        "Coordenador - Marketing",  # Contém hífen
        "Analista   Financeiro",    # Espaços múltiplos
        "  Supervisor  ",           # Espaços nas bordas
        "Nome Muito Longo Para Uma Role Que Pode Causar Problemas Na API Do Kommo"  # Muito longo
    ]
    
    def sanitize_role_name(name):
        """Função de sanitização (mesma lógica do código)"""
        clean_name = name.strip()
        clean_name = clean_name.replace(' - ', ' ')  # Remover hífens com espaços
        clean_name = clean_name.replace('-', ' ')    # Remover hífens simples
        clean_name = ' '.join(clean_name.split())    # Normalizar espaços múltiplos
        clean_name = clean_name[:50]                 # Limitar a 50 caracteres
        return clean_name
    
    print("\n📋 RESULTADOS DA SANITIZAÇÃO:")
    print("-" * 30)
    
    for original_name in test_names:
        sanitized_name = sanitize_role_name(original_name)
        
        if original_name == sanitized_name:
            status = "✅ OK"
        else:
            status = "🔧 CORRIGIDO"
        
        print(f"{status}")
        print(f"   Original: '{original_name}'")
        if original_name != sanitized_name:
            print(f"   Sanitizado: '{sanitized_name}'")
        print(f"   Tamanho: {len(sanitized_name)} caracteres")
        print()
    
    print("📊 RESUMO:")
    print("-" * 10)
    
    issues_found = 0
    for name in test_names:
        sanitized = sanitize_role_name(name)
        if name != sanitized:
            issues_found += 1
    
    print(f"Total de nomes testados: {len(test_names)}")
    print(f"Nomes que precisaram correção: {issues_found}")
    print(f"Nomes já corretos: {len(test_names) - issues_found}")
    
    print("\n✅ PRINCIPAIS CORREÇÕES APLICADAS:")
    print("-" * 35)
    print("1. 🔧 'Consultor - Vendas' → 'Consultor Vendas'")
    print("2. 🔧 'Coordenador - Marketing' → 'Coordenador Marketing'") 
    print("3. 🔧 'Analista   Financeiro' → 'Analista Financeiro'")
    print("4. 🔧 '  Supervisor  ' → 'Supervisor'")
    print("5. 🔧 Nomes longos truncados para 50 caracteres")
    
    print("\n🎯 BENEFÍCIOS ESPERADOS:")
    print("-" * 25)
    print("✅ Elimina erros 400 causados por hífens nos nomes")
    print("✅ Normaliza espaços múltiplos")
    print("✅ Remove espaços desnecessários nas bordas")
    print("✅ Limita tamanho para evitar erros da API")
    print("✅ Mantém nomes legíveis e profissionais")

if __name__ == "__main__":
    test_role_name_sanitization()

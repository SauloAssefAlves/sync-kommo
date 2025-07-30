#!/usr/bin/env python3
"""
Script para testar a validação de cores do Kommo
"""

def test_color_validation():
    """Testa a validação de cores do Kommo"""
    
    # Cores válidas do Kommo
    kommo_colors = [
        '#fffeb2', '#fffd7f', '#fff000', '#ffeab2', '#ffdc7f', '#ffce5a',
        '#ffdbdb', '#ffc8c8', '#ff8f92', '#d6eaff', '#c1e0ff', '#98cbff',
        '#ebffb1', '#deff81', '#87f2c0', '#f9deff', '#f3beff', '#ccc8f9',
        '#eb93ff', '#f2f3f4', '#e6e8ea'
    ]
    
    def get_valid_kommo_color(master_color, fallback_index):
        """Retorna uma cor válida do Kommo baseada na cor da master ou fallback"""
        if master_color and master_color.lower() in [c.lower() for c in kommo_colors]:
            return master_color
        else:
            # Se a cor da master não é válida, usar cor do índice como fallback
            return kommo_colors[fallback_index % len(kommo_colors)]
    
    # Cores de teste (possíveis cores da master)
    test_colors = [
        '#fff000',     # Válida (amarelo)
        '#ff0000',     # Inválida (vermelho puro)
        '#d6eaff',     # Válida (azul claro)
        '#00ff00',     # Inválida (verde puro)
        '#98cbff',     # Válida (azul)
        '#purple',     # Inválida (nome de cor)
        None,          # Sem cor
        '',            # Cor vazia
    ]
    
    print("🎨 TESTE DE VALIDAÇÃO DE CORES DO KOMMO")
    print("=" * 50)
    
    for i, test_color in enumerate(test_colors):
        valid_color = get_valid_kommo_color(test_color, i)
        status = "✅ VÁLIDA" if test_color and test_color.lower() in [c.lower() for c in kommo_colors] else "❌ INVÁLIDA"
        
        print(f"Teste {i+1}:")
        print(f"  Cor master: {test_color or 'None'}")
        print(f"  Status: {status}")
        print(f"  Cor final: {valid_color}")
        print()
    
    print("📋 CORES VÁLIDAS DO KOMMO:")
    for i, color in enumerate(kommo_colors):
        print(f"  {i+1:2d}. {color}")

if __name__ == "__main__":
    test_color_validation()

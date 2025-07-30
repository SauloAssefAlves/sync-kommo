#!/usr/bin/env python3
"""
Script para testar o novo mapeamento inteligente de cores
"""

def test_intelligent_color_mapping():
    """
    Testa o novo mapeamento inteligente de cores
    """
    print("🧠 Testando mapeamento inteligente de cores...")
    
    # Cores oficiais do Kommo
    kommo_colors = [
        '#fffeb2', '#fffd7f', '#fff000', '#ffeab2', '#ffdc7f', '#ffce5a',
        '#ffdbdb', '#ffc8c8', '#ff8f92', '#d6eaff', '#c1e0ff', '#98cbff',
        '#ebffb1', '#deff81', '#87f2c0', '#f9deff', '#f3beff', '#ccc8f9',
        '#eb93ff', '#f2f3f4', '#e6e8ea'
    ]
    
    def get_valid_kommo_color(master_color, fallback_index):
        """Função melhorada com mapeamento inteligente"""
        # Se a cor da master é válida, usar ela
        if master_color and master_color.lower() in [c.lower() for c in kommo_colors]:
            return master_color
        
        # Se não é válida, tentar mapear para cor similar
        if master_color:
            master_color_lower = master_color.lower()
            
            # Mapear cores azuis para cores azuis válidas do Kommo
            if any(blue_hint in master_color_lower for blue_hint in ['blue', 'azul']) or master_color_lower in ['#0000ff', '#0066ff', '#4169e1']:
                return '#98cbff'  # Azul forte do Kommo
            
            # Mapear cores verdes para cores verdes válidas do Kommo  
            if any(green_hint in master_color_lower for green_hint in ['green', 'verde']) or master_color_lower in ['#00ff00', '#008000', '#32cd32']:
                return '#87f2c0'  # Verde forte do Kommo
            
            # Mapear cores vermelhas/rosas para cores vermelhas válidas do Kommo
            if any(red_hint in master_color_lower for red_hint in ['red', 'vermelho', '#ff0000', '#dc143c', '#b22222']):
                return '#ff8f92'  # Rosa forte do Kommo
            
            # Mapear cores roxas para cores roxas válidas do Kommo
            if any(purple_hint in master_color_lower for purple_hint in ['purple', 'roxo', '#800080', '#9932cc', '#8a2be2']):
                return '#eb93ff'  # Magenta do Kommo
            
            # Mapear cores amarelas para cores amarelas válidas do Kommo
            if any(yellow_hint in master_color_lower for yellow_hint in ['yellow', 'amarelo', '#ffff00', '#ffd700', '#fff8dc']):
                return '#fff000'  # Amarelo forte do Kommo
            
            # Mapear cores laranjas para cores laranjas válidas do Kommo
            if any(orange_hint in master_color_lower for orange_hint in ['orange', 'laranja', '#ffa500', '#ff8c00', '#ff7f50']):
                return '#ffce5a'  # Laranja forte do Kommo
        
        # Se nenhum mapeamento específico, usar fallback por índice
        return kommo_colors[fallback_index % len(kommo_colors)]
    
    # Testes de cores inválidas que devem ser mapeadas inteligentemente
    test_colors = [
        ('#0000ff', 'Azul puro -> deve virar #98cbff (Azul forte Kommo)'),
        ('#00ff00', 'Verde puro -> deve virar #87f2c0 (Verde forte Kommo)'), 
        ('#ff0000', 'Vermelho puro -> deve virar #ff8f92 (Rosa forte Kommo)'),
        ('#800080', 'Roxo -> deve virar #eb93ff (Magenta Kommo)'),
        ('#ffff00', 'Amarelo puro -> deve virar #fff000 (Amarelo forte Kommo)'),
        ('#ffa500', 'Laranja -> deve virar #ffce5a (Laranja forte Kommo)'),
        ('#98cbff', 'Azul Kommo válido -> deve manter #98cbff'),
        ('#123456', 'Cor aleatória -> deve usar fallback por índice'),
    ]
    
    print("🎨 Testando mapeamento inteligente:")
    for i, (test_color, description) in enumerate(test_colors):
        result = get_valid_kommo_color(test_color, i)
        print(f"  {test_color} -> {result}")
        print(f"    {description}")
        
        # Verificar se é uma cor válida do Kommo
        is_valid = result.lower() in [c.lower() for c in kommo_colors]
        status = "✅" if is_valid else "❌"
        print(f"    {status} Resultado é válido no Kommo\n")
    
    print("🔍 Caso específico: status 'blue' com cor #0000ff")
    blue_result = get_valid_kommo_color('#0000ff', 2)  # Índice 2 seria fallback amarelo
    print(f"  Cor original: #0000ff (azul puro)")
    print(f"  Cor aplicada: {blue_result}")
    print(f"  ✅ Agora o status 'blue' será realmente AZUL!")

if __name__ == "__main__":
    test_intelligent_color_mapping()

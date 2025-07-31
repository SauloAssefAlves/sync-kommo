#!/usr/bin/env python3
"""
Teste offline da lógica de campos monetários (price/currency)
"""

import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_currency_field_update():
    """
    Simula o problema com campos monetários
    """
    logger.info("💰 SIMULANDO PROBLEMA COM CAMPOS MONETÁRIOS")
    logger.info("=" * 60)
    
    # Simular campo monetário na master
    master_field = {
        'name': 'moeda',
        'type': 'price',
        'currency': 'BRL',
        'sort': 525,
        'is_required': False
    }
    
    # Simular campo existente na slave (SEM currency)
    existing_field = {
        'name': 'moeda',
        'type': 'price',
        # currency: AUSENTE! ❌
        'sort': 523,
        'is_required': False
    }
    
    logger.info("📋 DADOS SIMULADOS:")
    logger.info(f"   Campo Master: {master_field}")
    logger.info(f"   Campo Existente na Slave: {existing_field}")
    
    # Simular lógica de atualização
    logger.info("\n🔄 SIMULANDO PROCESSO DE ATUALIZAÇÃO...")
    
    needs_update = False
    update_data = {}
    field_name = master_field['name']
    field_type = master_field['type']
    
    # Verificar sort
    existing_sort = existing_field.get('sort', 0)
    new_sort = master_field.get('sort', 0)
    if existing_sort != new_sort:
        update_data['sort'] = new_sort
        needs_update = True
        logger.info(f"Sort será atualizado: {existing_sort} -> {new_sort}")
    
    # Verificar currency (NOVO - a correção)
    if field_type == 'price':
        existing_currency = existing_field.get('currency')
        new_currency = master_field.get('currency', 'USD')
        if existing_currency != new_currency:
            update_data['currency'] = new_currency
            needs_update = True
            logger.info(f"💰 Currency será atualizada: {existing_currency} -> {new_currency}")
        elif 'currency' not in update_data:
            # Sempre incluir currency em atualizações de campos monetários
            update_data['currency'] = new_currency
            logger.info(f"💰 Currency mantida para campo monetário: {new_currency}")
    
    # Resultado
    logger.info(f"\n📊 RESULTADO DA ATUALIZAÇÃO:")
    logger.info(f"   Needs update: {needs_update}")
    logger.info(f"   Update data: {update_data}")
    
    if needs_update and update_data:
        logger.info(f"   ✅ Campo será atualizado com sucesso!")
        logger.info(f"   📤 Dados enviados para API: {update_data}")
    else:
        logger.warning(f"   ❌ Nenhuma atualização necessária")
    
    # Comparar com o erro anterior
    logger.info(f"\n🚨 COMPARAÇÃO COM ERRO ANTERIOR:")
    logger.info(f"   ANTES (erro): Tentava atualizar sem 'currency'")
    logger.info(f"   DEPOIS (corrigido): Sempre inclui 'currency' para campos price")
    
    # Simular dados que causavam erro
    problematic_update = {'sort': 525}  # SEM currency
    logger.info(f"   ❌ Dados problemáticos: {problematic_update}")
    logger.info(f"   ✅ Dados corrigidos: {update_data}")

def test_different_currency_scenarios():
    """
    Testa diferentes cenários de currency
    """
    logger.info("\n" + "=" * 60)
    logger.info("🧪 TESTANDO DIFERENTES CENÁRIOS DE CURRENCY")
    logger.info("=" * 60)
    
    scenarios = [
        {
            'name': 'Currency mudou',
            'master': {'currency': 'BRL', 'sort': 100},
            'existing': {'currency': 'USD', 'sort': 100},
            'expected': {'currency': 'BRL'}
        },
        {
            'name': 'Currency ausente na slave',
            'master': {'currency': 'BRL', 'sort': 100},
            'existing': {'sort': 100},  # SEM currency
            'expected': {'currency': 'BRL'}
        },
        {
            'name': 'Sort mudou + currency',
            'master': {'currency': 'BRL', 'sort': 200},
            'existing': {'currency': 'BRL', 'sort': 100},
            'expected': {'sort': 200, 'currency': 'BRL'}
        },
        {
            'name': 'Tudo igual',
            'master': {'currency': 'USD', 'sort': 100},
            'existing': {'currency': 'USD', 'sort': 100},
            'expected': {'currency': 'USD'}  # Sempre incluir currency
        }
    ]
    
    for scenario in scenarios:
        logger.info(f"\n🔍 CENÁRIO: {scenario['name']}")
        master = scenario['master']
        existing = scenario['existing']
        expected = scenario['expected']
        
        # Simular lógica
        needs_update = False
        update_data = {}
        
        # Verificar sort
        if existing.get('sort') != master.get('sort'):
            update_data['sort'] = master['sort']
            needs_update = True
        
        # Verificar currency (lógica corrigida)
        existing_currency = existing.get('currency')
        new_currency = master.get('currency', 'USD')
        if existing_currency != new_currency:
            update_data['currency'] = new_currency
            needs_update = True
        elif 'currency' not in update_data:
            # Sempre incluir currency
            update_data['currency'] = new_currency
        
        logger.info(f"   Master: {master}")
        logger.info(f"   Existing: {existing}")
        logger.info(f"   Update data: {update_data}")
        logger.info(f"   Expected: {expected}")
        
        # Verificar se a lógica está correta
        success = all(key in update_data and update_data[key] == expected[key] for key in expected)
        if success:
            logger.info(f"   ✅ SUCESSO: Lógica funcionou corretamente")
        else:
            logger.error(f"   ❌ FALHA: Lógica não funcionou como esperado")

if __name__ == "__main__":
    simulate_currency_field_update()
    test_different_currency_scenarios()

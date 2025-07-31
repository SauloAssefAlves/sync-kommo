#!/usr/bin/env python3
"""
Teste específico para campo monetário com currency
"""

import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_monetary_field_with_currency():
    """
    Simula o problema do campo 'moeda' que está faltando currency
    """
    logger.info("🧪 TESTE: CAMPO MONETÁRIO COM CURRENCY")
    logger.info("=" * 60)
    
    # Simular campo master 'moeda'
    master_field = {
        'name': 'moeda',
        'type': 'monetary',
        'sort': 525,
        'is_required': False,
        'currency': 'BRL',  # Currency brasileiro
        'group_id': 27941753738566  # Grupo master
    }
    
    # Simular campo existente na slave (SEM currency)
    existing_slave_field = {
        'id': 779808,
        'name': 'moeda',
        'type': 'monetary',
        'sort': 523,
        'is_required': False,
        # FALTANDO: 'currency'  <- ESTE É O PROBLEMA!
        'group_id': 71261753919476  # Grupo slave
    }
    
    logger.info("📋 DADOS DO TESTE:")
    logger.info(f"   Campo master: {master_field}")
    logger.info(f"   Campo slave existente: {existing_slave_field}")
    
    # Simular processo de atualização
    logger.info(f"\n🔄 SIMULANDO PROCESSO DE ATUALIZAÇÃO...")
    
    field_name = master_field['name']
    field_type = master_field['type']
    
    # Preparar dados de atualização
    update_data = {}
    needs_update = False
    
    # Verificar sort
    if existing_slave_field['sort'] != master_field['sort']:
        update_data['sort'] = master_field['sort']
        needs_update = True
        logger.info(f"Sort será atualizado: {existing_slave_field['sort']} -> {master_field['sort']}")
    
    # Verificar group_id
    if existing_slave_field.get('group_id') != master_field.get('group_id'):
        if master_field.get('group_id'):
            update_data['group_id'] = master_field['group_id']
            needs_update = True
            logger.info(f"Group_id será atualizado: {existing_slave_field.get('group_id')} -> {master_field['group_id']}")
    
    # CORREÇÃO: Verificar currency para campos monetários
    if field_type in ['price', 'monetary']:
        existing_currency = existing_slave_field.get('currency')
        new_currency = master_field.get('currency', 'USD')
        
        logger.info(f"💰 VERIFICANDO CURRENCY:")
        logger.info(f"   Currency existente: {existing_currency}")
        logger.info(f"   Currency desejada: {new_currency}")
        
        if existing_currency != new_currency:
            update_data['currency'] = new_currency
            needs_update = True
            logger.info(f"💰 Currency será atualizada: {existing_currency} -> {new_currency}")
        else:
            # SEMPRE incluir currency em atualizações de campos monetários
            update_data['currency'] = new_currency
            logger.info(f"💰 Currency mantida: {new_currency}")
    
    # Resultado
    logger.info(f"\n📊 RESULTADO DA SIMULAÇÃO:")
    logger.info(f"   Precisa atualizar: {needs_update}")
    logger.info(f"   Dados de atualização: {update_data}")
    
    if needs_update and update_data:
        logger.info(f"   ✅ Campo será atualizado com sucesso")
        logger.info(f"   📤 Dados enviados para API: {update_data}")
        
        # Simular resposta da API
        if 'currency' in update_data:
            logger.info(f"   ✅ API: Currency '{update_data['currency']}' aceita")
        else:
            logger.error(f"   ❌ API: Currency é obrigatória para campos monetários!")
            
    else:
        logger.warning(f"   ⚠️ Nenhuma atualização será feita")

def test_api_error_simulation():
    """
    Simula o erro exato que está acontecendo
    """
    logger.info(f"\n" + "=" * 60)
    logger.info("🚨 SIMULANDO ERRO REAL DA API")
    logger.info("=" * 60)
    
    # Dados que causaram o erro (SEM currency)
    problematic_data = {
        'sort': 525,
        'group_id': 71261753919476
        # FALTANDO: 'currency': 'BRL'
    }
    
    logger.info("❌ DADOS PROBLEMÁTICOS ENVIADOS:")
    logger.info(f"   {problematic_data}")
    
    logger.info("🔍 ERRO DA API:")
    logger.info('   400 Bad Request: {"validation-errors":[{"errors":[{"code":"FieldMissing","path":"currency","detail":"This field is missing."}]}]}')
    
    # Dados corretos (COM currency)
    correct_data = {
        'sort': 525,
        'group_id': 71261753919476,
        'currency': 'BRL'  # ADICIONADO!
    }
    
    logger.info("\n✅ DADOS CORRETOS:")
    logger.info(f"   {correct_data}")
    
    logger.info("\n💡 SOLUÇÃO IMPLEMENTADA:")
    logger.info("   - Detectar campos tipo 'monetary' e 'price'")
    logger.info("   - SEMPRE incluir 'currency' nas atualizações")
    logger.info("   - Usar currency da master ou 'USD' como padrão")

if __name__ == "__main__":
    test_monetary_field_with_currency()
    test_api_error_simulation()

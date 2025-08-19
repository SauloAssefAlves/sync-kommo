# CORREÇÃO IMPLEMENTADA: Status 142 e 143 nos Required_Statuses

## Problema Identificado
- Os status 142 (Won) e 143 (Lost) não estavam sendo salvos no banco de dados durante a sincronização
- Isso ocorria porque a função `_should_ignore_stage()` os ignorava completamente
- Quando os `required_statuses` dos campos tentavam mapear esses IDs, eles não eram encontrados nos mapeamentos
- Resultado: campos com `required_statuses` que dependiam desses status especiais falhavam na criação

## Solução Implementada
Modificamos **apenas** a função de sincronização de `required_statuses` em `/home/user/sync-kommo/src/services/kommo_api.py` (linhas ~1384-1399):

### Antes:
```python
if master_status_id and master_status_id in mappings.get('stages', {}):
    # Mapear normalmente
else:
    # Ignorar se não encontrado
```

### Depois:
```python
if master_status_id and master_status_id in mappings.get('stages', {}):
    # Mapear normalmente
elif master_status_id in [142, 143, 1]:  # Status especiais do sistema
    # Para required_statuses, mapear status especiais para eles mesmos
    # pois estes IDs são padrão do Kommo em todas as contas
    mapped_status = {
        'status_id': master_status_id,  # Mapear para ele mesmo
        'pipeline_id': slave_pipeline_id
    }
    mapped_required_statuses.append(mapped_status)
else:
    # Ignorar se não encontrado
```

## Comportamento Atual
1. **Funções normais** (sincronização de pipelines, roles, etc.): 
   - ✅ Status 142 e 143 continuam sendo **ignorados** como antes
   - ✅ Não são criados/sincronizados (gerenciados automaticamente pelo Kommo)

2. **Required_statuses de campos customizados**:
   - ✅ Status 142 e 143 são **incluídos** quando necessários
   - ✅ São mapeados para eles mesmos (IDs padrão do Kommo)
   - ✅ Campos que dependem desses status agora funcionam corretamente

## Testes Realizados
- ✅ Verificado que status especiais continuam ignorados nas funções normais
- ✅ Verificado que status especiais são incluídos nos required_statuses
- ✅ Testado cenário completo com múltiplos tipos de status

## Status dos Números Especiais
- **142** (Won): Mapeado para ele mesmo nos required_statuses
- **143** (Lost): Mapeado para ele mesmo nos required_statuses  
- **1** (Incoming): Também incluído para compatibilidade completa

## Resultado
Agora quando você criar campos customizados que têm `required_statuses` dependendo dos status 142 ou 143, eles serão encontrados e mapeados corretamente, resolvendo o problema de criação dos campos.

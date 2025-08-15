# Endpoint de Sincronização de Roles

## POST /sync/roles

Sincroniza somente as roles (funções/permissões) entre as contas Kommo master e slave.

### Descrição

Este endpoint permite sincronizar apenas as roles entre contas, sem afetar pipelines, campos personalizados ou outras configurações. É útil quando você precisa atualizar apenas as permissões de usuários entre as contas.

### Parâmetros (JSON)

| Parâmetro                  | Tipo           | Obrigatório | Descrição                                                                                     |
| -------------------------- | -------------- | ----------- | --------------------------------------------------------------------------------------------- |
| `master_account_id`        | integer        | Não         | ID da conta master. Se não fornecido, usa a primeira conta ativa com role 'master'            |
| `slave_account_ids`        | array[integer] | Não         | Array com IDs das contas slave. Se não fornecido, usa todas as contas ativas com role 'slave' |
| `batch_config`             | object         | Não         | Configurações de processamento em lotes                                                       |
| `batch_config.batch_size`  | integer        | Não         | Quantos itens processar por lote (padrão: 5)                                                  |
| `batch_config.batch_delay` | float          | Não         | Delay em segundos entre lotes (padrão: 1.0)                                                   |

### Exemplos de Uso

#### 1. Sincronização Automática (usar contas padrão)

```json
POST /sync/roles
{
  "batch_config": {
    "batch_size": 5,
    "batch_delay": 1.0
  }
}
```

#### 2. Sincronização com Contas Específicas

```json
POST /sync/roles
{
  "master_account_id": 1,
  "slave_account_ids": [2, 3, 4],
  "batch_config": {
    "batch_size": 3,
    "batch_delay": 2.0
  }
}
```

#### 3. Sincronização Rápida (lotes maiores, menos delay)

```json
POST /sync/roles
{
  "batch_config": {
    "batch_size": 10,
    "batch_delay": 0.5
  }
}
```

### Resposta de Sucesso (200)

```json
{
  "success": true,
  "message": "Sincronização de roles concluída",
  "results": {
    "total_accounts": 3,
    "success_accounts": 2,
    "failed_accounts": 1,
    "total_roles_created": 5,
    "total_roles_updated": 2,
    "total_roles_deleted": 1,
    "total_roles_skipped": 8,
    "account_details": [
      {
        "account_id": 2,
        "subdomain": "empresa-slave1",
        "status": "success",
        "results": {
          "created": 2,
          "updated": 1,
          "deleted": 0,
          "skipped": 4,
          "errors": []
        }
      },
      {
        "account_id": 3,
        "subdomain": "empresa-slave2",
        "status": "failed",
        "error": "Falha na conexão",
        "partial_results": null
      }
    ]
  }
}
```

### Respostas de Erro

#### 400 - Bad Request

```json
{
  "success": false,
  "error": "Nenhuma conta master encontrada"
}
```

#### 404 - Not Found

```json
{
  "success": false,
  "error": "Conta master 99 não encontrada"
}
```

#### 409 - Conflict

```json
{
  "success": false,
  "error": "Já existe uma sincronização em andamento"
}
```

#### 500 - Internal Server Error

```json
{
  "success": false,
  "error": "Erro ao extrair roles da master: Connection timeout"
}
```

### Funcionalidades

#### 🔐 Sincronização de Roles

- **Criação**: Roles da master que não existem na slave são criadas
- **Atualização**: Roles existentes têm suas permissões (rights) atualizadas
- **Exclusão**: Roles na slave que não existem na master são removidas (exceto roles de sistema)
- **Proteção**: Roles de sistema (admin, administrator) nunca são excluídas

#### 📊 Processamento em Lotes

- Processamento otimizado com controle de lotes
- Delay configurável entre lotes para evitar rate limiting
- Progress tracking em tempo real

#### 🛡️ Tratamento de Erros

- Validação de conexão com todas as contas antes de iniciar
- Continuação da sincronização mesmo se uma conta falhar
- Log detalhado de todos os erros

#### 📈 Monitoramento

- Status global da sincronização disponível via `GET /sync/status`
- Possibilidade de parar a sincronização via `POST /sync/stop`
- Logs detalhados de todas as operações

### Integração com Outros Endpoints

#### Verificar Status

```bash
GET /sync/status
```

#### Parar Sincronização

```bash
POST /sync/stop
```

#### Listar Contas

```bash
GET /sync/accounts
```

### Logs e Auditoria

Todas as sincronizações são registradas na tabela `sync_logs` com:

- Conta de origem (master)
- Conta de destino (slave)
- Tipo de sincronização: `'roles_only'`
- Status: `'success'` ou `'failed'`
- Detalhes: estatísticas e erros da sincronização

### Permissões de Roles

O sistema sincroniza todas as permissões (rights) das roles, incluindo:

- Permissões de visualização
- Permissões de edição
- Permissões de exclusão
- Permissões especiais de módulos
- Configurações de acesso a relatórios

### Casos de Uso

1. **Atualização de Permissões**: Quando novas roles são criadas na master
2. **Padronização**: Garantir que todas as contas slave tenham as mesmas roles
3. **Correção de Inconsistências**: Corrigir roles que foram modificadas manualmente
4. **Onboarding**: Configurar rapidamente novas contas slave com as roles corretas
5. **Manutenção**: Sincronização periódica para manter consistência

### Performance

- **Lotes**: Processamento em lotes evita sobrecarga da API
- **Rate Limiting**: Delay entre lotes respeita limites da API do Kommo
- **Concorrência**: Uma sincronização por vez para evitar conflitos
- **Otimização**: Apenas roles realmente diferentes são atualizadas

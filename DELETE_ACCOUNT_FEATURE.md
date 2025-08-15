# 🗑️ EXCLUSÃO DE CONTAS SLAVE

## ✅ **Funcionalidade Implementada**

### 📍 **Novo Endpoint: DELETE `/api/sync/accounts/{id}`**

- ✅ **Exclui uma conta específica** do banco de dados
- 🛡️ **Protege contas master** - não podem ser excluídas individualmente
- ✅ **Validações completas** - verifica se conta existe
- 📊 **Logs detalhados** - registra exclusões no sistema

## 🔧 **Como Usar**

### **Excluir uma conta slave específica:**

```bash
DELETE /api/sync/accounts/{id}
```

**Exemplo:**

```bash
curl -X DELETE http://localhost:5000/api/sync/accounts/123
```

**Resposta de sucesso:**

```json
{
  "success": true,
  "message": "Conta testedev.kommo.com removida com sucesso",
  "account": {
    "id": 123,
    "subdomain": "testedev.kommo.com",
    "account_role": "slave",
    "sync_group_id": 1
  }
}
```

## 🛡️ **Proteções Implementadas**

### **1. Conta Master Protegida**

```json
{
  "success": false,
  "error": "Não é possível excluir a conta master. Use /accounts/clear para remover todas as contas."
}
```

### **2. Conta Inexistente**

```json
{
  "success": false,
  "error": "Conta não encontrada"
}
```

## 📊 **Endpoints de Gerenciamento de Contas**

| Método   | Endpoint                       | Descrição                         |
| -------- | ------------------------------ | --------------------------------- |
| `GET`    | `/api/sync/accounts`           | Lista todas as contas             |
| `POST`   | `/api/sync/accounts`           | Adiciona nova conta               |
| `DELETE` | `/api/sync/accounts/{id}`      | **NOVO:** Remove conta específica |
| `DELETE` | `/api/sync/accounts/clear`     | Remove TODAS as contas            |
| `GET`    | `/api/sync/accounts/{id}/test` | Testa conexão da conta            |

## 🎯 **Casos de Uso**

### **1. Remover conta slave problemática:**

```bash
DELETE /api/sync/accounts/123
```

### **2. Limpar conta slave desatualizada:**

```bash
DELETE /api/sync/accounts/456
```

### **3. Reset completo (todas as contas):**

```bash
DELETE /api/sync/accounts/clear
```

## ⚠️ **Importante**

- ✅ **Apenas contas SLAVE** podem ser excluídas individualmente
- 👑 **Contas MASTER** são protegidas contra exclusão acidental
- 💾 **Exclusão é permanente** - não há recuperação
- 🔄 **Backup recomendado** antes de exclusões em produção

## 🧪 **Testar**

```bash
# Executar teste automatizado
python test_delete_account.py

# Ou testar manualmente
curl -X DELETE http://localhost:5000/api/sync/accounts/{id}
```

**A funcionalidade está pronta para uso! 🚀**

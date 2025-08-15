// Configuração da API
const API_CONFIG = {
  baseUrl: "http://89.116.186.230:5000",
  endpoint: "/api",
};

// Variáveis globais para controle do sistema
let syncInProgress = false;
let currentSyncType = null;
let statusInterval = null;
let logInterval = null;
let slaveAccounts = [];

// Configurações padrão
const defaultConfig = {
  batchSize: 10,
  batchDelay: 2.0,
  maxConcurrent: 3,
};

// Helper function para construir URLs da API
function buildApiUrl(path) {
  return `${API_CONFIG.baseUrl}${API_CONFIG.endpoint}${path}`;
}

// Initialize quando a página carregar
document.addEventListener("DOMContentLoaded", function () {
  initializeSystem();
  loadSyncStatus();
  refreshAccountsList();
  startAutoRefresh();
});

// Inicializar sistema
function initializeSystem() {
  // Aplicar configurações padrão
  document.getElementById("batchSize").value = defaultConfig.batchSize;
  document.getElementById("batchDelay").value = defaultConfig.batchDelay;
  document.getElementById("maxConcurrent").value = defaultConfig.maxConcurrent;

  // Setup event listeners
  setupEventListeners();

  addLog("Sistema inicializado e pronto para sincronização");
}

// Setup event listeners
function setupEventListeners() {
  // Escutar mudanças nas configurações
  ["batchSize", "batchDelay", "maxConcurrent"].forEach((id) => {
    document.getElementById(id).addEventListener("change", saveConfig);
  });
}

// Salvar configurações
function saveConfig() {
  const config = {
    batchSize: parseInt(document.getElementById("batchSize").value),
    batchDelay: parseFloat(document.getElementById("batchDelay").value),
    maxConcurrent: parseInt(document.getElementById("maxConcurrent").value),
  };

  localStorage.setItem("kommoSyncConfig", JSON.stringify(config));
  addLog(
    `Configurações salvas: Lote=${config.batchSize}, Delay=${config.batchDelay}s, Concurrent=${config.maxConcurrent}`
  );
}

// Carregar configurações salvas
function loadConfig() {
  const saved = localStorage.getItem("kommoSyncConfig");
  if (saved) {
    const config = JSON.parse(saved);
    document.getElementById("batchSize").value =
      config.batchSize || defaultConfig.batchSize;
    document.getElementById("batchDelay").value =
      config.batchDelay || defaultConfig.batchDelay;
    document.getElementById("maxConcurrent").value =
      config.maxConcurrent || defaultConfig.maxConcurrent;
  }
}

// Triggar sincronização em lotes
async function triggerBatchSync(syncType) {
  if (syncInProgress) {
    showAlert("Sincronização já está em andamento!", "warning");
    return;
  }

  const config = getBatchConfig();

  try {
    setSyncInProgress(true, syncType);
    addLog(`Iniciando sincronização em lotes: ${syncType}`);
    addLog(
      `Configuração: Lote=${config.batch_size}, Delay=${config.delay_between_batches}s`
    );

    const response = await fetch(buildApiUrl("/sync/trigger"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        sync_type: syncType,
        batch_config: config,
      }),
    });

    const result = await response.json();

    if (result.success) {
      addLog(`✅ Sincronização ${syncType} iniciada com sucesso`);
      startStatusMonitoring();
    } else {
      throw new Error(result.error || "Erro desconhecido");
    }
  } catch (error) {
    addLog(`❌ Erro ao iniciar sincronização: ${error.message}`);
    setSyncInProgress(false);
    showAlert("Erro ao iniciar sincronização: " + error.message, "error");
  }
}

// Triggar sincronização de múltiplas contas
async function triggerMultiAccountSync() {
  if (syncInProgress) {
    showAlert("Sincronização já está em andamento!", "warning");
    return;
  }

  const config = getBatchConfig();
  const parallel = document.getElementById("syncParallel").checked;
  const continueOnError = document.getElementById("continueOnError").checked;

  try {
    setSyncInProgress(true, "multi-account");
    addLog("Iniciando sincronização de múltiplas contas");
    addLog(
      `Configuração: Paralelo=${parallel}, Continuar com erro=${continueOnError}`
    );

    const response = await fetch(buildApiUrl("/sync/multi-account"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        batch_config: config,
        parallel: parallel,
        continue_on_error: continueOnError,
      }),
    });

    const result = await response.json();

    if (result.success) {
      addLog("✅ Sincronização multi-conta iniciada com sucesso");
      startStatusMonitoring();
    } else {
      throw new Error(result.error || "Erro desconhecido");
    }
  } catch (error) {
    addLog(`❌ Erro ao iniciar sincronização multi-conta: ${error.message}`);
    setSyncInProgress(false);
    showAlert("Erro ao iniciar sincronização: " + error.message, "error");
  }
}

// Parar sincronização
async function stopSync() {
  try {
    addLog("Parando sincronização...");

    const response = await fetch(buildApiUrl("/sync/stop"), {
      method: "POST",
    });

    const result = await response.json();

    if (result.success) {
      addLog("🛑 Sincronização parada com sucesso");
      setSyncInProgress(false);
    } else {
      throw new Error(result.error || "Erro ao parar sincronização");
    }
  } catch (error) {
    addLog(`❌ Erro ao parar sincronização: ${error.message}`);
    showAlert("Erro ao parar sincronização: " + error.message, "error");
  }
}

// Obter configuração de lote atual
function getBatchConfig() {
  return {
    batch_size:
      parseInt(document.getElementById("batchSize").value) ||
      defaultConfig.batchSize,
    delay_between_batches:
      parseFloat(document.getElementById("batchDelay").value) ||
      defaultConfig.batchDelay,
    max_concurrent:
      parseInt(document.getElementById("maxConcurrent").value) ||
      defaultConfig.maxConcurrent,
  };
}

// Definir sincronização em progresso
function setSyncInProgress(inProgress, syncType = null) {
  syncInProgress = inProgress;
  currentSyncType = syncType;

  // Atualizar UI
  const syncButtons = document.querySelectorAll(
    ".sync-actions .btn:not(#stopSyncBtn)"
  );
  const stopButton = document.getElementById("stopSyncBtn");

  syncButtons.forEach((btn) => {
    btn.disabled = inProgress;
  });

  if (inProgress) {
    stopButton.style.display = "inline-flex";
    updateSyncStatus("Sincronização em andamento...", 0, syncType);
  } else {
    stopButton.style.display = "none";
    updateSyncStatus("Aguardando", 0, "-");
    stopStatusMonitoring();
  }
}

// Iniciar monitoramento de status
function startStatusMonitoring() {
  if (statusInterval) {
    clearInterval(statusInterval);
  }

  statusInterval = setInterval(loadSyncStatus, 2000); // A cada 2 segundos
}

// Parar monitoramento de status
function stopStatusMonitoring() {
  if (statusInterval) {
    clearInterval(statusInterval);
    statusInterval = null;
  }
}

// Carregar status da sincronização
async function loadSyncStatus() {
  try {
    const response = await fetch(buildApiUrl("/sync/status"));
    const result = await response.json();

    if (result.success && result.status) {
      const status = result.status;

      updateSyncStatus(
        status.current_status || "Aguardando",
        status.progress || 0,
        status.current_operation || "-",
        status.current_batch || "-",
        status.estimated_time || "-"
      );

      // Verificar se sincronização terminou
      if (
        status.current_status === "completed" ||
        status.current_status === "failed"
      ) {
        setSyncInProgress(false);

        if (status.results) {
          updateStatistics(status.results);
        }
      } else if (status.current_status !== "idle") {
        setSyncInProgress(true, status.sync_type);
      }
    }
  } catch (error) {
    console.error("Erro ao carregar status:", error);
  }
}

// Atualizar status na UI
function updateSyncStatus(status, progress, operation, batch, estimatedTime) {
  document.getElementById("currentStatus").textContent = status;
  document.getElementById("currentOperation").textContent = operation;
  document.getElementById("currentBatch").textContent = batch;
  document.getElementById("estimatedTime").textContent = estimatedTime;

  // Atualizar barra de progresso
  const progressFill = document.getElementById("progressFill");
  const progressText = document.getElementById("progressText");

  progressFill.style.width = progress + "%";
  progressText.textContent = Math.round(progress) + "%";
}

// Atualizar estatísticas
function updateStatistics(results) {
  if (results.pipeline_stats) {
    document.getElementById(
      "pipelineStats"
    ).textContent = `${results.pipeline_stats.created} criados, ${results.pipeline_stats.updated} atualizados`;
  }

  if (results.group_stats) {
    document.getElementById(
      "groupStats"
    ).textContent = `${results.group_stats.created} criados, ${results.group_stats.updated} atualizados`;
  }

  if (results.field_stats) {
    document.getElementById(
      "fieldStats"
    ).textContent = `${results.field_stats.created} criados, ${results.field_stats.updated} atualizados`;
  }

  if (results.total_time) {
    document.getElementById("timeStats").textContent = `${Math.round(
      results.total_time
    )} segundos`;
  }
}

// Atualizar lista de contas
async function refreshAccountsList() {
  try {
    const response = await fetch(buildApiUrl("/sync/accounts/slaves"));
    const result = await response.json();

    if (result.success && result.accounts) {
      slaveAccounts = result.accounts;
      renderAccountsList();
    }
  } catch (error) {
    console.error("Erro ao carregar contas:", error);
    addLog("❌ Erro ao carregar lista de contas");
  }
}

// Renderizar lista de contas
function renderAccountsList() {
  const container = document.getElementById("slaveAccountsList");

  if (slaveAccounts.length === 0) {
    container.innerHTML =
      '<p style="color: #718096; text-align: center;">Nenhuma conta escrava configurada</p>';
    return;
  }

  container.innerHTML = slaveAccounts
    .map(
      (account) => `
        <div class="account-item">
            <div class="account-info">
                <strong>${account.subdomain}</strong><br>
                <small>${account.account_name || "Sem nome"}</small>
            </div>
            <div class="account-status ${account.status}">${
        account.status
      }</div>
            <div class="account-actions">
                <button class="btn btn-small btn-outline" onclick="testSingleAccount('${
                  account.id
                }')">
                    <i class="fas fa-vial"></i>
                </button>
                <button class="btn btn-small btn-secondary" onclick="syncSingleAccount('${
                  account.id
                }')">
                    <i class="fas fa-sync"></i>
                </button>
            </div>
        </div>
    `
    )
    .join("");
}

// Testar conta única
async function testSingleAccount(accountId) {
  try {
    addLog(`Testando conta ${accountId}...`);

    const response = await fetch(
      buildApiUrl(`/sync/accounts/${accountId}/test`),
      {
        method: "POST",
      }
    );

    const result = await response.json();

    if (result.success) {
      addLog(`✅ Teste da conta ${accountId} concluído`);
      showAlert("Teste concluído com sucesso!", "success");
    } else {
      throw new Error(result.error || "Erro no teste");
    }
  } catch (error) {
    addLog(`❌ Erro ao testar conta ${accountId}: ${error.message}`);
    showAlert("Erro no teste: " + error.message, "error");
  }
}

// Sincronizar conta única
async function syncSingleAccount(accountId) {
  if (syncInProgress) {
    showAlert("Sincronização já está em andamento!", "warning");
    return;
  }

  const config = getBatchConfig();

  try {
    setSyncInProgress(true, "single-account");
    addLog(`Sincronizando conta ${accountId}...`);

    const response = await fetch(buildApiUrl(`/sync/account/${accountId}`), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        batch_config: config,
      }),
    });

    const result = await response.json();

    if (result.success) {
      addLog(`✅ Sincronização da conta ${accountId} iniciada`);
      startStatusMonitoring();
    } else {
      throw new Error(result.error || "Erro na sincronização");
    }
  } catch (error) {
    addLog(`❌ Erro ao sincronizar conta ${accountId}: ${error.message}`);
    setSyncInProgress(false);
    showAlert("Erro na sincronização: " + error.message, "error");
  }
}

// Adicionar log
function addLog(message) {
  const logOutput = document.getElementById("logOutput");
  const timestamp = new Date().toLocaleTimeString();
  logOutput.textContent += `[${timestamp}] ${message}\n`;
  logOutput.scrollTop = logOutput.scrollHeight;
}

// Limpar logs
function clearLogs() {
  document.getElementById("logOutput").textContent = "Console limpo...\n";
}

// Baixar logs
function downloadLogs() {
  const logContent = document.getElementById("logOutput").textContent;
  const blob = new Blob([logContent], { type: "text/plain" });
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = `kommo-sync-logs-${new Date().toISOString().slice(0, 10)}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

// Mostrar alerta
function showAlert(message, type = "info") {
  // Criar elemento de alerta
  const alert = document.createElement("div");
  alert.className = `alert alert-${type}`;
  alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 1000;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;

  // Definir cor baseada no tipo
  const colors = {
    success: "#48bb78",
    error: "#f56565",
    warning: "#ed8936",
    info: "#667eea",
  };

  alert.style.backgroundColor = colors[type] || colors.info;
  alert.textContent = message;

  // Adicionar à página
  document.body.appendChild(alert);

  // Animar entrada
  setTimeout(() => {
    alert.style.transform = "translateX(0)";
  }, 100);

  // Remover após 4 segundos
  setTimeout(() => {
    alert.style.transform = "translateX(100%)";
    setTimeout(() => {
      document.body.removeChild(alert);
    }, 300);
  }, 4000);
}

// Iniciar auto-refresh
function startAutoRefresh() {
  // Atualizar lista de contas a cada 30 segundos
  setInterval(refreshAccountsList, 30000);

  // Carregar configurações salvas
  loadConfig();

  // Carregar grupos
  refreshGroups();
}

// ========================= FUNÇÕES DE GERENCIAMENTO DE GRUPOS =========================

let currentGroupId = null;
let groups = [];
let masterAccounts = [];

// Carregar grupos disponíveis
async function refreshGroups() {
  try {
    const response = await fetch(buildApiUrl("/groups"));
    if (response.ok) {
      const data = await response.json();
      groups = data.groups || [];
      updateGroupSelect();
    } else {
      addLog("Erro ao carregar grupos", "error");
    }
  } catch (error) {
    addLog(`Erro ao carregar grupos: ${error.message}`, "error");
  }
}

// Atualizar select de grupos
function updateGroupSelect() {
  const groupSelect = document.getElementById("groupSelect");
  groupSelect.innerHTML = '<option value="">Selecione um grupo...</option>';

  groups.forEach((group) => {
    const option = document.createElement("option");
    option.value = group.id;
    option.textContent = `${group.name} (${
      group.slave_accounts_count || 0
    } contas)`;
    groupSelect.appendChild(option);
  });

  // Configurar evento de mudança
  groupSelect.onchange = function () {
    const selectedGroupId = this.value;
    if (selectedGroupId) {
      currentGroupId = parseInt(selectedGroupId);
      loadGroupDetails(currentGroupId);
      document.getElementById("detailsBtn").disabled = false;
      document.getElementById("syncGroupBtn").disabled = false;
    } else {
      currentGroupId = null;
      hideGroupInfo();
      document.getElementById("detailsBtn").disabled = true;
      document.getElementById("syncGroupBtn").disabled = true;
    }
  };
}

// Carregar detalhes do grupo
async function loadGroupDetails(groupId) {
  try {
    const response = await fetch(buildApiUrl(`/groups/${groupId}`));
    if (response.ok) {
      const data = await response.json();
      const group = data.group;

      // Atualizar interface
      document.getElementById("groupName").textContent = group.name;
      document.getElementById("groupDescription").textContent =
        group.description || "Sem descrição";
      document.getElementById("masterAccount").textContent =
        group.master_account ? group.master_account.subdomain : "Não definida";
      document.getElementById("slaveCount").textContent = group.slave_accounts
        ? group.slave_accounts.length
        : 0;

      // Mostrar informações
      document.getElementById("groupInfo").style.display = "block";

      addLog(`Detalhes do grupo "${group.name}" carregados`);
    } else {
      addLog("Erro ao carregar detalhes do grupo", "error");
    }
  } catch (error) {
    addLog(`Erro ao carregar detalhes do grupo: ${error.message}`, "error");
  }
}

// Mostrar detalhes do grupo
function showGroupDetails() {
  if (currentGroupId) {
    loadGroupDetails(currentGroupId);
  }
}

// Esconder informações do grupo
function hideGroupInfo() {
  document.getElementById("groupInfo").style.display = "none";
}

// Mostrar modal de criação de grupo
async function showCreateGroupModal() {
  // Carregar contas mestres disponíveis
  await loadMasterAccounts();

  // Limpar formulário
  document.getElementById("groupNameInput").value = "";
  document.getElementById("groupDescriptionInput").value = "";
  document.getElementById("masterAccountSelect").selectedIndex = 0;

  // Mostrar modal
  document.getElementById("createGroupModal").style.display = "flex";
}

// Esconder modal de criação de grupo
function hideCreateGroupModal() {
  document.getElementById("createGroupModal").style.display = "none";
}

// Carregar contas mestres disponíveis
async function loadMasterAccounts() {
  try {
    const response = await fetch(buildApiUrl("/sync/accounts"));
    if (response.ok) {
      const data = await response.json();
      const accounts = data.accounts || [];

      // Filtrar contas que podem ser mestres
      masterAccounts = accounts.filter(
        (account) =>
          account.account_role === "master" ||
          account.is_master ||
          !account.sync_group_id
      );

      // Atualizar select
      const masterSelect = document.getElementById("masterAccountSelect");
      masterSelect.innerHTML =
        '<option value="">Selecione uma conta mestre...</option>';

      masterAccounts.forEach((account) => {
        const option = document.createElement("option");
        option.value = account.id;
        option.textContent = `${account.subdomain} (${account.status})`;
        masterSelect.appendChild(option);
      });
    } else {
      addLog("Erro ao carregar contas mestres", "error");
    }
  } catch (error) {
    addLog(`Erro ao carregar contas mestres: ${error.message}`, "error");
  }
}

// Criar novo grupo
async function createGroup() {
  const name = document.getElementById("groupNameInput").value.trim();
  const description = document
    .getElementById("groupDescriptionInput")
    .value.trim();
  const masterAccountId = document.getElementById("masterAccountSelect").value;

  if (!name) {
    showAlert("Por favor, insira um nome para o grupo", "error");
    return;
  }

  try {
    const response = await fetch(buildApiUrl("/groups"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: name,
        description: description || null,
        master_account_id: masterAccountId || null,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      showAlert(`Grupo "${name}" criado com sucesso!`, "success");
      hideCreateGroupModal();

      // Atualizar lista de grupos
      await refreshGroups();

      // Selecionar o novo grupo
      document.getElementById("groupSelect").value = data.group.id;
      currentGroupId = data.group.id;
      loadGroupDetails(currentGroupId);
      document.getElementById("detailsBtn").disabled = false;
      document.getElementById("syncGroupBtn").disabled = false;

      addLog(`Grupo "${name}" criado com ID: ${data.group.id}`);
    } else {
      const errorData = await response.json();
      showAlert(`Erro ao criar grupo: ${errorData.error}`, "error");
    }
  } catch (error) {
    showAlert(`Erro ao criar grupo: ${error.message}`, "error");
  }
}

// Sincronizar grupo específico
async function syncGroup() {
  if (!currentGroupId) {
    showAlert("Nenhum grupo selecionado", "error");
    return;
  }

  if (syncInProgress) {
    showAlert("Uma sincronização já está em andamento", "warning");
    return;
  }

  try {
    // Obter configurações de lote
    const batchConfig = {
      batch_size: parseInt(document.getElementById("batchSize").value),
      batch_delay: parseFloat(document.getElementById("batchDelay").value),
      max_concurrent: parseInt(document.getElementById("maxConcurrent").value),
    };

    const response = await fetch(
      buildApiUrl(`/groups/${currentGroupId}/sync`),
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          sync_type: "full",
          batch_config: batchConfig,
        }),
      }
    );

    if (response.ok) {
      const data = await response.json();
      showAlert("Sincronização do grupo iniciada!", "success");
      addLog(`Sincronização do grupo iniciada: ${data.message}`);

      // Iniciar monitoramento
      syncInProgress = true;
      currentSyncType = "group";
      startStatusMonitoring();
    } else {
      const errorData = await response.json();
      showAlert(`Erro ao iniciar sincronização: ${errorData.error}`, "error");
    }
  } catch (error) {
    showAlert(`Erro ao sincronizar grupo: ${error.message}`, "error");
  }
}

// Fechar modal ao clicar fora dele
document.addEventListener("click", function (event) {
  const createGroupModal = document.getElementById("createGroupModal");
  const createMasterModal = document.getElementById("createMasterAccountModal");

  if (event.target === createGroupModal) {
    hideCreateGroupModal();
  }

  if (event.target === createMasterModal) {
    hideCreateMasterAccountModal();
  }
});

// Fechar modal com ESC
document.addEventListener("keydown", function (event) {
  if (event.key === "Escape") {
    hideCreateGroupModal();
    hideCreateMasterAccountModal();
  }
});

// ========================= FUNÇÕES DE CRIAÇÃO DE CONTA MESTRE =========================

// Mostrar modal de criação de conta mestre
function showCreateMasterAccountModal() {
  // Limpar formulário
  document.getElementById("masterSubdomainInput").value = "";
  document.getElementById("masterRefreshTokenInput").value = "";
  document.getElementById("testConnectionCheckbox").checked = true;

  // Mostrar modal
  document.getElementById("createMasterAccountModal").style.display = "flex";
}

// Esconder modal de criação de conta mestre
function hideCreateMasterAccountModal() {
  document.getElementById("createMasterAccountModal").style.display = "none";
}

// Criar nova conta mestre
async function createMasterAccount() {
  const subdomain = document
    .getElementById("masterSubdomainInput")
    .value.trim();
  const refreshToken = document
    .getElementById("masterRefreshTokenInput")
    .value.trim();
  const testConnection = document.getElementById(
    "testConnectionCheckbox"
  ).checked;

  if (!subdomain) {
    showAlert("Por favor, insira o subdomínio", "error");
    return;
  }

  if (!refreshToken) {
    showAlert("Por favor, insira o refresh token", "error");
    return;
  }

  try {
    // Mostrar loading
    const createBtn = document.querySelector(
      "#createMasterAccountModal .btn-primary"
    );
    const originalText = createBtn.innerHTML;
    createBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Criando...';
    createBtn.disabled = true;

    // Criar conta
    const response = await fetch(buildApiUrl("/sync/accounts"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        subdomain: subdomain,
        refresh_token: refreshToken,
        is_master: true,
      }),
    });

    if (response.ok) {
      const data = await response.json();

      // Testar conexão se solicitado
      if (testConnection) {
        try {
          createBtn.innerHTML =
            '<i class="fas fa-spinner fa-spin"></i> Testando conexão...';

          const testResponse = await fetch(
            `/api/sync/accounts/${data.account_id}/test`
          );
          const testData = await testResponse.json();

          if (!testData.success) {
            showAlert(
              "Conta criada, mas falha no teste de conexão. Verifique o refresh token.",
              "warning"
            );
          } else {
            showAlert(
              `Conta mestre "${subdomain}" criada e testada com sucesso!`,
              "success"
            );
          }
        } catch (testError) {
          showAlert("Conta criada, mas erro ao testar conexão", "warning");
        }
      } else {
        showAlert(`Conta mestre "${subdomain}" criada com sucesso!`, "success");
      }

      // Fechar modal
      hideCreateMasterAccountModal();

      // Recarregar lista de contas mestres no modal de grupo
      await loadMasterAccounts();

      // Selecionar a nova conta no select
      const masterSelect = document.getElementById("masterAccountSelect");
      masterSelect.value = data.account_id;

      addLog(
        `Conta mestre "${subdomain}" adicionada com ID: ${data.account_id}`
      );
    } else {
      const errorData = await response.json();
      showAlert(`Erro ao criar conta: ${errorData.error}`, "error");
    }
  } catch (error) {
    showAlert(`Erro ao criar conta: ${error.message}`, "error");
  } finally {
    // Restaurar botão
    const createBtn = document.querySelector(
      "#createMasterAccountModal .btn-primary"
    );
    createBtn.innerHTML = '<i class="fas fa-save"></i> Adicionar Conta';
    createBtn.disabled = false;
  }
}

// ========================================
// VISUALIZAÇÃO DE CONTAS MASTER E ESCRAVAS
// ========================================

let accountsOverviewData = [];
let isCompactView = true;

// Carregar visão geral das contas
async function refreshAccountsOverview() {
  try {
    const response = await fetch(buildApiUrl("/groups/overview"));
    if (response.ok) {
      const data = await response.json();
      accountsOverviewData = data.groups || [];
      renderAccountsOverview();
      updateOverviewStats(data);
      addLog("Visão geral de contas atualizada");
    } else {
      addLog("Erro ao carregar visão geral de contas", "error");
    }
  } catch (error) {
    addLog(`Erro ao carregar visão geral: ${error.message}`, "error");
  }
}

// Atualizar estatísticas gerais
function updateOverviewStats(data) {
  // Você pode adicionar elementos para mostrar estatísticas gerais aqui
  if (data.total_groups > 0) {
    addLog(
      `📊 Estatísticas: ${data.total_groups} grupos, ${
        data.total_master_accounts
      } masters, ${data.total_slave_accounts} escravas, ${formatNumber(
        data.total_contacts
      )} contatos`
    );
  }
}

// Renderizar a visão geral das contas
function renderAccountsOverview() {
  const container = document.getElementById("accountsOverviewContainer");

  if (!container) {
    console.error("Container accountsOverviewContainer não encontrado");
    return;
  }

  // Aplicar classe do modo de visualização
  container.className = `accounts-container ${
    isCompactView ? "compact" : "expanded"
  }`;

  if (accountsOverviewData.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-network-wired"></i>
        <h3>Nenhum grupo encontrado</h3>
        <p>Crie seu primeiro grupo com contas master e escravas</p>
        <button class="btn btn-primary" onclick="showCreateGroupModal()">
          <i class="fas fa-plus"></i> Criar Primeiro Grupo
        </button>
      </div>
    `;
    return;
  }

  // Renderizar grupos com suas contas
  container.innerHTML = accountsOverviewData
    .map((group) => renderMasterAccountCard(group))
    .join("");
}

// Renderizar card de conta master
function renderMasterAccountCard(group) {
  const masterAccount = group.master_account;
  const slaveAccounts = group.slave_accounts || [];
  const totalContacts = group.total_contacts || 0;
  const lastSync = group.last_sync ? formatLastSync(group.last_sync) : "Nunca";

  return `
    <div class="master-account-card">
      <div class="master-header">
        <div class="master-title">
          <i class="fas fa-crown"></i>
          <span>${
            masterAccount ? masterAccount.subdomain : "Conta não definida"
          }</span>
        </div>
        <div class="master-status ${
          masterAccount && masterAccount.status === "active"
            ? "online"
            : "offline"
        }">
          ${
            masterAccount && masterAccount.status === "active"
              ? "Ativa"
              : "Inativa"
          }
        </div>
      </div>

      <div class="master-info">
        <div class="info-item">
          <div class="info-label">Grupo</div>
          <div class="info-value">${group.name}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Contas Escravas</div>
          <div class="info-value">${slaveAccounts.length}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Total Contatos</div>
          <div class="info-value">${formatNumber(totalContacts)}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Última Sync</div>
          <div class="info-value">${lastSync}</div>
        </div>
      </div>

      ${
        slaveAccounts.length > 0
          ? `
        <div class="slave-accounts">
          <div class="slave-accounts-header">
            <div class="slave-accounts-title">
              <i class="fas fa-users"></i>
              Contas Escravas
              <span class="slave-count-badge">${slaveAccounts.length}</span>
            </div>
            ${
              slaveAccounts.length > 4
                ? `
              <button class="btn btn-sm btn-secondary" onclick="showAllSlaveAccounts(${group.id}, '${group.name}')">
                <i class="fas fa-expand"></i> Ver todas
              </button>
            `
                : ""
            }
          </div>
          <div class="slave-accounts-grid">
            ${slaveAccounts
              .slice(0, 4)
              .map((slave) => renderSlaveAccountItem(slave))
              .join("")}
            ${
              slaveAccounts.length > 4
                ? `
              <div class="slave-account-item more-accounts">
                <div class="more-accounts-content">
                  <i class="fas fa-plus-circle"></i>
                  <div class="more-accounts-text">
                    +${slaveAccounts.length - 4} contas
                  </div>
                  <button class="btn btn-sm btn-link" onclick="showAllSlaveAccounts(${
                    group.id
                  }, '${group.name}')">
                    Ver todas
                  </button>
                </div>
              </div>
            `
                : ""
            }
          </div>
        </div>
      `
          : `
        <div class="slave-accounts">
          <div class="no-accounts-message">
            <i class="fas fa-info-circle"></i>
            Nenhuma conta escrava adicionada ainda
            <button class="btn btn-sm btn-primary" onclick="showAddSlaveModal(${group.id})" style="margin-top: 10px;">
              <i class="fas fa-plus"></i> Adicionar Primeira Conta
            </button>
          </div>
        </div>
      `
      }
    </div>
  `;
}

// Renderizar item de conta escrava
function renderSlaveAccountItem(slave) {
  const status = getAccountStatusFromData(slave);
  const contactCount = slave.contact_count || 0;

  return `
    <div class="slave-account-item">
      <div class="slave-account-name">
        <i class="fas fa-user"></i>
        ${slave.subdomain}
      </div>
      <div class="slave-account-status">
        ${formatNumber(contactCount)} contatos
      </div>
      <div class="slave-account-status">
        Status: ${status}
      </div>
    </div>
  `;
}

// Obter status da conta pelos dados
function getAccountStatusFromData(account) {
  if (account.status === "inactive") return "Inativa";
  if (!account.last_sync) return "Nunca sincronizado";

  const lastSync = new Date(account.last_sync);
  const now = new Date();
  const diffHours = (now - lastSync) / (1000 * 60 * 60);

  if (diffHours < 1) return "Recente";
  if (diffHours < 24) return `${Math.floor(diffHours)}h atrás`;
  if (diffHours < 168) return `${Math.floor(diffHours / 24)}d atrás`;
  return "Desatualizado";
}

// Formatar última sincronização
function formatLastSync(lastSync) {
  if (!lastSync.started_at) return "Nunca";

  const startDate = new Date(lastSync.started_at);
  const now = new Date();
  const diffHours = (now - startDate) / (1000 * 60 * 60);

  let timeStr;
  if (diffHours < 1) timeStr = "Agora";
  else if (diffHours < 24) timeStr = `${Math.floor(diffHours)}h atrás`;
  else if (diffHours < 168) timeStr = `${Math.floor(diffHours / 24)}d atrás`;
  else timeStr = "Há muito tempo";

  const statusIcon =
    lastSync.status === "completed"
      ? "✅"
      : lastSync.status === "running"
      ? "🔄"
      : "❌";

  return `${statusIcon} ${timeStr}`;
}

// Alternar modo de visualização
function toggleViewMode() {
  isCompactView = !isCompactView;
  const viewModeText = document.getElementById("viewModeText");
  if (viewModeText) {
    viewModeText.textContent = isCompactView
      ? "Modo Expandido"
      : "Modo Compacto";
  }
  renderAccountsOverview();
  addLog(
    `Modo de visualização alterado para: ${
      isCompactView ? "Compacto" : "Expandido"
    }`
  );
}

// Formatar números
function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toString();
}

// Mostrar modal para adicionar conta escrava
function showAddSlaveModal(groupId) {
  showAlert(
    `Para adicionar contas escravas ao grupo, use a seção "Gerenciamento de Grupos" abaixo e selecione o grupo desejado.`,
    "info"
  );

  // Selecionar o grupo automaticamente
  const groupSelect = document.getElementById("groupSelect");
  if (groupSelect) {
    groupSelect.value = groupId;
    // Trigger change event
    const event = new Event("change");
    groupSelect.dispatchEvent(event);
  }
}

// Validar subdomínio em tempo real
document.addEventListener("DOMContentLoaded", function () {
  const subdomainInput = document.getElementById("masterSubdomainInput");
  if (subdomainInput) {
    subdomainInput.addEventListener("input", function () {
      let value = this.value;

      // Remover caracteres especiais e espaços
      value = value.replace(/[^a-zA-Z0-9-]/g, "");

      // Remover .kommo.com se o usuário digitou
      value = value.replace(/\.kommo\.com.*$/i, "");

      this.value = value;
    });
  }

  // Inicializar visualização de contas
  refreshAccountsOverview();
});

// Atualizar automaticamente a visualização de contas
setInterval(refreshAccountsOverview, 60000); // A cada minuto

// ========================================
// MODAL PARA TODAS AS CONTAS ESCRAVAS
// ========================================

let currentGroupSlaveAccounts = [];

// Mostrar modal com todas as contas escravas
function showAllSlaveAccounts(groupId, groupName) {
  // Buscar os dados do grupo
  const group = accountsOverviewData.find((g) => g.id === groupId);
  if (!group) {
    showAlert("Grupo não encontrado", "error");
    return;
  }

  currentGroupSlaveAccounts = group.slave_accounts || [];

  // Atualizar título do modal
  const title = document.getElementById("slaveModalTitle");
  if (title) {
    title.textContent = `Todas as Contas Escravas - ${groupName}`;
  }

  // Renderizar todas as contas
  renderAllSlaveAccounts();

  // Mostrar modal
  const modal = document.getElementById("allSlaveAccountsModal");
  if (modal) {
    modal.style.display = "flex";
  }
}

// Esconder modal de todas as contas escravas
function hideAllSlaveAccountsModal() {
  const modal = document.getElementById("allSlaveAccountsModal");
  if (modal) {
    modal.style.display = "none";
  }
  currentGroupSlaveAccounts = [];
}

// Renderizar todas as contas escravas no modal
function renderAllSlaveAccounts() {
  const container = document.getElementById("allSlaveAccountsList");
  if (!container) return;

  if (currentGroupSlaveAccounts.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 40px; color: #6c757d;">
        <i class="fas fa-users" style="font-size: 3rem; margin-bottom: 15px; opacity: 0.5;"></i>
        <h3>Nenhuma conta escrava</h3>
        <p>Este grupo ainda não possui contas escravas configuradas.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = currentGroupSlaveAccounts
    .map(
      (slave) => `
    <div class="slave-detail-card">
      <div class="slave-detail-header">
        <i class="fas fa-user" style="color: #6c757d;"></i>
        <div class="slave-detail-name">${slave.subdomain}</div>
      </div>
      <div class="slave-detail-info">
        <div class="slave-info-item">
          <div class="slave-info-label">Contatos</div>
          <div class="slave-info-value">${formatNumber(
            slave.contact_count || 0
          )}</div>
        </div>
        <div class="slave-info-item">
          <div class="slave-info-label">Status</div>
          <div class="slave-info-value">${getAccountStatusFromData(slave)}</div>
        </div>
        <div class="slave-info-item">
          <div class="slave-info-label">Última Sync</div>
          <div class="slave-info-value">${
            slave.last_sync ? formatDate(slave.last_sync) : "Nunca"
          }</div>
        </div>
        <div class="slave-info-item">
          <div class="slave-info-label">Criada em</div>
          <div class="slave-info-value">${formatDate(slave.created_at)}</div>
        </div>
      </div>
    </div>
  `
    )
    .join("");
}

// Formatar data para exibição
function formatDate(dateString) {
  if (!dateString) return "Não disponível";

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Hoje";
  if (diffDays === 1) return "Ontem";
  if (diffDays < 7) return `${diffDays} dias atrás`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} semanas atrás`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} meses atrás`;

  return date.toLocaleDateString("pt-BR");
}

// Fechar modal ao clicar fora
document.addEventListener("click", function (event) {
  const modal = document.getElementById("allSlaveAccountsModal");
  if (modal && event.target === modal) {
    hideAllSlaveAccountsModal();
  }
});

// Fechar modal com ESC
document.addEventListener("keydown", function (event) {
  if (event.key === "Escape") {
    hideAllSlaveAccountsModal();
  }
});

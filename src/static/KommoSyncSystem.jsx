import React, { useState, useEffect } from 'react';

// Componente do Header
const Header = () => (
  <header className="text-center text-white mb-8">
    <h1 className="text-4xl font-bold mb-3 drop-shadow-lg">
      <i className="fas fa-sync-alt mr-3"></i>
      Kommo Sync System
    </h1>
    <p className="text-lg opacity-90">
      Sistema de Sincronização Avançado com Processamento em Lotes
    </p>
  </header>
);

// Componente de Configurações de Lote
const BatchConfig = ({ batchSize, setBatchSize, batchDelay, setBatchDelay, maxConcurrent, setMaxConcurrent }) => (
  <div className="bg-white rounded-2xl p-6 mb-6 shadow-xl backdrop-blur-sm border border-white/20">
    <h2 className="text-gray-600 mb-5 text-xl font-semibold flex items-center gap-3">
      <i className="fas fa-cogs"></i>
      Configurações de Lote
    </h2>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
      <div className="flex flex-col gap-2">
        <label htmlFor="batchSize" className="font-semibold text-gray-600">
          Tamanho do Lote:
        </label>
        <input
          type="number"
          id="batchSize"
          min="1"
          max="100"
          value={batchSize}
          onChange={(e) => setBatchSize(e.target.value)}
          className="p-3 border-2 border-gray-200 rounded-lg text-base transition-colors focus:outline-none focus:border-indigo-500"
        />
        <span className="text-sm text-gray-500 italic">
          Quantos itens processar por vez
        </span>
      </div>
      <div className="flex flex-col gap-2">
        <label htmlFor="batchDelay" className="font-semibold text-gray-600">
          Delay entre Lotes (segundos):
        </label>
        <input
          type="number"
          id="batchDelay"
          min="0"
          max="60"
          step="0.5"
          value={batchDelay}
          onChange={(e) => setBatchDelay(e.target.value)}
          className="p-3 border-2 border-gray-200 rounded-lg text-base transition-colors focus:outline-none focus:border-indigo-500"
        />
        <span className="text-sm text-gray-500 italic">
          Tempo de espera entre lotes para não sobrecarregar
        </span>
      </div>
      <div className="flex flex-col gap-2">
        <label htmlFor="maxConcurrent" className="font-semibold text-gray-600">
          Contas Simultâneas:
        </label>
        <input
          type="number"
          id="maxConcurrent"
          min="1"
          max="10"
          value={maxConcurrent}
          onChange={(e) => setMaxConcurrent(e.target.value)}
          className="p-3 border-2 border-gray-200 rounded-lg text-base transition-colors focus:outline-none focus:border-indigo-500"
        />
        <span className="text-sm text-gray-500 italic">
          Quantas contas sincronizar ao mesmo tempo
        </span>
      </div>
    </div>
  </div>
);

// Componente de Status da Sincronização
const SyncStatus = ({ status, progress, currentOperation, currentBatch, estimatedTime }) => (
  <div className="bg-white rounded-2xl p-6 mb-6 shadow-xl backdrop-blur-sm border border-white/20">
    <h2 className="text-gray-600 mb-5 text-xl font-semibold flex items-center gap-3">
      <i className="fas fa-chart-line"></i>
      Status da Sincronização
    </h2>
    <div className="space-y-4">
      <div className="flex justify-between items-center py-3 border-b border-gray-200">
        <span className="font-semibold text-gray-600">Status:</span>
        <span className="text-gray-800 font-medium">{status}</span>
      </div>
      <div className="flex justify-between items-center py-3 border-b border-gray-200">
        <span className="font-semibold text-gray-600">Progresso:</span>
        <div className="flex items-center gap-3 flex-1 max-w-xs">
          <div className="flex-1 h-5 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <span className="font-semibold text-gray-600 min-w-[45px]">{progress}%</span>
        </div>
      </div>
      <div className="flex justify-between items-center py-3 border-b border-gray-200">
        <span className="font-semibold text-gray-600">Operação Atual:</span>
        <span className="text-gray-800 font-medium">{currentOperation}</span>
      </div>
      <div className="flex justify-between items-center py-3 border-b border-gray-200">
        <span className="font-semibold text-gray-600">Lote:</span>
        <span className="text-gray-800 font-medium">{currentBatch}</span>
      </div>
      <div className="flex justify-between items-center py-3">
        <span className="font-semibold text-gray-600">Tempo Estimado:</span>
        <span className="text-gray-800 font-medium">{estimatedTime}</span>
      </div>
    </div>
  </div>
);

// Componente de Botão
const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'normal', 
  onClick, 
  disabled = false, 
  icon, 
  className = '',
  style = {}
}) => {
  const baseClasses = "px-6 py-3 border-none rounded-lg cursor-pointer font-semibold text-sm transition-all inline-flex items-center gap-2 text-decoration-none m-1";
  
  const variants = {
    primary: "bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:-translate-y-0.5 hover:shadow-lg hover:shadow-indigo-400/40",
    secondary: "bg-gray-50 text-gray-600 border-2 border-gray-200 hover:bg-gray-100 hover:border-gray-300",
    danger: "bg-gradient-to-r from-red-500 to-red-600 text-white hover:-translate-y-0.5 hover:shadow-lg hover:shadow-red-400/40",
    outline: "bg-transparent border-2 border-indigo-500 text-indigo-500 hover:bg-indigo-500 hover:text-white",
    'primary-large': "bg-gradient-to-r from-green-500 to-green-600 text-white text-base px-8 py-4 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-green-400/40"
  };
  
  const sizes = {
    small: "px-3 py-1.5 text-xs",
    normal: "px-6 py-3 text-sm",
    large: "px-8 py-4 text-base"
  };
  
  const disabledClasses = disabled ? "opacity-60 cursor-not-allowed transform-none shadow-none" : "";
  
  return (
    <button
      className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${disabledClasses} ${className}`}
      onClick={onClick}
      disabled={disabled}
      style={style}
    >
      {icon && <i className={icon}></i>}
      {children}
    </button>
  );
};

// Componente de Ações de Sincronização
const SyncActions = ({ onSync, onStop, syncInProgress }) => (
  <div className="bg-white rounded-2xl p-6 mb-6 shadow-xl backdrop-blur-sm border border-white/20">
    <h2 className="text-gray-600 mb-5 text-xl font-semibold flex items-center gap-3">
      <i className="fas fa-play"></i>
      Ações de Sincronização
    </h2>
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <Button
        variant="primary"
        onClick={() => onSync('full')}
        icon="fas fa-sync-alt"
        disabled={syncInProgress}
      >
        Sincronizar Tudo em Lotes
      </Button>
      <Button
        variant="secondary"
        onClick={() => onSync('pipelines')}
        icon="fas fa-sitemap"
        disabled={syncInProgress}
      >
        Sincronizar Pipelines
      </Button>
      <Button
        variant="secondary"
        onClick={() => onSync('field_groups')}
        icon="fas fa-folder"
        disabled={syncInProgress}
      >
        Sincronizar Grupos
      </Button>
      <Button
        variant="secondary"
        onClick={() => onSync('custom_fields')}
        icon="fas fa-tags"
        disabled={syncInProgress}
      >
        Sincronizar Campos
      </Button>
      <Button
        variant="secondary"
        onClick={() => onSync('required_statuses')}
        icon="fas fa-exclamation-triangle"
        disabled={syncInProgress}
      >
        Sincronizar Required Status
      </Button>
      {syncInProgress && (
        <Button
          variant="danger"
          onClick={onStop}
          icon="fas fa-stop"
        >
          Parar Sincronização
        </Button>
      )}
    </div>
  </div>
);

// Componente de Item de Conta
const AccountItem = ({ account, onAction }) => (
  <div className="bg-white p-4 rounded-lg mb-3 shadow-sm flex justify-between items-center">
    <div className="flex-1">
      <div className="font-semibold text-gray-800">{account.subdomain}</div>
      <div className="text-sm text-gray-600">{account.info}</div>
    </div>
    <div className="flex items-center gap-2">
      <span className={`px-2 py-1 rounded text-xs font-semibold uppercase ${
        account.status === 'online' ? 'bg-green-200 text-green-800' :
        account.status === 'offline' ? 'bg-red-200 text-red-800' :
        'bg-pink-200 text-pink-800'
      }`}>
        {account.status}
      </span>
      <div className="flex gap-1">
        <Button size="small" onClick={() => onAction('edit', account)}>
          Editar
        </Button>
        <Button size="small" variant="danger" onClick={() => onAction('delete', account)}>
          Remover
        </Button>
      </div>
    </div>
  </div>
);

// Componente de Múltiplas Contas
const MultiAccountSection = ({ accounts, onRefresh, onSync, onAccountAction, syncParallel, setSyncParallel, continueOnError, setContinueOnError }) => (
  <div className="bg-white rounded-2xl p-6 mb-6 shadow-xl backdrop-blur-sm border border-white/20">
    <h2 className="text-gray-600 mb-5 text-xl font-semibold flex items-center gap-3">
      <i className="fas fa-users"></i>
      Sincronização com Múltiplas Contas
    </h2>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div className="bg-gray-50 p-5 rounded-xl">
        <h3 className="mb-4 text-gray-600 font-medium">Contas Escravas Configuradas:</h3>
        <div className="max-h-80 overflow-y-auto">
          {accounts.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              Nenhuma conta configurada
            </div>
          ) : (
            accounts.map((account, index) => (
              <AccountItem 
                key={index} 
                account={account} 
                onAction={onAccountAction}
              />
            ))
          )}
        </div>
        <Button variant="outline" onClick={onRefresh} icon="fas fa-refresh">
          Atualizar Lista
        </Button>
      </div>
      <div className="flex flex-col gap-5">
        <Button
          variant="primary-large"
          onClick={onSync}
          icon="fas fa-network-wired"
        >
          Sincronizar Todas as Contas
        </Button>
        <div className="flex flex-col gap-3">
          <label className="flex items-center gap-2 cursor-pointer text-gray-600">
            <input
              type="checkbox"
              checked={syncParallel}
              onChange={(e) => setSyncParallel(e.target.checked)}
              className="w-4 h-4"
            />
            Sincronização Paralela (mais rápido)
          </label>
          <label className="flex items-center gap-2 cursor-pointer text-gray-600">
            <input
              type="checkbox"
              checked={continueOnError}
              onChange={(e) => setContinueOnError(e.target.checked)}
              className="w-4 h-4"
            />
            Continuar mesmo com erros
          </label>
        </div>
      </div>
    </div>
  </div>
);

// Componente de Logs
const LogsSection = ({ logs, onClear, onDownload }) => (
  <div className="bg-white rounded-2xl p-6 mb-6 shadow-xl backdrop-blur-sm border border-white/20">
    <h2 className="text-gray-600 mb-5 text-xl font-semibold flex items-center gap-3">
      <i className="fas fa-list-alt"></i>
      Logs da Sincronização
    </h2>
    <div className="bg-gray-900 rounded-xl overflow-hidden">
      <div className="bg-gray-800 p-4 flex justify-between items-center">
        <span className="text-white font-semibold">Console de Logs</span>
        <div className="flex gap-2">
          <Button size="small" onClick={onClear} icon="fas fa-trash">
            Limpar
          </Button>
          <Button size="small" onClick={onDownload} icon="fas fa-download">
            Baixar
          </Button>
        </div>
      </div>
      <div className="p-5 font-mono text-sm text-gray-200 max-h-96 overflow-y-auto whitespace-pre-wrap leading-relaxed">
        {logs || "Sistema pronto para sincronização..."}
      </div>
    </div>
  </div>
);

// Componente de Card de Estatística
const StatCard = ({ title, value, icon, gradient }) => (
  <div className={`${gradient} text-white p-5 rounded-xl text-center`}>
    <div className="flex items-center justify-center gap-2 mb-3">
      <i className={icon}></i>
      <h3 className="text-lg font-medium">{title}</h3>
    </div>
    <div className="text-xl font-semibold">{value}</div>
  </div>
);

// Componente de Estatísticas
const StatsSection = ({ stats }) => (
  <div className="bg-white rounded-2xl p-6 mb-6 shadow-xl backdrop-blur-sm border border-white/20">
    <h2 className="text-gray-600 mb-5 text-xl font-semibold flex items-center gap-3">
      <i className="fas fa-chart-bar"></i>
      Estatísticas
    </h2>
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
      <StatCard
        title="Pipelines"
        value={stats.pipelines}
        icon="fas fa-sitemap"
        gradient="bg-gradient-to-br from-blue-500 to-blue-600"
      />
      <StatCard
        title="Grupos de Campos"
        value={stats.groups}
        icon="fas fa-folder"
        gradient="bg-gradient-to-br from-green-500 to-green-600"
      />
      <StatCard
        title="Campos Personalizados"
        value={stats.fields}
        icon="fas fa-tags"
        gradient="bg-gradient-to-br from-purple-500 to-purple-600"
      />
      <StatCard
        title="Tempo Total"
        value={stats.time}
        icon="fas fa-clock"
        gradient="bg-gradient-to-br from-orange-500 to-orange-600"
      />
    </div>
  </div>
);

// Componente Principal
const KommoSyncSystem = () => {
  // Estados
  const [batchSize, setBatchSize] = useState('10');
  const [batchDelay, setBatchDelay] = useState('2.0');
  const [maxConcurrent, setMaxConcurrent] = useState('3');
  const [syncStatus, setSyncStatus] = useState('Aguardando');
  const [progress, setProgress] = useState(0);
  const [currentOperation, setCurrentOperation] = useState('-');
  const [currentBatch, setCurrentBatch] = useState('-');
  const [estimatedTime, setEstimatedTime] = useState('-');
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [logs, setLogs] = useState('');
  const [accounts, setAccounts] = useState([]);
  const [syncParallel, setSyncParallel] = useState(true);
  const [continueOnError, setContinueOnError] = useState(true);
  const [stats, setStats] = useState({
    pipelines: '0 criados, 0 atualizados',
    groups: '0 criados, 0 atualizados',
    fields: '0 criados, 0 atualizados',
    time: '0 segundos'
  });

  // Funções
  const handleSync = async (syncType) => {
    setSyncInProgress(true);
    setSyncStatus('Iniciando...');
    setCurrentOperation(`Sincronização ${syncType}`);
    
    // Simular sincronização
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 200));
      setProgress(i);
      setCurrentBatch(`${Math.floor(i/10) + 1}/10`);
    }
    
    setSyncInProgress(false);
    setSyncStatus('Concluído');
    setLogs(prev => prev + `\n[${new Date().toLocaleTimeString()}] Sincronização ${syncType} concluída com sucesso!`);
  };

  const handleStop = () => {
    setSyncInProgress(false);
    setSyncStatus('Parado');
    setLogs(prev => prev + `\n[${new Date().toLocaleTimeString()}] Sincronização interrompida pelo usuário.`);
  };

  const handleRefreshAccounts = () => {
    // Simular carregamento de contas
    setAccounts([
      { subdomain: 'conta1.kommo.com', status: 'online', info: 'Última sync: 2 min atrás' },
      { subdomain: 'conta2.kommo.com', status: 'offline', info: 'Última sync: 1 hora atrás' },
      { subdomain: 'conta3.kommo.com', status: 'error', info: 'Erro na última sync' }
    ]);
  };

  const handleMultiAccountSync = () => {
    handleSync('múltiplas contas');
  };

  const handleAccountAction = (action, account) => {
    setLogs(prev => prev + `\n[${new Date().toLocaleTimeString()}] Ação ${action} realizada na conta ${account.subdomain}`);
  };

  const handleClearLogs = () => {
    setLogs('');
  };

  const handleDownloadLogs = () => {
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'kommo-sync-logs.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  // Carregar contas na inicialização
  useEffect(() => {
    handleRefreshAccounts();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-600 to-purple-700">
      <div className="max-w-7xl mx-auto p-5">
        <Header />
        
        <BatchConfig
          batchSize={batchSize}
          setBatchSize={setBatchSize}
          batchDelay={batchDelay}
          setBatchDelay={setBatchDelay}
          maxConcurrent={maxConcurrent}
          setMaxConcurrent={setMaxConcurrent}
        />
        
        <SyncStatus
          status={syncStatus}
          progress={progress}
          currentOperation={currentOperation}
          currentBatch={currentBatch}
          estimatedTime={estimatedTime}
        />
        
        <SyncActions
          onSync={handleSync}
          onStop={handleStop}
          syncInProgress={syncInProgress}
        />
        
        <MultiAccountSection
          accounts={accounts}
          onRefresh={handleRefreshAccounts}
          onSync={handleMultiAccountSync}
          onAccountAction={handleAccountAction}
          syncParallel={syncParallel}
          setSyncParallel={setSyncParallel}
          continueOnError={continueOnError}
          setContinueOnError={setContinueOnError}
        />
        
        <LogsSection
          logs={logs}
          onClear={handleClearLogs}
          onDownload={handleDownloadLogs}
        />
        
        <StatsSection stats={stats} />
      </div>
    </div>
  );
};

export default KommoSyncSystem;

#!/usr/bin/env python3
"""
🔍 DIAGNÓSTICO: Análise dos IDs problemáticos em Roles Sync

Baseado nos logs reais, vamos analisar os padrões dos IDs
para entender se alguns IDs estão sendo incorretamente
identificados como master quando são da slave.

LOGS ANALISADOS:
❌ Status 63288851 não encontrado nos mapeamentos  
❌ Status 89684595 não encontrado nos mapeamentos
❌ Status 89686887 não encontrado nos mapeamentos (mas está na lista!)
❌ Status 89765891 não encontrado nos mapeamentos

✅ Status 63288855->89317579 (funcionou)
✅ Status 89774811->89775163 (funcionou)
"""

def analyze_status_ids():
    print("🔍 DIAGNÓSTICO: Análise dos IDs de Status")
    print("=" * 60)
    
    # IDs que falharam
    failed_ids = [63288851, 89684595, 89686887, 89765891]
    
    # IDs que funcionaram (master)
    working_master_ids = [63288855, 89774811, 89775999, 89776867, 89776871]
    
    # IDs que funcionaram (slave) 
    working_slave_ids = [89317579, 89775163, 89776043, 89776895, 90595635]
    
    # Mapeamentos disponíveis no banco
    available_mappings = [
        63288855, 89526047, 63288859, 63288863, 63288867, 142, 143, 
        89684599, 89684603, 89684607, 89686891, 89687219, 89686895, 89686899, 
        89765967, 89765895, 89765899, 89765903, 89765971, 89774811, 89774815, 
        89774819, 89774823, 89775999, 89776003, 89776039, 89776007, 89776011, 
        89776867, 89776871, 89776875, 89776879, 89776883, 89776887, 90463103, 90463107
    ]
    
    print("\n📊 ANÁLISE DE PADRÕES:")
    
    # Analisar IDs que falharam
    print(f"\n❌ IDs que falharam ({len(failed_ids)}):")
    for fid in failed_ids:
        in_available = fid in available_mappings
        id_range = "63xxx" if str(fid).startswith("632") else "89xxx+"
        print(f"   • {fid} - Range: {id_range} - Nos mapeamentos: {'✅' if in_available else '❌'}")
    
    # Analisar IDs que funcionaram
    print(f"\n✅ IDs master que funcionaram ({len(working_master_ids)}):")
    for mid in working_master_ids:
        in_available = mid in available_mappings
        id_range = "63xxx" if str(mid).startswith("632") else "89xxx+"
        print(f"   • {mid} - Range: {id_range} - Nos mapeamentos: {'✅' if in_available else '❌'}")
    
    print(f"\n✅ IDs slave correspondentes ({len(working_slave_ids)}):")
    for sid in working_slave_ids:
        id_range = "89xxx" if str(sid).startswith("89") else "90xxx+"
        print(f"   • {sid} - Range: {id_range}")
    
    print("\n🎯 HIPÓTESES:")
    
    # Hipótese 1: IDs 89xxx da master
    master_89_ids = [fid for fid in failed_ids if str(fid).startswith("89")]
    if master_89_ids:
        print(f"\n🤔 HIPÓTESE 1: IDs 89xxx sendo tratados como master")
        print(f"   IDs problemáticos: {master_89_ids}")
        print("   💡 Estes deveriam ser IDs da SLAVE, não da MASTER!")
        print("   🔧 Possível causa: Role da master tem IDs da slave por engano")
    
    # Hipótese 2: IDs faltando nos mapeamentos
    print(f"\n🔍 HIPÓTESE 2: Verificar se 89686887 realmente está nos mapeamentos")
    if 89686887 in available_mappings:
        print("   ✅ 89686887 ESTÁ nos mapeamentos disponíveis!")
        print("   🚨 Mas ainda assim falhou - problema no código de busca?")
    else:
        print("   ❌ 89686887 NÃO está nos mapeamentos")
    
    # Hipótese 3: Padrões de ID
    print(f"\n📈 HIPÓTESE 3: Padrões de numeração")
    print("   • IDs 632xxxxx = Geralmente contas antigas (master)")
    print("   • IDs 896xxxxx = Geralmente contas novas (slave)")  
    print("   • IDs 897xxxxx = Geralmente contas novas (slave)")
    print("   • IDs 905xxxxx = Geralmente contas muito novas (slave)")
    
    print("\n🔧 RECOMENDAÇÕES:")
    print("1. Verificar origem dos status_rights na role master")
    print("2. Conferir se alguns IDs 89xxx não deveriam estar na role master")
    print("3. Investigar por que 89686887 falha mesmo estando disponível")
    print("4. Adicionar logs para mostrar a fonte dos status_rights")

if __name__ == '__main__':
    analyze_status_ids()

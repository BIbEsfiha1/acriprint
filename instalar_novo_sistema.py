#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
import datetime
import json
import sys

def criar_pasta_se_necessario(path):
    """Cria uma pasta se ela não existir"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        print(f"Pasta criada: {path}")

def fazer_backup(arquivo, pasta_backup):
    """Faz backup de um arquivo"""
    if os.path.exists(arquivo):
        nome_base = os.path.basename(arquivo)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        novo_nome = f"{nome_base}.{timestamp}.bak"
        destino = os.path.join(pasta_backup, novo_nome)
        
        shutil.copy2(arquivo, destino)
        print(f"Backup de {arquivo} criado em {destino}")
        return destino
    else:
        print(f"Arquivo {arquivo} não encontrado para backup")
        return None

def copiar_arquivo(origem, destino):
    """Copia um arquivo para o destino"""
    try:
        shutil.copy2(origem, destino)
        print(f"Arquivo copiado: {origem} -> {destino}")
        return True
    except Exception as e:
        print(f"Erro ao copiar arquivo: {str(e)}")
        return False

def criar_config_inicial(config_original, novo_config):
    """Cria um arquivo de configuração para o novo sistema baseado no original"""
    try:
        # Carregar configuração antiga se existir
        if os.path.exists(config_original):
            with open(config_original, 'r', encoding='utf-8') as f:
                config_antiga = json.load(f)
            
            # Extrair dados relevantes
            impressora_windows = config_antiga.get('impressora_windows', '')
            largura_papel = config_antiga.get('largura_papel', 32)
            porta_serial = config_antiga.get('porta_manual', '')
            baudrate = config_antiga.get('baudrate', 9600)
            
            # Determinar métodos habilitados
            metodos_antigos = config_antiga.get('metodos_impressao', [])
            metodos_novos = []
            
            # Converter nomes dos métodos
            if isinstance(metodos_antigos, dict):
                # Se for dict no formato antigo
                for m, habilitado in metodos_antigos.items():
                    if habilitado and m == 'win32':
                        metodos_novos.append('windows')
                    elif habilitado and m == 'serial':
                        metodos_novos.append('serial')
                    elif habilitado and m == 'html':
                        metodos_novos.append('html')
            else:
                # Se for lista no formato novo
                for m in metodos_antigos:
                    if m == 'win32':
                        metodos_novos.append('windows')
                    elif m == 'serial':
                        metodos_novos.append('serial')
                    elif m == 'html':
                        metodos_novos.append('html')
            
            # Se nenhum método for configurado, usar padrão
            if not metodos_novos:
                metodos_novos = ["windows", "html"]
        else:
            # Valores padrão se não existir configuração anterior
            impressora_windows = ""
            largura_papel = 32
            porta_serial = ""
            baudrate = 9600
            metodos_novos = ["windows", "html"]
        
        # Criar nova configuração
        nova_config = {
            "metodos_impressao": metodos_novos,
            "impressora_windows": impressora_windows,
            "largura_papel": largura_papel,
            "porta_serial": porta_serial,
            "baudrate": baudrate,
            "timeout": 3,
            "encoding": "cp850"
        }
        
        # Salvar nova configuração
        os.makedirs(os.path.dirname(novo_config), exist_ok=True)
        with open(novo_config, 'w', encoding='utf-8') as f:
            json.dump(nova_config, f, indent=4)
        
        print(f"Nova configuração criada: {novo_config}")
        print(f"  Métodos habilitados: {metodos_novos}")
        print(f"  Impressora Windows: {impressora_windows}")
        
        return True
    except Exception as e:
        print(f"Erro ao criar configuração: {str(e)}")
        return False

def instalar_novo_sistema():
    """Instala o novo sistema de impressão"""
    print("="*50)
    print("INSTALAÇÃO DO NOVO SISTEMA DE IMPRESSÃO")
    print("="*50)
    
    # 1. Criar pasta de backup
    pasta_backup = 'backup_sistema'
    criar_pasta_se_necessario(pasta_backup)
    
    # 2. Fazer backup do sistema antigo
    arquivos_para_backup = [
        'impressora_v2.py',
        'config/printer_config.json'
    ]
    
    for arquivo in arquivos_para_backup:
        fazer_backup(arquivo, pasta_backup)
    
    # 3. Confirmar a instalação
    resposta = input("\nDeseja continuar com a instalação? (s/n): ")
    if resposta.lower() != 's':
        print("Instalação cancelada.")
        return
    
    # 4. Criar nova configuração baseada na antiga
    criar_config_inicial('config/printer_config.json', 'config/impressora_config.json')
    
    # 5. Renomear o arquivo original
    if os.path.exists('impressora_v2.py'):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        novo_nome = f"impressora_v2.py.{timestamp}.old"
        os.rename('impressora_v2.py', novo_nome)
        print(f"Arquivo original renomeado para {novo_nome}")
    
    # 6. Instalar o novo sistema
    print("\nInstalando novo sistema...")
    
    # Copiar nova_impressora.py para impressora.py
    if os.path.exists('nova_impressora.py'):
        copiar_arquivo('nova_impressora.py', 'impressora.py')
    else:
        print("ERRO: Arquivo nova_impressora.py não encontrado!")
        return
    
    print("\nInstalação concluída com sucesso!")
    print("\nO sistema antigo foi preservado nos arquivos de backup.")
    print("Para usar o novo sistema, importe de 'impressora' ao invés de 'impressora_v2'.")
    print("\nExemplo de uso:")
    print("from impressora import GerenciadorImpressao")
    print("impressora = GerenciadorImpressao()")
    print("impressora.imprimir_teste()")

if __name__ == "__main__":
    instalar_novo_sistema() 
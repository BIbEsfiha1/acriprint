#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import sys
import serial.tools.list_ports
import win32print
from impressora import GerenciadorImpressao

def limpar_tela():
    """Limpa a tela do terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def imprimir_titulo(titulo):
    """Imprime um título formatado"""
    print("\n" + "=" * 50)
    print(f"{titulo.center(50)}")
    print("=" * 50 + "\n")

def imprimir_secao(secao):
    """Imprime uma seção formatada"""
    print("\n" + "-" * 50)
    print(f" {secao} ")
    print("-" * 50)

def carregar_configuracao(arquivo='config/impressora_config.json'):
    """Carrega a configuração ou cria uma padrão se não existir"""
    try:
        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Configuração padrão
            config = {
                "metodos_impressao": ["windows", "html"],
                "impressora_windows": "",
                "largura_papel": 32,
                "porta_serial": "",
                "baudrate": 9600,
                "timeout": 3,
                "encoding": "cp850"
            }
            
            # Garantir que o diretório exista
            os.makedirs(os.path.dirname(arquivo), exist_ok=True)
            
            # Salvar a configuração padrão
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            
            return config
    except Exception as e:
        print(f"Erro ao carregar configuração: {str(e)}")
        sys.exit(1)

def salvar_configuracao(config, arquivo='config/impressora_config.json'):
    """Salva a configuração no arquivo"""
    try:
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Erro ao salvar configuração: {str(e)}")
        return False

def listar_portas_seriais():
    """Lista as portas seriais disponíveis no sistema"""
    try:
        portas = []
        for porta in serial.tools.list_ports.comports():
            portas.append({
                'nome': porta.device,
                'descricao': porta.description
            })
        return portas
    except Exception as e:
        print(f"Erro ao listar portas seriais: {str(e)}")
        return []

def listar_impressoras_windows():
    """Lista as impressoras disponíveis no Windows"""
    try:
        impressoras = []
        for flags, desc, nome, comment in win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
            impressoras.append({
                'nome': nome,
                'descricao': desc
            })
        return impressoras
    except Exception as e:
        print(f"Erro ao listar impressoras Windows: {str(e)}")
        return []

def configurar_metodos_impressao(config):
    """Configura os métodos de impressão disponíveis"""
    imprimir_secao("CONFIGURAÇÃO DE MÉTODOS DE IMPRESSÃO")
    metodos = config.get('metodos_impressao', ["windows", "html"])
    
    # Exibir métodos atuais
    print(f"Métodos atuais: {metodos}")
    
    # Verificar disponibilidade de impressoras Windows
    impressoras_windows = listar_impressoras_windows()
    metodo_windows_disponivel = len(impressoras_windows) > 0
    
    # Verificar disponibilidade de portas seriais
    portas_seriais = listar_portas_seriais()
    metodo_serial_disponivel = len(portas_seriais) > 0
    
    # Opções disponíveis
    opcoes = []
    if metodo_windows_disponivel:
        opcoes.append(("windows", "Impressão via Windows" + (" (Recomendado)" if metodo_windows_disponivel else "")))
    
    if metodo_serial_disponivel:
        opcoes.append(("serial", "Impressão via Serial/USB (impressoras térmicas)"))
    
    opcoes.append(("html", "Impressão via navegador HTML"))
    
    # Exibir opções
    print("\nMétodos disponíveis:")
    for i, (codigo, descricao) in enumerate(opcoes, 1):
        print(f"{i}. {descricao}")
    
    # Selecionar métodos
    print("\nSelecione os métodos de impressão (separados por vírgula ou 'todos'):")
    escolha = input("> ").strip().lower()
    
    novos_metodos = []
    if escolha == 'todos':
        novos_metodos = [op[0] for op in opcoes]
    else:
        try:
            indices = [int(idx.strip()) for idx in escolha.split(',') if idx.strip()]
            for idx in indices:
                if 1 <= idx <= len(opcoes):
                    novos_metodos.append(opcoes[idx-1][0])
        except ValueError:
            print("Entrada inválida. Mantendo configuração atual.")
            return config
    
    # Atualizar configuração
    if novos_metodos:
        config['metodos_impressao'] = novos_metodos
        print(f"Métodos atualizados: {novos_metodos}")
    else:
        print("Nenhum método selecionado. Mantendo configuração atual.")
    
    return config

def configurar_impressora_windows(config):
    """Configura a impressora Windows a ser utilizada"""
    imprimir_secao("CONFIGURAÇÃO DE IMPRESSORA WINDOWS")
    
    # Obter impressora atual
    impressora_atual = config.get('impressora_windows', '')
    
    # Listar impressoras disponíveis
    impressoras = listar_impressoras_windows()
    
    if not impressoras:
        print("Nenhuma impressora Windows encontrada no sistema.")
        return config
    
    print(f"Impressora atual: {impressora_atual or 'Nenhuma (usando padrão)'}")
    print("\nImpressoras disponíveis:")
    
    for i, imp in enumerate(impressoras, 1):
        padrao = " (ATUAL)" if imp['nome'] == impressora_atual else ""
        print(f"{i}. {imp['nome']}{padrao} - {imp['descricao']}")
    
    # Obter impressora padrão do sistema
    try:
        impressora_padrao = win32print.GetDefaultPrinter()
        print(f"\nImpressora padrão do Windows: {impressora_padrao}")
    except:
        impressora_padrao = ""
    
    # Opções
    print("\nEscolha uma opção:")
    print("1. Selecionar uma impressora da lista")
    print("2. Usar a impressora padrão do Windows")
    print("3. Voltar (manter atual)")
    
    escolha = input("> ").strip()
    
    if escolha == '1':
        idx = input("Número da impressora: ").strip()
        try:
            idx = int(idx)
            if 1 <= idx <= len(impressoras):
                config['impressora_windows'] = impressoras[idx-1]['nome']
                print(f"Impressora configurada: {impressoras[idx-1]['nome']}")
            else:
                print("Número inválido. Mantendo configuração atual.")
        except ValueError:
            print("Entrada inválida. Mantendo configuração atual.")
    
    elif escolha == '2' and impressora_padrao:
        config['impressora_windows'] = impressora_padrao
        print(f"Usando impressora padrão: {impressora_padrao}")
    
    return config

def configurar_porta_serial(config):
    """Configura a porta serial para impressoras térmicas"""
    imprimir_secao("CONFIGURAÇÃO DE PORTA SERIAL")
    
    # Obter configuração atual
    porta_atual = config.get('porta_serial', '')
    baudrate_atual = config.get('baudrate', 9600)
    
    # Listar portas disponíveis
    portas = listar_portas_seriais()
    
    if not portas:
        print("Nenhuma porta serial encontrada no sistema.")
        print("Verifique se a impressora está conectada.")
        return config
    
    print(f"Porta atual: {porta_atual or 'Nenhuma'}")
    print(f"Baudrate atual: {baudrate_atual}")
    
    print("\nPortas disponíveis:")
    for i, porta in enumerate(portas, 1):
        print(f"{i}. {porta['nome']} - {porta['descricao']}")
    
    # Opções
    print("\nEscolha uma opção:")
    print("1. Selecionar uma porta da lista")
    print("2. Limpar configuração de porta")
    print("3. Voltar (manter atual)")
    
    escolha = input("> ").strip()
    
    if escolha == '1':
        idx = input("Número da porta: ").strip()
        try:
            idx = int(idx)
            if 1 <= idx <= len(portas):
                config['porta_serial'] = portas[idx-1]['nome']
                print(f"Porta configurada: {portas[idx-1]['nome']}")
                
                # Configurar baudrate
                print("\nSelecione o baudrate:")
                baudrates = [9600, 19200, 38400, 57600, 115200]
                for i, baud in enumerate(baudrates, 1):
                    padrao = " (ATUAL)" if baud == baudrate_atual else ""
                    print(f"{i}. {baud}{padrao}")
                
                baud_escolha = input("> ").strip()
                try:
                    baud_idx = int(baud_escolha)
                    if 1 <= baud_idx <= len(baudrates):
                        config['baudrate'] = baudrates[baud_idx-1]
                        print(f"Baudrate configurado: {baudrates[baud_idx-1]}")
                except ValueError:
                    print("Entrada inválida. Mantendo baudrate atual.")
            else:
                print("Número inválido. Mantendo configuração atual.")
        except ValueError:
            print("Entrada inválida. Mantendo configuração atual.")
    
    elif escolha == '2':
        config['porta_serial'] = ''
        print("Configuração de porta serial removida.")
    
    return config

def configurar_formato(config):
    """Configura o formato de impressão"""
    imprimir_secao("CONFIGURAÇÃO DE FORMATO")
    
    # Obter largura atual
    largura_atual = config.get('largura_papel', 32)
    
    print(f"Largura atual: {largura_atual} caracteres")
    
    print("\nOpções comuns de largura:")
    larguras = {
        "1": 32,   # 58mm (impressora típica de PDV)
        "2": 42,   # 76mm
        "3": 48,   # 80mm
        "4": 80    # Impressora comum 
    }
    
    print("1. 32 caracteres (58mm, típica de PDV)")
    print("2. 42 caracteres (76mm)")
    print("3. 48 caracteres (80mm)")
    print("4. 80 caracteres (impressora comum)")
    print("5. Personalizado")
    
    escolha = input("\nSelecione uma opção: ").strip()
    
    if escolha in larguras:
        config['largura_papel'] = larguras[escolha]
        print(f"Largura configurada: {larguras[escolha]} caracteres")
    
    elif escolha == '5':
        try:
            nova_largura = int(input("Digite a largura desejada: ").strip())
            if 20 <= nova_largura <= 150:
                config['largura_papel'] = nova_largura
                print(f"Largura configurada: {nova_largura} caracteres")
            else:
                print("Valor fora da faixa válida (20-150). Mantendo configuração atual.")
        except ValueError:
            print("Valor inválido. Mantendo configuração atual.")
    
    return config

def testar_impressao():
    """Testa a impressão com a configuração atual"""
    imprimir_secao("TESTE DE IMPRESSÃO")
    
    try:
        # Criar instância da impressora
        impressora = GerenciadorImpressao()
        
        # Exibir configuração atual
        print("Configuração atual:")
        print(f"Métodos: {impressora.config.get('metodos_impressao', [])}")
        print(f"Impressora Windows: {impressora.config.get('impressora_windows', '') or 'Padrão do sistema'}")
        
        # Confirmar teste
        print("\nSerá impressa uma página de teste.")
        confirmar = input("Deseja continuar? (s/n): ").strip().lower()
        
        if confirmar == 's':
            print("Executando teste de impressão...")
            resultado = impressora.imprimir_teste()
            
            if resultado:
                print("\nTeste de impressão bem-sucedido!")
            else:
                print("\nO teste de impressão falhou.")
                print("Verifique o arquivo de log em logs/impressao_*.log para mais detalhes.")
        else:
            print("Teste cancelado.")
    
    except Exception as e:
        print(f"Erro ao testar impressão: {str(e)}")

def menu_principal():
    """Exibe o menu principal da ferramenta"""
    config = carregar_configuracao()
    
    while True:
        limpar_tela()
        imprimir_titulo("CONFIGURAÇÃO DO SISTEMA DE IMPRESSÃO")
        
        print("Configuração atual:")
        print(f"Métodos de impressão: {config.get('metodos_impressao', [])}")
        print(f"Impressora Windows: {config.get('impressora_windows', '') or 'Padrão do sistema'}")
        print(f"Porta Serial: {config.get('porta_serial', '') or 'Não configurada'}")
        print(f"Largura do papel: {config.get('largura_papel', 32)} caracteres")
        
        print("\nOpções:")
        print("1. Configurar métodos de impressão")
        print("2. Configurar impressora Windows")
        print("3. Configurar porta serial (impressoras térmicas)")
        print("4. Configurar formato de impressão")
        print("5. Testar impressão")
        print("0. Salvar e sair")
        
        escolha = input("\nEscolha uma opção: ").strip()
        
        if escolha == '1':
            config = configurar_metodos_impressao(config)
            salvar_configuracao(config)
        
        elif escolha == '2':
            config = configurar_impressora_windows(config)
            salvar_configuracao(config)
        
        elif escolha == '3':
            config = configurar_porta_serial(config)
            salvar_configuracao(config)
        
        elif escolha == '4':
            config = configurar_formato(config)
            salvar_configuracao(config)
        
        elif escolha == '5':
            testar_impressao()
            input("\nPressione Enter para continuar...")
        
        elif escolha == '0':
            print("Salvando configurações e saindo...")
            salvar_configuracao(config)
            break
        
        else:
            print("Opção inválida.")
            input("Pressione Enter para continuar...")

if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo usuário.")
    except Exception as e:
        print(f"Erro: {str(e)}")
        sys.exit(1) 
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import logging
import sys
import time
import traceback
from datetime import datetime
import serial
import serial.tools.list_ports
import win32print
import win32api
import tempfile
import webbrowser
import win32ui
from PIL import Image, ImageDraw, ImageFont, ImageOps
import qrcode
import win32con
import ctypes
import win32gui

logger = logging.getLogger('nova_impressora')

class ConfiguracaoImpressora:
    """Classe para gerenciar configurações da impressora"""
    
    def __init__(self, arquivo_config='config/impressora_config.json'):
        self.arquivo_config = arquivo_config
        self.config = self._carregar_config()
    
    def _carregar_config(self):
        """Carrega as configurações do arquivo JSON ou cria um padrão"""
        try:
            if os.path.exists(self.arquivo_config):
                with open(self.arquivo_config, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._config_padrao()
        except Exception as e:
            logging.error(f"Erro ao carregar configuração: {str(e)}")
            return self._config_padrao()
    
    def _config_padrao(self):
        """Configuração padrão caso o arquivo não exista"""
        return {
            "metodos_impressao": ["windows", "html"],
            "impressora_windows": "",
            "largura_papel": 32,
            "porta_serial": "",
            "baudrate": 9600,
            "timeout": 3,
            "encoding": "cp850"
        }
    
    def salvar(self, nova_config=None):
        """Salva a configuração no arquivo"""
        try:
            config_para_salvar = nova_config if nova_config else self.config
            os.makedirs(os.path.dirname(self.arquivo_config), exist_ok=True)
            with open(self.arquivo_config, 'w', encoding='utf-8') as f:
                json.dump(config_para_salvar, f, indent=4)
            self.config = config_para_salvar
            return True
        except Exception as e:
            logging.error(f"Erro ao salvar configuração: {str(e)}")
            return False
    
    def obter(self):
        """Retorna a configuração atual"""
        return self.config

class GerenciadorImpressao:
    """Classe principal para gerenciar impressão de documentos"""
    
    def __init__(self, arquivo_config='config/impressora_config.json'):
        # Configurar logger
        self.logger = self._configurar_logger()
        
        # Carregar configurações
        self.config_manager = ConfiguracaoImpressora(arquivo_config)
        self.config = self.config_manager.obter()
        
        # Conexão serial (se utilizada)
        self.conexao_serial = None
    
    def _configurar_logger(self):
        """Configura o logger para registro de eventos"""
        logger = logging.getLogger('nova_impressora')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Criar diretório de logs se não existir
            os.makedirs('logs', exist_ok=True)
            
            # Handler de arquivo
            file_handler = logging.FileHandler(
                f'logs/impressao_{datetime.now().strftime("%Y%m%d")}.log',
                encoding='utf-8'
            )
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # Handler de console
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = logging.Formatter(
                '%(levelname)s: %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def listar_impressoras_windows(self):
        """Lista todas as impressoras instaladas no Windows"""
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
            self.logger.error(f"Erro ao listar impressoras Windows: {str(e)}")
            return []
    
    def obter_impressora_padrao_windows(self):
        """Retorna o nome da impressora padrão do Windows"""
        try:
            return win32print.GetDefaultPrinter()
        except Exception as e:
            self.logger.error(f"Erro ao obter impressora padrão: {str(e)}")
            return ""
    
    def listar_portas_seriais(self):
        """Lista todas as portas seriais disponíveis"""
        try:
            portas = []
            for porta in serial.tools.list_ports.comports():
                portas.append({
                    'nome': porta.device,
                    'descricao': porta.description
                })
            return portas
        except Exception as e:
            self.logger.error(f"Erro ao listar portas seriais: {str(e)}")
            return []
    
    def formatar_texto_impressao(self, pedido):
        """Formata o pedido para impressão com layout adequado"""
        largura = self.config.get('largura_papel', 32)
        linhas = []
        
        # Cabeçalho
        linhas.append(self._centralizar("ACRIPRINT", largura))
        linhas.append(self._centralizar("PEDIDO", largura))
        linhas.append("-" * largura)
        
        # Dados do pedido
        numero = pedido.get('numero', 'N/D')
        data = pedido.get('data_pedido', datetime.now().strftime("%d/%m/%Y %H:%M"))
        linhas.append(f"Pedido: {numero}")
        linhas.append(f"Data: {data}")
        
        # Cliente
        cliente = pedido.get('cliente', {})
        if cliente:
            linhas.append("-" * largura)
            linhas.append("CLIENTE")
            linhas.append(f"Nome: {cliente.get('nome', 'N/D')}")
            linhas.append(f"Telefone: {cliente.get('telefone', 'N/D')}")
        
        # Itens
        itens = pedido.get('itens', [])
        if itens:
            linhas.append("-" * largura)
            linhas.append("ITENS")
            for item in itens:
                qtd = item.get('quantidade', 1)
                desc = item.get('descricao', 'Item')
                linhas.append(f"{qtd}x {desc}")
                
                preco = item.get('preco', 0)
                if preco:
                    valor_formatado = f"R$ {preco:.2f}".replace('.', ',')
                    linhas.append(f"   {valor_formatado}")
                
                obs = item.get('observacao', '')
                if obs:
                    # Quebrar observação em múltiplas linhas se necessário
                    obs_linhas = self._quebrar_texto(f"   Obs: {obs}", largura)
                    linhas.extend(obs_linhas)
        
        # Total
        total = pedido.get('total', 0)
        valor_total = f"R$ {total:.2f}".replace('.', ',')
        linhas.append("-" * largura)
        linhas.append(f"TOTAL: {valor_total}")
        
        # Observações gerais
        obs_geral = pedido.get('observacao', '')
        if obs_geral:
            linhas.append("-" * largura)
            linhas.append("OBSERVAÇÕES:")
            obs_linhas = self._quebrar_texto(obs_geral, largura)
            linhas.extend(obs_linhas)
        
        # Rodapé
        linhas.append("-" * largura)
        linhas.append(self._centralizar("Obrigado pela preferência!", largura))
        
        # Adicionar algumas linhas em branco no final
        linhas.extend(["", "", ""])
        
        return "\n".join(linhas)
    
    def _centralizar(self, texto, largura):
        """Centraliza o texto na largura especificada"""
        if len(texto) >= largura:
            return texto
        espacos = (largura - len(texto)) // 2
        return " " * espacos + texto
    
    def _quebrar_texto(self, texto, largura):
        """Quebra o texto em múltiplas linhas respeitando a largura"""
        resultado = []
        palavras = texto.split()
        linha_atual = ""
        
        for palavra in palavras:
            if len(linha_atual) + len(palavra) + 1 <= largura:
                linha_atual += " " + palavra if linha_atual else palavra
            else:
                resultado.append(linha_atual)
                linha_atual = palavra
        
        if linha_atual:
            resultado.append(linha_atual)
        
        return resultado
    
    def imprimir_windows(self, texto):
        """Imprime o texto usando a API do Windows"""
        self.logger.info("Iniciando impressão Windows")
        try:
            # Obter a impressora configurada ou usar a padrão
            impressora = self.config.get('impressora_windows', '')
            if not impressora:
                impressora = self.obter_impressora_padrao_windows()
                self.logger.info(f"Usando impressora padrão: {impressora}")
            else:
                self.logger.info(f"Usando impressora configurada: {impressora}")
            
            # Verificar se a impressora existe
            impressoras = self.listar_impressoras_windows()
            impressora_valida = False
            
            for p in impressoras:
                if p['nome'] == impressora:
                    impressora_valida = True
                    break
            
            if not impressora_valida:
                self.logger.warning(f"Impressora '{impressora}' não encontrada")
                # Usar a impressora padrão
                impressora = self.obter_impressora_padrao_windows()
                self.logger.info(f"Usando impressora padrão: {impressora}")
                
                # Atualizar a configuração
                self.config['impressora_windows'] = impressora
                self.config_manager.salvar(self.config)
            
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(
                    prefix='acriprint_', 
                    suffix='.txt', 
                    delete=False, 
                    mode='w', 
                    encoding='utf-8') as temp:
                temp.write(texto)
                arquivo_temp = temp.name
            
            self.logger.info(f"Arquivo temporário criado: {arquivo_temp}")
            
            # Enviar para impressão
            win32api.ShellExecute(
                0,             # Handle (0 = desktop)
                "print",       # Operação
                arquivo_temp,  # Arquivo
                None,          # Parâmetros
                ".",           # Diretório
                0              # Modo de exibição (0 = escondido)
            )
            
            self.logger.info("Comando de impressão enviado com sucesso")
            return True
        
        except Exception as e:
            self.logger.error(f"Erro na impressão Windows: {str(e)}")
            traceback.print_exc()
            return False
    
    def imprimir_html(self, texto):
        """Imprime o texto usando o navegador (HTML)"""
        self.logger.info("Iniciando impressão HTML")
        try:
            # Criar arquivo temporário HTML
            with tempfile.NamedTemporaryFile(
                    prefix='acriprint_', 
                    suffix='.html', 
                    delete=False, 
                    mode='w', 
                    encoding='utf-8') as temp:
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Impressão Acriprint</title>
    <style>
        body {{ font-family: monospace; font-size: 12pt; }}
        pre {{ white-space: pre-wrap; }}
        @media print {{
            body {{ margin: 0; }}
            .botoes {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="botoes">
        <button onclick="window.print()">Imprimir</button>
    </div>
    <pre>{texto}</pre>
</body>
</html>"""
                temp.write(html_content)
                arquivo_temp = temp.name
            
            self.logger.info(f"Arquivo HTML criado: {arquivo_temp}")
            
            # Abrir no navegador
            webbrowser.open(f'file://{arquivo_temp}')
            
            self.logger.info("Página HTML aberta no navegador")
            return True
        
        except Exception as e:
            self.logger.error(f"Erro na impressão HTML: {str(e)}")
            traceback.print_exc()
            return False
    
    def imprimir_serial(self, texto):
        """Imprime o texto usando a porta serial (para impressoras térmicas)"""
        self.logger.info("Iniciando impressão Serial")
        
        # Verificar se há porta configurada
        porta = self.config.get('porta_serial', '')
        if not porta:
            self.logger.error("Nenhuma porta serial configurada")
            return False
        
        try:
            # Fechar conexão anterior se existir
            if hasattr(self, 'conexao_serial') and self.conexao_serial and self.conexao_serial.is_open:
                self.conexao_serial.close()
                self.conexao_serial = None
            
            # Estabelecer conexão
            baudrate = self.config.get('baudrate', 9600)
            timeout = self.config.get('timeout', 3)
            
            self.logger.info(f"Conectando à porta {porta} (baudrate: {baudrate})")
            self.conexao_serial = serial.Serial(
                porta,
                baudrate=baudrate,
                timeout=timeout,
                writeTimeout=timeout
            )
            
            if not self.conexao_serial.is_open:
                self.logger.error("Falha ao abrir porta serial")
                return False
            
            # Preparar a impressora
            self.logger.info("Enviando comandos de inicialização")
            encoding = self.config.get('encoding', 'cp850')
            
            # Comandos ESC/POS básicos
            self.conexao_serial.write(b'\x1B\x40')  # ESC @ - Inicializar
            time.sleep(0.1)
            
            # Enviar texto linha por linha
            self.logger.info("Enviando texto para impressão")
            for linha in texto.split('\n'):
                # Remover caracteres não imprimíveis
                linha_limpa = ''.join(c for c in linha if 32 <= ord(c) <= 126 or c in '\n\r')
                dados = (linha_limpa + '\n').encode(encoding, errors='replace')
                self.conexao_serial.write(dados)
                self.conexao_serial.flush()
                time.sleep(0.01)  # Pequena pausa para buffer
            
            # Avançar papel e cortar
            self.conexao_serial.write(b'\n\n\n\n')  # Avançar papel
            self.conexao_serial.write(b'\x1D\x56\x01')  # GS V - Cortar papel
            self.conexao_serial.flush()
            
            # Fechar conexão
            self.conexao_serial.close()
            self.conexao_serial = None
            
            self.logger.info("Impressão serial concluída com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na impressão serial: {str(e)}")
            if hasattr(self, 'conexao_serial') and self.conexao_serial:
                try:
                    self.conexao_serial.close()
                except:
                    pass
                self.conexao_serial = None
            
            traceback.print_exc()
            return False
    
    def imprimir(self, pedido):
        """Método principal que tenta imprimir usando os métodos configurados"""
        self.logger.info(f"Iniciando impressão do pedido: {pedido.get('numero', 'N/D')}")
        
        # Formatar o texto
        texto_formatado = self.formatar_texto_impressao(pedido)
        
        # Obter métodos configurados
        metodos = self.config.get('metodos_impressao', ["windows", "html"])
        self.logger.info(f"Métodos configurados: {metodos}")
        
        # Tentar cada método na ordem configurada
        for metodo in metodos:
            self.logger.info(f"Tentando método: {metodo}")
            
            if metodo == "windows":
                if self.imprimir_windows(texto_formatado):
                    self.logger.info("Impressão Windows bem-sucedida")
                    return True
            
            elif metodo == "html":
                if self.imprimir_html(texto_formatado):
                    self.logger.info("Impressão HTML bem-sucedida")
                    return True
            
            elif metodo == "serial":
                if self.imprimir_serial(texto_formatado):
                    self.logger.info("Impressão Serial bem-sucedida")
                    return True
        
        self.logger.error("Falha em todos os métodos de impressão")
        return False
    
    def imprimir_teste(self):
        """Imprime um cupom de teste para verificar o funcionamento"""
        pedido_teste = {
            "numero": f"TESTE-{datetime.now().strftime('%H%M%S')}",
            "data_pedido": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "cliente": {
                "nome": "Cliente de Teste",
                "telefone": "(00) 0000-0000"
            },
            "itens": [
                {
                    "quantidade": 1,
                    "descricao": "Item de Teste",
                    "preco": 15.90,
                    "observacao": "Teste de impressão"
                }
            ],
            "total": 15.90,
            "observacao": "Este é um teste automático do sistema de impressão"
        }
        
        return self.imprimir(pedido_teste)

def gerar_qrcode(numero_pedido, tamanho=120):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=2,
        border=2,
    )
    qr.add_data(str(numero_pedido))
    qr.make(fit=True)
    # Gerar como monocromático P&B direto
    img = qr.make_image(fill_color="black", back_color="white").convert('1')
    img = img.resize((tamanho, tamanho), Image.NEAREST)
    return img

def quebrar_linhas(texto, largura):
    linhas = []
    while len(texto) > largura:
        corte = texto.rfind(' ', 0, largura)
        if corte == -1:
            corte = largura
        linhas.append(texto[:corte])
        texto = texto[corte:].lstrip()
    if texto:
        linhas.append(texto)
    return linhas

def formatar_pedido_para_texto_pos(pedido, largura=32):
    """Formata o pedido para impressão em impressora POS"""
    logger.debug("Formatando pedido para texto POS")
    linhas = []
    
    # Formatar cabeçalho
    nome_loja = pedido.get('loja', {}).get('nome', 'ACRIPRINT')
    # Garantir que não seja None
    nome_loja = nome_loja if nome_loja else 'ACRIPRINT'
    
    # Centralizar nome da loja e cabeçalho de pedido
    linhas.append("-" * largura)
    linhas.append(nome_loja.center(largura))
    linhas.append("PEDIDO".center(largura))
    linhas.append("-" * largura)
    
    # Informações do pedido
    numero_pedido = pedido.get('numero', 'N/D')
    linhas.append(f"Pedido: {numero_pedido}")
    
    # Data
    data_pedido = pedido.get('data', '')
    if data_pedido:
        try:
            # Tentar formatar a data se tiver formato ISO
            if 'T' in data_pedido:
                data_pedido = data_pedido.split('T')[0]
            if '-' in data_pedido:
                partes = data_pedido.split('-')
                if len(partes) == 3:
                    data_pedido = f"{partes[2]}/{partes[1]}/{partes[0]}"
        except Exception as e:
            logger.warning(f"Erro ao formatar data: {e}")
    linhas.append(f"Data: {data_pedido}")
    
    # Cliente
    cliente = pedido.get('cliente', pedido.get('contato', {}))
    if cliente and isinstance(cliente, dict):
        nome_cliente = cliente.get('nome', '')
        if nome_cliente:
            linhas.append(f"Cliente: {nome_cliente}")
    
    linhas.append("-" * largura)
    linhas.append("ITENS:")
    itens = pedido.get('itens', []) # Usar os itens já processados
    
    if not itens:
        # Tentar localizar itens em outras estruturas possíveis
        for campo_itens in ['items', 'produtos', 'pedidoProdutos', 'products', 'produto']:
            if campo_itens in pedido and isinstance(pedido[campo_itens], list) and pedido[campo_itens]:
                itens = pedido[campo_itens]
                logger.info(f"Encontrados itens no campo alternativo '{campo_itens}'")
                break
        
        # Buscar em estruturas aninhadas também
        if not itens:
            for key, value in pedido.items():
                if isinstance(value, dict):
                    for sub_key in ['itens', 'items', 'produtos', 'pedidoProdutos', 'products']:
                        if sub_key in value and isinstance(value[sub_key], list) and value[sub_key]:
                            itens = value[sub_key]
                            logger.info(f"Encontrados itens em estrutura aninhada: {key}.{sub_key}")
                            break
    
    if not itens:
        linhas.append("(Nenhum item encontrado)")
    else:
        logger.debug(f"Formatando {len(itens)} itens...") # Log: Quantos itens?
        for i, item in enumerate(itens):
            # <<< LOG DENTRO DO LOOP >>>
            logger.debug(f"  Formatando item {i+1}: {item}")
            
            # LÓGICA MELHORADA: Extração mais robusta dos dados do item
            # 1. Extrair descrição/nome do produto
            nome = None
            # Verificar em vários campos possíveis
            if 'descricao' in item:
                nome = item['descricao']
            elif 'produto' in item and isinstance(item['produto'], dict):
                if 'nome' in item['produto']:
                    nome = item['produto']['nome']
                elif 'descricao' in item['produto']:
                    nome = item['produto']['descricao']
            
            # Se não encontrou nome, tentar outros campos
            if not nome:
                for campo in ['nome', 'description', 'descr', 'item_name']:
                    if campo in item and item[campo]:
                        nome = item[campo]
                        break
            
            # Fallback - usar código como nome
            if not nome and 'codigo' in item:
                nome = f"Produto {item['codigo']}"
            elif not nome:
                nome = f"Produto #{i+1}"
            
            # 2. Extrair código/SKU do produto
            sku = None
            for campo_codigo in ['codigo', 'sku', 'id', 'code']:
                if campo_codigo in item and item[campo_codigo]:
                    sku = item[campo_codigo]
                    break
            
            # Verificar no objeto produto também
            if not sku and 'produto' in item and isinstance(item['produto'], dict):
                for campo_codigo in ['codigo', 'sku', 'id', 'code']:
                    if campo_codigo in item['produto'] and item['produto'][campo_codigo]:
                        sku = item['produto'][campo_codigo]
                        break
            
            # Se ainda não tiver SKU, gerar um número genérico
            if not sku:
                sku = f"SKU{i+1}"
            
            # 3. Extrair quantidade
            qtd = 1  # Valor padrão
            for campo_qtd in ['quantidade', 'qtde', 'qtd', 'quantity', 'amount']:
                if campo_qtd in item and item[campo_qtd] is not None:
                    try:
                        qtd = float(item[campo_qtd])
                        break
                    except (ValueError, TypeError):
                        logger.warning(f"Valor inválido para quantidade: {item[campo_qtd]}")
            
            # 4. Extrair valor unitário
            valor_unitario = 0.0
            for campo_valor in ['valorunidade', 'valor_unitario', 'valor', 'unit_price', 'preco', 'price']:
                if campo_valor in item and item[campo_valor] is not None:
                    try:
                        valor_unitario = float(item[campo_valor])
                        break
                    except (ValueError, TypeError):
                        logger.warning(f"Valor inválido para valor unitário: {item[campo_valor]}")
            
            # Verificar no objeto produto também
            if valor_unitario == 0.0 and 'produto' in item and isinstance(item['produto'], dict):
                for campo_valor in ['preco', 'valor', 'price']:
                    if campo_valor in item['produto'] and item['produto'][campo_valor] is not None:
                        try:
                            valor_unitario = float(item['produto'][campo_valor])
                            break
                        except (ValueError, TypeError):
                            pass
            
            # 5. Calcular ou extrair valor total do item
            valor_total_item = 0.0
            # Tentar obter valor total diretamente
            for campo_total in ['valorTotalItem', 'valor_total', 'total']:
                if campo_total in item and item[campo_total] is not None:
                    try:
                        valor_total_item = float(item[campo_total])
                        break
                    except (ValueError, TypeError):
                        pass
            
            # Se não encontrou valor total, calcular a partir de quantidade e valor unitário
            if valor_total_item == 0.0:
                valor_total_item = qtd * valor_unitario
            
            # 6. Extrair observação detalhada
            obs_detalhada = ""
            for campo_obs in ['descricaoDetalhada', 'observacao', 'obs', 'description_details', 'notas']:
                if campo_obs in item and item[campo_obs]:
                    obs_detalhada = item[campo_obs]
                    break

            # Formatar quantidade
            try:
                qtd_formatada = int(float(qtd))
            except (ValueError, TypeError):
                qtd_formatada = qtd
                
            # Formatar valores monetários
            try:
                vu_formatado = f"R$ {float(valor_unitario):.2f}".replace('.', ',')
            except (ValueError, TypeError):
                vu_formatado = "R$ -.--"
            try:
                vt_formatado = f"R$ {float(valor_total_item):.2f}".replace('.', ',')
            except (ValueError, TypeError):
                vt_formatado = "R$ -.--"

            # Linha principal do item
            linha_item = f"{qtd_formatada}X {nome} [{sku}]".strip()
            linhas_item_quebradas = quebrar_linhas(linha_item, largura)
            linhas.extend(linhas_item_quebradas)

            # Linha de valores (indentada)
            linha_valores = f"   VU: {vu_formatado} | VT: {vt_formatado}"
            linhas.append(linha_valores)

            # Linhas de observação (indentada)
            if obs_detalhada:
                obs_formatada = f"   Obs: {obs_detalhada}"
                linhas_obs_quebradas = quebrar_linhas(obs_formatada, largura)
                linhas.extend(linhas_obs_quebradas)
            # Adicionar uma linha em branco entre itens para clareza
            linhas.append("")

    linhas.append("-" * largura)
    linhas.append("\n\n\n") # Espaço final e corte (se aplicável)
    return "\n".join(linhas)

# Função para converter imagem PIL em comandos ESC/POS GS v 0
def gerar_comandos_escpos_imagem(img):
    """Converte uma imagem PIL monocromática em comandos ESC/POS GS v 0."""
    # Garantir que a imagem seja monocromática
    if img.mode != '1':
        img = img.convert('1')

    width, height = img.size
    width_bytes = (width + 7) // 8
    xl = width_bytes & 0xFF
    xh = (width_bytes >> 8) & 0xFF
    yl = height & 0xFF
    yh = (height >> 8) & 0xFF
    header = bytes([29, 118, 48, 0, xl, xh, yl, yh])
    data_bytes = bytearray()
    pixels = list(img.getdata())
    for y in range(height):
        byte_row = bytearray(width_bytes)
        for x_byte in range(width_bytes):
            for bit in range(8):
                x = x_byte * 8 + bit
                if x < width:
                    idx = y * width + x
                    if pixels[idx] == 0:
                        byte_row[x_byte] |= (1 << (7 - bit))
        data_bytes.extend(byte_row)
    return header + data_bytes

def imprimir_pedido_pos58(pedido, impressora_nome=None):
    # <<< LOG INICIAL >>>
    logger.debug(f"Iniciando imprimir_pedido_pos58. Dados recebidos:")
    try:
        # Usar json.dumps para formatar bem o dicionário no log
        pedido_json_str = json.dumps(pedido, indent=2, ensure_ascii=False)
        logger.debug(pedido_json_str)
    except Exception as log_err:
        logger.error(f"Erro ao tentar logar dados do pedido: {log_err}")
        logger.debug(str(pedido)) # Fallback para string simples

    # VERIFICAÇÃO DE SEGURANÇA: garantir que pedido seja um dicionário
    if not isinstance(pedido, dict):
        logger.error(f"Pedido inválido: não é um dicionário. Tipo: {type(pedido)}")
        return False

    if not impressora_nome:
        try:
            impressora_nome = win32print.GetDefaultPrinter()
            logger.info(f"Usando impressora padrão: {impressora_nome}")
        except Exception as e:
            logger.error(f"Erro ao obter impressora padrão: {e}")
            return False

    hprinter = None
    success = False

    try:
        # --- DADOS MÍNIMOS REQUERIDOS ---
        # Garantir que temos um número de pedido válido
        numero_pedido = pedido.get('numero', '')
        if not numero_pedido:
            # Tentar outros campos comuns
            for campo in ['id', 'numeroPedido', 'order_id', 'idVenda']:
                if campo in pedido and pedido[campo]:
                    numero_pedido = str(pedido[campo])
                    logger.info(f"Usando campo '{campo}' como número do pedido: {numero_pedido}")
                    break
            
            # Se ainda não tiver, gerar um temporário baseado em timestamp
            if not numero_pedido:
                numero_pedido = f"TEMP-{int(time.time())}"
                logger.warning(f"Número de pedido não encontrado. Usando temporário: {numero_pedido}")
        
        # Garantir que pedido tenha um campo 'itens' e seja uma lista
        if 'itens' not in pedido or not isinstance(pedido['itens'], list):
            logger.warning("Pedido sem campo 'itens' válido. Criando lista vazia.")
            pedido['itens'] = []

        # --- AJUSTES QR CODE ---
        # 1. Gerar QR Code (imagem PIL) - Tamanho aumentado para 150
        try:
            qr_img_original = gerar_qrcode(numero_pedido, tamanho=150)
            logger.debug(f"QR Code original gerado ({qr_img_original.width}x{qr_img_original.height}).")
            
            # 2. Criar imagem maior para centralizar o QR Code
            largura_papel_pixels = 384 # Largura comum para 58mm
            altura_qr = qr_img_original.height
            img_centralizada = Image.new('1', (largura_papel_pixels, altura_qr), 1) # Fundo branco (1)
            
            # Calcular posição para colar
            pos_x = (largura_papel_pixels - qr_img_original.width) // 2
            pos_y = 0
            img_centralizada.paste(qr_img_original, (pos_x, pos_y))
            logger.debug(f"QR Code colado na imagem centralizada em ({pos_x},{pos_y}).")
            
            # 3. Converter imagem CENTRALIZADA para comandos ESC/POS
            comandos_qr = gerar_comandos_escpos_imagem(img_centralizada)
            logger.debug(f"{len(comandos_qr)} bytes de comandos ESC/POS gerados para o QR Code centralizado.")
            qr_gerado_sucesso = True
        except Exception as qr_err:
            logger.error(f"Erro ao gerar QR Code: {qr_err}")
            logger.error(traceback.format_exc())
            comandos_qr = b''  # QR Code vazio se falhar
            qr_gerado_sucesso = False
        # --- FIM AJUSTES QR CODE ---

        # 4. Formatar Texto
        try:
            texto_pedido = formatar_pedido_para_texto_pos(pedido, largura=32)
            # <<< LOG DO TEXTO FORMATADO >>>
            logger.debug(f"Texto formatado para impressão:")
            logger.debug(f"\n-- INICIO TEXTO --\n{texto_pedido}\n-- FIM TEXTO --")
        except Exception as fmt_err:
            logger.error(f"Erro na formatação do texto do pedido: {fmt_err}")
            logger.error(traceback.format_exc())
            # Criar texto de emergência para garantir que alguma coisa seja impressa
            texto_pedido = f"""
---------------------------------
        PEDIDO EMERGENCIAL
---------------------------------
Número: {numero_pedido}
Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}

ATENÇÃO: Erro na formatação do pedido.
Por favor, verifique no sistema.
---------------------------------
            """
            logger.warning("Usando texto de emergência para impressão")

        # Converter texto para bytes
        try:
            texto_bytes = texto_pedido.encode('cp850', errors='replace')
        except LookupError:
            try:
                logger.warning("cp850 não disponível, usando cp437")
                texto_bytes = texto_pedido.encode('cp437', errors='replace')
            except Exception as enc_err:
                logger.error(f"Erro na codificação: {enc_err}. Usando ASCII.")
                texto_bytes = texto_pedido.encode('ascii', errors='replace')
        
        logger.debug(f"{len(texto_bytes)} bytes de texto formatado para impressão.")

        # 5. Abrir impressora e iniciar documento RAW
        try:
            hprinter = win32print.OpenPrinter(impressora_nome)
            doc_info = ("Pedido AcriPrint", None, "RAW")
            job_id = win32print.StartDocPrinter(hprinter, 1, doc_info)
            logger.debug(f"Job de impressão RAW iniciado: {job_id}")
            win32print.StartPagePrinter(hprinter)
            
            # 6. Enviar comandos ESC/POS do QR Code CENTRALIZADO
            if qr_gerado_sucesso and comandos_qr:
                try:
                    bytes_written_qr = win32print.WritePrinter(hprinter, comandos_qr)
                    logger.debug(f"{bytes_written_qr} bytes de comando QR escritos.")
                    if bytes_written_qr != len(comandos_qr):
                        logger.warning("Nem todos os bytes do comando QR foram escritos!")
                except Exception as qr_write_err:
                    logger.error(f"Erro ao enviar QR Code para impressora: {qr_write_err}")
            
            # 7. Enviar Texto
            try:
                newline_bytes = b'\n'
                win32print.WritePrinter(hprinter, newline_bytes)
                bytes_written_txt = win32print.WritePrinter(hprinter, texto_bytes)
                logger.debug(f"{bytes_written_txt} bytes de texto escritos.")
                if bytes_written_txt != len(texto_bytes):
                    logger.warning("Nem todos os bytes do texto foram escritos!")
            except Exception as txt_write_err:
                logger.error(f"Erro ao enviar texto para impressora: {txt_write_err}")
                # Mesmo com erro, consideramos sucesso parcial, pois o QR code pode ter sido impresso
            
            # 8. Finalizar impressão
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            success = True
            logger.info(f"Impressão (ESC/POS+RAW) do pedido {numero_pedido} enviada com sucesso.")
        
        except Exception as print_err:
            logger.error(f"Erro ao imprimir: {print_err}")
            logger.error(traceback.format_exc())
            success = False

    except Exception as e:
        logger.error(f"Erro geral ao imprimir pedido POS58 (ESC/POS+RAW): {e}")
        logger.error(traceback.format_exc())
        success = False

    finally:
        # Limpeza final (apenas o handle da impressora)
        if hprinter:
            try: 
                win32print.ClosePrinter(hprinter)
                logger.debug("Handle da impressora fechado com sucesso")
            except Exception as e: 
                logger.warning(f"Erro ao fechar handle da impressora (final): {e}")

    return success

# Função para teste direto
if __name__ == "__main__":
    # Teste básico do sistema de impressão
    impressora = GerenciadorImpressao()
    
    # Impressoras disponíveis
    print("Impressoras Windows disponíveis:")
    for imp in impressora.listar_impressoras_windows():
        print(f" - {imp['nome']}: {imp['descricao']}")
    
    # Portas seriais
    print("\nPortas seriais disponíveis:")
    for porta in impressora.listar_portas_seriais():
        print(f" - {porta['nome']}: {porta['descricao']}")
    
    # Teste de impressão
    print("\nExecutando teste de impressão...")
    resultado = impressora.imprimir_teste()
    print(f"Resultado: {'SUCESSO' if resultado else 'FALHA'}") 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo principal da aplicação AcriPrint.
Inicia a interface gráfica, configura o armazenamento e gerencia os componentes do sistema.
"""

import os
import sys
import logging
import argparse
import threading
import bcrypt
import traceback
import json
from datetime import datetime, timedelta

# Desativar mensagens de erro de fontes do Qt ANTES de importar qualquer módulo Qt
os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts=false;qt.qpa.backingstore=false"

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QDialog, 
    QWidget, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QThread, QSize, QEvent
from PySide6.QtGui import QFont

# Importações de autenticação
from auth.bling_oauth import BlingOAuth
from core.auth.auth_client import AuthClient  # Caminho corrigido para core.auth.auth_client

# Importações de dados
from data.storage import DataStorage, Storage  # Adicionado Storage à importação
from utils.config import Config  # Adicionando importação da classe Config

# Importações de interface
from ui.main_window import MainWindow, SignalManager
from ui.login_window import LoginWindow
from ui.lock_screen import LockScreen
from ui.themes import setup_dark_theme
from ui.dialog_manager import show_info, show_error, show_question
from ui.settings_dialog import SettingsDialog  # Adicionando importação do SettingsDialog

# Importações de impressão e layouts
from core.layout_printer import DefaultLayoutPrinter
from core.print_controller import PrintController

# Importações de processamento de pedidos
from core.polling import PedidosPoller
from core.filters import OrderFilter  # Caminho corrigido

# Importações de utilities
from utils.qt_utils import ensure_qapplication, safely_emit_in_main_thread

# Configuração do logger global
logger = logging.getLogger(__name__)

# Variável global para manter a thread de polling viva
_polling_auth_thread = None

# Classe para autenticação e polling definida fora da função para evitar destruição prematura
class PollingAuthThread(QThread):
    def __init__(self, oauth_handler, main_window, poller):
        super().__init__()
        self.oauth_handler = oauth_handler
        self.main_window = main_window
        self.poller = poller
        self.setObjectName("PollingAuthThread")
        
    def run(self):
        try:
            # Primeiro tentar autenticação automática
            if self.oauth_handler.authenticate_automatically():
                logger.info("Autenticação automática bem-sucedida, iniciando polling")
                safely_emit_in_main_thread(self.main_window.update_polling_status, "Iniciando verificação...", None)
                safely_emit_in_main_thread(self.main_window.add_activity_log, "Iniciando verificação automática de pedidos")
                
                # Iniciar o polling na thread principal
                safely_emit_in_main_thread(self.poller.start_polling)
            else:
                # Se falhar na autenticação automática, notificar o usuário
                logger.warning("Falha na autenticação automática para polling")
                safely_emit_in_main_thread(self.main_window.update_polling_status, "Erro de autenticação", False)
                safely_emit_in_main_thread(self.main_window.add_activity_log, "Falha na autenticação para verificação de pedidos")
                safely_emit_in_main_thread(self.main_window.show_error, 
                                         "Não foi possível conectar ao Bling. Verifique sua conexão e credenciais.")
        except Exception as e:
            logger.error(f"Erro na thread de autenticação para polling: {e}")
            import traceback
            logger.error(traceback.format_exc())
            safely_emit_in_main_thread(self.main_window.update_polling_status, "Erro", False)
            safely_emit_in_main_thread(self.main_window.show_error, f"Erro ao iniciar verificação: {str(e)}")

def setup_logging():
    """Configura o sistema de logging."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Mudar para DEBUG para desenvolvimento
    
    # Criar handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Mostrar todos os níveis no console
    
    # Formatar as mensagens
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Adicionar handler ao logger
    logger.addHandler(console_handler)
    
    return logger

_shutdown_in_progress = False

def main():
    """Função principal da aplicação."""
    
    # Importar necessários antes de qualquer uso
    from data.storage import DataStorage
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AcriPrint - Sistema de impressão de etiquetas Bling")
    parser.add_argument("--homologation", action="store_true", help="Executar processo de homologação do Bling")
    args = parser.parse_args()
    
    # Configurar logging
    global logger
    logger = setup_logging()
    
    # Se o argumento de homologação foi passado, executar apenas esse processo
    if args.homologation:
        from tests.test_auth import test_homologation
        
        logger.info("Executando processo de homologação do Bling...")
        
        # Inicializar storage
        storage = DataStorage()
        
        # Executar processo de homologação
        success = test_homologation(storage)
        
        if success:
            logger.info("Processo de homologação concluído com sucesso!")
            return 0
        else:
            logger.error("Falha no processo de homologação!")
            return 1
    
    logger.info("Iniciando aplicação AcriPrint...")
    
    # Importar utilitários Qt
    from utils.qt_utils import ensure_qapplication
    
    # Garantir que o QApplication existe antes de prosseguir
    # e torná-lo global para que outros módulos possam acessá-lo
    global qt_app
    qt_app, _ = ensure_qapplication()
    
    qt_app.setApplicationName("AcriPrint")
    qt_app.setApplicationVersion("3.0.0")
    qt_app.setQuitOnLastWindowClosed(False)
    
    # Configurar estilo escuro moderno
    setup_dark_theme(qt_app)
    
    # Definir fonte segura do sistema e evitar problemas com MS Sans Serif
    safe_font = QFont("Arial", 9)  # Fonte padrão Windows segura
    qt_app.setFont(safe_font)
    
    # Forçar o uso de fontes seguras em todos os widgets
    app_style = qt_app.style()
    app_style.setProperty("standardFont", safe_font)
    
    # Verificar se as correções do layout de impressão estão configuradas
    logger.info("Verificando configurações de impressão...")
    try:
        # Mostrar mensagem explícita sobre as correções
        logger.info("==========================================")
        logger.info("FORMATAÇÃO DE IMPRESSÃO ATUALIZADA:")
        logger.info("1. Nome da loja aparece no topo (após código de barras)")
        logger.info("2. NÃO mostra 'Pedido #' abaixo do código de barras")
        logger.info("3. Quantidades formatadas como 'x1', 'x2' (sem decimais)")
        logger.info("4. Quantidades > 1 com fonte aumentada")
        logger.info("==========================================")

        # Não modificar DefaultLayout - as correções já estão no arquivo
    except Exception as e:
        logger.error(f"Erro ao verificar configurações de impressão: {e}")
    
    # Inicializar componentes do sistema
    logger.info("Inicializando componentes do sistema...")
    
    # Inicializar o sistema de armazenamento
    storage = DataStorage()
    
    # Limpar cache expirado na inicialização para evitar excesso de dados
    try:
        storage.clean_expired_orders_cache(days_threshold=60)
        logger.info("Cache de pedidos expirados limpo na inicialização")
    except Exception as e:
        logger.warning(f"Não foi possível limpar cache expirado: {e}")
    
    # Verificar usuário admin
    logger.info("Verificando usuário admin...")
    logger.debug(f"Usuários carregados do banco: {storage.get_users()}")
    
    # Garantir que o usuário admin tenha senha definida
    admin_users = [u for u in storage.get_users() if u.get('name', '').lower() == 'admin']
    if admin_users:
        # Admin existe, garantir que tenha senha
        admin = admin_users[0]
        logger.info("Garantindo senha para usuário admin...")
        storage.set_user_password('admin', 'admin')
        logger.info("Senha do usuário admin verificada/definida")
    
    # Gerenciador de sinais para comunicação entre componentes
    signal_manager = SignalManager()
    
    # Inicializar componentes de autenticação e API
    try:
        oauth_handler = BlingOAuth(parent=None, storage=storage.storage)
        logger.info("BlingOAuth inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar BlingOAuth: {e}")
        traceback.print_exc()
        oauth_handler = BlingOAuth(parent=None, storage=None)
        logger.warning("BlingOAuth inicializado sem storage devido a erro")
        
    auth_client = AuthClient(storage)
    
    # Configurar o filtro de pedidos
    order_filter = OrderFilter(storage)
    
    # Criar o layout printer
    layout_printer = DefaultLayoutPrinter()
    
    # Criar o print controller
    print_controller = PrintController(storage, layout_printer)
    
    # Verificar configuração da impressora
    printer_config = print_controller._get_print_config()
    logger.debug(f"Configuração de impressora carregada: {printer_config}")
    if printer_config.get('printer'):
        logger.info(f"Impressora configurada: {printer_config.get('printer')}")
    else:
        logger.warning("ATENÇÃO: Nenhuma impressora configurada! Configure uma impressora nas Configurações.")
    
    # Inicializar cliente Bling como None, será inicializado pela MainWindow quando necessário
    bling_client = None
    
    # Inicializar poller (verificação periódica de pedidos)
    try:
        poller = PedidosPoller(oauth_handler, storage.storage)
        logger.info("Serviço de polling inicializado com sucesso")
        
        # Ajustar intervalo de polling para ser mais conservador
        # Por padrão, usar um intervalo maior para economizar requisições
        default_settings = storage.get_settings() or {}
        if 'polling_interval' not in default_settings:
            # Definir um intervalo padrão mais conservador (5 minutos = 300 segundos)
            try:
                storage.set_config('polling_interval', 300)
                logger.info("Configurado intervalo de polling padrão de 5 minutos para economizar requisições")
            except Exception as e:
                logger.warning(f"Não foi possível configurar intervalo padrão: {e}")
    except Exception as e:
        logger.error(f"Erro ao inicializar serviço de polling: {e}")
        traceback.print_exc()
        poller = None
        logger.warning("Serviço de polling não pôde ser inicializado")
    
    # Variáveis para controlar as threads
    auth_thread = None
    
    # Timer para atualização do status de polling
    polling_status_timer = QTimer()
    polling_status_timer.setInterval(5000)  # Atualizar a cada 5 segundos
    
    # 4. Fluxo da UI - Começar com a tela de login
    logger.info("Iniciando interface do usuário...")
    login_window = LoginWindow()
    
    # Variáveis para controlar as janelas
    main_window = None
    current_user = None
    
    def handle_login(username, password, remember=False):
        """Manipula a tentativa de login do usuário."""
        nonlocal main_window, current_user
        
        logger.info(f"Tentativa de login: {username}")
        
        # Obter usuários do storage
        users = storage.get_users()
        logger.debug(f"Usuários encontrados: {len(users)}")
        
        user_found = None
        
        for user in users:
            logger.debug(f"Verificando usuário: {user.get('name')}, role: {user.get('role')}")
            if user.get('name') == username:
                user_found = user
                logger.debug(f"Usuário encontrado: {user}")
                break
        
        if not user_found:
            logger.warning(f"Usuário não encontrado: {username}")
            QMessageBox.warning(login_window, "Erro de Login", 
                                "Usuário não encontrado.")
            return
        
        # Verificar senha com bcrypt
        stored_password = user_found.get('password')
        logger.debug(f"Senha armazenada (tipo): {type(stored_password)}")
        logger.debug(f"Senha fornecida: {password}")
        
        if not stored_password:
            logger.error(f"Usuário {username} não tem senha armazenada")
            QMessageBox.warning(login_window, "Erro de Login", 
                                "Erro de configuração: usuário sem senha.")
            return
        
        # Para debugging, usar a senha hardcoded "admin" para o usuário admin
        if username == "admin" and password == "admin":
            logger.info(f"Login com credenciais padrão: {username}")
            current_user = user_found
            
            # Salvar usuário se a opção "lembrar" estiver marcada
            if remember:
                logger.info(f"Salvando usuário para lembrar: {username}")
                storage.set_config('remembered_username', username)
            elif storage.get_config('remembered_username'):
                # Se não lembrar, mas havia um usuário salvo, remover
                storage.delete_config('remembered_username')
            
            # Fechar a janela de login e abrir a principal
            login_window.close()
            main_window = MainWindow(user_found)
            main_window.show()
            auth_client.authenticate_user(username, password)
            connect_signals()
            # Somente agora, após o login, iniciar o fluxo de autorização OAuth
            if not oauth_handler.has_valid_token():
                logger.info("Iniciando autorização OAuth após login...")
                oauth_handler.start_authorization_flow()
            return
        
        try:
            pwd_match = bcrypt.checkpw(
                password.encode('utf-8'), 
                stored_password.encode('utf-8') if isinstance(stored_password, str) else stored_password
            )
            logger.debug(f"Resultado da verificação de senha: {pwd_match}")
            
            if not pwd_match:
                logger.warning(f"Senha incorreta para usuário: {username}")
                QMessageBox.warning(login_window, "Erro de Login", 
                                    "Senha incorreta.")
                return
                
        except Exception as e:
            logger.error(f"Erro ao verificar senha: {str(e)}")
            QMessageBox.warning(login_window, "Erro de Login", 
                                "Erro ao verificar senha.")
            return
            
        # Login bem-sucedido
        logger.info(f"Login bem-sucedido: {username} (Perfil: {user_found.get('role')})")
        current_user = user_found
        
        # Salvar usuário se a opção "lembrar" estiver marcada
        if remember:
            logger.info(f"Salvando usuário para lembrar: {username}")
            storage.set_config('remembered_username', username)
        elif storage.get_config('remembered_username'):
            # Se não lembrar, mas havia um usuário salvo, remover
            storage.delete_config('remembered_username')
        
        # Fechar a janela de login e abrir a principal
        login_window.close()
        main_window = MainWindow(user_found)
        main_window.show()
        auth_client.authenticate_user(username, password)
        connect_signals()
        # Somente agora, após o login, iniciar o fluxo de autorização OAuth
        if not oauth_handler.has_valid_token():
            logger.info("Iniciando autorização OAuth após login...")
            oauth_handler.start_authorization_flow()
    
    def handle_reset_password(username):
        """Manipula a solicitação de redefinição de senha."""
        logger.info(f"Solicitação de redefinição de senha para: {username}")
        
        if not username:
            QMessageBox.warning(login_window, "Redefinição de Senha", 
                                "Por favor, digite seu nome de usuário primeiro.")
            return
        
        # Verificar se o usuário existe
        users = storage.get_users()
        user_found = None
        
        for user in users:
            if user.get('name') == username:
                user_found = user
                break
        
        if not user_found:
            logger.warning(f"Usuário não encontrado para redefinição de senha: {username}")
            QMessageBox.warning(login_window, "Redefinição de Senha", 
                                "Usuário não encontrado.")
            return
        
        # Chamar o método de reset de senha no auth_client para emitir os sinais
        auth_client.reset_password(username)
        
        # Em um sistema real, aqui enviaria um email com link de redefinição
        # Para este protótipo, vamos mostrar uma mensagem de confirmação
        msg = QMessageBox(login_window)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Redefinição de Senha")
        msg.setText(f"Instruções de redefinição de senha foram enviadas para o email associado à conta {username}.")
        msg.setInformativeText("Por favor, verifique seu email para continuar o processo de redefinição.")
        msg.exec()
        
        logger.info(f"Solicitação de redefinição de senha processada para: {username}")
    
    def handle_new_order(order):
        """Manipula novo pedido recebido"""
        if not order:
            logger.error("Pedido recebido é inválido (None)")
            return
        
        try:
            # Verifica se recebemos uma lista ou um único pedido
            if isinstance(order, list):
                logger.info(f"Recebidos {len(order)} novos pedidos")
                for single_order in order:
                    if isinstance(single_order, dict):
                        order_id = single_order.get('id', 'ID não encontrado')
                        logger.info(f"Processando pedido da lista: {order_id}")
                        # TODO: Implementar lógica para cada pedido individual
                    else:
                        logger.warning(f"Item inválido na lista de pedidos: {type(single_order)}")
            elif isinstance(order, dict):
                order_id = order.get('id', 'ID não encontrado')
                logger.info(f"Novo pedido recebido: {order_id}")
                # TODO: Implementar lógica de novo pedido
            else:
                logger.warning(f"Tipo de pedido recebido não suportado: {type(order)}")
        except Exception as e:
            logger.error(f"Erro ao processar novo pedido: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def handle_polling_error(error_message):
        """Manipula erro no polling"""
        if not error_message:
            error_message = "Erro desconhecido no polling"
        logger.error(f"Erro no polling: {error_message}")
        # TODO: Implementar lógica de erro no polling
    
    def handle_auth_success():
        """Manipula o evento de sucesso na autenticação."""
        try:
            # Usar uma variável estática para evitar múltiplas chamadas em rápida sucessão
            if hasattr(handle_auth_success, "last_call_time"):
                import time
                current_time = time.time()
                # Se chamado novamente em menos de 3 segundos, ignorar
                if current_time - handle_auth_success.last_call_time < 3:
                    logger.debug("Ignorando chamada duplicada de auth_success (menos de 3s)")
                    return
                handle_auth_success.last_call_time = current_time
            else:
                import time
                handle_auth_success.last_call_time = time.time()
            
            current_thread = threading.current_thread()
            logger.info(f"Autenticação bem sucedida (Thread: {current_thread.name}, ID: {current_thread.ident})")
            
            # Importar o utilitário Qt para execução thread-safe
            from utils.qt_utils import ensure_qapplication, safely_emit_in_main_thread, qt_helper
            
            # Verificar se temos um token válido e salvar na configuração
            valid_token = oauth_handler.get_valid_access_token()
            if valid_token:
                logger.info("Token OAuth válido obtido, salvando na configuração")
                try:
                    config = Config()
                    config.set('bling', 'api_key', valid_token)
                    config.save()
                    logger.info("Token OAuth salvo na configuração com sucesso")
                except Exception as config_error:
                    logger.error(f"Erro ao salvar token na configuração: {config_error}")
            
            # Função a ser executada na thread da UI
            def update_ui():
                ui_thread = threading.current_thread()
                logger.debug(f"Executando update_ui no thread: {ui_thread.name}, ID: {ui_thread.ident}")
                
                # Verificar se main_window já existe no escopo global ou criar nova referência
                nonlocal main_window
                if main_window is None:
                    logger.warning("main_window ainda não foi inicializada")
                    return
                    
                # Atualizar status
                main_window.update_oauth_status("Autenticado", True)
                
                # Inicializar o cliente Bling com o token recém-obtido
                if hasattr(main_window, '_init_bling_client'):
                    try:
                        logger.info("Inicializando cliente Bling após autenticação")
                        # Forçar recarregamento das configurações antes de inicializar
                        from utils.config import Config
                        config = Config()
                        config.reload()  # Recarregar para garantir token atualizado
                        # Inicializar cliente
                        main_window._init_bling_client()
                    except Exception as e:
                        logger.error(f"Erro ao inicializar cliente Bling após autenticação: {e}")
                
                # Iniciar polling se configurado para isso e não estiver ativo
                auto_start = storage.get_config('auto_start_polling', False)
                if auto_start and not poller.is_polling():
                    logger.info("Iniciando polling automático após autenticação")
                    start_polling()
            
            # Garantir que temos um QApplication válido
            app, created = ensure_qapplication()
            
            # Usar QTimer.singleShot para executar no thread da UI
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, update_ui)
            
        except Exception as e:
            logger.error(f"Erro ao processar sucesso de autenticação: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def handle_auth_failure(error_message):
        """Manipula falha na autenticação"""
        try:
            if not error_message:
                error_message = "Erro desconhecido na autenticação"
            logger.error(f"Falha na autenticação: {error_message}")
            
            # Importar o utilitário Qt para execução thread-safe
            from utils.qt_utils import ensure_qapplication
            
            # Função para atualizar a UI no thread principal
            def update_ui():
                logger.debug("Executando update_ui de falha no thread principal")
                if 'main_window' in globals() and main_window is not None:
                    main_window.update_oauth_status("Não autenticado", False)
                    main_window.add_activity_log(f"Falha na autenticação: {error_message}", "error")
            
            # Garantir que temos um QApplication válido
            app, _ = ensure_qapplication()
            
            # Usar QTimer.singleShot para executar no thread da UI
            try:
                from PySide6.QtCore import QTimer
                timer_class = QTimer
                qt_version = "PySide6"
            except ImportError:
                # Não tentamos mais importar PyQt5 como fallback
                logger.error("PySide6 não está instalado")
                raise
            
            # Agendar para o thread da UI
            logger.debug(f"Auth failure: Agendando update_ui para o thread principal ({qt_version})")
            timer_class.singleShot(0, update_ui)
            
        except Exception as e:
            logger.error(f"Erro ao processar falha de autenticação: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def handle_print_success(order_id):
        """Manipula sucesso na impressão"""
        if not order_id:
            logger.warning("ID do pedido não fornecido para impressão bem sucedida")
            return
        
        logger.info(f"Ordem {order_id} impressa com sucesso")
        main_window.update_print_status(f"Pedido {order_id} impresso", True)
        main_window.add_activity_log(f"Pedido {order_id} impresso com sucesso")
    
    def handle_print_error(order_id, error_message):
        """Manipula erro na impressão"""
        if not error_message:
            error_message = "Erro desconhecido na impressão"
        
        order_id_str = order_id if order_id else "desconhecido"
        logger.error(f"Erro na impressão do pedido {order_id_str}: {error_message}")
        main_window.update_print_status(f"Erro na impressão do pedido {order_id_str}", False)
        main_window.add_activity_log(f"Erro na impressão do pedido {order_id_str}: {error_message}")
    
    def handle_login_success():
        """Manipula sucesso no login"""
        logger.info("Login realizado com sucesso")
        main_window.update_login_status("Logado", True)
        main_window.add_activity_log("Login realizado com sucesso")
    
    def handle_login_failure(error_message):
        """Manipula falha no login"""
        if not error_message:
            error_message = "Erro desconhecido no login"
        logger.error(f"Falha no login: {error_message}")
        main_window.update_login_status("Não logado", False)
        main_window.add_activity_log(f"Falha no login: {error_message}")
    
    def handle_password_reset_success():
        """Manipula sucesso no reset de senha"""
        logger.info("Senha resetada com sucesso")
        # Mostrar mensagem de sucesso
        show_info(main_window, "Sucesso", "Senha resetada com sucesso")
        main_window.add_activity_log("Senha resetada com sucesso")
    
    def handle_password_reset_failure(error_message):
        """Manipula falha no reset de senha"""
        if not error_message:
            error_message = "Erro desconhecido no reset de senha"
        logger.error(f"Falha no reset de senha: {error_message}")
        main_window.show_error("Erro no reset de senha", error_message)
        main_window.add_activity_log(f"Falha no reset de senha: {error_message}")
    
    def connect_signals():
        """Conecta sinais entre as classes."""
        # Sinais do polling
        poller.new_orders_found.connect(handle_new_order)
        poller.error_occurred.connect(handle_polling_error)
        
        # Sinais de autenticação OAuth
        oauth_handler.signals.auth_succeeded.connect(handle_auth_success)
        oauth_handler.signals.auth_failed.connect(handle_auth_failure)
        oauth_handler.signals.authorization_needed.connect(start_bling_auth)
        
        # Sinais de impressão
        print_controller.signals.print_finished.connect(handle_print_success)
        print_controller.signals.print_error.connect(handle_print_error)
        
        # Sinais de login
        auth_client.login_success.connect(handle_login_success)
        auth_client.login_failure.connect(handle_login_failure)
        auth_client.password_reset_success.connect(handle_password_reset_success)
        auth_client.password_reset_failure.connect(handle_password_reset_failure)
        
        # Sinais da janela principal
        if hasattr(main_window, 'toggle_polling_requested'):
            main_window.toggle_polling_requested.connect(lambda start: start_polling() if start else stop_polling())
        
        # Conectar janela principal para atualizar status de ferramentas
        if polling_status_timer is not None:
            polling_status_timer.timeout.connect(main_window.update_polling_status)
        
        # Sinais do SettingsDialog
        if hasattr(SettingsDialog, 'settings_saved'):
            # Pegar a instância do diálogo quando for criada em open_settings
            # e conectar o sinal
            logger.debug("Settings dialog tem sinal settings_saved")
        else:
            logger.debug("Settings dialog NÃO tem sinal settings_saved")
            
        # Conectando botões específicos da UI
        logger.debug("Conectando action_settings...")
        if hasattr(main_window, 'action_settings'):
            main_window.action_settings.triggered.connect(open_settings)
            
        # Conectar o settings_action (na toolbar)
        logger.debug("Conectando settings_action...")
        if hasattr(main_window, 'settings_action'):
            main_window.settings_action.triggered.connect(open_settings)
            
        logger.debug("Conectando settings_button...")
        if hasattr(main_window, 'settings_button'):
            # Verificar se settings_button tem o método clicked (DashboardButton) ou triggered (QAction)
            if hasattr(main_window.settings_button, 'clicked'):
                logger.debug("Conectando settings_button.clicked...")
                main_window.settings_button.clicked.connect(open_settings)
            elif hasattr(main_window.settings_button, 'triggered'):
                logger.debug("Conectando settings_button.triggered...")
                main_window.settings_button.triggered.connect(open_settings)
            else:
                logger.warning("settings_button não tem sinal clicked nem triggered")
            
        # Conectar botão de autenticação Bling
        if hasattr(main_window, 'bling_auth_button'):
            # Desconectar conexões automáticas criadas na MainWindow para evitar conflito
            try:
                main_window.bling_auth_button.clicked.disconnect()
                logger.info("Desconectado eventos anteriores do botão de autenticação Bling")
            except Exception:
                pass
            
            # Conectar o botão ao método de autenticação deste módulo
            main_window.bling_auth_button.clicked.connect(start_bling_auth)
    
    def start_bling_auth():
        """Inicia o processo de autenticação com o Bling usando o fluxo OAuth."""
        nonlocal auth_thread
        logger.info("Iniciando autenticação com Bling...")
        
        # Verificar se a janela principal já está inicializada
        if not main_window:
            logger.error("Não é possível iniciar autenticação Bling sem a janela principal")
            return
        
        # Verificar primeiro se já temos um token válido
        if oauth_handler.has_valid_token():
            logger.info("Token OAuth já é válido, executando handle_auth_success")
            handle_auth_success()
            return
            
        # Verificar se a autenticação já está em andamento
        if oauth_handler.is_authenticating:
            logger.warning("Processo de autenticação já está em andamento")
            return
            
        # Criar uma nova thread para executar a autenticação automática
        class AuthThread(QThread):
            def run(self):
                try:
                    logger.info("Iniciando processo de autenticação automática em thread separada")
                    result = oauth_handler.authenticate_automatically()
                    logger.info(f"Resultado da autenticação automática: {'sucesso' if result else 'falha'}")
                    
                    # Se falhar na autenticação automática, tentar o fluxo normal
                    if not result:
                        logger.info("Tentando iniciar fluxo de autorização padrão")
                        oauth_handler.start_authorization_flow()
                except Exception as e:
                    logger.error(f"Erro na thread de autenticação: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
        
        # Criar e iniciar a thread
        auth_thread = AuthThread()
        auth_thread.setObjectName("BlingAuthThread")
        auth_thread.start()
        
        # Exibir mensagem para o usuário
        main_window.statusBar().showMessage("Conectando ao Bling, aguarde...", 5000)
    
    def start_polling():
        """Inicia o polling de pedidos."""
        nonlocal auth_thread
        
        logger.info("Iniciando processo de autenticação para polling...")
        
        # Verificar se já existe uma thread rodando e pará-la
        if auth_thread and auth_thread.isRunning():
            logger.info("Thread de polling já está em execução, parando antes de iniciar nova")
            try:
                auth_thread.quit()
                if not auth_thread.wait(3000):  # Aguardar até 3 segundos
                    logger.warning("Thread de polling não encerrou, forçando término")
                    auth_thread.terminate()
                    auth_thread.wait(1000)
            except Exception as e:
                logger.error(f"Erro ao parar thread de polling existente: {e}")
        
        # Atualizar status inicial
        main_window.update_polling_status("Autenticando...", None)
        main_window.add_activity_log("Iniciando autenticação para verificação de pedidos")
        
        # Limpar cache de pedidos expirados antes de iniciar
        try:
            storage.clean_expired_orders_cache(days_threshold=60)
            logger.info("Cache de pedidos expirados limpo antes de iniciar polling")
        except Exception as e:
            logger.warning(f"Não foi possível limpar cache expirado: {e}")
            
        # Iniciar thread de autenticação para polling usando a classe global
        auth_thread = PollingAuthThread(oauth_handler, main_window, poller)
        
        # Garantir que a thread termine corretamente quando o aplicativo é encerrado
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(auth_thread.quit)
        
        # Manter referência global ao thread para evitar que seja coletado pelo garbage collector
        global _polling_auth_thread
        _polling_auth_thread = auth_thread
        
        auth_thread.start()
    
    def stop_polling():
        """Interrompe o polling de pedidos."""
        logger.info("Parando verificação de pedidos...")
        main_window.update_polling_status("Parando...", None)
        main_window.add_activity_log("Parando verificação automática de pedidos")
        
        # Parar o polling
        poller.stop_polling()
    
    def open_settings():
        """Abre a janela de configurações."""
        logger.info("Abrindo janela de configurações.")
        
        try:
            # Usar o diálogo de configurações existente
            from ui.settings_dialog import show_settings_dialog
            
            # Exibir o diálogo e processar o resultado
            if show_settings_dialog(main_window, current_user=current_user):
                logger.info("Configurações salvas com sucesso")
                # Chamar função de atualização quando as configurações são salvas
                on_settings_saved()
            else:
                logger.info("Configurações canceladas pelo usuário")
            
        except Exception as e:
            logger.error(f"Erro ao abrir configurações: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Exibir mensagem de erro para o usuário
            QMessageBox.critical(main_window, "Erro", f"Erro ao abrir configurações: {e}")
    
    def show_lock_screen():
        """Exibe a tela de bloqueio."""
        logger.info("Bloqueando aplicação")
        lock_screen = LockScreen()
        main_window.hide()
        
        def handle_unlock(password):
            """Manipula tentativa de desbloqueio."""
            # Verificar senha do usuário atual
            stored_password = current_user.get('password')
            if bcrypt.checkpw(
                password.encode('utf-8'), 
                stored_password.encode('utf-8') if isinstance(stored_password, str) else stored_password
            ):
                logger.info("Aplicação desbloqueada")
                lock_screen.close()
                main_window.show()
                return True
            else:
                logger.warning("Tentativa de desbloqueio com senha incorreta")
                QMessageBox.warning(lock_screen, "Erro de Desbloqueio", 
                                    "Senha incorreta.")
                return False
        
        lock_screen.unlock_requested.connect(handle_unlock)
        lock_screen.exec()
    
    # Função para desligar a aplicação de forma segura
    def shutdown_app():
        global _shutdown_in_progress
        if _shutdown_in_progress:
            logger.info("Shutdown já em andamento, ignorando chamada duplicada.")
            return
        _shutdown_in_progress = True
        nonlocal auth_thread, main_window
        
        logger.info("=============================================")
        logger.info("Iniciando desligamento seguro da aplicação...")
        logger.info("=============================================")
        
        # Encerrar thread global de polling se existir
        global _polling_auth_thread
        if _polling_auth_thread is not None and _polling_auth_thread.isRunning():
            logger.info("Encerrando thread global de polling...")
            try:
                _polling_auth_thread.quit()
                # Espera até 3 segundos para a thread terminar
                if not _polling_auth_thread.wait(3000):
                    logger.warning("Thread global não encerrou, forçando término...")
                    _polling_auth_thread.terminate()
                    _polling_auth_thread.wait(1000)
            except Exception as e:
                logger.error(f"Erro ao encerrar thread global de polling: {e}")
        
        # Tentar obter informações sobre threads ativas
        active_threads = threading.enumerate()
        logger.info(f"Threads ativas no momento do desligamento: {len(active_threads)}")
        for thread in active_threads:
            logger.info(f" - Thread: {thread.name} (ID: {thread.ident}), Daemon: {thread.daemon}")
        
        # Parar o polling se estiver ativo
        if 'poller' in globals() and poller and poller.is_polling():
            logger.info("Parando verificação de pedidos...")
            try:
                poller.stop_polling()
                logger.info("Aguardando finalização do polling (até 5 segundos)...")
                if not poller.wait(5000):  # Espera até 5 segundos
                    logger.warning("Thread de polling não finalizou em tempo, forçando término...")
                    poller.terminate()
                    poller.wait(1000)
                logger.info("Polling finalizado")
            except Exception as e:
                logger.error(f"Erro ao parar thread de polling: {e}")
        else:
            logger.info("Polling não está ativo, não é necessário parar")
        
        # Encerrar thread de autenticação se estiver ativa
        if auth_thread and auth_thread.isRunning():
            logger.info("Encerrando thread de autenticação...")
            try:
                auth_thread.quit()
                # Espera até 3 segundos para a thread terminar
                logger.info("Aguardando finalização da thread de autenticação (até 3 segundos)...")
                if not auth_thread.wait(3000):
                    logger.warning("Thread de autenticação não encerrou normalmente, forçando término...")
                    auth_thread.terminate()
                    auth_thread.wait(1000)
                logger.info("Thread de autenticação finalizada")
            except Exception as e:
                logger.error(f"Erro ao encerrar thread de autenticação: {e}")
        else:
            logger.info("Thread de autenticação não está ativa, não é necessário encerrar")
        
        # Limpar referências para objetos principais
        if main_window:
            try:
                # Fechar e limpar a janela principal
                logger.info("Fechando e limpando janela principal")
                if not main_window.isHidden():
                    main_window.close()
                main_window.deleteLater()
                logger.info("Janela principal fechada")
            except Exception as e:
                logger.error(f"Erro ao fechar janela principal: {e}")
        
        # Garantir que todas as threads QThread sejam encerradas
        try:
            from utils.qt_utils import shutdown_threads
            logger.info("Chamando utilitário shutdown_threads...")
            threads_closed = shutdown_threads()
            logger.info(f"shutdown_threads finalizou {threads_closed} threads")
        except Exception as e:
            logger.error(f"Erro ao encerrar threads via shutdown_threads: {e}")
            
            # Fallback: tentar encerrar threads manualmente
            try:
                from PySide6.QtCore import QThread
                qthreads = [obj for obj in globals().values() 
                          if isinstance(obj, QThread) and obj.isRunning()]
                
                logger.info(f"Fallback: Encontradas {len(qthreads)} threads QThread ainda em execução")
                
                for thread in qthreads:
                    try:
                        thread_name = thread.objectName() or str(thread)
                        logger.warning(f"Forçando encerramento da thread: {thread_name}")
                        thread.quit()
                        if not thread.wait(1500):  # Esperar mais tempo (1.5s)
                            logger.warning(f"Thread {thread_name} não finalizou com quit(), usando terminate()")
                            thread.terminate()
                            thread.wait(1000)
                        logger.info(f"Thread {thread_name} finalizada")
                    except Exception as thread_err:
                        logger.error(f"Erro ao terminar thread {thread}: {thread_err}")
            except Exception as thread_err:
                logger.error(f"Erro ao processar lista de threads: {thread_err}")
        
        # Liberar outros recursos, se necessário
        try:
            # Aguardar um momento para permitir que as threads terminem
            import time
            logger.info("Aguardando 0.5 segundo para garantir que todas as operações foram concluídas...")
            time.sleep(0.5)
            
            # Verificar novamente threads ativas
            active_threads = threading.enumerate()
            logger.info(f"Threads ativas após tentativa de encerramento: {len(active_threads)}")
            for thread in active_threads:
                if thread != threading.main_thread():
                    logger.info(f" - Thread não principal ainda ativa: {thread.name} (ID: {thread.ident}), Daemon: {thread.daemon}")
            
            # Logging final
            logger.info("Desligamento seguro concluído")
            
            # Limpar referências QApplication
            if 'qt_app' in globals() and qt_app:
                # Processar eventos pendentes antes de sair
                logger.info("Processando eventos pendentes...")
                qt_app.processEvents()
                logger.info("Chamando QApplication.quit()...")
                qt_app.quit()
                logger.info("QApplication.quit() chamado")
                import sys
                sys.exit(0)
        except Exception as e:
            logger.error(f"Erro no encerramento final: {e}")
            import sys
            sys.exit(1)
        
        logger.info("=============================================")
        logger.info("Processo de desligamento concluído")
        logger.info("=============================================")
    
    # Conectar o handler de fechamento quando a janela principal for criada
    def handle_main_window_close(event):
        """Manipula o evento de fechamento da janela principal."""
        logger.info("Evento de fechamento da janela principal recebido")
        
        # Verificar se há thread de autenticação em execução e garantir que termine
        nonlocal auth_thread
        if auth_thread and auth_thread.isRunning():
            logger.info("Thread de autenticação em execução, parando...")
            try:
                auth_thread.quit()
                if not auth_thread.wait(3000):  # Aguardar até 3 segundos
                    logger.warning("Thread de autenticação não encerrou normalmente, forçando término")
                    auth_thread.terminate()
                    auth_thread.wait(1000)
            except Exception as e:
                logger.error(f"Erro ao parar thread de autenticação: {e}")
        else:
            logger.info("Thread de autenticação não está ativa, não é necessário encerrar")
        
        # Verificar se é um usuário admin
        if current_user.get('role') == 'admin':
            logger.info("Fechando aplicação (usuário admin)")
            shutdown_app()
            event.accept()
        else:
            # Para usuários não-admin, solicitar senha de administrador
            logger.info("Tentativa de fechamento por usuário não-admin. Solicitando confirmação...")
            lock_screen = LockScreen(exit_confirmation=True)
            
            def handle_exit_confirmation(password):
                # Verificar se há algum usuário admin
                admin_users = [u for u in storage.get_users() if u.get('role') == 'admin']
                
                if not admin_users:
                    logger.error("Não há usuários admin cadastrados!")
                    QMessageBox.critical(lock_screen, "Erro", 
                                        "Não há usuários administradores cadastrados no sistema.")
                    return False
                
                # Verificar senha contra todos os admins (qualquer um pode autorizar)
                for admin in admin_users:
                    stored_password = admin.get('password')
                    if bcrypt.checkpw(
                        password.encode('utf-8'), 
                        stored_password.encode('utf-8') if isinstance(stored_password, str) else stored_password
                    ):
                        logger.info(f"Fechamento autorizado pelo admin: {admin.get('name')}")
                        lock_screen.close()
                        shutdown_app()
                        
                        # Usar QTimer para garantir que o evento de fechamento ocorra após o processamento atual
                        QTimer.singleShot(0, lambda: main_window.close())
                        return True
                
                logger.warning("Fechamento negado: senha de admin incorreta")
                QMessageBox.warning(lock_screen, "Acesso Negado", 
                                    "Senha de administrador incorreta.")
                return False
            
            lock_screen.unlock_requested.connect(handle_exit_confirmation)
            
            # Se o diálogo for cancelado, ignorar o evento de fechamento
            if lock_screen.exec() == 0:
                logger.info("Fechamento cancelado pelo usuário")
                event.ignore()
            else:
                event.ignore()  # Manter a janela aberta até confirmação
    
    # Conectar os sinais da janela de login
    login_window.login_requested.connect(handle_login)
    login_window.reset_password_requested.connect(handle_reset_password)
    
    # Carregar usuário lembrado, se houver
    remembered_username = storage.get_config('remembered_username')
    if remembered_username:
        logger.info(f"Carregando usuário lembrado: {remembered_username}")
        login_window.set_remembered_username(remembered_username)
    
    # Garantir que a aplicação seja encerrada corretamente
    qt_app.aboutToQuit.connect(shutdown_app)
    
    # Recarregar configurações de impressão quando as configurações forem salvas
    def on_settings_saved():
        """Função chamada quando as configurações são salvas."""
        logger.info("Configurações salvas, recarregando configurações de impressão...")
        if print_controller:
            print_controller.reload_config()
            
        # Verificar e ajustar configurações de polling
        try:
            settings = storage.get_settings() or {}
            polling_interval = settings.get('polling_interval', 0)
            
            # Se o intervalo de polling for muito pequeno, aumentar para evitar muitas requisições
            if polling_interval > 0 and polling_interval < 60:
                logger.warning(f"Intervalo de polling muito pequeno ({polling_interval}s), ajustando para mínimo de 60s")
                storage.set_config('polling_interval', 60)
                
                # Notificar usuário se a janela principal existir
                if main_window:
                    main_window.add_activity_log("Intervalo de polling ajustado para mínimo de 60 segundos para evitar excesso de requisições")
                    QMessageBox.information(main_window, "Ajuste de Intervalo", 
                                          "O intervalo de polling foi ajustado para o mínimo de 60 segundos para evitar excesso de requisições à API.")
            
            # Atualizar poller se estiver ativo
            if poller:
                poller.update_settings()
                logger.info("Configurações de polling atualizadas")
        except Exception as e:
            logger.error(f"Erro ao ajustar configurações de polling: {e}")
    
    # Configurar as credenciais do usuário Bling se disponíveis nas configurações
    def configure_bling_credentials():
        """Configura as credenciais do usuário Bling a partir das configurações."""
        try:
            # Obter credenciais das configurações
            settings = storage.get_settings() or {}
            bling_settings = settings.get('bling', {})
            
            username = bling_settings.get('username')
            password = bling_settings.get('password')
            
            if username and password:
                logger.info("Configurando credenciais do usuário Bling a partir das configurações")
                logger.debug(f"Usando usuário '{username}' para autenticação Bling")
                oauth_handler.save_bling_user_credentials(username, password)
                return True
            else:
                logger.warning("Credenciais do usuário Bling não encontradas nas configurações")
                if not username:
                    logger.debug("Username não encontrado nas configurações")
                if not password:
                    logger.debug("Password não encontrado nas configurações")
                return False
        except Exception as e:
            logger.error(f"Erro ao configurar credenciais do usuário Bling: {e}")
            return False
    
    # Tentar configurar credenciais do Bling
    configure_bling_credentials()

    # Loop principal da aplicação
    logger.info("Iniciando loop de eventos Qt...")
    
    # Registrar objeto da aplicação Qt para acessibilidade global
    from utils.qt_utils import qt_helper
    qt_helper.ensure_app()  # Garantir que temos um QApplication
    
    try:
        # Mostrar a janela de login
        login_window.show()
        
        # Verificar se deve auto-preencher o nome de usuário
        remembered_username = storage.get_config('remembered_username', '')
        if remembered_username:
            login_window.set_remembered_username(remembered_username)
            
        # Iniciar o loop de eventos
        result = qt_app.exec()
        shutdown_app()  # Garantir limpeza mesmo após saída normal
        sys.exit(result)
    except KeyboardInterrupt:
        logger.info("Interrupção de teclado detectada, finalizando...")
        shutdown_app()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro no loop principal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        shutdown_app()
        sys.exit(1)


if __name__ == "__main__":
    main() 
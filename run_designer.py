#!/usr/bin/env python3
"""
Script para executar o Designer de Impressão de forma independente.
Este script garante que o QApplication seja inicializado corretamente.
"""

import sys
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    # Criar a aplicação explicitamente
    app = QApplication(sys.argv)
    
    # Importar o PrintDesignerDialog apenas após criar a aplicação
    from ui.print_designer import PrintDesignerDialog
    
    # Criar e mostrar o diálogo
    designer = PrintDesignerDialog(None)
    
    # Executar o diálogo
    result = designer.exec_()
    
    # Sair da aplicação
    sys.exit(app.exec_()) 
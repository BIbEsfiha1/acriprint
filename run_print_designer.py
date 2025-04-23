#!/usr/bin/env python3
"""
Script independente para executar o designer de impressão.
Usado para resolver problemas de compatibilidade entre PyQt5 e PySide6.
"""

import sys
import os
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Função principal para executar o designer de impressão."""
    # Verificar os argumentos
    if len(sys.argv) != 2:
        print("Uso: python run_print_designer.py <caminho_saida>")
        return 1
    
    output_path = sys.argv[1]
    logger.info(f"Iniciando designer de impressão. Saída para: {output_path}")
    
    try:
        # Tentar importar PyQt5
        from PyQt5.QtWidgets import QApplication, QDialog
        
        # Importar o designer
        try:
            from ui.print_designer import PrintDesignerDialog
        except ImportError:
            logger.error("Não foi possível importar PrintDesignerDialog. Verifique o caminho.")
            return 2
        
        # Criar aplicação QApplication limpa
        app = QApplication([])
        
        # Criar e exibir o diálogo
        dialog = PrintDesignerDialog(None, True)
        
        # Executar o diálogo
        result = dialog.exec_()
        
        # Processar o resultado
        if result == QDialog.Accepted and dialog.canvas:
            # Obter dados do layout
            layout_data = dialog.canvas.get_elements_data()
            
            # Salvar dados em arquivo JSON
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(layout_data, f, indent=2)
            
            logger.info(f"Layout salvo com sucesso em: {output_path}")
            return 0
        else:
            logger.info("Designer fechado sem salvar alterações")
            return 1
            
    except ImportError:
        logger.error("PyQt5 não está instalado. Instalando...")
        try:
            import subprocess
            result = subprocess.run([sys.executable, "-m", "pip", "install", "PyQt5"], 
                                    capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("PyQt5 instalado com sucesso. Execute este script novamente.")
            else:
                logger.error(f"Erro ao instalar PyQt5: {result.stderr}")
        except Exception as e:
            logger.error(f"Erro ao instalar PyQt5: {e}")
        return 3
        
    except Exception as e:
        logger.error(f"Erro ao executar o designer de impressão: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 4

if __name__ == "__main__":
    sys.exit(main()) 
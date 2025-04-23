#!/usr/bin/env python3
"""
Script para aplicar imediatamente mudanças na formatação de quantidades
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("QuantityPatcher")

def patch_layouts_default_layout():
    """
    Aplica um patch no arquivo layouts/default_layout.py para substituir
    a formatação de quantidades e torná-las muito mais visíveis.
    """
    logger.info("Iniciando patch da formatação de quantidades...")
    
    # Caminho para o arquivo de layout
    default_layout_path = Path("layouts/default_layout.py")
    
    if not default_layout_path.exists():
        logger.error(f"Arquivo {default_layout_path} não encontrado!")
        return False
    
    # Ler o conteúdo do arquivo
    logger.info(f"Lendo arquivo {default_layout_path}")
    try:
        with open(default_layout_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Erro ao ler o arquivo: {e}")
        return False
    
    # Substituição 1: Modificar a formatação de quantidade
    # Procurar o bloco que formata a quantidade e substituí-lo
    target_block = """                    # Formatar quantidade como "x1", "x2", etc.
                    qtd_text = f"x{int(qtd) if qtd.is_integer() else qtd}"
                    
                    # Configurar fonte para quantidade (negrito se for maior que 1)
                    if qtd > 1:
                        painter.setFont(QFont("Arial", font_size, QFont.Bold))
                    
                    # Se a descrição for longa, quebrar em múltiplas linhas
                    y_item_start = y_pos
                    painter.drawText(0, y_pos + metrics.height(), qtd_text)
                    
                    # Restaurar fonte padrão após desenhar a quantidade
                    if qtd > 1:
                        painter.setFont(default_font)"""
    
    replacement_block = """                    # Formatar quantidade com destaque visual para qtd > 1
                    if qtd > 1:
                        # Usar fonte muito maior e adicionar ponto de exclamação
                        qtd_text = f"x{int(qtd) if qtd.is_integer() else qtd}!"
                        super_large_font = QFont("Arial", font_size + 5, QFont.Bold)
                        painter.setFont(super_large_font)
                        painter.drawText(0, y_pos + metrics.height(), qtd_text)
                        logger.info(f"Imprimindo quantidade {qtd} com DESTAQUE VISUAL")
                    else:
                        # Formato padrão para qtd = 1
                        qtd_text = f"x{int(qtd) if qtd.is_integer() else qtd}"
                        painter.setFont(default_font)
                        painter.drawText(0, y_pos + metrics.height(), qtd_text)
                    
                    # Restaurar fonte padrão após desenhar a quantidade
                    painter.setFont(default_font)
                    
                    # Registrar posição inicial do item para referência
                    y_item_start = y_pos"""
    
    # Realizar a substituição
    if target_block in content:
        logger.info("Encontrado bloco de formatação de quantidade! Aplicando substituição...")
        new_content = content.replace(target_block, replacement_block)
        
        # Fazer backup do arquivo original
        backup_path = default_layout_path.with_suffix(".py.bak")
        logger.info(f"Criando backup em {backup_path}")
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            return False
        
        # Escrever o novo conteúdo
        logger.info("Escrevendo novo conteúdo com formatação melhorada")
        try:
            with open(default_layout_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except Exception as e:
            logger.error(f"Erro ao escrever o arquivo modificado: {e}")
            return False
        
        logger.info("Patch aplicado com sucesso!")
        return True
    else:
        logger.error("Bloco de formatação de quantidade não encontrado no arquivo!")
        return False

if __name__ == "__main__":
    if patch_layouts_default_layout():
        print("SUCESSO! A formatação de quantidades foi atualizada para alta visibilidade.")
        print("As quantidades > 1 agora serão exibidas em fonte muito maior e com ponto de exclamação!")
        print("Execute novamente o aplicativo para ver as mudanças.")
        sys.exit(0)
    else:
        print("ERRO! Não foi possível aplicar as alterações.")
        print("Verifique o log para mais detalhes.")
        sys.exit(1) 
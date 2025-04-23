#!/usr/bin/env python3
from PySide6.QtWidgets import QApplication
import sys
from data.storage import Storage
from auth.bling_oauth import BlingOAuth

def main():
    app = QApplication(sys.argv)
    
    # Criar instância do storage
    storage = Storage()
    
    # Criar instância do BlingOAuth
    oauth = BlingOAuth(storage=storage)
    
    # Salvar credenciais
    success = oauth._save_credentials(
        "daca08ae8076306f6c7ac1eea81e5cdd721e5a98",
        "3b077a6999a6c8255f97dd18fce5717be5b25bc456e168dbf0965fa802f0",
        remember=True
    )
    
    if success:
        print("Credenciais salvas com sucesso!")
    else:
        print("Erro ao salvar credenciais!")

if __name__ == "__main__":
    main() 
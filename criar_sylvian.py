from data.storage import DataStorage
import bcrypt

storage = DataStorage()
nome = "sylvian"
email = "sylvian@local"
senha = "admin"
role = "admin"

# Verifica se já existe
users = storage.get_users()
if any(u.get('name') == nome for u in users):
    print("Usuário 'sylvian' já existe.")
else:
    senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user_data = {
        'name': nome,
        'email': email,
        'role': role,
        'password': senha_hash
    }
    storage.create_user(user_data)
    print("Usuário 'sylvian' criado com sucesso!") 
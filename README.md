Okay, let's transform that detailed technical specification into a comprehensive README.md file suitable for a project repository (like GitHub). This README will cover the system's purpose, features, architecture, setup, usage, and technical details, making it useful for users, administrators, and developers.

# Sistema de Impressão Automática de Pedidos - Bling API v3

<!-- Adicionar Badges aqui (Ex: Build Status, License, Version) -->
<!-- [![Build Status](link_para_badge_build)](link_para_pipeline_ci) -->
<!-- [![License: MIT](link_para_badge_licenca)](link_para_licenca) -->

## Visão Geral

Este projeto é um aplicativo desktop desenvolvido em Python, projetado para automatizar a impressão de pedidos de venda integrados à API v3 do Bling. O sistema oferece uma interface gráfica moderna e intuitiva, suporte multiusuário com diferentes níveis de acesso, e opera de forma contínua e resiliente.

O objetivo principal é fornecer uma solução robusta e segura que monitora novos pedidos no Bling em tempo real (via polling da API v3) e os imprime automaticamente em uma impressora configurada, formatando as informações essenciais como número do pedido (com código de barras Code128), nome do cliente e SKUs dos itens. A autenticação com o Bling é feita de forma segura usando o protocolo OAuth 2.0, com renovação automática de tokens para operação ininterrupta.

## ✨ Funcionalidades Principais

*   **Interface Gráfica Moderna:** UI intuitiva e amigável (desenvolvida com PyQt5/PySide6 ou Flet), com suporte a temas claro/escuro e design responsivo.
*   **Suporte Multiusuário:** Perfis de acesso distintos (Administrador e Operador) com controle de permissões.
*   **Tela de Bloqueio Segura:** Bloqueio manual da aplicação e exigência de senha de administrador para encerrar o sistema, prevenindo interrupções acidentais ou não autorizadas.
*   **Integração Segura com Bling API v3:** Autenticação via OAuth 2.0 com fluxo de Authorization Code e renovação automática de `refresh_token`.
*   **Armazenamento Seguro de Credenciais:** Tokens OAuth e senhas de usuários internos armazenados de forma segura (criptografados ou via Keyring do SO).
*   **Polling Automático:** Verificação periódica e configurável da API do Bling para detectar novos pedidos de venda (apenas pedidos recebidos após a inicialização do monitoramento).
*   **Impressão Automática:** Impressão instantânea de novos pedidos detectados em impressora local ou de rede configurada.
*   **Layout de Impressão Otimizado:**
    *   Código de barras **Code128** para o número do pedido.
    *   Número do pedido destacado (negrito).
    *   Nome do cliente.
    *   Lista de itens com foco nos **SKUs**.
    *   Data e hora da impressão.
*   **Configuração de Impressão:** Ajuste de espaçamento de linha, tamanho de fonte e largura do papel.
*   **Filtro de Lojas e SKUs:** Capacidade de definir quais lojas (por ID) e quais SKUs devem ser impressos, com modos de filtro configuráveis (incluir listados, excluir listados, imprimir todos).
*   **Resiliência e Robustez:** Tratamento de erros (API, impressão), reinício automático de processos internos em caso de falha, persistência de estado (último pedido, configurações) e logs detalhados de atividades e erros.
*   **Notificações:** Alertas sonoros e/ou visuais opcionais para novos pedidos impressos e erros críticos.
*   **Histórico de Impressão:** Registro dos pedidos impressos com possibilidade de consulta e reimpressão manual.
*   **Layouts de Impressão Personalizáveis (Opcional):** Suporte a múltiplos modelos de layout de impressão.

## 🖼️ Interface do Usuário (Screenshots)

*A interface foi projetada para ser limpa e funcional.*

<!-- Adicionar screenshots aqui -->
*   *Tela de Login*
    ```
    [Placeholder: Imagem da Tela de Login]
    ```
*   *Painel Principal (Dashboard)*
    ```
    [Placeholder: Imagem do Dashboard mostrando status e feed de atividades]
    ```
*   *Tela de Configurações*
    ```
    [Placeholder: Imagem da Tela de Configurações com abas]
    ```
*   *Tela de Bloqueio*
    ```
    [Placeholder: Imagem da Tela de Bloqueio]
    ```

## 🛠️ Pilha Tecnológica (Technical Stack)

*   **Linguagem:** Python 3.10+
*   **Interface Gráfica:**
    *   **PySide6 (Qt for Python 6)** ou PyQt5: Para uma GUI desktop nativa e robusta. *(Recomendado)*
    *   *Alternativa:* Flet (Flutter para Python): Para UI moderna e multiplataforma via web rendering.
*   **Comunicação API & OAuth2:**
    *   `requests`: Para chamadas HTTP à API do Bling.
    *   `requests-oauthlib` ou `Authlib`: Para gerenciamento simplificado do fluxo OAuth 2.0 e renovação de tokens.
*   **Manipulação de Dados:**
    *   `json` (builtin): Para parsing de respostas da API.
    *   `sqlite3` (builtin) ou SQLAlchemy: Para banco de dados local (configurações, histórico, usuários).
*   **Segurança:**
    *   `keyring`: Para armazenamento seguro de credenciais no gerenciador do SO.
    *   `cryptography`: Para criptografia manual de tokens/dados sensíveis.
    *   `bcrypt` ou `hashlib`: Para hashing seguro de senhas de usuários internos.
*   **Impressão:**
    *   `QtPrintSupport` (via PySide6/PyQt5): Para integração com o sistema de impressão do SO.
    *   *Alternativa Windows:* `PyWin32` (`win32print`): Para acesso direto à API de impressão do Windows.
*   **Geração de Código de Barras:**
    *   `python-barcode`: Para gerar imagens de código de barras Code128.
    *   `Pillow`: Dependência do `python-barcode` para manipulação de imagens.
*   **Notificações:**
    *   `winsound` (Windows) ou `simpleaudio`/`pygame`: Para notificações sonoras.
    *   `plyer` / `win10toast` ou `QSystemTrayIcon` (Qt): Para notificações visuais (toast).
*   **Logging:**
    *   `logging` (builtin): Para registro detalhado de atividades e erros, com rotação de arquivos.
*   **Threading/Agendamento:**
    *   `threading` (builtin) ou `QThread` (Qt): Para execução do polling em background sem bloquear a UI.
*   **Empacotamento:**
    *   `PyInstaller` ou `cx_Freeze`: Para criar um executável distribuível para Windows.

## 🏗️ Arquitetura do Sistema

O sistema é modularizado para separar responsabilidades e facilitar a manutenção:

1.  **Módulo UI (Interface Gráfica):** Responsável pela apresentação (PySide6/Flet) e interação com o usuário. Contém as janelas (Login, Principal, Configurações, etc.) e envia ações do usuário para a camada de lógica.
2.  **Módulo Autenticação OAuth:** Gerencia o fluxo OAuth 2.0 com a API do Bling, incluindo obtenção e renovação automática de tokens, utilizando bibliotecas como `Authlib`.
3.  **Módulo API Bling:** Encapsula as chamadas à API REST v3 do Bling (`requests`), tratando requisições e respostas JSON.
4.  **Módulo Lógica de Negócio (Core):** Contém a lógica central:
    *   **Controlador de Polling:** Gerencia o loop periódico de verificação de novos pedidos (em thread separada).
    *   **Controlador de Impressão:** Orquestra o processo de impressão, chamando formatação e envio para a impressora.
    *   **Filtros:** Aplica as regras de filtro de Lojas e SKUs.
    *   **Gerenciador de Estado:** Mantém o estado atual da aplicação (usuário logado, último pedido, etc.).
5.  **Módulo Impressão:** Lida com a geração do layout do pedido (incluindo código de barras com `python-barcode`) e a comunicação com a impressora selecionada (via `QPrinter` ou `win32print`).
6.  **Módulo Persistência:** Responsável pelo armazenamento e recuperação de dados locais (configurações, tokens criptografados, histórico de pedidos, usuários internos) usando SQLite ou arquivos seguros.
7.  **Módulo Logs:** Configura e gerencia o logging de eventos e erros em arquivos (com rotação).
8.  **Módulo Inicialização (main.py):** Ponto de entrada da aplicação, responsável por configurar o ambiente, instanciar os módulos principais e iniciar a UI.

*Fluxo Geral:* Login -> Autenticação Bling (OAuth2) -> Início do Polling -> Detecção de Novo Pedido -> Filtragem (Loja/SKU) -> Formatação e Impressão -> Notificação -> Registro no Histórico -> Repete Polling. Erros são capturados, logados e o sistema tenta se recuperar.

*(Consulte a especificação técnica para um fluxograma detalhado)*

## ⚙️ Instalação

1.  **Pré-requisitos:**
    *   Python 3.10 ou superior.
    *   Acesso à internet (para autenticação e API do Bling).
    *   Sistema Operacional: Windows (foco principal devido a dependências como `win32print`, mas pode ser adaptável).
    *   Conta no Bling com acesso à API v3 e permissão para criar aplicações de integração.

2.  **Obtenha o Código:**
    ```bash
    git clone https://github.com/seu_usuario/seu_repositorio.git
    cd seu_repositorio
    ```

3.  **Crie um Ambiente Virtual (Recomendado):**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/macOS
    source venv/bin/activate
    ```

4.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Nota: O arquivo `requirements.txt` deve listar todas as bibliotecas mencionadas na Pilha Tecnológica)*

5.  **Cadastro da Aplicação no Bling:**
    *   Acesse sua conta Bling e vá para a seção de gerenciamento de API/Aplicações.
    *   Crie uma nova aplicação para obter o `Client ID` e `Client Secret`.
    *   Configure o `Redirect URI` conforme necessário para a aplicação desktop (ex: `http://localhost:PORTA_TEMPORARIA` para loopback ou um esquema custom `myapp://callback`). Guarde essas credenciais, elas serão necessárias na configuração.

6.  **(Opcional) Empacotamento para Executável:**
    Se desejar criar um `.exe` independente:
    ```bash
    pyinstaller --onefile --windowed main.py --name BlingPrinterApp
    ```
    *(Ajuste os parâmetros do PyInstaller conforme necessário, garantindo que assets como ícones e arquivos de som sejam incluídos)*

## 🔧 Configuração

Após a instalação (ou na primeira execução), a aplicação exigirá algumas configurações iniciais, geralmente realizadas por um usuário com perfil de **Administrador**:

1.  **Login Interno:** Crie o primeiro usuário Administrador (se ainda não existir) ou faça login com um usuário existente.
2.  **Autenticação Bling (OAuth 2.0):**
    *   Acesse a seção de configuração da API/Bling.
    *   Insira o `Client ID` e `Client Secret` obtidos no Bling.
    *   Inicie o fluxo de autorização. O sistema abrirá um navegador ou webview para você fazer login no Bling e autorizar a aplicação.
    *   Após a autorização bem-sucedida, o sistema obterá e armazenará os tokens de forma segura.
3.  **Configurações de Impressão:**
    *   Selecione a **impressora padrão** na lista de impressoras detectadas no sistema.
    *   Ajuste o **layout de impressão:** tamanho da fonte, espaçamento entre linhas, largura do papel (ex: 80mm para térmica, A4).
    *   (Opcional) Habilite/desabilite **notificações sonoras/visuais**.
    *   Use o botão "Impressão de Teste" para verificar o layout.
4.  **Configurações de Polling:**
    *   Defina o **intervalo de verificação** da API (em segundos ou minutos). Ex: 60 segundos.
5.  **Configurações de Lojas e SKUs:**
    *   **Lojas Permitidas:** Cadastre os **IDs das lojas** do Bling cujos pedidos devem ser impressos. Se a lista estiver vazia, todos os pedidos podem ser impressos (comportamento padrão ou configurável).
    *   **Filtro de SKUs:**
        *   Cadastre a lista de SKUs relevantes (se necessário).
        *   Selecione o **modo de filtro**:
            *   `Imprimir apenas SKUs cadastrados`: Imprime somente itens cujo SKU está na lista.
            *   `Não imprimir SKUs cadastrados`: Imprime todos os itens, exceto aqueles cujo SKU está na lista.
            *   `Imprimir tudo`: Ignora a lista de SKUs e imprime todos os itens.
6.  **Gerenciamento de Usuários (Admin):**
    *   Cadastre outros usuários (Operadores ou Admins).
    *   Gerencie senhas e perfis.

*Todas as configurações são salvas localmente de forma persistente.*

## ▶️ Uso da Aplicação

1.  **Iniciar a Aplicação:** Execute o script principal (`python main.py`) ou o executável (`BlingPrinterApp.exe`).
2.  **Login:** Insira suas credenciais de usuário interno (criadas previamente pelo admin).
3.  **Painel Principal (Dashboard):**
    *   Monitore o **Status da Conexão** com a API do Bling.
    *   Acompanhe o **Status do Polling** (última verificação, próxima verificação, erros).
    *   Veja o **Feed de Atividades** (pedidos impressos, erros, etc.).
    *   Use os botões **Iniciar/Parar Polling** para controlar a impressão automática.
4.  **Operação Normal:** O sistema rodará em background, verificando e imprimindo novos pedidos automaticamente conforme configurado.
5.  **Histórico:** Acesse a tela de histórico para visualizar pedidos já impressos e, se necessário, reimprimir algum manualmente.
6.  **Bloquear Tela:** Use a opção de bloqueio para proteger a aplicação quando se ausentar (requer senha para desbloquear).
7.  **Encerrar Aplicação:** Para fechar o sistema, utilize a opção de sair. **Importante:** Por segurança, será solicitada a senha de um usuário **Administrador** para confirmar o encerramento, evitando paradas acidentais.

## 🔐 Segurança

A segurança é um pilar fundamental deste sistema:

*   **Proteção de Tokens OAuth:** Tokens de acesso e refresh são armazenados de forma segura usando criptografia (biblioteca `cryptography`) ou o `keyring` do sistema operacional, nunca em texto plano.
*   **PKCE (Proof Key for Code Exchange):** Implementado no fluxo OAuth 2.0 (se suportado pelo Bling) para maior segurança em aplicações nativas.
*   **Hashing de Senhas:** Senhas de usuários internos são armazenadas usando hash forte com salt (ex: `bcrypt`).
*   **Controle de Acesso:** Permissões rigorosas baseadas nos perfis Admin/Operador. Ações críticas (configuração, encerramento) são restritas.
*   **Comunicação Segura:** Todas as chamadas à API do Bling são feitas via HTTPS com verificação de certificado SSL/TLS.
*   **Validação e Sanitização:** Entradas do usuário e dados da API são validados e tratados adequadamente para prevenir erros e vulnerabilidades.
*   **Logs Seguros:** Logs não registram informações sensíveis como tokens completos ou senhas em texto claro.

## 🔄 Resiliência e Logging

*   **Tolerância a Falhas:** O sistema é projetado para lidar com erros (ex: falha de rede, API indisponível, erro de impressora) de forma graciosa, registrando o problema e tentando se recuperar automaticamente (ex: retentativas, reinício do ciclo de polling).
*   **Persistência de Estado:** O estado crítico (último pedido processado, tokens, configurações) é salvo localmente, permitindo que o sistema retome a operação corretamente após reinicializações (manuais ou por falha).
*   **Logs Detalhados:** Registro abrangente de atividades (pedidos impressos, polling), erros e ações administrativas em arquivos de log (`.log`) com rotação automática. Níveis de log (INFO, ERROR, DEBUG) configuráveis ajudam na depuração e auditoria.

## 🚀 Funcionalidades Extras

*   **Notificações Sonoras/Visuais:** Alertas opcionais para novos pedidos impressos ou erros críticos, configuráveis pelo usuário.
*   **Histórico de Pedidos Impressos:** Tela para consultar o histórico de impressões, com opção de busca e reimpressão manual.
*   **Layouts de Impressão Personalizáveis:** Possibilidade de definir ou escolher entre diferentes modelos de layout para a impressão (ex: compacto, completo, com logo). *(Pode ser uma melhoria futura)*

## 👨‍💻 Desenvolvimento

*   **Ambiente:** Use um ambiente virtual Python.
*   **Dependências:** Instale via `pip install -r requirements.txt`.
*   **Testes:** Utilize `pytest` ou `unittest` para testes unitários e de integração dos módulos de lógica, API e persistência. Testes de UI podem requerer abordagens específicas (ex: `Qt Test`) ou serem manuais.
*   **Contribuições:** Siga as diretrizes de estilo de código (ex: PEP 8) e submeta Pull Requests para revisão.

## 📄 Licença

Este projeto está licenciado sob a [Nome da Licença - Ex: MIT License](LINK_PARA_ARQUIVO_LICENSE).

## 📞 Contato

Para dúvidas ou suporte, entre em contato com [Seu Nome/Email] ou abra uma [Issue](LINK_PARA_ISSUES_NO_REPOSITORIO) no repositório.


Observações sobre o README:

Placeholders: Substitua os placeholders como [Placeholder: Imagem...], link_para_..., seu_usuario/seu_repositorio, [Nome da Licença - Ex: MIT License], [Seu Nome/Email] pelos valores corretos.

Screenshots: Adicionar screenshots reais da aplicação é altamente recomendado para ilustrar a interface.

Badges: Considere adicionar badges (shields.io) para status de build, cobertura de código, versão, licença, etc., para dar uma visão rápida do estado do projeto.

Requirements.txt: Certifique-se de que o arquivo requirements.txt esteja completo e atualizado com todas as dependências.

Detalhes da API Bling: Pode ser útil adicionar um link para a documentação oficial da API v3 do Bling para referência.

Adaptação: Adapte seções como Instalação e Tecnologias se a escolha final (ex: PyQt vs Flet) ou detalhes de implementação mudarem.

Este README.md agora reflete a estrutura e o conteúdo da especificação técnica, organizado de uma forma padrão e útil para quem interage com o projeto.

## Características Principais

- Autenticação segura com API Bling via OAuth 2.0
- Monitoramento contínuo de novos pedidos
- Filtragem de pedidos por loja e SKUs
- Impressão automática com layout otimizado (código de barras, detalhes do pedido)
- Interface gráfica moderna com PySide6 (Qt)
- Armazenamento seguro de credenciais
- Suporte multiusuário com diferentes níveis de acesso
- Tratamento de erros e resiliência

## Componentes do Sistema

### 1. Autenticação Bling (auth/bling_oauth.py)

Gerencia o fluxo completo de autenticação OAuth 2.0 com a API Bling v3, incluindo:
- Fluxo de autorização via código
- Armazenamento seguro de tokens
- Renovação automática de tokens expirados

### 2. Cliente API Bling (bling_api/client.py)

Implementa a comunicação com a API Bling v3:
- Métodos para buscar pedidos de venda
- Tratamento inteligente de erros (token expirado, limites de taxa, etc.)
- Suporte para paginação e filtragem

### 3. Motor de Polling (core/polling.py)

Verifica novos pedidos periodicamente em uma thread separada:
- Execução em segundo plano sem bloquear a interface
- Verificação de pedidos após um timestamp específico
- Notificação de novos pedidos via sinais Qt
- Integração com o sistema de filtros

### 4. Sistema de Filtros (core/filters.py)

Filtra quais pedidos e itens devem ser impressos:
- Filtragem por ID de loja (permitir apenas lojas específicas)
- Filtragem de itens por SKU com modos configuráveis:
  - **Include**: Imprime apenas SKUs na lista
  - **Exclude**: Imprime apenas SKUs que NÃO estão na lista
  - **All**: Imprime todos os SKUs

### 5. Armazenamento de Dados (data/storage.py)

Gerencia o armazenamento persistente de:
- Último pedido processado (ID e timestamp)
- Configurações do sistema (intervalo de polling)
- Configurações de filtros (lojas permitidas, lista de SKUs, modo de filtro)

## Fluxo de Funcionamento

1. O usuário se autentica com o Bling via OAuth 2.0
2. O sistema inicia o motor de polling em segundo plano
3. Periodicamente, o sistema busca novos pedidos na API do Bling
4. Os pedidos são filtrados de acordo com as regras configuradas:
   - Apenas pedidos das lojas permitidas são processados
   - Os itens dos pedidos são filtrados de acordo com as regras de SKU
5. Os pedidos que passam nos filtros são enviados para impressão
6. O sistema atualiza o registro do último pedido processado
7. O ciclo se repete de acordo com o intervalo configurado

## Configuração

### Filtros de Pedidos

Os filtros podem ser configurados através da interface ou diretamente via código:

```python
# Configurar lojas permitidas
storage.set_allowed_store_ids(["1001", "1002"])  # Lista vazia = todas permitidas

# Configurar lista de SKUs
storage.set_sku_list(["SKU001", "SKU002", "SKU003"])

# Configurar modo de filtro
storage.set_sku_filter_mode(FILTER_MODE_INCLUDE)  # "include", "exclude" ou "all"
```

## Desenvolvimento

O sistema é desenvolvido em Python 3.10+ com as seguintes tecnologias:
- PySide6 (Qt) para interface gráfica
- Requests para comunicação HTTP
- Threading para operações em segundo plano
- SQLite para armazenamento local de dados

O código segue boas práticas de orientação a objetos, com separação clara de responsabilidades e testes unitários abrangentes.
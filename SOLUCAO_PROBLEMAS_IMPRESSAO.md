# Guia de Solução de Problemas de Impressão

## Problemas Comuns

### 1. Programa fecha ao tentar imprimir

**Problema**: O aplicativo AcriPrint fecha de forma inesperada sem mostrar mensagens de erro quando tenta imprimir.

**Solução**: Este problema geralmente ocorre devido a conflitos do Qt com drivers de impressora ou problemas de permissão.

Os seguintes passos foram implementados para resolver este problema:

1. Implementamos um sistema de impressão completamente separado do aplicativo principal.
2. Este sistema não usa bibliotecas Qt para impressão, evitando os conflitos.
3. O novo sistema usa três métodos alternativos de impressão:
   - Comunicação direta com impressoras térmicas via porta serial
   - Impressão via Notepad (método de fallback)
   - Geração de HTML para impressão via navegador (último recurso)

O problema deve estar resolvido com a versão atual, mas se persistir, tente as seguintes ações:

- Execute o aplicativo como administrador
- Execute a ferramenta de diagnóstico `teste_impressora_serial.py`
- Verifique o arquivo de log `print_log.txt` para detalhes sobre falhas

### 2. Erro "Acesso Negado" às portas COM

**Problema**: O log mostra erros de "Acesso Negado" (PermissionError) ao tentar acessar portas COM.

**Soluções**:

1. **Verificar se outro programa está usando a porta**
   - Feche outros aplicativos que possam estar usando a impressora
   - Reinicie o computador para liberar todas as portas

2. **Execute como administrador**
   - Clique com botão direito no AcriPrint e escolha "Executar como administrador"

3. **Utilize a ferramenta de diagnóstico**
   ```
   python teste_impressora_serial.py
   ```
   - Esta ferramenta pode detectar e ajudar a encerrar processos que estão usando a porta

4. **Verificar configurações no Device Manager**
   - Abra o Gerenciador de Dispositivos
   - Localize a impressora ou porta COM
   - Clique com botão direito → Propriedades
   - Verifique se não há conflitos de recursos ou problemas reportados

5. **Tente outra porta COM**
   - Algumas impressoras térmicas podem ser configuradas para usar diferentes portas
   - Edite o arquivo `config/printer_config.json` e altere a porta em `"porta_manual"`

### 3. Impressora térmica não imprime corretamente

**Problema**: Impressão sai cortada, com caracteres estranhos ou não imprime.

**Soluções**:

1. **Verifique o baudrate**
   - Use a ferramenta de diagnóstico para testar diferentes baudrates:
   ```
   python teste_impressora_serial.py
   ```
   - Atualize o baudrate correto no arquivo `config/printer_config.json`

2. **Verifique o papel**
   - Certifique-se de que há papel suficiente na impressora
   - Verifique se o papel está preso ou mal posicionado

3. **Verifique os drivers**
   - Atualize ou reinstale os drivers da impressora
   - Se for uma impressora USB/Serial, tente reinstalar os drivers do adaptador

4. **Teste com o padrão de teste**
   - Execute a ferramenta de diagnóstico e use a opção para imprimir o padrão de teste
   - Isso pode ajudar a identificar se é um problema de configuração ou hardware

### 4. Método alternativo (Notepad) não funciona

**Problema**: A impressão via Notepad não funciona corretamente.

**Soluções**:

1. **Verifique se tem uma impressora padrão configurada**
   - Windows → Configurações → Dispositivos → Impressoras e scanners
   - Certifique-se de que há uma impressora definida como padrão

2. **Teste a impressora com Notepad manualmente**
   - Abra o Notepad e crie um arquivo de texto simples
   - Tente imprimir usando Ctrl+P ou menu Arquivo → Imprimir
   - Se isto funcionar, a impressora está OK mas pode haver um problema no caminho de impressão do aplicativo

3. **Verifique permissões**
   - Execute o programa como administrador
   - Verifique se a pasta temp (TEMP ou TMP) tem permissões de gravação

## Soluções Avançadas

### Acesso à porta serial bloqueado

Se o problema de acesso negado persistir, você pode tentar:

1. **Identificar o processo bloqueando a porta**

   No PowerShell como administrador, execute:
   ```powershell
   Get-Process | Where-Object {$_.Modules.FileName -like '*COM3*'}
   ```
   (Substitua COM3 pela porta que você está usando)

2. **Encerrar o processo**
   
   Se encontrar o processo, encerre-o:
   ```powershell
   Stop-Process -Id [ID_DO_PROCESSO] -Force
   ```

3. **Liberação forçada da porta**

   Em casos extremos, reinicie o serviço de Spooler de impressão:
   ```powershell
   Stop-Service -Name Spooler
   Start-Service -Name Spooler
   ```

### Atualizando a configuração manualmente

Se precisar atualizar a configuração, edite o arquivo `config/printer_config.json`:

```json
{
    "porta_manual": "COM3",
    "baudrate": 9600,
    "timeout": 1,
    "tentativas_conexao": 5,
    "tempo_espera_entre_tentativas": 1.5,
    "baudrates": [9600, 115200, 57600, 38400, 19200, 4800],
    "cortar_papel": true,
    "metodos_impressao": ["serial", "notepad", "html"],
    "largura_papel": 80,
    "avancar_linhas_final": 5,
    "verificar_porta_antes": true,
    "tempo_liberacao_porta": 3,
    "imprimir_logo": false
}
```

- `porta_manual`: Define uma porta COM específica a ser usada
- `baudrate`: Taxa de transmissão (bits por segundo)
- `timeout`: Tempo de espera para operações de leitura/escrita
- `tentativas_conexao`: Número de tentativas antes de desistir
- `tempo_espera_entre_tentativas`: Tempo (segundos) entre tentativas
- `baudrates`: Lista de baudrates a tentar caso o principal falhe
- `metodos_impressao`: Define a ordem dos métodos de impressão a tentar
- `verificar_porta_antes`: Verifica se a porta está disponível antes de tentar usar
- `tempo_liberacao_porta`: Tempo máximo a esperar para a porta ser liberada

## Logs e Diagnóstico

### Verificando logs

O arquivo de log `print_log.txt` na pasta principal contém informações detalhadas sobre o processo de impressão. Informações importantes a procurar:

- Mensagens `ERROR` ou `WARNING` que indicam falhas
- Informações sobre portas disponíveis
- Resultado das tentativas de conexão com diferentes baudrates
- Mensagens sobre qual método de impressão foi utilizado

### Realizando testes isolados

Para testar apenas o componente de impressão:

```
python teste_impressao_real.py
```

Para testar apenas o diagnóstico de portas e comunicação:

```
python teste_impressora_serial.py
```

## Contato para Suporte

Se mesmo depois de todas estas etapas o problema persistir, entre em contato com o suporte técnico fornecendo:

1. Cópia do arquivo `print_log.txt`
2. Descrição exata do problema
3. Modelo da impressora que está sendo usada
4. Versão do Windows utilizada 
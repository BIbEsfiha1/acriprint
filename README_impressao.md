# Sistema de Impressão do AcriPrint

## Resumo das Melhorias

O sistema de impressão foi completamente refeito para resolver problemas de travamento e falhas durante a impressão de pedidos. A nova implementação contém as seguintes melhorias:

1. **Comunicação direta com impressoras térmicas**: O sistema agora usa o módulo `pyserial` para se comunicar diretamente com impressoras térmicas via porta serial, eliminando a dependência do Qt e outras bibliotecas gráficas que poderiam causar travamentos.

2. **Detecção automática de impressoras**: O sistema detecta automaticamente a impressora térmica conectada através da verificação de todas as portas COM disponíveis.

3. **Comandos ESC/POS nativos**: Implementação de comandos ESC/POS nativos para formatação profissional de recibos, incluindo centralização de texto, negrito e fonte dupla para títulos, corte automático de papel e alinhamento correto dos valores.

4. **Sistema de fallback**: Se a impressão direta falhar, o sistema usa métodos alternativos (Notepad ou HTML) para garantir que os pedidos sejam sempre impressos.

5. **Tratamento de erros aprimorado**: Implementação de tratamento de erros detalhado para identificar exatamente onde ocorrem falhas na impressão.

6. **Sistema de logging completo**: Cada etapa do processo de impressão é registrada, facilitando a depuração e solução de problemas.

7. **Limpeza automática de arquivos temporários**: O sistema limpa automaticamente arquivos temporários antigos para evitar acúmulo de arquivos desnecessários.

8. **Suporte a caracteres especiais**: Utilização da codificação CP-850 para suporte adequado a caracteres portugueses.

## Como funciona

O processo de impressão segue estes passos:

1. A janela principal gera um arquivo JSON com os dados do pedido
2. Um processo separado (`print_process.py`) é iniciado para lidar com a impressão
3. O processo tenta imprimir diretamente na impressora térmica (se disponível)
4. Se a impressão direta falhar, o processo cria um arquivo de texto e o imprime usando o Notepad
5. Se o Notepad falhar, o processo cria um arquivo HTML e tenta imprimi-lo usando o navegador
6. O resultado da operação é registrado em um arquivo JSON para ser lido pela aplicação principal

## Requisitos

- Python 3.6 ou superior
- Módulo `pyserial` (instalado via `pip install pyserial`)
- Windows com Notepad (para o método alternativo)

## Configuração

A configuração de impressão é controlada pelo arquivo `data/print_config.json`, que permite personalizar:

- Nome da impressora
- Largura do papel
- Margens
- Tamanho da fonte
- Elementos a serem impressos (código de barras, nome do cliente, etc.)

## Solução de Problemas

Se ocorrerem problemas com a impressão:

1. Verifique o arquivo de log `print_log.txt` para detalhes do erro
2. Certifique-se de que a impressora está conectada e ligada
3. Verifique se o módulo `pyserial` está instalado
4. Se estiver usando impressora térmica via USB, verifique se os drivers estão instalados corretamente
5. Teste com o método alternativo usando o parâmetro `--force-notepad`

## Personalização

Para personalizar a saída de impressão, você pode:

1. Editar o arquivo `data/print_config.json`
2. Modificar o método `imprimir_pedido_serial()` em `print_process.py` para ajustar a formatação
3. Criar um layout personalizado editando a função `criar_arquivo_texto()` 
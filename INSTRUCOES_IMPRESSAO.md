# Instruções para o Sistema de Impressão

## Visão Geral

O sistema de impressão do AcriPrint foi totalmente reformulado para resolver o problema de fechamento inesperado do programa durante a impressão. Agora, o sistema utiliza um processo separado para realizar a impressão, o que torna o aplicativo muito mais estável.

## Como Funciona

1. **Sistema Robusto**: O novo sistema de impressão funciona de forma independente do aplicativo principal, evitando que problemas de impressão causem o fechamento do programa.

2. **Múltiplos Métodos de Impressão**: O sistema tenta primeiro imprimir diretamente em impressoras térmicas via porta serial. Se isso falhar, ele utiliza métodos alternativos como o Notepad para garantir que o pedido seja sempre impresso.

3. **Configuração Automática**: O sistema detecta automaticamente impressoras térmicas conectadas e tenta se comunicar com elas usando os parâmetros corretos.

## Solucionando Problemas

Se você encontrar qualquer problema com a impressão:

1. **Verifique o Arquivo de Log**: Examine o arquivo `print_log.txt` na pasta do programa para ver detalhes sobre o que está acontecendo durante a impressão.

2. **Verifique a Impressora**: Certifique-se de que a impressora está conectada, ligada e configurada corretamente.

3. **Reinicie o Aplicativo**: Às vezes, reiniciar o aplicativo pode resolver problemas temporários.

4. **Verifique o Papel**: Para impressoras térmicas, verifique se há papel disponível e se não está preso.

5. **Teste a Impressora**: Tente imprimir um documento de teste fora do aplicativo para verificar se a impressora está funcionando corretamente.

## Requisitos

- O novo sistema de impressão utiliza o módulo `pyserial` para comunicação direta com impressoras térmicas.
- Para o método alternativo de impressão, o sistema utiliza o Notepad do Windows.

## Personalização

Se você deseja personalizar a aparência dos recibos impressos:

1. Edite o arquivo `data/print_config.json` para ajustar configurações como tamanho da fonte, margens, etc.

2. A formatação do recibo pode ser personalizada editando o arquivo `print_process.py` conforme necessário.

## Suporte a Impressoras

O sistema suporta:

- **Impressoras Térmicas**: Conectadas via USB/Serial (COM port)
- **Impressoras Padrão do Windows**: Através do método alternativo de impressão

## Em Caso de Problemas Persistentes

Se você continuar enfrentando problemas com a impressão:

1. Tente reinstalar os drivers da impressora
2. Tente utilizar uma impressora diferente
3. Entre em contato com o suporte técnico 
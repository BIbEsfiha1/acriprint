# Alterações realizadas no sistema de impressão

## Problemas identificados
1. A impressora estava imprimindo apenas 3 letras por linha, desperdiçando o papel térmico.
2. O código QR não estava sendo impresso corretamente.
3. Faltavam funções importantes no código (`obter_porta_impressora` e `conectar_impressora_serial`).
4. O formato do texto para impressão não estava otimizado para impressoras térmicas de 58mm.

## Alterações realizadas

### 1. Adição de funções ausentes
- Adicionada a função `obter_porta_impressora` para determinar a porta correta da impressora.
- Adicionada a função `conectar_impressora_serial` para estabelecer conexão com a impressora, tentando diversos baudrates e verificando a disponibilidade da porta.

### 2. Implementação de QR Code real
- Criada a função `gerar_qrcode_escpos` para gerar QR Codes usando comandos ESC/POS nativos.
- A função implementa todos os passos necessários: modelo, tamanho, correção de erro, armazenamento de dados e impressão.

### 3. Melhoria na formatação do texto
- Atualizada a função `imprimir_pedido_serial` para formatar corretamente o texto para a impressora de 58mm.
- Configurada a largura adequada do papel de acordo com as configurações (32 caracteres para 58mm).
- Implementada a formatação centralizada para cabeçalhos, títulos e rodapés.
- Formatação específica para itens, com destaque para quantidades maiores que 1.

### 4. Otimização da função de criação de arquivo de texto
- Melhorada a função `criar_arquivo_texto` para gerar um arquivo bem formatado.
- Adicionado suporte para quebra de texto longo em múltiplas linhas.
- Implementadas funções auxiliares para centralizar, alinhar à esquerda e à direita.
- Formatação melhorada para cada seção: cabeçalho, dados do cliente, itens e observações.

### 5. Tratamento de erros e diagnóstico
- Implementado um melhor tratamento de erros na conexão com a impressora.
- Adicionados logs detalhados para facilitar o diagnóstico de problemas.
- Criado script `teste_formato_impressao.py` para visualizar o formato de impressão sem necessidade de imprimir.

## Resultados
- A impressora agora imprime corretamente com a largura de papel adequada (32 caracteres por linha para 58mm).
- O QR Code é gerado e impresso corretamente.
- A formatação do texto está otimizada para impressoras térmicas.
- Os arquivos gerados para impressão são mais legíveis e bem formatados.

## Próximos passos recomendados
1. Testar com a impressora física para confirmar que todas as alterações resolveram o problema.
2. Ajustar qualquer parâmetro adicional de formatação se necessário após o teste físico.
3. Considerar ajustes no tamanho do QR Code se ele estiver muito grande ou pequeno. 
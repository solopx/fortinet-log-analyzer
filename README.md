# FortiNet Log Analyzer

![Python](https://img.shields.io/badge/Python-3.x-blue.svg) ![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green.svg) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Um aplicativo de desktop simples e leve para visualização, análise e tratamento de logs de equipamentos Fortinet, desenvolvido em Python.

Este aplicativo torna mais fácil a análise e a gerência de logs de dispositivos UTM para usuários da área de segurança sem a necessidade da utilização de um appliance FortiAnaltzer.

## Funcionalidades

- **Visualização gráfica de Logs**: Carrega e exibe de forma detalhada arquivos logs em formato `.log` ou `.txt` no formato `key=value`.
- **Busca dinâmica:** Filtra logs por qualquer termo em todos os campos, com busca case-insensitive.
- **Análise Visual Simples:** Coloração automática para níveis críticos (alert, critical, error) e ações de bloqueio (deny, block).
- **Painel lateral:** Estatísticas em tempo real (Top IPs de origem, Top Ações e Níveis).
- **Ordenação de Colunas:** Classifique os logs clicando nos cabeçalhos das colunas (crescente/decrescente).
- **Inspeção Detalhada:** Clique duplo em qualquer linha para abrir uma janela de detalhes com todos os campos do log selecionado.
- **Interface de Alta Performance:** Suporta arquivos grandes através de um sistema de paginação dinâmica (3.000 registros por página), mantendo a fluidez da interface.
- **Exportação de Dados**: Possibilidade de exportação dos dados selecionados em formatos .csv ou .json

## Screenshots

![Screenshot 2](/assets/screenshot-01.png)

## 🛠️ Como Usar

### Pré-requisitos
Python 3.x

### Execução

1.  **Baixe o Repositório**
    ```bash
    git clone https://github.com/solopx/fortinet-log-analyzer.git
    cd fortinet-log-analyzer
    ```
2.  **Instale as dependências**
    ```bash
    pip install -r requirements.txt
    ```    
2.  **Execute o Script**
    ```bash
    python src/main.py
    ```

### Utilização da Interface

1. Carregar Logs: Clique no botão "Abrir Log" e selecione um arquivo de log (extensões .log ou .txt).
2. Filtragem: Digite termos de pesquisa na barra de busca. Clique em limpar para limpar os termos de busca e mostrar todos os resultados.
3. Ordenação: Clique nos cabeçalhos das colunas para ordenar os dados.
4. Clique com o botão direito sobre as linhas para exportar as linhas como texto.
5. Clique em "Exportar CSV" ou Exportar JSON" para exportar os resultados da busca para os formatos .csv ou .json.
6. Duplo clique sobre a linha do log abre uma janela com os dados completos da entrada de log.
7. Estatísticas: Visualize no painel à direita os padrões de tráfego mais comuns encontrados no log.

## Estrutura dos Logs Esperada

O script analisa entrada de logs no formato `key=value`, como por exemplo:

`date=2023-10-27 time=10:30:00 logid=0000000000 type=traffic subtype=forward srcip=192.168.1.10 srcport=54321 srcintf="port1" dstip=8.8.8.8 dstport=53 dstintf="wan1" policyid=1 action=accept service="dns" utmaction=passthrough sentbyte=123 rcvdbyte=456`

## Contribuições

Contribuições são bem-vindas! Se você tiver ideias para melhorias, sinta-se à vontade para abrir uma *issue* ou enviar um *pull request*.

## Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---
Desenvolvido por solopx
GitHub: [https://github.com/solopx/](https://github.com/solopx/)

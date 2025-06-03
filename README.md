# Analisador de Primeiras Palavras

Aplicação Streamlit para análise das primeiras palavras em descrições.

## Como usar

1. Faça upload de um arquivo Excel ou CSV contendo uma coluna "Descrição"
2. A aplicação irá analisar as primeiras palavras de cada descrição
3. Os resultados são exibidos em tabela e gráfico
4. Você pode adicionar palavras para ignorar na análise

## Implantação no Render

1. Crie um novo serviço Web no Render
2. Conecte ao seu repositório GitHub
3. Use as seguintes configurações:
   - Runtime: Python 3.9
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. Defina a variável de ambiente `PORT` como `10000`

## Pré-requisitos

- Python 3.9+
- Bibliotecas listadas em requirements.txt

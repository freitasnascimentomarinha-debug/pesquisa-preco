# Pesquisa de Preços - Dados Abertos (Compras Governamentais)

[](https://pesquisa-preco.streamlit.app/)

Ferramenta desenvolvida para agilizar a pesquisa de preços de mercado utilizando a API de Dados Abertos do Governo Federal.

🔗 **Acesse a aplicação online:** [https://pesquisa-preco.streamlit.app/](https://pesquisa-preco.streamlit.app/)

> **Nota sobre o Fork:** Este projeto é um *fork* de uma ferramenta anterior que realizava a consulta e gerava apenas um arquivo CSV para download. Nesta versão, o código foi refatorado para exibir os resultados **diretamente na tela** e aprimorado com métricas estatísticas avançadas para uma análise imediata dos preços de referência.

## 🎯 Funcionalidades

  - **Consulta Flexível:** Permite pesquisar tanto por **Materiais** quanto por **Serviços**.
  - **Busca de Códigos:** Integração via *iframe* com o [Catálogo de Materiais e Serviços do Governo Federal](https://catalogo.compras.gov.br/cnbs-web/busca) para facilitar a localização do `Código do Item`.
  - **Análise Estatística Completa:** Exibe instantaneamente indicadores fundamentais para a composição de mapas de preços, auxiliando na identificação de sobrepreço ou inexequibilidade:
      - **Média**
      - **Mediana**
      - **Desvio Padrão**
      - **Coeficiente de Variação**
  - **Visualização de Dados:** Apresenta a tabela completa de resultados (Dataframe) diretamente na interface do usuário, formatada com valores em Reais (R$).

## 🛠️ Tecnologias Utilizadas

  - [Streamlit](https://streamlit.io/)
  - [Pandas](https://pandas.pydata.org/)
  - [Requests](https://pypi.org/project/requests/)

## 🚀 Como Executar Localmente

Se preferir rodar a aplicação na sua própria máquina:

### Pré-requisitos

Certifique-se de ter o Python instalado.

1.  Clone este repositório.
2.  Instale as dependências listadas no arquivo `requirements.txt`:

<!-- end list -->

```bash
pip install -r requirements.txt
```

### Rodando a Aplicação

Navegue até a pasta do projeto e execute:

```bash
streamlit run streamlit_app.py
```

A aplicação será aberta no seu navegador padrão (geralmente em `http://localhost:8501`).

## 📖 Como Usar

1.  **Identifique o Código:** Utilize a janela do catálogo (iframe) na tela inicial para buscar o item desejado e copiar seu código (CATMAT ou CATSER).
2.  **Configure a Busca:** Selecione o tipo ("Material" ou "Serviço") e cole o código no campo indicado.
3.  **Consulte:** Clique no botão `Consultar`.
4.  **Analise:** Verifique o painel estatístico no topo (Média, Mediana, Desvio Padrão, CV) e explore a tabela detalhada com os registros de compras.

## 📡 Fonte de Dados

O sistema consome dados diretamente dos *endpoints* do Portal de Dados Abertos de Compras Governamentais:

  * `modulo-pesquisa-preco/1_consultarMaterial`
  * `modulo-pesquisa-preco/3_consultarServico`

## 🎨 Visual (ui_tema.py)

O módulo `ui_tema.py` concentra o visual do sistema: mascote animado "Ata", o balconista de preços, na sidebar (olhos que seguem o mouse, lupa, etiqueta de preço que muda, balão de falas, pula ao clicar), cartões em vidro, botões, abas, barra de progresso de rolagem e botão "voltar ao topo" em JavaScript. É só apresentação: nenhuma regra de negócio passa por ele.

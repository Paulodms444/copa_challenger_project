# 🏆 Copa Challenger — Ranking FIFA

Projeto desenvolvido para a **Copa Challenger**, competição de dados da
comunidade *Dados por Todos*, que simula o ciclo completo de um projeto real
de dados: da extração à inteligência artificial.

Dataset utilizado: [FIFA Football World Cup](https://www.kaggle.com/datasets/piterfm/fifa-football-world-cup)
(Kaggle, por *piterfm*), restrito ao ranking das Copas de **2018 e 2022**.

---

## 📖 Sobre o projeto

O objetivo é responder três perguntas de negócio a partir do ranking FIFA:

1. Como as confederações (UEFA, CONMEBOL, CAF, AFC, CONCACAF, OFC) se
   comparam em pontuação média?
2. Quais seleções tiveram as maiores movimentações (altas e quedas) de
   posição entre atualizações do ranking?
3. É possível prever se uma seleção estará no **Top 20** com base apenas em
   seu status anterior?

O projeto percorre as quatro missões da competição:

| Missão | Tema | Ferramentas |
|---|---|---|
| 1 | SQL e Entendimento dos Dados | MySQL, Docker, SQLAlchemy |
| 2 | Análise Exploratória de Dados (EDA) | Python, Pandas, Matplotlib, Seaborn |
| 3 | Dashboard e Storytelling | Streamlit, Plotly |
| 4 | Inteligência Artificial | Scikit-learn |

---

## 🗂️ Estrutura do repositório

```
copa_challenger/
├── app.py                          # Dashboard Streamlit (Missão 3)
├── eda_copa.ipynb                  # Notebook: SQL + EDA (Missões 1 e 2)
├── docker-compose.yml              # Sobe o MySQL usado nas Missões 1 e 2
├── fifa_ranking_2022-10-06.csv     # Dataset (fallback local/deploy)
├── requirements.txt                # Dependências do projeto
└── README.md
```

---

## 🛠️ Tecnologias

- **Python 3.13**
- **MySQL 8.0** (via Docker)
- **SQLAlchemy** + **PyMySQL** — camada de acesso ao banco
- **Pandas** / **NumPy** — manipulação e análise de dados
- **Matplotlib** / **Seaborn** — visualizações estáticas (EDA)
- **Streamlit** + **Plotly** — dashboard interativo
- **Scikit-learn** — modelo de classificação (Missão 4)
- **uv** — gerenciamento de ambiente virtual e pacotes

---

## 🚀 Como rodar o projeto localmente

### Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) instalado

### 1. Clonar o repositório

```bash
git clone https://github.com/Paulodms444/copa_challenger_project.git
cd copa_challenger_project
```

### 2. Subir o banco MySQL

```bash
docker compose up -d
```

### 3. Criar o ambiente virtual e instalar dependências

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 4. Rodar o notebook (Missões 1 e 2)

Abra `eda_copa.ipynb` no VS Code ou Jupyter e execute as células em ordem
(ou use "Run All").

> ⚠️ A connection string do banco usa as credenciais definidas no
> `docker-compose.yml`. Ajuste usuário/senha em `create_engine(...)` caso
> tenha alterado o arquivo.

### 5. Rodar o dashboard (Missão 3)

```bash
streamlit run app.py
```

O app abre automaticamente em `http://localhost:8501`. Caso o MySQL não
esteja acessível (por exemplo, em ambiente de deploy na nuvem), o app faz
fallback automático para o CSV incluso no repositório.

---

## 📊 Principais insights (Missões 1 e 2)

- A **UEFA** apresenta a maior média de pontos entre as confederações,
  seguida por CONMEBOL — uma diferença superior a 500 pontos em relação à
  confederação com menor média.
- O dataset não apresentou valores ausentes, duplicatas ou inconsistências
  de padronização — 211 seleções únicas para 211 linhas.
- A posição no ranking é predominantemente **estável** entre atualizações;
  poucas seleções concentram as maiores altas e quedas de posição.

Detalhes completos, com queries SQL e o passo a passo do tratamento de
dados, estão documentados no notebook `eda_copa.ipynb` e no relatório da
solução.

---

## 🎨 Dashboard

O painel interativo permite filtrar por confederação e ajustar o Top N de
seleções exibidas, com textos de interpretação gerados dinamicamente a
partir dos dados filtrados.

🔗 **Link do dashboard publicado:** https://copa-challenger-ranking-fifa.streamlit.app/

---

## 🤖 Modelo Preditivo (Missão 4)

Classificador binário que prevê se uma seleção estará no Top 20 do ranking,
usando apenas `previous_rank`, `previous_points` e `association` como
atributos — sem vazamento de dados do período atual. Modelos comparados:
Regressão Logística e Random Forest, avaliados via validação cruzada
estratificada (AUC-ROC).

---

## 🔗 Links do projeto

- 📓 [Notebook Kaggle](https://www.kaggle.com/code/pyronsk/notebook53c0971197)
- 📄 Relatório da Solução: [docs/Relatorio_Solucao.md](docs/Relatorio_Solucao.md)
- 🎨 Dashboard: https://copa-challenger-ranking-fifa.streamlit.app/
- 🎥 Vídeo demonstrativo: https://youtu.be/Im0eh3no_0Q

---

## 👤 Autor

**Paulo Damasceno dos Santos**
Projeto desenvolvido para a Copa Challenger — Comunidade Dados por Todos.

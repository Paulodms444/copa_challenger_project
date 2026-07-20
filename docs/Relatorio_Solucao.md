# Relatório da Solução — Copa Challenger: Ranking FIFA

**Autor(a):** Paulo Damasceno dos Santos
**Competição:** Copa Challenger — Comunidade Dados por Todos
**Dataset:** [FIFA Football World Cup](https://www.kaggle.com/datasets/piterfm/fifa-football-world-cup) (Kaggle, piterfm) — Copas 2018 e 2022

---

## Sumário

1. [Resumo Executivo](#1-resumo-executivo)
2. [Objetivo do Projeto](#2-objetivo-do-projeto)
3. [Pipeline e Engenharia de Dados](#3-pipeline-e-engenharia-de-dados)
4. [Principais Descobertas](#4-principais-descobertas)
5. [UX/UI e Storytelling Visual](#5-uxui-e-storytelling-visual)
6. [Estratégia Adotada](#6-estratégia-adotada)
7. [Conclusões Finais](#7-conclusões-finais)
8. [Links e Referências](#8-links-e-referências)

---

## 1. Resumo Executivo

Este projeto foi desenvolvido no contexto da Copa Challenger, uma competição estruturada em quatro missões que simulam o ciclo de vida de um projeto real de dados — da extração à inteligência artificial. Este relatório documenta as Missões 1 (SQL e Entendimento dos Dados), 2 (Análise Exploratória de Dados) e 3 (Dashboard e Storytelling), aplicadas sobre o dataset público de ranking FIFA referente às Copas do Mundo de 2018 e 2022.

O problema de negócio endereçado é: *como estruturar, limpar e comunicar dados de ranking esportivo de forma que padrões de dominância regional, estabilidade e movimentação entre seleções fiquem evidentes para um público não técnico, sem sacrificar rigor analítico?*

A resposta foi um pipeline que parte de um banco relacional MySQL containerizado, passa por uma camada de tratamento e validação em Python/Pandas, e culmina em um dashboard interativo construído em Streamlit. Os principais achados indicam forte concentração de pontuação nas seleções da UEFA e CONMEBOL, ausência de problemas estruturais de qualidade nos dados (sem nulos, sem duplicatas), e uma distribuição de variação de ranking predominantemente estável, com poucas seleções concentrando as maiores altas e quedas.

---

## 2. Objetivo do Projeto

O objetivo técnico do projeto foi construir um pipeline reprodutível — da ingestão ao consumo analítico — capaz de responder três perguntas centrais:

- Como as confederações (UEFA, CONMEBOL, CAF, AFC, CONCACAF, OFC) se comparam em termos de pontuação média no ranking FIFA?
- Quais seleções apresentaram as maiores movimentações (altas e quedas) entre a atualização anterior e a atual do ranking?
- O dataset, tal como disponibilizado, exige tratamento de qualidade (valores ausentes, inconsistências, outliers) antes de sustentar decisões analíticas?

Do ponto de vista de produto, o objetivo foi entregar um artefato final — o dashboard — que comunique esses achados sem exigir conhecimento prévio de SQL ou Python por parte de quem o consome.

---

## 3. Pipeline e Engenharia de Dados

### 3.1 Fonte de Dados

O dataset utilizado é o "FIFA Football World Cup" (piterfm), disponível publicamente no Kaggle, restrito às edições de 2018 e 2022. A tabela de trabalho, `fifa_ranking`, contém 211 registros (uma linha por seleção) e sete colunas: `team`, `team_code`, `association`, `rank`, `previous_rank`, `points` e `previous_points`.

### 3.2 Arquitetura de Ingestão

Optou-se por um banco relacional (MySQL 8.0) provisionado via Docker Compose como camada intermediária entre o CSV de origem e as análises, em vez de consumir o arquivo diretamente em Pandas. Essa decisão foi deliberada: simula o cenário real de um ambiente corporativo, no qual dados de origem raramente chegam como arquivos soltos, e força a validação do pipeline via SQL antes de qualquer transformação em Python — etapa explicitamente exigida na Missão 1 do desafio.

A camada de acesso foi implementada com SQLAlchemy (`dialect mysql+pymysql`), o que introduziu duas decisões técnicas relevantes:

- **Parâmetros de driver:** o parâmetro `allowPublicKeyRetrieval`, comum em clientes Java (MySQL Connector/J), não é reconhecido pelo driver PyMySQL e foi removido da connection string, já que o PyMySQL resolve a negociação de chave RSA do plugin `caching_sha2_password` sem essa flag explícita.
- **Identificadores reservados:** a coluna `rank` colide com a função de janela nativa `RANK()` do MySQL 8.0+. Todas as consultas que referenciam essa coluna a delimitam com crases (`` `rank` ``) — a sintaxe correta de escape de identificadores no MySQL (aspas simples denotam string literal; aspas duplas só funcionam como identificador com o modo `ANSI_QUOTES` ativo, que não é o padrão do servidor).

### 3.3 Consultas SQL (Missão 1)

Três consultas analíticas foram desenvolvidas diretamente no MySQL para caracterizar o dataset antes de qualquer manipulação em Pandas:

```sql
SELECT association,
       ROUND(AVG(points), 1) AS media_pontos,
       COUNT(*) AS qtd_selecoes
FROM fifa_ranking
GROUP BY association
ORDER BY media_pontos DESC;
```
*Consulta 1 — média de pontos e contagem de seleções por confederação.*

```sql
SELECT team, `rank`, previous_rank,
       (previous_rank - `rank`) AS subiu
FROM fifa_ranking
ORDER BY subiu DESC
LIMIT 10;
```
*Consulta 2 — maiores altas de posição no ranking (variação positiva).*

Uma terceira consulta, estruturalmente idêntica à segunda com `ORDER BY ASC`, isola as maiores quedas. As três consultas formam a base quantitativa da Seção 4 e alimentam diretamente os componentes "Maiores Altas" e "Maiores Quedas" do dashboard.

### 3.4 Tratamento e Validação (Missão 2)

A tabela foi carregada em um DataFrame Pandas via `pd.read_sql()` para a etapa de Análise Exploratória. A validação seguiu quatro frentes:

| Verificação | Resultado | Ação tomada |
|---|---|---|
| Valores ausentes | 0 nulos em todas as colunas | Nenhuma imputação necessária |
| Duplicatas | 211 times únicos / 211 linhas | Nenhuma remoção necessária |
| Tipos de dados | `rank`/`previous_rank`: int64; `points`/`previous_points`: float64 | Tipos já adequados na origem |
| Padronização categórica | 6 confederações, grafia consistente | Nenhuma normalização necessária |

*Tabela 1 — resumo da checagem de qualidade de dados (Missão 2).*

A ausência de problemas estruturais é, em si, um achado relevante: reduz o risco de viés introduzido por decisões de imputação e permite que a análise avance diretamente para a caracterização estatística e detecção de outliers.

### 3.5 Detecção de Outliers

Outliers em `points` foram identificados pelo método do Intervalo Interquartil (IQR), com limites definidos em Q1 − 1,5×IQR e Q3 + 1,5×IQR. Esse método foi preferido ao Z-score por não assumir distribuição normal dos dados — premissa que os dados de ranking, com cauda mais longa à direita, violam. Complementarmente, foram calculadas as variáveis derivadas `points_change` e `rank_change` (diferença entre valor atual e anterior), que permitem isolar seleções com movimentação atípica mesmo quando seu valor absoluto de pontos não é, isoladamente, um outlier estatístico.

---

## 4. Principais Descobertas

Os KPIs abaixo resumem o estado do ranking no snapshot analisado (211 seleções, seis confederações):

| Seleções | Média de Pontos | Maior Alta | Maior Queda |
|---|---|---|---|
| 211 | 1221 | +28 pos. | -27 pos. |

*Figura 1 — indicadores-chave exibidos no cabeçalho do dashboard (valores de exemplo; consulte o painel ao vivo para os valores correntes ao aplicar filtros).*

### 4.1 Concentração de Poder por Confederação

A UEFA apresenta a maior média de pontos entre as confederações, seguida por CONMEBOL. A diferença entre a confederação líder e a de menor média é superior a 500 pontos — uma disparidade que reflete diretamente a força histórica e a densidade competitiva dessas regiões no futebol internacional. Esse padrão também aparece de forma visual no Top 10 do dashboard, dominado por seleções europeias e sul-americanas.

### 4.2 Estabilidade Geral, com Exceções Pontuais

O gráfico de dispersão entre rank atual e rank anterior mostra a maioria das seleções próxima à diagonal de identidade — ou seja, sem grande movimentação entre atualizações consecutivas do ranking. As exceções, no entanto, são analiticamente relevantes: seleções que saltam dezenas de posições em uma única atualização sinalizam eventos concretos (resultados de eliminatórias, jogos amistosos de alto impacto, ou recalibração da metodologia FIFA) que não são explicáveis apenas pelos dados de ranking — um limite reconhecido deste dataset, discutido na Seção 7.

### 4.3 Ausência de Problemas de Qualidade

Como detalhado na Seção 3.4, o dataset não apresentou valores ausentes, duplicatas ou inconsistências categóricas. Isso reduz a incerteza sobre a confiabilidade dos KPIs apresentados no dashboard e permitiu que o esforço do projeto fosse direcionado à análise e à comunicação, em vez de à limpeza de dados — um cenário favorável, mas não representativo da maioria dos projetos reais de dados, onde a etapa de tratamento costuma consumir a maior parte do tempo.

---

## 5. UX/UI e Storytelling Visual

O dashboard foi construído em Streamlit, com visualizações em Plotly, e projetado para ser autoexplicativo — ou seja, para comunicar o insight sem exigir que o usuário leia este relatório em paralelo.

### 5.1 Fluxo de Leitura e Hierarquia Visual

Os quatro KPIs principais (Seleções, Média de Pontos, Maior Alta, Maior Queda) foram posicionados no topo da página, imediatamente abaixo do título, seguindo o padrão de leitura em "Z" comum em dashboards executivos: o olhar do usuário varre a linha superior antes de descer para os gráficos. Essa escolha permite que qualquer anomalia agregada seja percebida nos primeiros segundos de contato com o painel, antes mesmo da exploração visual mais detalhada.

### 5.2 Escolha de Visualizações

| Pergunta analítica | Visualização escolhida | Justificativa |
|---|---|---|
| Quem lidera o ranking? | Gráfico de barras horizontais (Top N) | Facilita a leitura de nomes de países e comparação direta de magnitude |
| Como os pontos se distribuem? | Histograma + boxplot marginal | Expõe forma da distribuição e outliers na mesma visualização |
| Confederações se comparam como? | Boxplot por categoria | Compara mediana, dispersão e outliers entre grupos simultaneamente |
| Houve mudança de posição? | Dispersão (rank atual x anterior) | A diagonal de referência torna desvios (subidas/quedas) imediatamente visíveis |

*Tabela 2 — mapeamento entre pergunta de negócio e escolha de gráfico.*

### 5.3 Paleta de Cores e Acessibilidade

Foi definida uma paleta fixa de cores por confederação (mapeamento explícito via `color_discrete_map` no Plotly), garantindo que cada confederação mantenha a mesma cor em todos os gráficos do painel, independentemente dos filtros aplicados. Essa consistência reduz a carga cognitiva do usuário, que não precisa reaprender a legenda a cada seção do dashboard. Os limites do eixo Y dos boxplots são recalculados dinamicamente a partir dos dados filtrados, evitando o corte visual de caixas quando o usuário restringe a seleção de confederações.

### 5.4 Interatividade

Dois controles na barra lateral — filtro multi-seleção de confederação e slider de Top N — permitem que o usuário reconfigure todo o painel sem qualquer conhecimento técnico. Todos os textos interpretativos acima dos gráficos são gerados dinamicamente a partir do DataFrame filtrado (não são strings estáticas), de forma que a narrativa do dashboard permanece coerente com o que está sendo exibido, mesmo após a aplicação de filtros.

---

## 6. Estratégia Adotada

A estratégia geral do projeto seguiu a sequência de missões proposta pelo desafio, com uma decisão adicional de engenharia: o carregamento de dados no dashboard (função `carregar_dados`) tenta primeiro uma conexão direta ao MySQL local e, em caso de falha, recorre a um CSV local como fonte alternativa.

Essa decisão resolve um problema concreto de portabilidade: o ambiente de desenvolvimento roda o MySQL em um container Docker local, inacessível a partir de um deploy em nuvem (Streamlit Community Cloud). O fallback automático elimina a necessidade de reescrever a camada de dados no momento da publicação, mantendo o mesmo código-fonte válido em ambos os contextos — desenvolvimento local e produção.

Adicionalmente, os dados são armazenados em cache via o decorador `@st.cache_data`, evitando reprocessamento a cada interação do usuário com os filtros e mantendo o tempo de resposta do painel abaixo de um segundo em uso local.

---

## 7. Conclusões Finais

O projeto demonstra um pipeline completo e reprodutível — de um banco relacional containerizado até um dashboard interativo publicável — aplicado a um problema real de comunicação de dados esportivos. Os principais achados sustentam três conclusões:

- Há concentração estrutural de força competitiva nas confederações UEFA e CONMEBOL, visível tanto na média de pontos quanto na composição do Top 10 do ranking.
- O ranking, embora predominantemente estável entre atualizações, contém casos de movimentação expressiva que representam oportunidades de análise mais profunda (cruzamento com resultados de partidas específicas).
- A qualidade estrutural do dataset de origem permitiu que o esforço do projeto fosse concentrado na análise e na comunicação, evidenciando o valor de investir em design de storytelling mesmo quando a etapa de limpeza é mínima.

### 7.1 Limitações

- O dataset representa um snapshot pontual do ranking, não uma série temporal completa — análises de tendência ao longo de múltiplas atualizações não são suportadas pelos dados atuais.
- Não há variáveis de contexto (resultados de partidas, calendário de jogos) que expliquem causalmente as movimentações observadas; o dashboard descreve o quê, não o porquê.

### 7.2 Próximos Passos

- Incorporar dados de partidas das Copas de 2018 e 2022 para relacionar variações de ranking a resultados específicos (Missão 4 — modelagem preditiva).
- Expandir o dashboard com uma linha do tempo, caso versões históricas do ranking sejam integradas ao pipeline.

---

## 8. Links e Referências

- **Notebook Kaggle (Missões 1 a 4):** https://www.kaggle.com/code/pyronsk/notebook53c0971197
- **Repositório GitHub:** https://github.com/Paulodms444/copa_challenger_project
- **Dashboard Streamlit:** https://copa-challenger-ranking-fifa.streamlit.app/
- **Vídeo demonstrativo:** https://youtu.be/Im0eh3no_0Q
- **Dataset de origem (Kaggle):** [FIFA Football World Cup](https://www.kaggle.com/datasets/piterfm/fifa-football-world-cup)

> Nota: os links acima devem ser substituídos pelos endereços reais antes da submissão final.

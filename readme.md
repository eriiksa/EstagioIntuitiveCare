# Teste Técnico - Estágio em Desenvolvimento (Intuitive Care)

Este projeto é uma solução completa de **ETL (Extração, Transformação e Carga)** e **API** para consulta de dados de operadoras de planos de saúde, utilizando dados públicos da ANS.

---

## 🛠 Tecnologias Utilizadas

* **Linguagem:** **Python 3.x** (Minha escolha principal pela facilidade com manipulação de dados).
* **Automação/Scraping:** `Selenium`, `os`, `zipfile`.
* **Banco de Dados:** **PostgreSQL** (Primeira vez utilizando, escolhido pela robustez).
* **API:** **Flask** (Escolhido pela simplicidade para quem está começando).
* **ORM:** `SQLAlchemy`.

---

## 💡 Decisões Técnicas e Trade-offs

Como este é um teste para estágio e com prazo curto, priorizei ferramentas que eu já dominava para a parte lógica e "quebrei a cabeça" para aprender as tecnologias novas (Postgres,Postman e criar APIs ) durante a semana. Abaixo explico os porquês:

### 1. Python vs Java
Optei pelo **Python** pois é a linguagem onde tenho mais experiência prática. Como o prazo era curto, usar uma linguagem familiar me permitiu focar nos desafios novos (como a modelagem do banco e a API) sem me preocupar com a sintaxe. 
* **Ferramentas e modelagem de dados** O Python é uma linguagem extremamente consolidada no tratamento de dados. Utilizei a biblioteca Pandas pela sua alta performance no processamento de grandes volumes de informações, o SQLAlchemy para garantir uma camada de segurança e abstração no banco de dados, e o Flask pela agilidade na construção da API. Acredito que esta foi a escolha correta para o projeto, pois uniu minha experiência prévia com ferramentas que se complementam perfeitamente para entregar uma solução robusta.

### 2. Escolha do Banco de Dados (PostgreSQL)
A instrução do teste permitia MySQL ou PostgreSQL. Mesmo nunca tendo desenvolvido com **PostgreSQL**, escolhi ele não somente por ser o padrão da indústria para dados, mas porque ele também utiliza do princípio ACID (Atomicidade, Consistência, Isolamento e Durabilidade) trazendo segurança para os dados monetários. Usei a lib **SQLAlchemy** para facilitar o desenvolvimento com a utilização de ORMs que utilizam de classes e objetos, sendo mais similar com minhas experiências anteriores de desenvolvimento ao invés do SQL puro, que é novo para mim. 
* **Segurança:** SQLalchemy também traz uma camada de segurança contra SQL injection, já que ele não utiliza diretamente concatenação, trazendo esse adicional de segurança muito interessante ao projeto e que também foi solicitado no teste.

### 3. Estratégia de ETL (Selenium e Limpeza)

* **Extração:** Usei **Selenium** em modo *headless* para baixar os arquivos ZIP. A automação com selenium foi a parte onde me senti mais confortável, pois já tenho experiência profissional com automação de arquivos e pastas (`os`, `zipfile`).
* **Filtragem de Despesas:** Para identificar o que era despesa administrativa, filtrei pelo código contábil iniciando em **"411"** ou pela descrição textual. Achei mais seguro converter tudo para *string* antes de processar para não perder zeros à esquerda ou sofrer com arredondamentos.
* **Duplicatas:** Percebi que os arquivos da ANS traziam valores incrementais e repetidos, ao ordenar os valores em ordem descrescente (como pede o teste). Minha solução foi ordenar os valores de forma decrescente e então manter apenas o **maior valor** (o mais atual) para cada CNPJ/Trimestre, garantindo que o banco não ficasse sujo.

### 4. Construção da API (Flask)
Como eu nunca havia desenvolvido uma API antes (apenas consumido), escolhi o **Flask**.

* **Por que não Django/FastAPI?** O Flask é mais minimalista. Para o escopo do teste, achei melhor fazer algo simples que eu conseguisse entender e explicar, do que usar um framework complexo e me perder na configuração.
* **Paginação:** Implementei uma paginação simples baseada em `page` e `limit` (**Offset**). Vi que era uma forma mais intuitiva para quem está começando e funcionou bem para o volume de dados.

---


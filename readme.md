# Teste Técnico - Estágio em Desenvolvimento (Intuitive Care)

Este projeto é uma solução completa de **ETL (Extração, Transformação e Carga)** e **API** para consulta de dados de operadoras de planos de saúde, utilizando dados públicos da ANS.

---

## 🛠 Tecnologias Utilizadas

* **Linguagem:** `Python 3.9`
* **Automação/Scraping:** `Selenium`, `os`, `zipfile`
* **Banco de Dados:** `PostgreSQL`
* **API:** `Flask` 
* **ORM:** `SQLAlchemy`
* **Frontend:** `Vue.js (Vite)`

---
## 💻 Como Executar o Projeto (Via Docker)

A aplicação foi totalmente "dockerizada" para garantir que rode em qualquer máquina sem necessidade de configurar ambiente Python, Node.js ou Banco de Dados manualmente.

### 📋 Pré-requisitos
* **Docker** e **Docker Compose** instalados e rodando.

### Passo a Passo
1. Abra o terminal na raiz do projeto.

   ```
    cd projeto-intuitive
2. Execute o comando de construção e inicialização:

   ```
   docker-compose up --build
3. Aguarde a inicialização:
O **Docker** irá baixar as dependências e subir 3 serviços: **Frontend**, **Backend** e **Data Base**.

* Um serviço automático de ETL (intuitive_etl) iniciará o download dos dados da ANS. Isso pode levar alguns minutos. Acompanhe os logs no terminal.
  
## 🔗 Acessando a Aplicação
Após os containers subirem, acesse o Frontend :
```
http://localhost:5173
```
API Backend :
```
http://localhost:5000/api/operadoras
```
Banco de Dados PostgresSQL (User: postgres / Pass: password) :
```
localhost:5432
```
## 💡 Decisões Técnicas e Trade-offs

Como este é um teste para estágio e com prazo curto, priorizei ferramentas que eu já dominava para a parte lógica e "quebrei a cabeça" para aprender as tecnologias novas (Postgres,Postman e criar APIs ) durante a semana. Abaixo explico os porquês:

### Python vs Java
Optei pelo **Python** pois é a linguagem onde tenho mais experiência prática. Como o prazo era curto, usar uma linguagem familiar me permitiu focar nos desafios novos (como a modelagem do banco e a API) sem me preocupar com a sintaxe. 
* **Ferramentas e modelagem de dados** O Python é uma linguagem extremamente consolidada no tratamento de dados. Utilizei a biblioteca Pandas pela sua alta performance no processamento de grandes volumes de informações, o SQLAlchemy para garantir uma camada de segurança e abstração no banco de dados, e o Flask pela agilidade na construção da API. Acredito que esta foi a escolha correta para o projeto, pois uniu minha experiência prévia com ferramentas que se complementam perfeitamente para entregar uma solução robusta.

### Banco de Dados (PostgreSQL)
A instrução do teste permitia MySQL ou PostgreSQL. Mesmo nunca tendo desenvolvido com **PostgreSQL**, escolhi ele não somente por ser o padrão da indústria para dados, mas porque ele também utiliza do princípio ACID (Atomicidade, Consistência, Isolamento e Durabilidade) trazendo segurança para os dados monetários. 

**Objet Relational Mapping:** Usei a lib **SQLAlchemy** para facilitar o desenvolvimento com a utilização de ORMs que utilizam de classes e objetos, sendo mais similar com minhas experiências anteriores de desenvolvimento ao invés do SQL puro, que é novo para mim. 

**Normalização:** Criei duas tables `operadoras_ativas` e `despesas_consolidadas` . Isso evita repetir dados como Razão social e CNPJ diversas vezes na tabela de despesas, economizando armazenamento e facilitando atualização dos dados da operadora.

**Tipos de Dados:** Para a coluna `vl_saldo_final`, utilizei `Numeric(18,2)` garantindo exatidão com centavos e limitando a apenas duas casas após a virgula, já que float é impreciso e isso pode causar prejuizos monetários, principalmente com grandes volumes de dados.

* **Segurança:** SQLalchemy também traz uma camada de segurança contra SQL injection, já que ele não utiliza diretamente concatenação, trazendo esse adicional de segurança muito interessante ao projeto e que também foi solicitado no teste.

### Estratégia de ETL (Selenium e Limpeza)

* **Extração:** Usei **Selenium** em modo *headless* para baixar os arquivos ZIP. A automação com selenium foi a parte onde me senti mais confortável, pois já tenho experiência profissional com automação de arquivos e pastas (`os`, `zipfile`).
  
* **Processamento na memória:** Optei por processar os arquivos na memória via Pandas, devido ao tamanho dos arquivos. Em média eles eram arquivos de 60mb, então não iriam consumir muita ram e consguiriam facilmente ser rodados por máquinas com 16gb de ram. O processamento em memória também é MUITO mais rápido que o incremental, o que torna ainda mais interessante processa-los em memória nesse caso.

* **Validação de CNPJ:** Utilizei a biblioteca validate-docbr para garantir a integridade dos dados. Por ser uma solução consolidada para documentos brasileiros,isso segue o princípio KISS (Keep It Simple) solicitado no teste, evitando "reinventar a roda". A biblioteca valida o CNPJ matematicamente e, caso o número seja inválido, optei por descartar o registro. Essa decisão prioriza a confiabilidade da base de dados em detrimento da quantidade, garantindo que apenas informações consistentes sejam processadas.

* **Estratégia de Join (Inner Join)** : Fiz um Inner Join entre as Despesas e o Cadastro de Operadoras, já que só me interessam despesas de operadoras que tenham cadastro ativo e válido na ANS. Registros "órfãos" (despesas sem operadora cadastrada) foram ignorados para manter a consistência relacional.
  
* **Filtragem de Despesas:** Para identificar o que era despesa administrativa, filtrei pelo código contábil iniciando em **"411"**. Achei mais seguro converter tudo para *string* antes de processar para não perder zeros à esquerda ou sofrer com arredondamentos.
  
* **Duplicatas:** Percebi que os arquivos da ANS traziam valores incrementais e repetidos, ao ordenar os valores em ordem descrescente (como pede o teste). Minha solução foi ordenar os valores de forma decrescente e então manter apenas o **maior valor** (o mais atual) para cada CNPJ/Trimestre, garantindo que o banco não ficasse sujo.

### Construção da API (Flask)
Como eu nunca havia desenvolvido uma API antes (apenas consumido), escolhi o **Flask**.

* **Por que não Django/FastAPI?** O Flask é mais minimalista. Para o escopo do teste, achei melhor fazer algo simples que eu conseguisse entender e explicar, do que usar um framework complexo e me perder na configuração.
  
* **Paginação:** Implementei uma paginação simples baseada em `page` e `limit` (**Offset**) para pular registros em valores pré-determinados. Eu já havia usado offset em outro projeto e também funcionou bem para o volume de dados dessa vez, evitando que houvesse muito tempo para carregar os elementos no DOM ou até travar o navegador.

* **Busca e Filtro (Server-side):** A busca pela razão social ou CNPJ é feita via query SQL (`ILIKE`) buscando o termo fornecido pelo usuário na query **SQL**. Assim o banco filtra a base de dados primeiro e então devolve o output com até 10 resultados para o frontend.

*  **Cache:** Optei por não usar cache (Redis) na rota de estatísticas. Os dados só mudam trimestralmente (quando o ETL roda). O PostgreSQL lida bem com as agregações atuais. Adicionar Redis traria complexidade de infraestrutura desnecessária para o escopo deste MVP.

### Frontend Vue.js (Vite):

* **Gerenciamento de Estado:** Utilizei `Props` e estado local. Para uma aplicação deste tamanho, usar bibliotecas complexas como Vuex ou Pinia seria excesso de engenharia ("Overengineering"). Manter o estado simples facilitou o desenvolvimento e a leitura do código.

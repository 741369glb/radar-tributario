# Radar Tributário: guia de instalação para iniciantes

Este guia leva você do zero até um site no ar que se atualiza sozinho todos os dias às 6h da manhã. Você não vai escrever nenhuma linha de código: só criar contas, clicar em botões e copiar e colar. Reserve uns 30 a 40 minutos.

## O que tem nesta pasta

| Arquivo | Para que serve |
|---|---|
| `coletor.py` | O "robô" que busca as novidades e escreve os resumos. Não precisa mexer. |
| `fontes.txt` | A lista de assuntos e sites que o robô pesquisa. Você pode editar quando quiser. |
| `requirements.txt` | Lista de peças que o robô precisa. Não precisa mexer. |
| `.github/workflows/atualizar.yml` | O "despertador" que roda o robô todo dia. Não precisa mexer. |
| `docs/index.html` | A página do site. |
| `docs/dados.json` | O arquivo onde ficam as notícias coletadas. Começa vazio. |
| `docs/.nojekyll` | Arquivo vazio que evita um erro na publicação do site. Não apague. |

## Como funciona, em uma frase

Todo dia às 6h, o GitHub (um serviço gratuito) liga o robô, que pesquisa notícias, julgamentos e normas tributárias, pede ao Claude para resumir e explicar cada item, salva tudo e o site já mostra a edição nova.

---

## Passo 1: Descompacte o arquivo

Clique com o botão direito no arquivo `radar-tributario.zip` que você baixou e escolha **Extrair tudo** (Windows) ou dê dois cliques nele (Mac). Vai aparecer uma pasta chamada `radar-tributario`.

## Passo 2: Crie sua conta no GitHub

1. Acesse **github.com** e clique em **Sign up**.
2. Preencha e-mail, senha e um nome de usuário. Anote o nome de usuário: ele fará parte do endereço do seu site (por exemplo, `https://seunome.github.io/radar-tributario/`).
3. Confirme o e-mail. O plano gratuito é suficiente.

## Passo 3: Crie o repositório e envie os arquivos

"Repositório" é só o nome que o GitHub dá a uma pasta de projeto.

1. Já logado, clique no **+** no canto superior direito e escolha **New repository**.
2. Em **Repository name**, escreva `radar-tributario`.
3. Marque **Public**. Isso é necessário para hospedar o site de graça. O código fica visível, mas nenhuma senha sua fica exposta.
4. Clique em **Create repository**.
5. Na tela seguinte, procure o link **uploading an existing file** e clique nele.
6. Abra a pasta `radar-tributario` no seu computador, selecione **tudo o que está dentro dela** (os arquivos e a pasta `docs`) e arraste para a área indicada na página.
7. Espere todos os arquivos aparecerem na lista e clique no botão verde **Commit changes**.

Confira: na página do repositório devem aparecer `coletor.py`, `fontes.txt`, `requirements.txt`, `automacao.yml`, `LEIA-ME.md` e a pasta `docs`. Se a pasta `docs` não apareceu, repita o envio arrastando só ela.

## Passo 4: Crie o "despertador" diário

O GitHub só executa automações que estão numa pasta com nome especial. Vamos criá-la.

1. Na página do repositório, clique em **Add file** e depois em **Create new file**.
2. No campo do nome do arquivo, digite exatamente: `.github/workflows/atualizar.yml`
   Ao digitar cada barra `/`, o GitHub cria uma pasta automaticamente. Isso é normal.
3. No seu computador, abra o arquivo `automacao.yml` com o Bloco de Notas (Windows: botão direito, **Abrir com**, **Bloco de Notas**; Mac: **Abrir com**, **TextEdit**).
4. Selecione todo o conteúdo (Ctrl+A ou Cmd+A), copie e cole na área grande de texto do GitHub.
5. Clique em **Commit changes** e confirme.

## Passo 5 (recomendado): Ative os resumos didáticos com o Claude

Sem esta etapa o site funciona, mas mostra só manchetes com classificação automática simples. Com ela, cada item ganha resumo didático, a seção "Na prática", termos técnicos explicados, o grifo de alta relevância e o "Panorama do dia".

**5.1. Crie a chave da API**

1. Acesse **console.anthropic.com** e crie uma conta.
2. Em **Billing** (cobrança), cadastre um cartão e adicione um crédito pequeno, como US$ 5. O robô usa o modelo mais econômico do Claude, então o gasto mensal costuma ser baixo; você pode acompanhar o consumo nessa mesma tela e definir um limite.
3. Vá em **API Keys** e clique em **Create Key**. Dê um nome (por exemplo, `radar`) e copie a chave que aparecer, que começa com `sk-ant-`. Ela só é mostrada uma vez.

**5.2. Guarde a chave no GitHub com segurança**

1. No seu repositório, clique em **Settings** (aba no topo).
2. No menu da esquerda, clique em **Secrets and variables** e depois em **Actions**.
3. Clique em **New repository secret**.
4. Em **Name**, escreva exatamente: `ANTHROPIC_API_KEY`
5. Em **Secret**, cole a chave.
6. Clique em **Add secret**.

A chave fica guardada de forma secreta: ninguém consegue vê-la, nem você, nem quem visitar o repositório.

## Passo 6: Coloque o site no ar

1. Ainda em **Settings**, clique em **Pages** no menu da esquerda.
2. Em **Source**, escolha **Deploy from a branch**.
3. Em **Branch**, escolha `main` e, ao lado, a pasta `/docs`. Clique em **Save**.
4. Aguarde de 1 a 3 minutos e recarregue a página. Vai aparecer o endereço do seu site, algo como `https://seunome.github.io/radar-tributario/`.

## Passo 7: Rode o robô pela primeira vez

Não precisa esperar até amanhã às 6h.

1. Clique na aba **Actions** no topo do repositório. Se aparecer um aviso pedindo para habilitar as automações, clique no botão verde para habilitar.
2. Na lista à esquerda, clique em **Atualizar Radar Tributário**.
3. Clique em **Run workflow** e depois no botão verde **Run workflow**.
4. Aguarde de 2 a 5 minutos. Quando aparecer um círculo verde com ✓, deu certo.
5. Abra o endereço do seu site. Se ainda estiver vazio, espere mais 1 ou 2 minutos e recarregue (Ctrl+F5).

**Pronto!** A partir de agora o site se atualiza sozinho todos os dias às 6h (horário de Brasília).

---

## Personalizando

**Mudar os assuntos pesquisados.** Abra `fontes.txt` no GitHub, clique no ícone de lápis, edite e clique em **Commit changes**. Cada linha `busca:` vira uma pesquisa no Google Notícias. Exemplos que você pode adicionar:

```
busca: ITCMD (STF OR alíquota OR herança)
busca: "Simples Nacional" (Receita OR resolução OR CGSN)
busca: "imposto seletivo"
```

Também dá para incluir o feed RSS de qualquer site, no formato `Nome | endereço-do-feed`.

**Mudar o horário.** No arquivo `.github/workflows/atualizar.yml`, altere a linha `cron: "0 9 * * *"`. O horário está em UTC, que é Brasília mais 3 horas. Para 7h em Brasília, use `"0 10 * * *"`. Para rodar duas vezes por dia (6h e 18h), use `"0 9,21 * * *"`.

**Mais ou menos itens por dia.** O padrão é até 40 itens novos por execução. Para mudar, adicione ao arquivo de automação, logo abaixo de `ANTHROPIC_API_KEY: ...`, a linha `RADAR_MAX_NOVOS: "60"`, com o mesmo recuo.

## Se algo der errado

**O círculo na aba Actions ficou vermelho.** Clique nele, depois em `atualizar` e veja qual etapa tem um ❌. Os casos mais comuns:

- Erro na etapa **Salvar no site** mencionando permissão (`403` ou `Permission denied`): vá em **Settings**, **Actions**, **General**, role até **Workflow permissions**, marque **Read and write permissions** e clique em **Save**. Depois rode de novo.
- Erro na etapa **Coletar** mencionando `401`: a chave da API foi colada errada. Refaça o passo 5.2 (exclua o segredo e crie de novo).
- Erro mencionando `credit` ou `billing`: acabaram os créditos da API. Adicione mais em console.anthropic.com.

**O site mostra "Não foi possível carregar dados.json".** Confira se a pasta `docs` foi enviada com os dois arquivos dentro (passo 3) e se o Pages está apontando para `/docs` (passo 6).

**O site aparece desatualizado.** Tecle Ctrl+F5 (Windows) ou Cmd+Shift+R (Mac) para forçar o navegador a buscar a versão nova.

**A automação parou de rodar sozinha.** O GitHub pode pausar automações agendadas de repositórios sem atividade por 60 dias. Se isso acontecer, entre na aba Actions e clique para reativar.

## Aviso importante

Os resumos são gerados automaticamente por inteligência artificial a partir de manchetes e trechos públicos, e o robô foi instruído a não inventar informações. Ainda assim, trate o boletim como ponto de partida: antes de usar qualquer informação profissionalmente, confira a fonte original e, no caso de julgamentos, o acórdão ou a certidão de julgamento no site do tribunal.

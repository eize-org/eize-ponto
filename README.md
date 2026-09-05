# pOnto — Sistema de Controle de Ponto Gratuito

O pOnto é um sistema de controle de ponto simples, gratuito e de código aberto. Foi criado para suprir a falta de soluções acessíveis para quem precisa de um controle de ponto básico sem custos ou complexidade desnecessária.

O projeto foi pensado para dois tipos de público: pessoas que só querem **usar** o sistema no dia a dia (sem precisar entender de programação) e desenvolvedores que querem **estudar ou contribuir** com o código.

## Funcionalidades

- Registro de entrada e saída por bolsista, com um clique e confirmação via modal
- Cálculo automático de minutos trabalhados
- Controle de diferença em relação à jornada esperada (4 horas)
- Controle de pendência (horas devidas) por bolsista, com abatimento automático
- Pagamento fragmentado de pendência — o bolsista pode quitar horas devidas em qualquer momento, separado do ponto normal
- Proteção contra duplicidade de registros (cliques duplos, requisições simultâneas ou dois tipos de ponto abertos ao mesmo tempo)
- Painel administrativo completo para o gerente, incluindo histórico de sessões
- Restrição de acesso por IP — apenas máquinas autorizadas conseguem abrir o sistema
- Scripts de configuração e inicialização para Windows

## Tecnologias

- Python 3.x
- Django 6.0.2
- Django REST Framework 3.16.1
- SQLite
- Bootstrap 5.3.3

## Pré-requisitos

- Python 3.x instalado — [python.org/downloads](https://www.python.org/downloads/)
- Git instalado (opcional — veja abaixo) — [git-scm.com](https://git-scm.com/)

## Instalação

Você pode baixar o pOnto de duas formas. Escolha a que for mais confortável:

### Opção 1 — Sem Git (recomendado para quem só vai usar o sistema)

1. Acesse o repositório: [eize-pOnto](https://github.com/eize-org/eize-ponto)
2. Clique no botão verde **"Code"** e depois em **"Download ZIP"**
3. Descompacte o arquivo baixado em uma pasta de sua escolha

### Opção 2 — Com Git (recomendado para desenvolvedores)

```bash
git clone https://github.com/eize-org/eize-ponto.git
cd eize-ponto
```

### Configuração inicial (apenas na primeira vez)

Dentro da pasta do projeto, dê dois cliques em:
```
setup.bat
```

Durante o setup você será solicitado a:
- Informar os IPs das máquinas que terão acesso ao sistema
- Criar o usuário administrador (gerente)

### Uso diário

Para ligar o sistema, dê dois cliques em:
```
iniciar.bat
```

Mantenha essa janela aberta enquanto o sistema estiver em uso — fechá-la desliga o servidor.

## Como usar — Bolsista (bater o ponto)

### Ponto normal (entrada e saída)

1. Acesse a página inicial pelo navegador
2. Clique no botão com o seu nome
3. Confirme o registro na janela que aparece

O sistema alterna automaticamente entre entrada e saída: o primeiro clique do dia registra a entrada, o clique seguinte registra a saída.

Uma mensagem de confirmação aparece após cada registro — verde para entrada, laranja para saída. Se você tentar bater o ponto novamente muito rápido (menos de 5 segundos), o sistema bloqueia e avisa qual ação já foi registrada, evitando duplicidade.

### Pagando horas pendentes

Bolsistas com pendência (horas devidas) podem quitá-las de forma fragmentada, sem precisar esperar o próximo dia de trabalho. Por exemplo: pagar 2 horas à tarde e depois cumprir o expediente normal à noite.

1. Na página inicial, clique no botão **"Pagar horas pendentes"**, logo abaixo dos botões normais
2. Os botões dos bolsistas aparecem na cor laranja
3. Clique no seu nome e confirme o registro

Assim como o ponto normal, o primeiro clique abre a sessão e o clique seguinte a fecha. Todo o tempo trabalhado nessa sessão é descontado diretamente da pendência — diferente do ponto normal, aqui não há relação com a jornada de 4 horas.

> **Importante:** não é possível ter um ponto normal e um pagamento de pendência abertos ao mesmo tempo. Se você tentar bater um tipo de ponto enquanto o outro está em aberto, o sistema bloqueia e avisa que é necessário fechar a sessão aberta primeiro.

## Como usar — Administrador (gerente)

O painel administrativo é acessado em `/admin/`, usando o usuário criado durante o setup.

### Acessando o painel

1. No navegador, acesse `http://<IP-do-servidor>:8000/admin/`
2. Informe o usuário e a senha do administrador
3. Você verá duas seções principais: **Bolsistas** e **Sessãos**

### Cadastrando um novo bolsista

1. No painel, clique em **Bolsistas**
2. Clique em **Adicionar Bolsista** (canto superior direito)
3. Preencha o **nome** do bolsista
4. Deixe o campo **Pendência (HH:MM)** como `00:00` (sem pendência inicial)
5. Clique em **Salvar**

> 💡 **Importante:** Após salvar, o sistema vai gerar automaticamente um **Link do histórico** (pessoal e intransferível). Copie esse link e **envie para o bolsista** (ex: via WhatsApp). É por ele que o bolsista poderá acompanhar suas horas trabalhadas diretamente do próprio celular de casa.

O bolsista aparece imediatamente na tela pública de registro de ponto.

### Acompanhando as sessões de um bolsista

1. No painel, clique em **Bolsistas**
2. Clique no nome do bolsista desejado
3. Role até a seção **Sessão trabalho** — lá aparece o histórico completo: tipo de sessão (normal ou pagamento de pendência), entrada, saída, tempo trabalhado, diferença em relação às 4h esperadas e quanto foi abatido da pendência em cada dia

> Por segurança, entrada e saída não podem ser editadas manualmente — elas são sempre geradas pelo próprio sistema no momento em que o bolsista bate o ponto.

### Adicionando uma pendência (falta ou ajuste de horas)

Use este recurso quando o bolsista faltar e precisar compensar as horas depois, ou quando for necessário ajustar manualmente o saldo dele.

1. No painel, clique em **Bolsistas**
2. Clique no nome do bolsista
3. No campo **Pendência (HH:MM)**, digite o valor desejado — por exemplo, `04:00` para 1 turno (4 horas)
4. Clique em **Salvar**

A partir daí, a pendência pode ser quitada de duas formas:

- **Pelo ponto normal:** sempre que o bolsista trabalhar **mais** que as 4 horas esperadas em um dia, o excedente é descontado automaticamente da pendência
- **Pelo pagamento de pendência:** o bolsista bate esse ponto separadamente e todo o tempo registrado é descontado da pendência, independente da jornada normal

Se o tempo pago (excedente ou pagamento de pendência) for maior que a pendência restante, a sobra não vira hora extra — ela simplesmente não é contabilizada.

### Consultando quem está com pendência

Na lista de **Bolsistas**, a coluna **Pendência** mostra o saldo devedor de cada um no formato `HH:MMh`. Bolsistas sem pendência aparecem como `00:00h`.

## Acesso

| Página | URL |
|---|---|
| Bater ponto | `http://<IP-do-servidor>:8000/` |
| Painel do administrador | `http://<IP-do-servidor>:8000/admin/` |

Substitua `<IP-do-servidor>` pelo IP da máquina onde o sistema está rodando.

## ☁️ Arquitetura em Nuvem (Histórico Público)

Para permitir que bolsistas acessem o histórico de casa sem expor o PC da biblioteca, o projeto conta com uma arquitetura de sincronização de 3 peças:
1. **Este repositório (PC Local):** É a fonte da verdade. Dispara signals sempre que o ponto é batido ou o bolsista é atualizado, enviando um POST silencioso (em background) para a nuvem.
2. **[eize-ponto-historico](https://github.com/eize-org/eize-ponto-historico) (GitHub Pages):** O frontend (HTML/JS) e o armazenamento (JSONs). O PC local escreve os dados diretamente nessa pasta via API do GitHub, e a página lê os arquivos instantaneamente (sem servidor intermediário).

## Como descobrir o IP de uma máquina

**No Windows**, abra o Prompt de Comando e execute:
```
ipconfig
```
Procure pela seção **"Adaptador de Rede sem Fio"** (Wi-Fi) ou **"Adaptador Ethernet"** (cabo) e anote o valor de **Endereço IPv4**, que terá um formato parecido com `192.168.1.105`.

Para abrir o Prompt de Comando rapidamente pressione `Win + R`, digite `cmd` e pressione Enter.

> **Dica:** Computadores conectados via cabo tendem a ter IPs fixos na rede local, o que evita a necessidade de atualizar o `.env` com frequência. Máquinas conectadas via Wi-Fi podem ter o IP alterado pelo roteador ao reconectar.

## Configuração de IPs

O sistema restringe o acesso apenas às máquinas autorizadas. Os IPs são definidos durante o setup e ficam armazenados no arquivo `.env`:

```
ALLOWED_IPS=XXX.X.X.X,XXX.X.X.X
```

Ao acessar de um IP fora dessa lista, o sistema exibe "Acesso negado."

Para adicionar ou remover IPs, edite o arquivo `.env` diretamente e reinicie o servidor.

> **Importante:** o IP do próprio servidor deve estar incluído na lista (geralmente `127.0.0.1`), além do IP de cada máquina que vai acessar pelo navegador. É o IP do **servidor** que deve ser digitado no navegador das outras máquinas — não o IP da máquina que está acessando.

## Estrutura do projeto

```text
pOnto/
├── config/               # Configurações gerais do Django (settings, urls principais)
├── core/                 # App principal
│   ├── models.py         # Bolsista e SessaoTrabalho (com regras de negócio no save)
│   ├── views.py          # Lógica de registro de ponto
│   ├── admin.py          # Painel administrativo
│   ├── middleware.py     # Restrição de acesso por IP
│   ├── sync.py           # Envio de dados para a nuvem em background (threads)
│   └── signals.py        # Gatilhos automáticos de sincronização ao salvar dados
├── docs/                 # Documentações técnicas e regras do projeto
├── templates/core/       # Interfaces HTML do usuário
├── setup.bat             # Configuração inicial do ambiente Windows (executar uma vez)
├── iniciar.bat           # Inicialização diária do servidor local
├── atualizar.bat         # Atualização automatizada do sistema (puxando do GitHub)
├── requirements.txt      # Dependências do projeto (Django, decouple, requests)
└── .env.example          # Template e explicação das variáveis de ambiente
```

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `DJANGO_SECRET_KEY` | Chave secreta do Django (gerada no momento do setup) |
| `DJANGO_DEBUG` | Ativa o modo debug do Django (`True` ou `False`) |
| `ALLOWED_IPS` | IPs autorizados a acessar o sistema, separados por vírgula |
| `GITHUB_TOKEN` | Token do GitHub com acesso ao repositório do histórico (Recomenda-se usar uma conta "Bot" colaboradora para segurança) |
| `GITHUB_REPO` | Nome do repositório destino (ex: `eize-org/eize-ponto-historico`) |

## Proteção contra duplicidade

Para evitar registros duplicados por duplo clique, requisições simultâneas ou conflito entre tipos de ponto, o sistema conta com quatro camadas de proteção:

- O botão de confirmação é desabilitado assim que clicado, evitando duplo envio pelo navegador
- O banco de dados trava a linha do bolsista durante o registro (`select_for_update`), impedindo que duas requisições simultâneas leiam o mesmo estado
- Um intervalo mínimo de 5 segundos entre registros do mesmo bolsista bloqueia tentativas muito próximas, informando qual ação já havia sido registrada
- Se já existe uma sessão aberta de um tipo (normal ou pagamento de pendência), o sistema impede a abertura de uma sessão do outro tipo e avisa que é necessário fechar a sessão em aberto primeiro

## Como contribuir

Contribuições são bem-vindas! Se você encontrou um bug, tem uma sugestão ou quer adicionar uma funcionalidade:

1. Faça um fork do repositório
2. Crie uma branch para sua alteração:
```bash
git checkout -b minha-alteracao
```
3. Faça o commit das suas mudanças:
```bash
git commit -m "Descrição da alteração"
```
4. Envie para o seu fork:
```bash
git push origin minha-alteracao
```
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---

Desenvolvido por [eize-org](https://github.com/eize-org)

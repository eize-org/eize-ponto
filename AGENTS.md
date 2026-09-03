# Regras de Sistema — pOnto (Antigravity)

Estas são as regras globais que qualquer agente trabalhando neste projeto deve seguir. O objetivo é manter consistência com o que já foi construído, mesmo sem memória de conversas anteriores.

## 1. Stack — não desviar sem justificativa explícita

- **Backend:** Django 6.0.2 puro (não introduzir FastAPI, Flask, etc.)
- **Frontend:** templates Django + Bootstrap 5.3.3 via CDN. **Não introduzir Next.js, React, Vue ou qualquer build step de frontend** — essa opção já foi avaliada e descartada deliberadamente em favor de simplicidade de instalação (o público-alvo inclui pessoas não-técnicas que só têm Python instalado)
- **Banco:** SQLite. Não migrar para Postgres/MySQL sem discussão explícita — a simplicidade de "um arquivo só" é parte do design para instalação fácil
- **Variáveis de ambiente:** sempre `python-decouple` (`from decouple import config`). Nunca introduzir `python-dotenv` — são padrões conflitantes e o projeto já escolheu um
- Antes de adicionar qualquer nova dependência ao `requirements.txt`, considerar se ela é realmente necessária — o projeto valoriza poucas dependências, instalação rápida e simples

## 2. Convenções de nomenclatura

- **Nomes em português**, seguindo o que já existe no projeto: `Bolsista`, `SessaoTrabalho`, `pendencia_min`, `pagina_ponto`, `historico_bolsista`. Não traduzir para inglês nem misturar idiomas dentro do mesmo domínio — manter consistência com o código existente
- Nomes de arquivos de template em português: `ponto.html`, `historico.html`
- Nomes de rotas (`name=` no `path()`) em português, casando com o nome da view
- Variáveis de ambiente em `MAIUSCULO_COM_UNDERSCORE`, prefixadas quando fizer sentido (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `ALLOWED_IPS`)

## 3. Onde a lógica de negócio deve viver

- **Regras de cálculo (horas trabalhadas, diferença, abatimento de pendência) vivem no `save()` do model**, não na view. Isso é deliberado: garante que a regra vale não importa de onde a sessão seja salva (view pública, admin, script de sincronização futuro). Ao adicionar nova lógica de cálculo, seguir esse padrão — não duplicar cálculo na view
- Views devem ficar finas: validação de entrada, orquestração (locking, mensagens), delegando o cálculo pesado para o model
- Constantes de regra de negócio (como `MINUTOS_ESPERADOS = 240`) ficam no topo do `models.py`, não hardcoded espalhadas pelo código

## 4. Concorrência e integridade de dados

- Qualquer operação de escrita que possa ser disparada por múltiplos cliques/requisições simultâneas **deve** usar `transaction.atomic()` + `select_for_update()` nas linhas afetadas — este é o padrão já estabelecido em `pagina_ponto` e deve ser replicado em qualquer nova view de escrita
- Nunca confiar apenas em desabilitar o botão no frontend como única proteção contra duplicidade — é uma camada complementar, não substitui a trava no banco

## 5. Migrações — regra crítica, já causou incidentes reais

- **Migrações são versionadas no Git.** Nunca adicionar `migrations/*.py` ao `.gitignore` novamente — isso já causou dessincronização severa de schema entre ambientes de produção
- **Nunca adicionar um campo novo com `unique=True` diretamente em uma tabela que já pode ter dados.** Sempre em 3 passos:
  1. Migração que adiciona o campo sem `unique=True` (com `default` ou `blank=True`)
  2. Data migration (`RunPython`) que popula os valores existentes
  3. Migração separada que altera o campo para `unique=True`
- Ao gerar uma migração, sempre rodar `showmigrations` antes e depois para confirmar que não há "leaf nodes" conflitantes (isso acontece quando arquivos de migração não commitados divergem entre máquinas)
- Scripts `.bat` que operam em produção (`atualizar.bat`, `iniciar.bat`, `setup.bat`) **devem estar versionados no repositório**, nunca criados manualmente só na máquina cliente — evita conflitos de merge

## 6. Tratamento de erros

- Falhas em operações **secundárias/auxiliares** (ex: sincronização com serviço externo, logging) nunca podem quebrar o fluxo principal do usuário. Envolver em `try/except`, logar o erro, e seguir — bater ponto localmente sempre tem que funcionar, mesmo se a internet cair
- Mensagens de erro voltadas ao usuário final (bibliotecário, bolsista) devem ser em português, claras, específicas o suficiente para a pessoa entender o que aconteceu e o que fazer (ex: "A entrada de Guilherme já foi registrada", não "Erro 400")
- Nunca silenciar exceções de forma que o desenvolvedor perca visibilidade — usar `logging`, não apenas `pass`

## 7. Arquitetura de histórico remoto (em desenvolvimento — seguir o desenho já decidido)

Ao trabalhar na funcionalidade de acesso remoto ao histórico, seguir o desenho já definido em `tech_spec.md` (seção 5), não propor uma arquitetura alternativa sem justificativa forte:

- **GitHub Pages** hospeda só HTML/CSS/JS estático — a "cara" do histórico, lendo o token da query string e consumindo dados via `fetch()`. Vive em `eize-org/eize-ponto-historico`, repositório separado
- **PythonAnywhere** é só uma **API JSON**, sem template/HTML — recebe sincronização do PC local (protegida por chave secreta) e responde consultas de histórico. Código-fonte vive em `eize-org/eize-ponto-api-historico`, repositório separado
- **PC local** continua sendo a fonte da verdade dos dados (este repositório, `eize-org/eize-ponto`); a sincronização é unidirecional (local → nuvem), nunca o contrário
- Essa separação existe para que o domínio público (`.github.io`) seja permanente e gratuito de verdade, e para reduzir a responsabilidade do PythonAnywhere a algo simples de manter (só dados, sem renderização)
- **Três repositórios, três responsabilidades — não misturar código de um no outro.** Se o agente estiver trabalhando dentro de `eize-ponto` (este repo), qualquer código do frontend estático ou da API do PythonAnywhere pertence a outro repositório, não deve ser criado aqui

## 8. Segurança

- A segurança de acesso do sistema é primariamente por **restrição de rede** (`IPWhitelistMiddleware`), não por autenticação de usuário — isso é intencional, dado o público não-técnico e o caso de uso interno. Não propor adicionar login/senha para bolsistas sem alinhar antes, é uma mudança de modelo de segurança, não um detalhe de implementação
- O acesso ao histórico individual é protegido por token longo e aleatório (`secrets.token_urlsafe(24)`), não por senha — manter esse padrão para qualquer nova funcionalidade de acesso "sem login"
- Qualquer endpoint que vá ficar exposto à internet pública (ex: rotas de sincronização com PythonAnywhere) precisa de autenticação por chave secreta compartilhada, no mínimo — nunca deixar uma rota de escrita pública sem proteção alguma

## 9. Estilo e formatação de código

- Python: seguir PEP 8 razoavelmente, mas o projeto já usa alinhamento de `=` em alguns blocos de definição de campos de model (estilo "tabela") — manter esse estilo ao editar models existentes, não é obrigatório introduzir em código novo
- Sem type hints extensivos no código atual — não é uma convenção forte do projeto, mas adicionar em código novo é bem-vindo se não conflitar com legibilidade
- HTML/templates: manter Bootstrap utility classes, evitar CSS customizado extenso — quando necessário, usar `<style>` inline no próprio template (padrão já usado em `ponto.html` e `historico.html`), já que não há pipeline de assets

## 10. Documentação

- Toda funcionalidade nova voltada ao usuário final deve ser refletida no `README.md` (que é bilíngue de público: serve tanto para quem só usa quanto para quem desenvolve)
- Mudanças de arquitetura relevantes devem atualizar `tech_spec.md` e `current_state.md` (ou os arquivos equivalentes que existirem no momento)

## 11. O que NUNCA fazer sem confirmação explícita do dono do projeto

- Introduzir custo recorrente (domínio pago, hospedagem paga, serviço pago) — restrição orçamentária real
- Adicionar autenticação de usuário/senha para bolsistas
- Tornar a jornada de trabalho configurável por pessoa (hoje é fixa em 4h para todos)
- Permitir edição manual de entrada/saída de sessões pelo admin
- Remover ou enfraquecer o `IPWhitelistMiddleware` na tela de bater ponto e no admin
- Migrar o frontend para um framework JS ou introduzir build step

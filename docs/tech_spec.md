# Tech Spec — pOnto

## 1. Stack tecnológica (real, confirmada)

> **Nota importante:** este projeto **não usa Next.js nem nenhum frontend separado**. Essa opção foi cogitada no início e descartada deliberadamente em favor de simplicidade — o frontend é feito com templates Django server-side rendered + Bootstrap via CDN, sem build step, sem Node.js envolvido.

- **Backend:** Django 6.0.2
- **API:** Django REST Framework 3.16.1 (existe, mas o uso principal do sistema hoje é via views tradicionais + templates, não via API)
- **Frontend:** Templates Django (`.html`) + Bootstrap 5.3.3 (CDN) + JavaScript vanilla inline (sem framework, sem bundler)
- **Banco de dados:** SQLite
- **Variáveis de ambiente:** `python-decouple` (não usar `python-dotenv` — decisão de padronização do projeto)
- **Hospedagem atual:** um único PC Windows local, sem servidor dedicado, rodando `python manage.py runserver 0.0.0.0:8000`
- **Hospedagem em desenvolvimento:** PythonAnywhere (free tier) para uma segunda instância, só da rota de histórico (ver seção 5)

## 2. Arquitetura atual (single-server, rede local)

```
┌────────────────────────────────────┐
│         PC da Biblioteca             │
│  (único servidor, Windows, local)    │
│                                       │
│  Django rodando em 0.0.0.0:8000      │
│  SQLite (db.sqlite3)                 │
│                                       │
│  IPWhitelistMiddleware restringe     │
│  acesso a IPs autorizados (.env)     │
└──────────────┬────────────────────────┘
               │
      Rede local (LAN/Wi-Fi da biblioteca)
               │
      ┌────────┴────────┐
      │                 │
  PC autorizado 1   PC autorizado 2
  (bate ponto/admin) (bate ponto/admin)
```

**Restrição de segurança atual:** `core/middleware.py` (`IPWhitelistMiddleware`) verifica `request.META['REMOTE_ADDR']` contra uma lista em `settings.ALLOWED_IPS` (vinda do `.env`, variável `ALLOWED_IPS`). Qualquer IP fora da lista recebe `403 Forbidden` com a mensagem "Acesso negado."

## 3. Modelo de dados atual

### `Bolsista`
```python
class Bolsista(models.Model):
    nome = models.CharField(max_length=100)
    pendencia_min = models.IntegerField(default=0)  # minutos devidos
    token = models.CharField(max_length=64, unique=True, blank=True)
    # token gerado automaticamente no save() via secrets.token_urlsafe(24)
    # se estiver vazio no momento do save
```

Métodos relevantes:
- `sessao_aberta()` → retorna a `SessaoTrabalho` em aberto (qualquer tipo), se existir
- `pendencia_display()` → formata `pendencia_min` como `HH:MMh`

### `SessaoTrabalho`
```python
class SessaoTrabalho(models.Model):
    NORMAL = 'normal'
    PENDENCIA = 'pendencia'
    TIPOS = [(NORMAL, 'Normal'), (PENDENCIA, 'Pagamento de pendência')]

    bolsista = models.ForeignKey(Bolsista, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPOS, default=NORMAL)
    entrada = models.DateTimeField(default=timezone.now)  # NÃO é auto_now_add
    saida = models.DateTimeField(null=True, blank=True)
    min_trabalhados = models.IntegerField(null=True, blank=True)
    diferenca_min = models.IntegerField(null=True, blank=True)  # só para tipo NORMAL
    pendencia_abatida_min = models.IntegerField(null=True, blank=True)
```

**Regra de negócio central, implementada dentro do `save()` do model** (não na view — decisão deliberada para que a lógica funcione independente de onde a sessão for salva, admin ou view pública):

```python
MINUTOS_ESPERADOS = 240  # 4 horas, constante fixa

def save(self, *args, **kwargs):
    if self.entrada and self.saida:
        self.min_trabalhados = int((self.saida - self.entrada).total_seconds() / 60)

        if self.pendencia_abatida_min is None:  # só abate uma vez por sessão
            if self.tipo == self.PENDENCIA:
                self.diferenca_min = None
                abatido = min(self.min_trabalhados, self.bolsista.pendencia_min)
                self.bolsista.pendencia_min -= abatido
                self.bolsista.save()
                self.pendencia_abatida_min = abatido
            else:
                self.diferenca_min = self.min_trabalhados - MINUTOS_ESPERADOS
                excedente = max(self.diferenca_min, 0)
                abatido = 0
                if excedente > 0 and self.bolsista.pendencia_min > 0:
                    abatido = min(excedente, self.bolsista.pendencia_min)
                    self.bolsista.pendencia_min -= abatido
                    self.bolsista.save()
                self.pendencia_abatida_min = abatido

    super().save(*args, **kwargs)
```

Funções utilitárias (`core/models.py`, nível de módulo):
```python
def minutos_para_horas(minutos):  # -> "HH:MMh", ex: "04:00h", "-03:52h"
def horas_para_minutos(texto):    # parseia "HH:MM" de volta para int
```

## 4. Rotas existentes

### API (DRF, sob prefixo `/api/`, definidas em `core/urls.py`)
```
GET  /api/bolsistas/                    → lista_bolsistas
GET  /api/bolsistas/<int:pk>/           → busca_bolsista
POST /api/bolsistas/<int:pk>/ponto/     → ponto_bolsista (alterna entrada/saída, tipo normal apenas — não tem tipo pendência ainda na API)
GET  /api/bolsistas/<int:pk>/sessoes/   → sessoes_bolsista
```

### Web (templates, servidas na raiz `/`, definidas em `core/urls_web.py`)
```
GET/POST /                          → pagina_ponto (tela pública de bater ponto, ambos os tipos)
GET      /historico/<str:token>/    → historico_bolsista (histórico individual por token)
```

### Admin
```
/admin/  → Django Admin padrão, com BolsistaAdmin e SessaoTrabalhoAdmin customizados
```

**Observação de inconsistência conhecida:** a API (`ponto_bolsista`) ainda não foi atualizada para suportar o campo `tipo` (normal/pendência) nem as proteções de duplicidade que a view web (`pagina_ponto`) já tem (`select_for_update`, intervalo de 5s, bloqueio de tipo conflitante). Hoje a API é secundária — o fluxo real de uso é todo via `pagina_ponto`. Se a API for retomada como canal ativo, precisa de paridade de regras com a view web.

## 5. Rotas/arquitetura implementada (GitHub Pages + PythonAnywhere)

**Objetivo:** permitir que o histórico do bolsista seja acessível de qualquer lugar (fora da rede local), sem expor a tela de bater ponto nem o admin, e sem custo de domínio/hospedagem.

**Por que não é possível resolver só localmente:** a rede da universidade onde a biblioteca fica é segmentada em sub-redes que não se enxergam entre si (ex: PC servidor em `10.124.99.x` via cabo, celulares em `10.114.119.x` via Wi-Fi) — não há acesso/permissão para alterar essa infraestrutura de rede.

**Arquitetura decidida — três partes, separando visual de dados:**

```
PC local (fonte da verdade, dados reais)
   │  POST autenticado a cada mudança relevante
   ▼
PythonAnywhere (cópia/espelho, free tier)
   │  API "burra", só devolve JSON — sem HTML, sem template
   │  GET /api/historico/<token>/  →  {"bolsista": ..., "sessoes": [...]}
   ▲
   │  fetch() via JavaScript
   │
GitHub Pages (github.io, estático, grátis e permanente)
   │  HTML com campo pra colar/receber o token
   │  JS busca os dados na API do PythonAnywhere e monta a tabela
   ▼
Celular do bolsista (de qualquer lugar)
```

**Por que separar assim:** o GitHub Pages nunca expira, nunca muda de domínio e é 100% gratuito de forma permanente — mas só serve conteúdo estático (HTML/CSS/JS), não consegue consultar banco de dados diretamente. O PythonAnywhere continua sendo necessário como a peça que efetivamente acessa dados, mas fica reduzido a uma API JSON simples, sem responsabilidade de renderizar nada — reduz a superfície do que pode quebrar do lado da nuvem, e o design/UX fica centralizado e versionado como uma página estática comum.

O link enviado ao bolsista pode continuar no formato de sempre (com o token na URL), agora apontando para o GitHub Pages, ex:
```
https://eize-org.github.io/eize-ponto-historico/?token=<token>
```
O JavaScript da página lê o `token` da query string, chama a API do PythonAnywhere, e renderiza a tabela.

### A construir no PythonAnywhere (projeto novo/separado — API apenas)
- Projeto Django enxuto com models equivalentes a `Bolsista` e `SessaoTrabalho` (só o necessário para responder consultas — não precisa da lógica de abatimento/cálculo, já que os valores já vêm calculados e prontos do PC local)
- Rotas de sincronização (recebendo dados do PC local), protegidas por chave secreta em header (ex: `X-Sync-Key`):
  ```
  POST /sincronizar/bolsista/    → cria ou atualiza um Bolsista (por id ou token)
  POST /sincronizar/sessao/      → cria ou atualiza uma SessaoTrabalho (por id)
  ```
- Rota pública de consulta, **retornando JSON, não HTML**:
  ```
  GET /api/historico/<str:token>/   → JSON com nome do bolsista, pendência atual e lista de sessões
  ```
  Precisa de **CORS habilitado** (`django-cors-headers` ou equivalente) para aceitar requisições vindas do domínio do GitHub Pages — isso é uma peça nova, não existia necessidade de CORS no projeto até agora, já que tudo era same-origin.

### A construir no GitHub Pages (repositório novo ou pasta `docs/` do mesmo repo)
- Uma página HTML simples + JS puro (ou pode reaproveitar visualmente o CSS/estrutura de `templates/core/historico.html` como referência de estilo)
- Lê o `token` da query string (`?token=...`)
- Faz `fetch()` para a API do PythonAnywhere
- Renderiza a tabela de sessões, badges de tipo (normal/pendência), pendência atual — replicando a experiência visual que já existe hoje em `historico.html`
- Trata erro de token inválido/não encontrado de forma amigável (hoje isso é um 404 do Django; na versão estática, precisa ser tratado no JS a partir do status da resposta da API)

### A construir no PC local (projeto principal)
- Disparo de sincronização (`requests.post`) após:
  - Criar/editar um `Bolsista` no admin (nome, pendência, token)
  - Fechar uma `SessaoTrabalho` (entrada + saída preenchidas)
- Novas variáveis de ambiente no `.env` (via `python-decouple`, seguindo o padrão já usado):
  ```
  SYNC_URL=https://<usuario>.pythonanywhere.com/sincronizar/
  SYNC_KEY=<chave secreta compartilhada>
  ```
- **Falha de sincronização não pode bloquear o fluxo principal** — bater ponto localmente sempre funciona, mesmo se a internet cair ou o PythonAnywhere estiver fora do ar. Tratar com try/except silencioso + log, no mínimo.
- A rota local `/historico/<token>/` (view + template) provavelmente deixa de ser necessária no PC local, já que a experiência de histórico passa a viver inteiramente em GitHub Pages + PythonAnywhere. Avaliar remoção ou manutenção como fallback interno (ex: para o bibliotecário conferir algo rapidamente sem depender da sincronização).

### Decisões técnicas implementadas
1. **Retry de sincronização:** A sincronização local (`requests.post`) roda em threads separadas (`daemon=True`) via signals (`post_save`), com um timeout de 5 segundos. Falhas (sem internet) são ignoradas com log local, sem bloquear a usabilidade para a biblioteca.
2. **Chave de correlação:** O `token` atua como chave de upsert para os Bolsistas. Para `SessaoTrabalho`, o `id` local é mapeado para um campo `id_origem` no banco remoto, evitando a complexidade de adicionar UUIDs no MVP.
3. **Escopo do JSON:** O retorno envia dados pré-formatados (ex: `pendencia_display`, `trabalhado_display`), mantendo a API e o frontend puramente focados na exibição da informação sem recalcular horas.
4. **CORS e Segurança:** A API no PythonAnywhere usa `django-cors-headers` restrito ao GitHub Pages. As rotas de sincronização validam o header `X-Sync-Key` contra o `.env`.
5. **UX:** O admin Django do PC local gera e exibe a URL pública do GitHub Pages (`?token=...`) para facilitar o compartilhamento.

### Organização de repositórios (decidido)

O projeto passa a ser composto por **três repositórios**, cada um com responsabilidade única:

1. **`eize-org/eize-ponto`** (já existe, é este repositório) — sistema principal Django, roda no PC local da biblioteca. Continua contendo tudo que já existe hoje (models, views, admin, migrações, scripts `.bat`)
2. **`eize-org/eize-ponto-historico`** (novo) — repositório dedicado ao GitHub Pages. Contém só HTML/CSS/JS estático, sem nenhum código Python. Publicado via GitHub Pages a partir da branch principal (ou de uma pasta `docs/` dentro dele, dependendo da configuração escolhida no momento de ativar o Pages)
3. **`eize-org/eize-ponto-api-historico`** (novo) — projeto Django enxuto que roda no PythonAnywhere. Contém só os models espelho e as rotas de sincronização/consulta (seção acima)

**Por que três repositórios e não um só com pastas:** cada peça tem ciclo de deploy e ambiente de execução completamente diferentes (PC Windows local / GitHub Pages / PythonAnywhere) — misturar tudo em um repositório só dificultaria versionamento e deploy independente de cada parte. Também evita que uma mudança no sistema principal quebre acidentalmente o site público ou a API, e vice-versa.

## 6. Scripts de operação (Windows, `.bat`)

- `setup.bat` — primeira configuração: venv, dependências, `.env` (via `setup_env.py`), migrações, superusuário
- `iniciar.bat` — uso diário: `python manage.py runserver 0.0.0.0:8000`
- `atualizar.bat` — puxa código novo e aplica migrações (deve estar **versionado no Git**, nunca criado manualmente na máquina cliente, senão gera conflito de merge)

## 7. Convenções de infraestrutura já estabelecidas

- `.env` e `db.sqlite3` nunca vão para o Git
- **Migrações VÃO para o Git** (mudança recente — antes eram ignoradas, isso causou problemas sérios de sincronização de schema entre ambientes e foi corrigido)
- Padrão de migração para campos `unique=True` novos em tabela com dados existentes: sempre em 3 passos — (1) adicionar campo sem unique, (2) data migration populando valores, (3) migração separada aplicando `unique=True`

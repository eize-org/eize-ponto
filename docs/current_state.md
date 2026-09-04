# Estado Atual — pOnto

## 1. Estrutura de pastas (projeto principal, local)

```
eize-ponto/
├── config/
│   ├── settings.py
│   ├── urls.py            # inclui admin/, api/ (core.urls), '' (core.urls_web)
│   └── wsgi.py
├── core/
│   ├── models.py           # Bolsista, SessaoTrabalho
│   ├── views.py             # views de API (DRF) + views web
│   ├── admin.py              # BolsistaForm, BolsistaAdmin, SessaoTrabalhoAdmin, FiltroSemana
│   ├── urls.py                 # rotas da API, sob /api/
│   ├── urls_web.py              # rotas web, sob '/'
│   ├── middleware.py             # IPWhitelistMiddleware
│   ├── serializers.py             # BolsistaSerializer, SessaoTrabalhoSerializer
│   └── migrations/                 # VERSIONADAS no Git (0001 até 0008 aplicadas e testadas)
├── templates/core/
│   ├── ponto.html            # tela pública de bater ponto (dois tipos: normal e pendência)
│   └── historico.html         # tela pública (por token) de histórico individual
├── setup.bat
├── iniciar.bat
├── atualizar.bat               # deve estar versionado no Git
├── setup_env.py
├── requirements.txt
└── .env.example
```

## 2. O que já está codificado e funcionando (testado em produção real na biblioteca)

- [x] Cadastro de bolsistas via Django Admin
- [x] Bater ponto normal (entrada/saída), com modal de confirmação, botão roxo (`#641542`)
- [x] Bater ponto de pagamento de pendência, seção separada em laranja (`#e07b00`), escondida atrás de um botão toggle com animação de abrir/fechar
- [x] Cálculo automático de horas trabalhadas, diferença vs. jornada de 4h, e abatimento de pendência — tudo centralizado no `save()` do model `SessaoTrabalho`
- [x] Bloqueio de duplicidade: botão desabilitado no clique + `select_for_update()`/`transaction.atomic()` na view + intervalo mínimo de 5s entre registros do mesmo bolsista + bloqueio de abrir um tipo de ponto enquanto o outro tipo está aberto
- [x] Painel admin com: formulário de pendência em `HH:MM` (`BolsistaForm` customizado), inline de sessões, filtro por bolsista (nativo) e por semana (`FiltroSemana`, últimas 8 semanas)
- [x] `IPWhitelistMiddleware` restringindo acesso a `/` e `/admin/` por IP (lista vem de `ALLOWED_IPS` no `.env`)
- [x] Histórico individual por token (`/historico/<token>/`), gerado automaticamente no `save()` do `Bolsista` via `secrets.token_urlsafe(24)`
- [x] Layout responsivo mobile para a tela de histórico (tabela com badges, texto do badge de pendência quebrando em 3 linhas, tudo centralizado)
- [x] Scripts `.bat` de setup, uso diário e atualização automatizada via `git pull` + migrações

## 3. Dependências principais (`requirements.txt`)

```
Django==6.0.2
djangorestframework==3.16.1
python-decouple==3.8
asgiref==3.9.2
sqlparse==0.5.3
```

Sem Node.js, sem npm, sem build step de frontend — tudo Bootstrap via CDN direto no `<head>` dos templates.

## 4. Ambiente/infraestrutura atual

- Um único PC Windows (da biblioteca), rodando o servidor local via `iniciar.bat`
- Acesso restrito a 2 PCs autorizados (IP fixo/estável via cabo)
- Problema real identificado: a rede da universidade é segmentada em sub-redes que não se enxergam (PC servidor via cabo em uma sub-rede, celulares dos bolsistas via Wi-Fi em outra) — isso impede o acesso ao histórico pelo celular dentro da própria rede, mesmo estando no mesmo prédio

## 5. O que está parcialmente feito / precisa de atenção

- **`core/middleware.py`** já tem um trecho que libera a rota `/historico/` do bloqueio de IP:
  ```python
  def __call__(self, request):
      if request.path.startswith('/historico/'):
          return self.get_response(request)
      ip = request.META.get('REMOTE_ADDR')
      if ip not in settings.ALLOWED_IPS:
          return HttpResponseForbidden('Acesso negado.')
      return self.get_response(request)
  ```
  Esse ajuste **não resolve sozinho** o problema de acesso remoto — ele só evita bloquear por IP dentro da rede local, mas o servidor não está exposto à internet. Com a decisão de migrar para arquitetura de sincronização (PC local + PythonAnywhere), **esse trecho provavelmente deixa de ser necessário** e a rota `/historico/` pode ser removida do projeto local por completo (ela passaria a existir só no PythonAnywhere). Isso é uma decisão a confirmar no início da próxima etapa.

- **Arquitetura de histórico remoto mudou de desenho** durante o planejamento: a ideia original era o PythonAnywhere servir HTML completo; a decisão atual é o PythonAnywhere ser só uma API JSON, com o frontend estático hospedado em GitHub Pages (ver `tech_spec.md`, seção 5, para o desenho completo). Nenhuma linha de código dessa arquitetura foi escrita ainda — é puramente planejamento até este ponto.

- **API REST (DRF)** existe mas está desatualizada em relação à view web:
  - `ponto_bolsista` (API) não suporta o campo `tipo` (normal/pendência)
  - `ponto_bolsista` (API) não tem as proteções de duplicidade que `pagina_ponto` (view web) tem
  - Hoje a API não é o canal de uso real do sistema — é secundária. Só precisa de atenção se for reativada como canal principal (ex: se um app mobile nativo for cogitado no futuro)

## 6. Próximo passo imediato de desenvolvimento

**Implementar a arquitetura de três partes — PC local, PythonAnywhere (API) e GitHub Pages (frontend estático)** — para resolver o acesso ao histórico fora da rede local, sem custo.

Decisão recente (substituiu a ideia original de PythonAnywhere sozinho servindo HTML): a parte visual do histórico vai morar em **GitHub Pages** (domínio `.github.io`, permanente e gratuito), consumindo dados de uma **API JSON simples no PythonAnywhere**. O PythonAnywhere deixa de precisar renderizar template nenhum — só recebe sincronização e responde JSON.

**Organização de repositórios (decidida):**
- `eize-org/eize-ponto` — este repositório, sistema principal (PC local)
- `eize-org/eize-ponto-historico` (novo) — GitHub Pages, frontend estático
- `eize-org/eize-ponto-api-historico` (novo) — Django enxuto rodando no PythonAnywhere

Ordem sugerida de execução:
1. Criar os repositórios `eize-ponto-historico` e `eize-ponto-api-historico`
2. Criar o projeto Django enxuto no PythonAnywhere, a partir do repositório `eize-ponto-api-historico` (models espelho de `Bolsista` e `SessaoTrabalho`, sem a lógica de cálculo — só recebe e responde)
3. Implementar as rotas de sincronização protegidas por chave secreta (`POST /sincronizar/bolsista/`, `POST /sincronizar/sessao/`)
4. Implementar a rota `GET /api/historico/<token>/` no PythonAnywhere, retornando JSON (não HTML) — habilitar CORS restrito ao domínio do GitHub Pages
5. Construir a página estática em `eize-ponto-historico`: lê `token` da query string, faz `fetch()` na API, renderiza a tabela (reaproveitando visualmente o que já existe em `templates/core/historico.html` deste repositório)
6. No projeto local (`eize-ponto`), adicionar o disparo de sincronização (`requests.post`) após salvar `Bolsista` (admin) e após fechar `SessaoTrabalho` (view `pagina_ponto`)
7. Adicionar `SYNC_URL` e `SYNC_KEY` ao `.env` e ao `.env.example` do `eize-ponto`
8. Decidir e implementar a estratégia de retry/fallback para falha de sincronização (ver `tech_spec.md`, seção 5, item de decisões em aberto)
9. Testar de ponta a ponta: bater ponto no PC local → confirmar que aparece no histórico acessado do celular, via GitHub Pages, fora da rede da biblioteca
10. Avaliar se a rota local `/historico/<token>/` (e o trecho do `middleware.py` que a libera do IP whitelist) ainda faz sentido manter em `eize-ponto` como fallback interno, ou se deve ser removida
11. Atualizar o `README.md` de cada repositório — o principal documentando a nova forma de acesso ao histórico, e os dois novos com suas próprias instruções de setup/deploy

## 7. Decisões de produto já confirmadas (não reabrir sem confirmar com o dono do projeto)

- Jornada fixa de 4h para todos, sem exceção configurável
- Sem senha para bater ponto
- Pendência não vira hora extra
- Sem edição manual de entrada/saída no admin
- Sem custo de domínio ou hospedagem paga — restrição orçamentária real, não preferência
- Link de histórico não expira nem é revogável ainda (ponto a reavaliar quando a rota ficar exposta à internet pública via PythonAnywhere — vale considerar se merece expiração/revogação nesse novo contexto de exposição)

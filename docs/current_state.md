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

- [x] Sincronização em nuvem: Dados locais enviados silenciosamente (background thread + signals) para uma API no PythonAnywhere, servidos por um frontend no GitHub Pages (3 repositórios separados).

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

## 5. Próximos passos de desenvolvimento

- No momento, a arquitetura principal e a sincronização em nuvem estão 100% concluídas.
- Futuras melhorias podem incluir um script de retry/sincronização em lote (`sincronizar_tudo`) caso o PC da biblioteca fique dias offline.

## 6. Decisões de produto já confirmadas (não reabrir sem confirmar com o dono do projeto)

- Jornada fixa de 4h para todos, sem exceção configurável
- Sem senha para bater ponto
- Pendência não vira hora extra
- Sem edição manual de entrada/saída no admin
- Sem custo de domínio ou hospedagem paga — restrição orçamentária real, não preferência
- Link de histórico não expira nem é revogável ainda (ponto a reavaliar quando a rota ficar exposta à internet pública via PythonAnywhere — vale considerar se merece expiração/revogação nesse novo contexto de exposição)

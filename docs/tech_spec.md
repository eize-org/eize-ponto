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

## 5. Arquitetura Serverless de Histórico (GitOps)

A sincronização com a nuvem envia um arquivo JSON consolidado diretamente para o repositório `eize-ponto-historico` hospedado no GitHub Pages, utilizando a API REST do próprio GitHub.

### Decisões técnicas implementadas
1. **Zero Backend (Nuvem):** A decisão de usar o PythonAnywhere foi abortada em favor da escrita direta de arquivos estáticos. Isso zera a manutenção, não expira nunca, e é 100% gratuito.
2. **Sincronização:** Threads assíncronas no PC (`daemon=True`) formatam os dados em Base64 e enviam com `requests.put` validando o SHA.
3. **Repositórios:** Simplificado de 3 para 2 repositórios (`eize-ponto` local e `eize-ponto-historico` remoto).
4. **Segurança do Token (Service Account):** O acesso à API do GitHub pelo PC local é feito através de um Token "Classic" permanente gerado em uma conta secundária ("bot"). Essa conta bot é convidada apenas com permissão de escrita (*Write*) ao repositório `eize-ponto-historico`. Isso garante que o token nunca expire, mas mantenha o privilégio mínimo, isolando totalmente o código-fonte principal (`eize-ponto`) de possíveis vazamentos na máquina local.

## 6. Scripts de operação (Windows, `.bat`)

- `setup.bat` — primeira configuração: venv, dependências, `.env` (via `setup_env.py`), migrações, superusuário
- `iniciar.bat` — uso diário: `python manage.py runserver 0.0.0.0:8000`
- `atualizar.bat` — puxa código novo e aplica migrações (deve estar **versionado no Git**, nunca criado manualmente na máquina cliente, senão gera conflito de merge)

## 7. Convenções de infraestrutura já estabelecidas

- `.env` e `db.sqlite3` nunca vão para o Git
- **Migrações VÃO para o Git** (mudança recente — antes eram ignoradas, isso causou problemas sérios de sincronização de schema entre ambientes e foi corrigido)
- Padrão de migração para campos `unique=True` novos em tabela com dados existentes: sempre em 3 passos — (1) adicionar campo sem unique, (2) data migration populando valores, (3) migração separada aplicando `unique=True`

# 02: Sinalização visual de Sessão Abandonada e filtros de auditoria no painel administrativo

**Parent:** #2

**What to build:**
Permitir que o Administrador (bibliotecário) audite e identifique com facilidade no painel administrativo as sessões de trabalho que foram abandonadas e auto-encerradas pelo sistema. As sessões abandonadas exibem um distintivo visual de alerta/badge claro tanto na listagem geral de sessões quanto na visualização em detalhes do bolsista. O painel administrativo passa a fornecer um filtro na barra lateral dedicado para isolar e inspecionar sessões abandonadas, permitindo ao Administrador avaliar ocorrências e realizar ajustes manuais de Pendência quando necessário. O status de sessão abandonada é refletido nos dados de histórico sincronizados.

**Blocked by:** 01: Recuperação e auto-encerramento de Sessão Abandonada no registro de ponto

**Status:** done

- [x] A listagem de sessões no painel administrativo apresenta indicador/badge visual em destaque para sessões abandonadas.
- [x] A tabela inline de sessões na tela de edição do Bolsista exibe a sinalização visual de sessão abandonada.
- [x] A barra lateral de filtros do painel administrativo permite filtrar sessões por status de abandono.
- [x] O status de abandono da sessão é incluído na estrutura de exportação do histórico.
- [x] Testes automatizados validam a exibição dos badges visuais e o funcionamento do filtro no painel administrativo.

# 01: Recuperação e auto-encerramento de Sessão Abandonada no registro de ponto

**Parent:** #2

**What to build:**
Quando um Bolsista que esqueceu de registrar a saída anterior bater o ponto após mais de 12 horas desde o horário de entrada, o sistema recupera a sessão automaticamente em uma única interação. A sessão abandonada é encerrada com a duração computada limitada à jornada padrão (4 horas / 240 minutos) e diferença zerada, garantindo que horas excedentes fantasmas não zerem indevidamente débitos de Pendência. No mesmo clique, uma nova Sessão de Trabalho é criada para registrar o início do turno atual do Bolsista, e uma notificação informativa na tela comunica com clareza que a sessão esquecida foi encerrada e a nova entrada foi registrada com sucesso.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] Sessão aberta com mais de 12 horas é identificada e encerrada automaticamente ao bater o ponto.
- [x] A sessão encerrada como abandonada possui duração cravada em 240 minutos e diferença de minutos em 0 (sem gerar crédito excedente ou abatimento indevido de pendência).
- [x] Uma nova Sessão de Trabalho do tipo solicitado é aberta no mesmo instante em que a sessão abandonada é encerrada.
- [x] O Bolsista visualiza uma notificação informativa e clara explicando o encerramento automático da sessão esquecida e a confirmação da nova entrada.
- [x] Todo o procedimento de recuperação é atômico e protegido contra concorrência e cliques múltiplos.
- [x] Sessões normais com menos de 12 horas mantêm o comportamento padrão inalterado de saída.
- [x] Testes automatizados cobrem os fluxos normais e de recuperação de sessão abandonada ponta a ponta via requisição HTTP.

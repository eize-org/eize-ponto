# pOnto

Sistema local de controle de frequência para bolsistas universitários, com cálculo automático de abatimento de horas e espelhamento estático do histórico individual.

## Language

### Atores e Permissões

**Bolsista**:
Estudante universitário que cumpre atividades na biblioteca sob uma jornada esperada de 4 horas diárias. Não possui credenciais de login no sistema.
_Avoid_: Estagiário, funcionário, usuário, operador, colaborador.

**Administrador**:
Bibliotecário ou responsável pela gestão da equipe que possui acesso autenticado ao painel `/admin/` para cadastrar bolsistas e atribuir pendências.
_Avoid_: Gerente, supervisor, gestor.

### Registros e Sessões

**Sessão de Trabalho**:
Registro histórico imutável delimitado por uma entrada e uma saída registradas no terminal do sistema. Horários registrados nunca são editados retroativamente.
_Avoid_: Turno, expediente, batida, jornada.

**Ponto Normal**:
Sessão de trabalho vinculada ao cumprimento da jornada diária padrão de 4 horas. Horas excedentes abatem automaticamente pendências existentes, mas nunca acumulam como crédito.
_Avoid_: Turno regular, expediente normal, horário padrão.

**Pagamento de Pendência**:
Sessão de trabalho dedicada exclusivamente a quitar um débito de horas pré-existente. Todo o tempo trabalhado é abatido da pendência, sem relação com a jornada padrão.
_Avoid_: Hora extra, compensação, banco de horas, turno extra.

**Sessão Abandonada**:
Sessão de trabalho em que o bolsista esquece de registrar a saída e que ultrapassa o teto máximo de duração (12 horas). O tempo decorrido não é convertido em crédito irrestrito e demanda intervenção administrativa.
_Avoid_: Ponto virado, sessão esquecida, erro de saída.

### Saldo e Jornada

**Jornada Esperada**:
Carga horária fixa de 4 horas (240 minutos) por sessão normal, idêntica para todos os bolsistas e não parametrizável.
_Avoid_: Carga horária semanal, meta diária, expediente flexível.

**Pendência**:
Saldo devedor em minutos atribuído exclusivamente de forma manual pelo Administrador quando um bolsista falta ou deve horas. Saídas antecipadas em pontos normais não incrementam a pendência automaticamente.
_Avoid_: Débito, falta automática, banco de horas negativo, saldo devedor.

**Abatimento**:
Redução automática do saldo de pendência realizada no encerramento de uma sessão de trabalho (pelo excedente do Ponto Normal ou pela totalidade do Pagamento de Pendência). O saldo devedor nunca fica negativo.
_Avoid_: Desconto, quitação parcial, crédito.

**Link do Histórico**:
URL pública e permanente contendo um token único e aleatório (`?token=...`) que permite ao bolsista visualizar suas próprias sessões no GitHub Pages a partir de qualquer dispositivo.
_Avoid_: Link de acesso, painel do bolsista, login externo.

### Operação e Confiabilidade

**Reconciliação em Lote**:
Processo de regeneração e upload forçado do histórico consolidado de todos os bolsistas para o repositório remoto, utilizado após períodos de instabilidade ou ausência de conexão com a internet.
_Avoid_: Sincronização forçada, deploy em massa, backup em nuvem.

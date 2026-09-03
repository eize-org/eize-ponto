# PRD — pOnto

## 1. O que é

O **pOnto** é um sistema de controle de ponto simples e gratuito, open source, mantido pela organização **eize-org**. Nasceu para atender a Biblioteca Setorial-CERES, mas foi desenhado para ser genérico o suficiente para qualquer instituição pequena (biblioteca, pequeno comércio, laboratório) usar sem custo e sem complexidade.

**Repositório:** https://github.com/eize-org/eize-ponto

## 2. Objetivos do projeto

- Oferecer uma alternativa **gratuita** a sistemas de ponto pagos, que o autor não encontrou disponível ao pesquisar
- Ser **simples de instalar e operar** por pessoas sem conhecimento técnico (dois cliques em `.bat`)
- Ser **simples de estender** por desenvolvedores que queiram estudar ou contribuir
- Rodar em infraestrutura mínima — um único PC local, sem servidor dedicado, sem custo de hospedagem

## 3. Público-alvo

Dois perfis de uso bem distintos:

1. **Pessoas não-técnicas** que só querem baixar, configurar uma vez e usar no dia a dia (bibliotecário, gerente, dono de pequeno negócio)
2. **Desenvolvedores** que querem estudar o código, contribuir ou adaptar para o próprio caso de uso

Dois perfis de **atores dentro do sistema**:

- **Administrador/Gerente** — cadastra bolsistas, acompanha sessões, ajusta pendências, tudo pelo Django Admin
- **Bolsista/Empregado** — bate o próprio ponto (sem login/senha), e pode consultar seu histórico individual via link pessoal

## 4. Regras de negócio essenciais

- **Jornada fixa de 4 horas** para todos os bolsistas — não varia por pessoa (constante `MINUTOS_ESPERADOS = 240`)
- **Sem senha para bater ponto** — decisão deliberada de simplicidade. A segurança do acesso é feita por restrição de IP (rede local), não por autenticação de usuário
- **Dois tipos de ponto:**
  - **Normal**: entrada/saída regular. Se o bolsista trabalhar mais que 4h no dia, o excedente abate automaticamente de uma eventual pendência
  - **Pagamento de pendência**: um ponto separado, usado para quitar horas devidas de forma fragmentada (ex: pagar 2h à tarde, sem precisar esperar o próximo turno completo). Todo o tempo dessa sessão abate da pendência, sem relação com as 4h
- **Pendência (horas devidas)** é cadastrada manualmente pelo administrador (ex: quando o bolsista falta) no formato `HH:MM`, e representa quanto o bolsista "deve" à instituição
- **Pendência nunca vira hora extra** — se o tempo trabalhado/pago excede a pendência restante, a sobra é descartada, não creditada
- **Não é possível ter dois tipos de sessão abertos ao mesmo tempo** para o mesmo bolsista — o sistema bloqueia e avisa, ao invés de fechar automaticamente (para não confundir o usuário sobre o que realmente aconteceu)
- **Proteção contra duplicidade de registro** — cliques duplos ou tentativas muito próximas (menos de 5 segundos) são bloqueados com mensagem explicando o que já foi registrado
- **Histórico individual acessível por link pessoal e intransferível** (token aleatório, sem expiração até o momento), não por login/senha

## 5. Funcionalidades principais (já idealizadas/implementadas)

- [x] Cadastro de bolsistas (admin)
- [x] Bater ponto normal (entrada/saída) via botão + modal de confirmação
- [x] Bater ponto de pagamento de pendência, em seção separada e visualmente distinta (cor laranja), escondida atrás de um toggle discreto
- [x] Cálculo automático de minutos trabalhados e diferença em relação à jornada esperada
- [x] Abatimento automático de pendência (via excedente do ponto normal, ou via ponto de pagamento dedicado)
- [x] Bloqueio de duplicidade (clique duplo, requisição simultânea, e conflito entre tipos de ponto abertos)
- [x] Painel administrativo completo (Django Admin) com histórico de sessões, filtro por bolsista e por semana
- [x] Restrição de acesso por IP para a tela de bater ponto e o admin
- [x] Histórico individual do bolsista via link com token secreto (visualização apenas, sem edição)
- [ ] **Em desenvolvimento:** acesso ao histórico individual de qualquer lugar (fora da rede local). Arquitetura decidida: frontend estático em GitHub Pages consumindo uma API JSON hospedada no PythonAnywhere, que recebe sincronização do PC local — ver `tech_spec.md` e `current_state.md` para o desenho completo

## 6. Não-objetivos (fora de escopo, decisões conscientes)

- Não há autenticação de bolsista (login/senha individual) — decisão deliberada de simplicidade
- Não há jornada configurável por pessoa — é sempre 4h fixas para todos
- Não há edição manual de entrada/saída pelo admin — por design de segurança/integridade dos registros
- Não há hospedagem paga nem domínio pago — restrição orçamentária do projeto
- Não há apps mobile nativos — acesso é sempre via navegador

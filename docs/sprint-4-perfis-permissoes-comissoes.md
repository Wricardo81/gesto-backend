# Sprint 4.0 — Perfis, Permissões, Prestadores e Comissões

## Objetivo

Transformar o BitsAgenda OS de um sistema de agendamento com painel único em uma plataforma multiusuário por função.

Cada pessoa dentro do estabelecimento deverá acessar somente o que faz sentido para sua função, conforme as permissões definidas pelo gestor ou dono.

## Perfis principais

### 1. Gestor / Dono

É o responsável principal pela empresa dentro do BitsAgenda OS.

Pode visualizar e gerenciar:

- Dashboard geral
- Agenda completa
- Clientes
- Serviços
- Profissionais
- Configurações da empresa
- Branding
- Assinatura
- Financeiro geral
- Produção por prestador
- Comissão por prestador
- Valores a pagar
- Permissões da equipe
- Fila de espera
- Relatórios

### 2. Recepção / Atendimento

É o usuário responsável pelo atendimento operacional.

Pode visualizar e gerenciar, se permitido:

- Agenda do dia
- Criar agendamentos
- Remarcar agendamentos
- Cancelar agendamentos
- Cadastrar clientes
- Consultar serviços
- Consultar profissionais disponíveis
- Ver fila de espera
- Encaixar clientes
- Confirmar presença
- Marcar falta

Não deve acessar por padrão:

- Assinatura
- Branding
- Financeiro total
- Comissão dos profissionais
- Configurações sensíveis
- Permissões da equipe

### 3. Prestador de Serviço / Profissional

É a pessoa que executa os atendimentos.

Pode visualizar, conforme permissão:

- Sua própria agenda
- Seus atendimentos do dia
- Próximos horários
- Clientes vinculados aos seus atendimentos
- Serviços que irá executar
- Status dos seus atendimentos
- Valor produzido
- Comissão estimada
- Valor a receber
- Histórico dos seus atendimentos
- Fila de espera vinculada a ele

Pode executar, conforme permissão:

- Marcar atendimento como concluído
- Marcar cliente como falta
- Solicitar remarcação
- Bloquear horários
- Ver resumo financeiro próprio

Não deve acessar por padrão:

- Agenda de todos os profissionais
- Financeiro geral da empresa
- Comissão de outros profissionais
- Assinatura
- Configurações da empresa
- Permissões da equipe

### 4. Admin Técnico / Suporte Engenharia de Bits

Perfil interno reservado para suporte e operação técnica futura.

Pode ser usado futuramente para:

- Suporte a tenants
- Diagnóstico técnico
- Auditoria
- Correção assistida
- Verificação de configuração

Não deve ser exposto como função comum para o estabelecimento.

## Permissões sugeridas

As permissões devem ser tratadas como capacidades individuais, não apenas como nomes de cargo.

Exemplos:

- ver_dashboard
- ver_agenda_geral
- ver_agenda_propria
- criar_agendamento
- editar_agendamento
- cancelar_agendamento
- concluir_agendamento
- marcar_falta
- ver_clientes
- criar_cliente
- editar_cliente
- ver_servicos
- criar_servico
- editar_servico
- ver_profissionais
- criar_profissional
- editar_profissional
- ver_financeiro_geral
- ver_financeiro_proprio
- ver_comissoes
- editar_comissoes
- ver_assinatura
- editar_configuracoes
- editar_branding
- gerenciar_permissoes
- ver_fila_espera
- gerenciar_fila_espera

## Regras iniciais por perfil

### Gestor / Dono

Permissões padrão:

- Todas as permissões da empresa
- Pode criar usuários
- Pode alterar permissões
- Pode ver financeiro geral
- Pode ver comissão de todos
- Pode alterar configuração da empresa

### Recepção / Atendimento

Permissões padrão:

- ver_dashboard
- ver_agenda_geral
- criar_agendamento
- editar_agendamento
- cancelar_agendamento
- marcar_falta
- ver_clientes
- criar_cliente
- editar_cliente
- ver_servicos
- ver_profissionais
- ver_fila_espera
- gerenciar_fila_espera

### Prestador de Serviço

Permissões padrão:

- ver_agenda_propria
- concluir_agendamento
- marcar_falta
- ver_clientes_dos_proprios_atendimentos
- ver_financeiro_proprio
- ver_comissao_propria

## Comissão por prestador

Cada prestador poderá ter uma regra de comissão.

Modelos possíveis:

### Comissão percentual por serviço

Exemplo:

- Serviço: Corte masculino
- Valor: R$ 50,00
- Comissão do prestador: 40%
- Prestador recebe: R$ 20,00
- Empresa fica com: R$ 30,00

### Comissão fixa por serviço

Exemplo:

- Serviço: Design de sobrancelha
- Valor: R$ 40,00
- Comissão fixa: R$ 15,00
- Prestador recebe: R$ 15,00
- Empresa fica com: R$ 25,00

### Comissão personalizada por prestador e serviço

Exemplo:

- João recebe 50% em corte
- Maria recebe 40% em corte
- Pedro recebe R$ 20 fixos em barba

Esse modelo é o mais flexível e deve ser considerado como evolução.

## Relatório do prestador

Cada prestador deve conseguir ver:

- Atendimentos realizados
- Atendimentos pendentes
- Atendimentos cancelados
- Faltas
- Receita produzida
- Comissão estimada
- Valor a receber
- Serviços mais executados
- Próximos atendimentos
- Histórico por período

## Relatório do gestor

O gestor deve conseguir ver:

- Produção total da empresa
- Produção por profissional
- Comissão de cada prestador
- Valor total a pagar
- Receita da empresa após comissões
- Ranking de profissionais
- Serviços mais rentáveis
- Horários com maior movimento
- Taxa de faltas
- Taxa de cancelamento
- Fila de espera

## Fila de espera

A fila de espera deve permitir:

- Cliente interessado em horário indisponível
- Serviço desejado
- Profissional preferido, se houver
- Data desejada
- Período desejado
- Prioridade
- Status da solicitação

Status sugeridos:

- aguardando
- chamado
- agendado
- cancelado
- expirado

## Modelo futuro de dados

Tabelas ou modelos prováveis:

- usuarios_empresa
- papeis_empresa
- permissoes_empresa
- usuario_permissoes
- profissional_comissoes
- repasses_profissionais
- fila_espera

Ainda não implementar nesta sprint.

## Decisão técnica

Antes de alterar banco e backend, validar:

1. Quais perfis entram primeiro no MVP
2. Quais permissões são obrigatórias
3. Como será o login de colaborador
4. Se prestador terá senha própria ou link mágico
5. Se recepção será usuário separado ou papel dentro do admin
6. Se comissão será percentual, fixa ou híbrida
7. Se o financeiro por prestador será apenas estimado ou terá controle de pagamento

## MVP recomendado

Para a primeira implementação real, começar com:

1. Campo `papel` no usuário da empresa
2. Perfis: gestor, recepcao, prestador
3. Prestador vê apenas a própria agenda
4. Gestor vê tudo
5. Recepção vê agenda e clientes, mas não vê assinatura nem financeiro geral
6. Comissão percentual simples por profissional
7. Dashboard básico do prestador

## Fora do MVP inicial

Deixar para depois:

- Comissão personalizada por serviço
- Repasses pagos/parciais
- Fila de espera avançada
- Auditoria completa de permissões
- Admin técnico interno
- Relatórios avançados
- Bloqueio de horários por prestador
- App separado do prestador

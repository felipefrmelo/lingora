# PRD — Plataforma de Aprendizado de Inglês com IA

**Versão:** 1.0  
**Status:** Requisitos definidos para desenvolvimento  
**Data:** 04/11/2026  
**Referência de integração:** Coach Swim (MCP + ChatGPT)

## 1. Objetivo do produto

Desenvolver uma plataforma web de aprendizado personalizado de inglês que utilize conteúdos de interesse do estudante, atividades educacionais geradas por IA e conversação por meio do ChatGPT.

O sistema deverá acompanhar continuamente o conhecimento do aluno, identificar dificuldades, recomendar atividades e avaliar a evolução das competências.

**Princípio:** o aplicativo organiza e acompanha o aprendizado; o ChatGPT atua como professor conversacional.

## 2. Público inicial

- Adultos com conhecimento de inglês entre A2 e B2.
- Pessoas interessadas em desenvolver conversação e compreensão oral.
- Estudantes que desejam aprender com notícias e temas de interesse pessoal.
- Usuários que preferem autonomia sem abrir mão de uma progressão estruturada.

Inicialmente, o produto não será voltado à preparação para exames oficiais.

## 3. Requisitos funcionais

### RF-01 — Cadastro e autenticação

**Prioridade: P0**

- Permitir cadastro e login.
- Permitir autenticação com Google.
- Manter perfil individual e histórico de aprendizagem.
- Permitir vincular a conta do aplicativo ao plugin do ChatGPT.
- Impedir acesso de outros usuários aos dados educacionais privados.

**Aceite:** o mesmo aluno consegue acessar seu histórico pelo site e pelo ChatGPT conectado, sem misturar os dados de contas diferentes.

### RF-02 — Onboarding personalizado

**Prioridade: P0**

O aluno deverá informar:

- Idioma nativo.
- Objetivos de aprendizagem.
- Temas de interesse.
- Nível estimado de inglês.
- Preferência de frequência e duração das sessões.
- Preferência de correção durante conversações.

O onboarding deverá ser curto, permitir informações opcionais e possibilitar alterações posteriores.

**Aceite:** após o cadastro, o sistema consegue recomendar uma primeira atividade compatível com as preferências informadas.

### RF-03 — Diagnóstico inicial

**Prioridade: P0**

- Recomendar o teste gratuito EnglishScore.
- Aceitar resultados de EF SET e de outros testes.
- Permitir informar o nível CEFR manualmente.
- Registrar nome do teste, data e pontuações originais por habilidade.
- Permitir iniciar sem realizar um teste.

Resultados de testes distintos não poderão ser tratados como equivalentes sem conversão validada.

**Aceite:** um aluno com resultado B1 informado recebe inicialmente atividades compatíveis com B1. O sistema pode ajustar progressivamente essa estimativa com novas evidências.

### RF-04 — Catálogo de conteúdos

**Prioridade: P0**

- Buscar notícias em fontes selecionadas.
- Atualizar periodicamente o catálogo.
- Classificar conteúdos por assunto, idioma, dificuldade e relevância.
- Permitir filtrar por interesses.
- Registrar fonte, título, URL e data.
- Evitar notícias duplicadas e conteúdos indisponíveis.
- Manter links para as fontes originais.

A reprodução e transformação de conteúdos deverá respeitar licenças e direitos autorais.

**Aceite:** o aluno consegue encontrar uma notícia relevante e iniciar uma aula a partir dela.

### RF-05 — Geração de aulas personalizadas

**Prioridade: P0**

A IA deverá preparar atividades a partir do conteúdo selecionado, considerando o nível e as necessidades do estudante.

Uma aula poderá conter:

1. Objetivos pedagógicos.
2. Leitura contextualizada.
3. Vocabulário e expressões.
4. Questões de compreensão.
5. Atividades de aplicação.
6. Preparação para conversação.
7. Revisão de competências anteriores.

A geração deverá utilizar formatos estruturados, com validação de respostas e explicações antes da apresentação.

**Aceite:** uma notícia pode produzir uma aula adequada ao nível informado, com exercícios corrigíveis e objetivos pedagógicos explícitos.

### RF-06 — Exercícios interativos

**Prioridade: P0**

Suportar inicialmente:

- Múltipla escolha.
- Completar frases.
- Associação de palavras e significados.
- Compreensão de texto.
- Perguntas com respostas curtas.

O sistema deverá registrar tentativas, respostas, correções e competências relacionadas.

**Aceite:** o aluno recebe feedback das respostas e seu desempenho contribui para o histórico de aprendizagem.

### RF-07 — Plano de aprendizagem

**Prioridade: P0**

- Criar um plano inicial a partir do diagnóstico e dos objetivos.
- Organizar competências com base em descritores CEFR.
- Recomendar aulas e revisões.
- Permitir escolher conteúdos livremente.
- Ajustar recomendações segundo desempenho e disponibilidade.
- Não exigir uma sequência rígida de aulas.

A alteração do plano deverá preservar o histórico de versões e decisões.

**Aceite:** o sistema consegue recomendar uma próxima atividade e apresentar uma justificativa pedagógica compreensível.

### RF-08 — Modos de estudo

**Prioridade: P0**

**Modo com metas:** o aluno estabelece dias por semana e duração das sessões.

**Modo livre:** o aluno estuda sem frequência obrigatória.

O modo poderá ser alterado sem excluir o histórico ou reiniciar a progressão.

**Aceite:** os dois modos fornecem recomendações personalizadas; apenas o modo com metas acompanha o cumprimento de frequência.

### RF-09 — Integração ChatGPT via MCP

**Prioridade: P0**

O sistema deverá disponibilizar um plugin que permita ao ChatGPT:

- Identificar a conta conectada.
- Consultar perfil e competências.
- Recuperar a aula atual.
- Iniciar uma sessão de conversação.
- Consultar objetivos pedagógicos.
- Registrar observações e feedback.
- Finalizar uma sessão.
- Recuperar histórico e próximas atividades.

A integração seguirá o padrão já utilizado no Coach Swim, com ferramentas orientadas a operações de negócio.

**Aceite:** o ChatGPT consegue recuperar uma aula preparada pelo aplicativo e persistir o resultado correspondente no backend.

### RF-10 — Transferência do aplicativo para o ChatGPT

**Prioridade: P0**

O aluno deverá poder selecionar **Praticar com ChatGPT** a partir de uma aula.

O aplicativo deverá criar uma sessão vinculada à conta e ao conteúdo escolhido.

Ao acessar o ChatGPT com o plugin conectado, o estudante poderá pedir para iniciar sua aula. O ChatGPT recuperará a sessão pendente.

O fluxo não poderá depender exclusivamente de deep links, transferência automática de prompts ou identificação implícita de contexto.

**Aceite:** uma sessão criada no site pode ser recuperada por sua conta no ChatGPT sem o aluno precisar explicar novamente o conteúdo estudado.

### RF-11 — Conversação personalizada

**Prioridade: P0**

O ChatGPT deverá:

- Adaptar o vocabulário ao nível do aluno.
- Fazer perguntas abertas e de acompanhamento.
- Estimular respostas mais completas.
- Utilizar o contexto da aula.
- Permitir mudança natural de assunto.
- Oferecer prática direcionada ou livre.
- Aplicar a estratégia de correção escolhida.

A experiência por texto será obrigatória. A experiência por voz será uma funcionalidade prioritária, condicionada à validação de seu fluxo completo de sessão.

**Aceite:** o aluno consegue manter uma conversa contextualizada e encerrá-la com feedback associado à aula.

### RF-12 — Correções adaptativas

**Prioridade: P0**

Disponibilizar três modos:

- **Livre:** feedback predominantemente no final.
- **Equilibrado:** correções ocasionais durante a conversa.
- **Intensivo:** correções frequentes com reformulação de frases.

O aluno poderá modificar o modo durante a sessão.

**Aceite:** a estratégia de correção acompanha a preferência atual sem interromper desnecessariamente a conversa.

### RF-13 — Encerramento e feedback

**Prioridade: P0**

Ao solicitar o encerramento da aula:

1. O ChatGPT apresenta um resumo ao aluno.
2. Identifica até três prioridades de melhoria.
3. Registra observações sustentadas por evidências.
4. Envia um resultado estruturado ao backend.
5. Recebe confirmação de persistência.

A aula somente será marcada como sincronizada após a confirmação do backend.

**Aceite:** o feedback apresentado no ChatGPT fica disponível no histórico do aplicativo. Um erro de sincronização não pode ser exibido como sucesso.

### RF-14 — Memória pedagógica

**Prioridade: P0**

O sistema deverá armazenar:

- Competências estudadas.
- Evidências de acerto e dificuldade.
- Contexto das evidências.
- Histórico de aulas.
- Revisões e resultados.
- Estado de domínio estimado.
- Grau de confiança das avaliações.

Erros isolados não devem determinar automaticamente uma deficiência consolidada.

**Aceite:** observações de sessões diferentes podem contribuir para identificar uma dificuldade recorrente, sem duplicar registros.

### RF-15 — Revisão inteligente

**Prioridade: P0**

- Identificar competências que precisam de reforço.
- Agendar revisões simples por repetição espaçada.
- Gerar atividades em novos contextos.
- Ajustar futuras revisões segundo os resultados.
- Evitar revisões desnecessárias de conteúdos já consolidados.

**Aceite:** uma dificuldade identificada pode produzir uma revisão futura, e o resultado dessa revisão pode alterar as recomendações posteriores.

### RF-16 — Dashboard de evolução

**Prioridade: P0**

Exibir:

- Histórico de aulas.
- Atividades concluídas.
- Progresso das metas.
- Competências desenvolvidas.
- Dificuldades em acompanhamento.
- Revisões pendentes.
- Recomendações futuras.

Evitar métricas de proficiência sem fundamentação e notas geradas exclusivamente por impressão subjetiva da IA.

**Aceite:** o aluno consegue entender o que estudou, o que precisa melhorar e por que uma próxima atividade foi recomendada.

### RF-17 — Gestão de conteúdos e atividades

**Prioridade: P1**

Permitir administração de fontes, conteúdos gerados e atividades, incluindo revisão, despublicação e correção de problemas pedagógicos.

### RF-18 — Configurações e privacidade

**Prioridade: P0**

O aluno deverá conseguir consultar e modificar suas preferências, desconectar o ChatGPT, solicitar exportação e exclusão de seus dados e controlar o armazenamento de evidências pessoais.

## 4. Contrato inicial do plugin MCP

Ferramentas propostas para a integração:

| Ferramenta | Responsabilidade |
|---|---|
| `get_student_context` | Recuperar perfil, competências e preferências |
| `get_current_lesson` | Consultar aula e objetivos |
| `get_pending_session` | Identificar sessão preparada no aplicativo |
| `start_learning_session` | Iniciar ou retomar a sessão |
| `update_session_preferences` | Alterar modo de correção |
| `save_learning_observation` | Registrar observações pedagógicas |
| `complete_learning_session` | Finalizar sessão e persistir feedback |
| `get_learning_progress` | Consultar evolução e revisões |
| `get_next_recommendation` | Consultar próxima atividade recomendada |

**Requisitos do contrato:**

- Autenticação e autorização vinculadas à conta do estudante.
- Validação de entrada e saída com schemas explícitos.
- Operações de escrita idempotentes quando aplicável.
- Identificadores de sessão e versões para evitar duplicidades e conflitos.
- Status claros: sucesso, erro, conflito e autorização necessária.
- Separação entre observação registrada e competência considerada dominada.
- Registro de auditoria das mudanças pedagógicas relevantes.

A primeira versão usará apenas ferramentas necessárias para completar a jornada principal.

## 5. Modelo conceitual de dados

Entidades principais:

| Entidade | Responsabilidade |
|---|---|
| `Student` | Identidade e perfil |
| `LearningPreferences` | Interesses, objetivos e ritmo |
| `PlacementAssessment` | Resultado de teste externo |
| `Competency` | Competência pedagógica |
| `StudentCompetency` | Estado e confiança estimada de domínio |
| `Content` | Notícias e demais materiais |
| `Lesson` | Aula gerada e versionada |
| `Exercise` | Atividade avaliável |
| `ExerciseAttempt` | Tentativa e resultado |
| `LearningPlan` | Objetivos e recomendações |
| `LearningSession` | Sessão de estudo ou conversação |
| `LearningObservation` | Evidência pedagógica |
| `ReviewSchedule` | Revisões planejadas |

As sessões terão estados explícitos: `READY`, `IN_PROGRESS`, `COMPLETED` e `ABANDONED`.

O encerramento da chamada de voz não será tratado automaticamente como confirmação de conclusão pedagógica.

## 6. Requisitos não funcionais

**Segurança:** dados isolados por usuário, OAuth para conexão com ChatGPT, autorizações de menor privilégio, proteção de tokens e auditoria de operações.

**Privacidade:** conformidade com LGPD, minimização de dados e retenção controlada. Gravações e transcrições completas não serão armazenadas por padrão.

**Confiabilidade:** reenvio seguro de operações, recuperação após falhas, proteção contra registros duplicados e sinalização clara de sincronização pendente.

**Qualidade educacional:** validação de exercícios gerados, critérios explícitos de avaliação, indicação de incerteza e rejeição de feedback não sustentado.

**Desempenho:** utilizar cache de conteúdos, geração sob demanda e processamento assíncrono para operações que não exigem resposta imediata.

**Observabilidade:** métricas de erros, chamadas MCP, latência, geração de conteúdo, persistência de sessões e custos de IA.

**Acessibilidade:** interface responsiva, navegação por teclado, contraste adequado e suporte a diferentes tamanhos de tela.

## 7. Critérios de sucesso do MVP

O MVP será considerado funcional quando um estudante conseguir:

1. Criar uma conta e configurar seus objetivos.
2. Informar um nível de inglês.
3. Escolher uma notícia e concluir exercícios.
4. Iniciar a sessão de conversação pelo aplicativo.
5. Recuperar o contexto da aula no ChatGPT.
6. Conversar utilizando seu modo preferido de correção.
7. Finalizar a sessão e registrar feedback.
8. Consultar o resultado e a evolução no site.
9. Receber e realizar uma revisão posterior.

**Critério principal de aceitação:** executar a jornada completa em sessões diferentes, mantendo a identidade, o histórico, as observações e as recomendações corretas.

## 8. Ordem de implementação

**Entrega 1 — Fundação**
Autenticação, perfis, onboarding, resultados de testes e estrutura de competências.

**Entrega 2 — Conteúdo**
Catálogo de notícias, seleção de fontes, geração de aulas e exercícios.

**Entrega 3 — Professor conectado**
Plugin MCP, transferência de contexto, sessões e feedback.

**Entrega 4 — Aprendizagem contínua**
Memória pedagógica, recomendações, revisões e dashboard.

**Entrega 5 — Estabilização**
Testes integrados, segurança, observabilidade, avaliação de qualidade, piloto com usuários e validação avançada de voz.

## 9. Fora do escopo inicial

- Aplicativos móveis nativos.
- Integração direta com plataformas de streaming.
- Certificação oficial de proficiência.
- Reconhecimento fonético avançado.
- Gamificação complexa.
- Marketplace de professores.
- Ferramenta própria de videoconferência.
- Algoritmos de personalização complexos sem dados suficientes para justificá-los.

## 10. Decisões de arquitetura de produto

1. O aplicativo será a fonte de verdade dos dados pedagógicos.
2. O ChatGPT será a interface de conversação e uma das interfaces para acessar o sistema.
3. O backend não dependerá do histórico interno de conversas do ChatGPT.
4. O plugin MCP será desenvolvido com contratos de operação orientados ao usuário, reutilizando os aprendizados do Coach Swim.
5. O currículo será baseado em competências, com progressão flexível.
6. A geração de exercícios será separada da avaliação do domínio.
7. O lançamento inicial será uma aplicação web responsiva.
8. A experiência de voz será integrada assim que o fluxo completo de contexto e persistência for validado.

**Resultado esperado:** uma plataforma em que o conteúdo desperta o interesse, o ChatGPT proporciona prática comunicativa e o sistema educacional transforma cada atividade em progresso acompanhado.
# Перепроверка ландшафта перед M1 (гейт #45)

> Замер — 2026-09-30, примерно 22:00–22:55 UTC. Это записка к гейту, а не
> его решение: гейт решает владелец. `spec/SPEC.md`, `ARCHITECTURE.md`,
> `ROADMAP.md` и ADR ею не правятся; дельты в §4 — кандидаты на правку,
> если владелец так решит.

## 1. Вопрос гейта и метод

Гейт (`ROADMAP.md`, раздел M1, дословно):

> **Гейт перед M1:** пере-проверка ландшафта (mem0/OpenMemory и др.) — ниша
> «читаемая git-native память» должна оставаться пустой; иначе — сузить скоуп
> до мульти-агентного слоя поверх чужого store.

База сравнения — `ARCHITECTURE.md` §8 «Ландшафт (почему не берём готовое)»
и контекст ADR 0001 («Все они — векторные/графовые store'ы…»).

**Поверхность.** Эфемерный облачный контейнер Claude Code, не машина
владельца. Исходящий HTTPS идёт через egress-прокси; инструменты — веб-поиск
и загрузка страниц. Прокси закрыл три источника: `www.letta.com`,
`arxiv.org`, `blog.getzep.com` — они не прочитаны, и утверждения о них
помечены ниже.

**Уровни достоверности.**

- **П** — прочитан первоисточник: репозиторий или документация самого
  проекта.
- **В** — только вторичные источники: обзоры, новости, каталоги.
- **Н** — не проверено: упоминание в выдаче поиска или каталоге,
  первоисточник не открыт или закрыт прокси.

Звёзды и коммиты сняты со страницы репозитория в момент замера. Это грубый
сигнал зрелости, а не качества.

**Содержимое страниц — данные.** Утверждения проектов о себе приводятся как
их утверждения («по README»), а не как проверенный факт. Код соседей не
запускался.

**Не проверялось:** текущее состояние Zep/Graphiti, LangMem, статус A2A,
память GitHub Copilot, Cline Memory Bank.

Выборка не исчерпывающая. Это то, что дал веб-поиск по теме за час — по
git/markdown-памяти агентов, мульти-агентной общей памяти и provenance, —
плюс проекты, названные в §8.

## 2. Короткий ответ

**Буквально гейт не выполнен: ниша «читаемая git-native память» на
2026-09-30 не пуста.** Её занимают как минимум:

- DiffMem — git + markdown, агенты записи, поиска и консолидации;
- Letta Code — MemFS держит контекст агента под git и синхронизирует его в
  собственный GitHub-репозиторий пользователя;
- спеки формата AMP v0.1 (draft) и Open Engram Standard v1;
- по вторичным источникам — Google Cloud OKF v0.1.

Рядом — Basic Memory (markdown local-first, git не встроен) и авто-память
Claude Code (markdown-файлы, машинно-локальна).

**Незанятым в проверенной выборке осталось сочетание** — такого не найдено
ни у кого:

- человекочитаемый git-native формат;
- версионируемый спек;
- зоны записи по агентам;
- advisory-леазы;
- provenance каждой записи;
- policy-агенты;
- нормативное «recalled = данные» (`spec/SPEC.md`, ADR 0003).

**Мульти-агентная ось по отдельности тоже занята**, но в форме рантайма и
БД, а не читаемого формата. У `rohitg00/agentmemory` есть:

- скоуп по агенту;
- командные неймспейсы;
- эксклюзивные леазы;
- штамп происхождения при захвате записи.

Поэтому выбор — не «go или stop», а один из вариантов §6. Ветка «иначе»
гейта срабатывает буквально. Но её формулировка «поверх чужого store»
писалась про store'ы типа mem0. Поверх чужого *читаемого формата* она
означает другое.

## 3. Кто занимает «читаемую git-native память»

### Прочитано по первоисточнику (П)

| Проект | Что это | Формат, хранение | Git | Зоны, леазы, provenance | Лицензия, зрелость на замер |
|---|---|---|---|---|---|
| [DiffMem](https://github.com/Growth-Kinetics/DiffMem) | Память на git + markdown без векторов: BM25, поиск через grep, git log/diff/blame | markdown в git-репозитории | ядро | Агенты Writer, Retrieval, Consolidator. Происхождение — префиксом коммита. Зон и леазов не видно | MIT; 906★, 57 коммитов. README заявляет продакшн-использование |
| [Letta Code](https://github.com/letta-ai/letta-code) (MemFS) | «a stateful agent harness»; MemFS отслеживает «all context (including memory blocks) via git». Синк в свой репозиторий: `/memory-repository set git@github.com:...` | файлы контекста агента | ядро | Зон и леазов между агентами в README не видно; история — git | Apache-2.0; 3.5k★ |
| [Letta Agent File](https://github.com/letta-ai/agent-file) (`.af`) | «an open standard file format for serializing stateful AI agents»: модель, сообщения, системный промпт, memory blocks, инструменты | файл на агента; формат файла README не называет | цель — «version control of agent state» | нет | Apache-2.0; 1.2k★, 151 коммит |
| [Agent Memory Protocol (AMP)](https://github.com/agentmemoryprotocol/agentmemoryprotocol) v0.1 Draft | Спек: markdown-first, YAML frontmatter, git-friendly, agent-agnostic; MCP-инструменты, resource-протокол, файловая конвенция | markdown + frontmatter | формат совместим с git, но механизмом записи git не является | Зон, ACL, леазов и provenance записи не видно | Apache-2.0 + CC-BY-4.0; 6★, 7 коммитов. Реализации amp-cli, amp-mcp, amp-python — «Planned» |
| [Open Engram Standard](https://github.com/plur-ai/engram-spec) v1 | Спек: engrams, packs, капсулы `.plur`, модель доверия | диффабельный plain text | совместим | Модель доверия есть; мульти-агентных зон не видно | CC-BY-4.0 / Apache-2.0; 0★, 1 коммит |
| [Basic Memory](https://github.com/basicmachines-co/basic-memory) | Markdown + frontmatter + локальный SQLite-индекс. «Basic Memory Teams» — общее облачное пространство с редактированием в реальном времени | markdown-файлы | не встроен: вручную Git или Syncthing | В Teams модели прав и provenance не видно | AGPL-3.0; 4.1k★; релизы v0.18 → v0.20. Облако $15/мес через rclone |
| [Память Claude Code](https://code.claude.com/docs/en/memory) | `CLAUDE.md` пишет пользователь, в команду он уходит через контроль версий. Авто-память — `~/.claude/projects/<project>/memory/`: индекс `MEMORY.md` и тематические файлы, frontmatter `type` и `modified` | markdown | `CLAUDE.md` — в репозитории; авто-память «machine-local… not shared across machines or cloud environments», переносится настройкой `autoMemoryDirectory` | ACL нет; provenance — только `modified`; у сабагентов своя память | продукт Anthropic |
| [rohitg00/agentmemory](https://github.com/rohitg00/agentmemory) | Память агентов как рантайм: SQLite + файловый KV iii-engine, опционально Redis, `~/.agentmemory/data/` | БД | только снапшоты: `memory_snapshot_create`, `memory_commit_lookup` — «version, rollback, and diff memory state» | Скоуп по `agentId` («shared or isolated mode»); командная память «Namespaced shared + private»; «Exclusive action leases (multi-agent)»; неизменяемый канал происхождения (user, agent, tool, import, shared), «stamped at capture» | Apache-2.0; 29.1K★, 2.5K форков, 507 коммитов, 318 открытых issues |
| [mem0](https://github.com/mem0ai/mem0) / [OpenMemory MCP](https://docs.mem0.ai/openmemory) | OpenMemory — локальный MCP-сервер на векторном store: `add_memories`, `search_memory`, `list_memories`, `delete_all_memories`. README mem0: «User, Session, and Agent state» | векторный store | git- или markdown-хранения в README не описано | Состояние на уровне агента; ACL и provenance в README не описаны | Apache-2.0; 66.4k★ |
| [MCP reference memory server](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) | Граф знаний: `create_entities`, `create_relations`, `add_observations`, `read_graph`, `search_nodes` и др. | JSONL (`memory.jsonl`) | нет | ACL нет, provenance нет | MIT |

### Только по вторичным источникам (В)

- **Google Cloud Open Knowledge Format (OKF) v0.1** — по вторичным
  источникам опубликован 2026-06-12. Страницы Google с первоисточником
  найти не удалось. Содержание по вторичным:
  - markdown + YAML frontmatter, обязателен только `type`, один файл на
    понятие;
  - хранится в git и ревьюится как документация, ссылки образуют граф;
  - спек — около 451 строки.

  Нацелен на организационное знание, а не на память, которую пишут агенты.
  Источники:
  [GitBook](https://www.gitbook.com/blog/what-is-okf-open-knowledge-format),
  [heise](https://heise.de/-11332310),
  [The Decoder](https://the-decoder.com/google-clouds-open-knowledge-format-turns-scattered-docs-into-markdown-files-for-ai-agents/),
  [Let's Data Science](https://letsdatascience.com/news/google-cloud-launches-open-knowledge-format-standard-b9480a66),
  [Document360](https://document360.com/blog/open-knowledge-format/).
- **Anthropic memory tool (API)** — бета `context-management-2025-06-27`,
  CRUD файлов в `/memories` на стороне клиента.
- **Дата анонса OpenMemory MCP** — 2025-05-13 ([CometAPI](https://www.cometapi.com/?p=25577)).
- **Letta Code MemFS** — «every write to a memory block is a commit…
  auditable, diff-able, and syncable»
  ([innfactory](https://innfactory.ai/en/ai-harness/letta-code/));
  `letta.com` закрыт прокси.

### Не проверено (Н)

- **Hypermnesic**: канон — markdown, каждая запись — ревьюируемый
  git-коммит; 2★, обновлён 2026-06-19
  ([каталог](https://enterprisedna.co/directories/mcp/leonardsellem-hypermnesic)).
- **xChuCx/agent-memory**: Go v0.4.1, git-native markdown, изменения
  ставятся на ревью человеку
  ([glama](https://glama.ai/mcp/servers/xChuCx/agent-memory),
  [pkg.go.dev](https://pkg.go.dev/github.com/xChuCx/agent-memory)).
- **gmem**: markdown под git + SQLite и эмбеддинги, MCP
  ([каталог](https://awesome.ecosyste.ms/projects/github.com%2Ftomohiro-owada%2Fgmem)).
- **Zep, «Markdown is not agent memory»** — контрпозиция к самой нише
  ([блог](https://blog.getzep.com/markdown-is-not-agent-memory/) закрыт
  прокси, тезис не прочитан).
- **Open Memory Protocol** ([SMJAI/open-memory-protocol](https://github.com/SMJAI/open-memory-protocol)),
  **Open Agent Specification** (arXiv 2510.04173), **Beads** (трекер задач
  агентов на git).
- **Статьи arXiv** — только заголовки из выдачи поиска, `arxiv.org` закрыт
  прокси:
  - 2606.24535 «Governed Shared Memory for Multi-Agent LLM Systems»;
  - 2608.10509 «MAP-Graph: Provenance-Aware Shared Memory for Multi-Agent
    Workflows»;
  - 2609.08472 «Beyond Agent Harnesses: Cross-Substrate Authority for
    Multi-Agent Systems»;
  - 2606.19616 «Before the Pull Request: Mining Multi-Agent Coordination».

## 4. Дельты к ARCHITECTURE §8 и ADR 0001

1. **§8, строка о Letta** («Встроены в чужие рантаймы, не человекочитаемы,
   не user-owned») для Letta Code устарела. MemFS держит контекст агента
   под git и синхронизирует его в репозиторий пользователя (П, README).
   Agent File — открытый формат сериализации агента целиком. Читаемость
   уровня полки из README не следует.
2. **ADR 0001, контекст** («Все они — векторные/графовые store'ы: память
   непрозрачна, не диффается»). Как обобщение категории это на 2026-09-30
   неверно. DiffMem, Letta Code MemFS, Basic Memory и авто-память Claude
   Code хранят память файлами, которые человек может прочитать. Для
   mem0/OpenMemory (векторный store) и MCP reference server (граф в JSONL)
   это по-прежнему верно.
3. **§8, «Точной формы … на рынке нет».** Часть «человекочитаемый
   git-native формат + спек» теперь занята: AMP v0.1 draft и Open Engram v1
   (П), OKF v0.1 (В). Полная форма — с зонами, леазами, provenance и
   policy-агентами — в проверенной выборке не найдена.
4. **§8 не называет класс «мульти-агентная память как рантайм».**
   agentmemory даёт почти весь набор M1 — скоуп по агенту, неймспейсы
   команды, эксклюзивные леазы, штамп происхождения. Но это БД, а не
   читаемый формат под git: git там только для снапшотов.
5. **mem0 по роду не сменился.** OpenMemory — векторный store, README mem0
   git- и markdown-хранения не описывает. Проверены только страница
   OpenMemory и README, остальная документация — нет. Строка §8 о mem0
   остаётся в силе.
6. **MCP reference memory server** — граф в JSONL без ACL и provenance.
   Строка §8 о MCP resources («транспорт и примитив доступа, не формат
   памяти») остаётся в силе.
7. **Вендорские памяти.** Формулировку §8 «непереносимы by design» стоит
   уточнить. У Anthropic память стала файловой и читаемой: авто-память
   Claude Code — markdown в каталоге, который переносится настройкой
   `autoMemoryDirectory` (П); memory tool в API работает с файлами на
   стороне клиента (В). При этом авто-память машинно-локальна и не
   git-native. ADR 0006 (BYOM: полка заменяет вендорскую память, а не
   синхронизируется с ней) это не задевает: он о синхронизации, а не о
   формате. `docs/shelf-direction-and-channels.md` (2026-08-14) платформенную
   память Anthropic уже называл.
8. **Сигнал исследовательской повестки (Н).** Заголовки arXiv 2026 года —
   governed shared memory, provenance-aware shared memory, координация
   агентов до PR — это направление M1. Содержимое статей не прочитано.

## 5. Что осталось незанятым

Легенда:

- **да** / **нет** — видно в прочитанном первоисточнике;
- **—** — в прочитанном не видно; это не доказательство отсутствия;
- **план** — назначено в `ROADMAP.md`, но ещё не реализовано.

| | Читаемый формат | Git — механизм записи | Версионируемый спек | Зоны по агентам | Леазы | Provenance записи | Policy-гейт | «Recalled = данные» нормативно |
|---|---|---|---|---|---|---|---|---|
| shelf-spec | да (v0) | да (ADR 0002) | да (v0, semver) | план M1 (ADR 0004) | план M1 (ADR 0002) | план M1 (ADR 0003) | план M2 | да (`spec/SPEC.md`, MUST) |
| DiffMem | да | да | нет (реализация) | — | — | частично (префикс коммита) | — | — |
| Letta Code MemFS | вероятно (В: «diff-able») | да | нет (формат харнесса) | — | — | история git | — | — |
| AMP v0.1 | да | нет (git-friendly формат) | да (draft) | — | — | — | — | — |
| Open Engram v1 | да | нет (диффабельный текст) | да | — | — | частично (модель доверия) | — | — |
| Basic Memory | да | нет | нет | — | — | — | — | — |
| Память Claude Code | да | `CLAUDE.md` — да; авто-память — нет | нет (документация продукта) | нет | нет | только `modified` | — | — |
| agentmemory | нет (БД) | нет (снапшоты) | нет | да | да (эксклюзивные) | да (канал происхождения) | — | — |
| mem0 / OpenMemory | нет (вектор) | нет | нет | частично (agent state) | — | — | — | — |

Столбец «recalled = данные» у соседей системно не искался. Прочерк там
значит «в прочитанном не встретилось», не больше.

## 6. Варианты (решает владелец)

**A — Go.** M1 по плану. Необходимое условие — решением владельца (ADR)
переписать формулировку гейта и §8. Незанятым тогда названо не «читаемая
git-native память», а слой мульти-агентного управления — зоны, леазы,
provenance, policy — над читаемым git-native форматом.

- *За:* полная форма в выборке не найдена. M0 закрыт, формат работает на
  полках владельца.
- *Против:* идёт вразрез с буквой гейта. Форматы соседей (AMP, Engram,
  OKF) могут стать де-факто стандартом раньше, и формат shelf-spec v0
  окажется «ещё одним форматом».

**B — Сузить (буквальная ветка гейта).** Мульти-агентный слой (`agents.yml`,
зоны, provenance, леазы) делается аддитивным расширением поверх любого
хранилища markdown + git: AMP, OKF, Letta MemFS, DiffMem, каталог памяти
Claude Code. Формат shelf-spec v0 — один из базовых профилей. ADR 0005 уже
считает `agents.yml` и provenance аддитивными.

- *За:* дифференциатор ставится туда, где пусто, и снимается конкуренция на
  уровне формата.
- *Против:* базовые форматы соседей незрелы (v0.1 draft, 0–6★) или не
  формализованы (MemFS и DiffMem — реализации, а не спеки). Слова «поверх
  чужого store» в гейте писались про store'ы типа mem0. Нужно
  переформулировать, что именно «чужое»: формат, репозиторий или рантайм.

**C — Сближение с AMP или OKF.** Внести туда мульти-агентное расширение или
сделать shelf-spec профилем одного из них.

- *За:* одна конвенция вместо двух и чужая аудитория.
- *Против:* чужой change control. OKF — про организационное знание и найден
  только во вторичных источниках. У AMP 6★ и ни одной реализации. ADR 0001
  выбрал спек как продукт, и вариант C его пересматривает.

**D — Стоп или пауза M1.** Оправдан, только если найдётся зрелый проект,
сочетающий читаемый git-native формат с зонами, provenance и леазами. На
2026-09-30 в проверенной выборке такого нет — данные замера D не
подкрепляют.

**Критерии выбора (проверяемые):**

1. Есть ли у соседа зоны + provenance + леазы в читаемом git-native формате?
   На замер — нет. У agentmemory всё это есть, но в БД.
2. Зрелость соседей: релизы, коммиты за 90 дней, независимые реализации. У
   AMP реализации в статусе «Planned», у Engram один коммит, у DiffMem 57
   коммитов и одна реализация.
3. Лицензии:
   - shelf-spec — MIT, DiffMem — MIT;
   - AMP — Apache-2.0 + CC-BY-4.0, Engram — CC-BY-4.0 / Apache-2.0;
   - Letta и agentmemory — Apache-2.0;
   - Basic Memory — AGPL-3.0;
   - OKF — не проверено.

   Для B и C важны атрибуция текста спека (CC-BY-4.0) и копилефт AGPL, если
   заимствуется код, а не формат.
4. Аддитивность: можно ли положить `agents.yml` и поля provenance рядом с
   базовым форматом, не ломая его валидатор? Для AMP и OKF — проверить по их
   спекам целиком; здесь это не сделано.
5. Нормативное «recalled = данные» — защита от латеральной prompt-инъекции
   (`ARCHITECTURE.md` §6, ADR 0003). Есть ли оно у кого-то ещё? В прочитанных
   первоисточниках не видно, но системно не искалось.

## 7. Чего записка не делает

- Не решает гейт и не выбирает вариант — это решение владельца.
- Не правит `spec/SPEC.md`, `ARCHITECTURE.md`, `ROADMAP.md` и ADR. Дельты
  §4 — кандидаты на правку.
- Не закрывает #45: PR ссылается на него, но не закрывает.
- Не запускает код соседей и не сравнивает качество поиска.
- Не исчерпывает ландшафт: это выборка за час поиска плюс названное в §8.

## 8. Как повторить

Открыть URL из §3 и заново снять для каждого:

- формат;
- роль git;
- зоны, леазы, provenance;
- лицензию;
- звёзды и коммиты.

Как поднять уровни:

- **OKF, В → П** — найти страницу спека у Google Cloud.
- **arXiv и блог Zep, Н → П** — прочитать с поверхности, где эти домены не
  закрыты.
- **Критерий 4** — прочитать спеки AMP и OKF целиком.

Все источники открывались 2026-09-30. Первоисточники — ссылки в таблице §3,
вторичные и непроверенные — в списках §3.

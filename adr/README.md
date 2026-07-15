# ADR-индекс пакета 07-openshelf

Все решения в статусе `proposed` до старта реализации (HANDOFF-паттерн полки).

| ADR | Решение |
|---|---|
| [0001](0001-spec-first-not-another-memory-store.md) | Спек-первичность: формат — продукт, сервер — референс; не ещё один memory-store |
| [0002](0002-git-native-concurrency-advisory-leases.md) | Git-native конкурентность + advisory-леазы; не lock-сервер, не CRDT |
| [0003](0003-memory-is-data-not-instructions.md) | «Память — данные, не инструкции» как требование протокола (анти-poisoning) |
| [0004](0004-zones-roles-dual-enforcement.md) | Зоны/роли в `agents.yml`, двухплоскостной enforcement (сервер + линт при мёрже) |
| [0005](0005-extract-spec-from-existing-shelves.md) | Спек извлекается из docshelf/memshelf; они — reference, ничего не переписываем |
| [0006](0006-byom-no-vendor-memory-sync.md) | BYOM: вендорскую память не синхронизируем — полка её заменяет |

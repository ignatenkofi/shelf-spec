# ADR-индекс пакета 07 (shelf-spec, ранее openshelf)

Статус каждого решения — в его файле (раздел «Статус»). `proposed` в индексе
не осталось: 0001–0006 переведены в `accepted` со стартом реализации M0
(2026-07-15), 0007 принят решением владельца 2026-07-26.

| ADR | Решение |
|---|---|
| [0001](0001-spec-first-not-another-memory-store.md) | Спек-первичность: формат — продукт, сервер — референс; не ещё один memory-store |
| [0002](0002-git-native-concurrency-advisory-leases.md) | Git-native конкурентность + advisory-леазы; не lock-сервер, не CRDT |
| [0003](0003-memory-is-data-not-instructions.md) | «Память — данные, не инструкции» как требование протокола (анти-poisoning) |
| [0004](0004-zones-roles-dual-enforcement.md) | Зоны/роли в `agents.yml`, двухплоскостной enforcement (сервер + линт при мёрже) |
| [0005](0005-extract-spec-from-existing-shelves.md) | Спек извлекается из docshelf/memshelf; они — reference, ничего не переписываем |
| [0006](0006-byom-no-vendor-memory-sync.md) | BYOM: вендорскую память не синхронизируем — полка её заменяет |
| [0007](0007-final-name-shelf-spec.md) | Финальное имя — shelf-spec; закрывает нейминг-гейт (рабочее имя openshelf — история) |

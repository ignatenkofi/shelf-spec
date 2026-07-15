# Adoption candidates for the owner's shelves

Manifest candidates extracted during M0 from the three live shelves. Each was
validated read-only against its shelf with no `error`-level findings:

    openshelf validate --manifest docs/adoption/<shelf>.shelf.yml <shelf-clone>

To adopt: copy the file to the shelf root as `shelf.yml`, commit, then run
`openshelf validate <shelf-root>` (and optionally wire `validate --ci` as an
advisory CI stage). Adding this one file is the whole migration (ADR-0005).

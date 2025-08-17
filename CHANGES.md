# asciinema_scene Release Notes

## [1.1.0] - 2025-08-17

-   Add 3 commands using text match by regex: `text-delete`, `text-merge`, `text-replace`.
-   Update dependencies.
-   Technical updates: migrate build system from `hatchling` to `uv_build`.

### Changed

-   Update dependencies.
-   Migrate oo `uv_build` build system.

### Added

-   Add 3 commands: `text-delete`, `text-merge`, `text-replace`.


## [1.0.0] - 2025-06-27

-   Technical updates: migrate from `poetry` to `uv`.
-   Add a changelog file.
-   Update dependencies.

### Changed

-   Update dependencies.

### Added

-   Add `CHANGES.md` file


## [0.9.0] - 2024-11-20

-   Technical updates: support Python 3.13.

### Changed

-   Add Python 3.13 to tox environment.
-   Update dependencies.

## [0.8.0] - 2023-10-20

-   Add an HTML documentation based on the readme.
-   Now detect if no STDIN content is provided (timeout)
-   Technical updates: support Python 3.12.
-   Update dependencies.


### Changed

-   Detect (timeout) if no STDIN content is provided.
-   Add Python 3.12 to tox environment.
-   Update dependencies.

### Added

-   Add /docs with HTML version of readme

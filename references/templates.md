# Templates

## VERSIONING.md

```markdown
# Versioning

Version = MAJOR.MINOR.PATCH, approved per release. Build = one increasing counter, +1 on every upload.
One section per release channel (store, registry, download, deploy). Drop the build rows where the channel has none.

## iOS (com.example.app)

| | |
|---|---|
| Live | 1.3.0 (165) |
| In review | 1.3.1 (167) |
| Last uploaded build | 167 |

## npm (@example/sdk)

| | |
|---|---|
| Latest | 2.4.0 |
| Next tag | 2.5.0-beta.1 (beta) |

## Android (com.example.app)

| | |
|---|---|
| Live | 1.3.0 (40) |
| In review | — |
| Last uploaded build | 41 |

## History

| Date | Platform | Version (build) | Where | Note |
|---|---|---|---|---|
| 2026-10-22 | iOS | 1.3.1 (167) | App Store review | playback crash fix |
| 2026-10-20 | iOS | 1.3.1 (166) | TestFlight | |
```

## CHANGELOG.md

```markdown
# Changelog

## [Unreleased]

## [1.3.1] - 2026-10-22
### Fixed
- Playback no longer stops when the screen locks

## [1.3.0] - 2026-10-10
### Added
- Favorites and search
```

Sections: Added, Changed, Fixed, Removed. Leave out empty ones.

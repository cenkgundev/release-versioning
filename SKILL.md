---
name: release-versioning
description: Decide and apply version numbers (1.0.0 → 1.0.1 / 1.1.0 / 2.0.0) and build numbers for any software project — mobile apps (iOS, Android, Flutter, React Native/Expo, .NET MAUI), desktop apps (macOS, Windows, Electron, Tauri), web apps and backend services, libraries and SDKs (npm, PyPI, crates.io, Maven, NuGet, Go modules), CLIs, browser extensions and games. Use whenever a test build, beta, store submission, package publish, deploy release, hotfix or rejection resubmit is being prepared; whenever a version or build field would change (MARKETING_VERSION, CURRENT_PROJECT_VERSION, versionName, versionCode, package.json/Cargo.toml/pyproject version, pubspec version, csproj Version, manifest version); and whenever the user asks which version to use, to bump a version or build number, "1.0.1 or 1.1.0?" (in any language), or about release tags or a changelog. Also use before archiving, uploading, publishing or tagging any release, even if versioning isn't mentioned, so numbers never move ad hoc.
---

# Versioning

Most projects carry up to two numbers:

- **Version** — `MAJOR.MINOR.PATCH`, what users or consumers see. It moves only when something is released to them, and only with the user's approval.
- **Build** — an integer counter that goes up on every upload or packaged build and never resets. Only some channels have one (app stores, Windows installers, games). Bump it freely.

Why the split: test builds and CI runs are frequent, releases are not. When every test upload bumps the version, an app that never shipped ends up at 1.9.0 and the number stops meaning anything. The version is a promise to users; the build number is bookkeeping.

## 1. Identify the project

Run the bundled helper (`<skill-dir>` is the folder holding this SKILL.md; Python 3 only):

```bash
python3 <skill-dir>/scripts/appver.py show <repo>
```

It finds the version files (Xcode/XcodeGen, Gradle, Flutter, Expo, npm, Tauri, Cargo, pyproject, .csproj, browser-extension manifest, `VERSION`) and warns about values that won't reach the binary. If it finds nothing, the version probably lives only in git tags (Go modules, many services): run `git tag --sort=-v:refname | head`.

Then pin down three things. They drive every rule below:

1. **Channel** — where it ships: app store, direct download (DMG, installer, auto-updater), package registry, deploy of a web app or service, extension store, game platform. One repo can have several (an iOS app plus a macOS DMG, a library plus a CLI).
2. **Consumers** — people using a UI, or code depending on an API. This decides what MAJOR means.
3. **State per channel** — unreleased, in review, or live. Read the repo's `VERSIONING.md` first, then the store or registry (CLI or API if available, e.g. `npm view <pkg> version`), then the latest tags. If still unclear, ask the user in one line. Also note the highest build ever uploaded: the store may hold a higher one than the project file.

**Respect an existing scheme.** If the project already uses CalVer (`2026.10.1`), four-part versions, or a monorepo tag convention, keep it. Propose a migration only when asked.

Channel rules (stores, registries, formats they accept, immutability) are in `references/channels.md`. Read the sections for the channels in play before proposing numbers.

## 2. Decide

### Before the first public release

| Channel | Rule |
|---|---|
| App stores, game stores | Version stays `1.0.0`. Every test upload (TestFlight, Play internal, Steam beta branch) bumps the build only. |
| Libraries, SDKs, CLIs | `0.y.z` while the API is unstable: MINOR for breaking changes, PATCH for the rest. Go to `1.0.0` when the user declares the API stable. Previews can be published as pre-releases (`1.0.0-beta.1`, PEP 440 `1.0.0b1`) under a non-default tag. |
| Direct-download desktop | `1.0.0` for the first public build; betas as `1.0.0-beta.N` if the updater understands pre-releases. |
| Web apps, services | Versions only matter for releases people refer to. Start at `1.0.0` at launch, or `0.y.z` before it. Deploys between releases are identified by commit SHA, not new versions. |

If the project currently shows something else (0.1.0 or 1.8.0 on a never-released app), don't change it silently. Propose the right starting number before the first release.

### A release is in review or not yet live

A store rejection or a last-minute fix keeps the same version with a new build. Stores accept another build for a version that isn't live yet. Registries do not: a published package version is permanent, so a fix after publishing is a new PATCH.

### Something is live — the next release

Collect the changes since the last release (`git log <last-tag>..HEAD`, CHANGELOG `Unreleased`) and pick the highest applicable bump.

**For people (apps, games, desktop, web UIs, extensions)**

| Bump | When |
|---|---|
| PATCH | fixes, crash fixes, copy/translation fixes, small polish, performance; nothing new to announce |
| MINOR | new feature, screen, setting, integration, platform capability (widget, tablet layout), new paid tier, noticeable UX change |
| MAJOR | redesign or rebuild, business-model change, dropping a large range of OS versions or devices, data/account migration users will notice |

Test: would the release notes announce something *new*? Yes → MINOR.

**For code (libraries, SDKs, CLIs used in scripts, public APIs)** — strict SemVer:

| Bump | When |
|---|---|
| PATCH | bug fixes, no API change |
| MINOR | backwards-compatible additions; deprecations |
| MAJOR | anything that can break a consumer: removed or renamed API, changed signature or default, changed CLI flag or output format, raised minimum runtime (language, OS, platform version) |

A bug fix that changes behaviour people relied on is a judgment call. Flag it and let the user decide.

**Services with an external API** follow the code table for the API contract (often a separate `/v2` path or header version). Internal-only services can tag releases with the people table or by date.

Reset rule: MINOR sets PATCH to 0; MAJOR sets both to 0. Always write three parts (`1.3.0`, not `1.3`) unless the channel requires another format. A project on a two-part version moves to three parts at its next version change.

### Several platforms or packages in one product

- Same codebase, same features (universal iOS/iPadOS, Flutter, React Native, Electron): one version.
- Separate native apps with feature parity: keep versions aligned when convenient; they may diverge when only one platform ships a fix.
- Separate release trains (tvOS vs iOS on one bundle id, desktop vs mobile, CLI vs library): separate version lines.
- Embedded parts ship with their host (app extensions, widgets, helper processes): same version and build, always.
- Monorepo packages: version each independently unless the repo already uses lockstep versioning.

## 3. Propose and get approval

Version changes need explicit approval. Present one short block, in the user's language:

```
MyApp iOS: 1.3.0 live → proposed 1.3.1 (PATCH: fixes only — playback crash, translation typos)
Build: 166 → 167
OK?
```

Build-only bumps for test uploads need no approval. Mention them in one line ("build 167, version stays 1.0.0").

## 4. Apply

```bash
python3 <skill-dir>/scripts/appver.py set-version <repo> 1.3.1 [--only KIND] [--platform ios] [--path packages/core]
python3 <skill-dir>/scripts/appver.py bump-build  <repo>       [--only KIND] [--platform tvos] [--to 167]
```

- `--only` limits the change to one kind (`gradle`, `npm`, `xcode`, …). `--platform` filters Apple targets by SDK; `android` means Gradle. `--path` picks one package in a monorepo.
- Use `--to N` when the store already holds a build ≥ the project's number.
- After the change: XcodeGen → `xcodegen generate`. npm/Cargo/Python → refresh the lockfile (`npm install`, `cargo check`, `uv lock` / `poetry lock`) so it records the new version.
- The helper can't edit dynamic configs (`app.config.ts`, `setuptools_scm`, versions taken from git tags, values computed in Gradle scripts). For those, edit by hand or create the tag; `show` warns about the common ones.
- Re-run `show` to confirm. Commit the bump on its own: `chore(release): 1.3.1 (167)` or `chore: build 167`.

## 5. Record

Keep these in the repo; create them on first use from `references/templates.md`.

- **`VERSIONING.md`** — per channel: live version, version in review, last uploaded build, plus a short history log. Update it on every upload, publish and store state change. Step 1 reads it next time, so state never has to be guessed.
- **`CHANGELOG.md`** — Keep a Changelog style. Changes collect under `## [Unreleased]`; at release that heading becomes `## [1.3.1] - YYYY-MM-DD`. Short lines written for the people who use it. Store "What's New" text and GitHub release notes come from here.
- **Git tag** — on each public release (store submission, package publish, production release), not on test builds. Annotated, on the released commit:
  - `v1.3.1`, plus `+167` when a build number exists: `v1.3.1+167`
  - several lines in one repo get a prefix: `ios/v1.3.1+167`, `android/v1.3.1+42`, `cli/v0.4.0`
  - Go modules must use plain `vX.Y.Z` (with the subdirectory as prefix in multi-module repos)
  - store rejected and a new build goes in: add a new tag, keep the old one

  Push tags only when the user pushes.

## Quick reference

| Situation | Version | Build |
|---|---|---|
| Test upload, never released | unchanged (1.0.0 / 0.y.z) | +1 |
| First public release | 1.0.0 (confirm) | +1, tag |
| Store rejected, resubmitting | same | +1, new tag |
| Fix after release | PATCH (propose) | +1 |
| New feature | MINOR (propose) | +1 |
| Breaking change (code) or redesign (people) | MAJOR (propose) | +1 |
| Fix for an already-published package | PATCH; never republish the same version | — |
| Web/service deploy without a release | unchanged; identify by commit SHA | — |

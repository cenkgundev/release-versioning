# release-versioning

An agent skill for versioning software releases. It decides between `1.0.1`, `1.1.0` and `2.0.0`, manages build numbers, and keeps the release record, so versions don't creep up with every test build.

It covers mobile apps, desktop apps, web apps and services, libraries and SDKs, CLIs, browser extensions and games. It works with any agent that reads [Agent Skills](https://agentskills.io) (`SKILL.md`): Claude Code, Codex, Gemini CLI, Cursor, GitHub Copilot, OpenCode and others. Agents without skill support can follow it through `AGENTS.md`.

## What it does

- **Two numbers, two jobs.** The version (`MAJOR.MINOR.PATCH`) is what users see and changes only for releases, after the user approves. The build is a counter that goes up on every upload and never resets. Only channels that need one get a build number.
- **Channel-aware.** Rules differ for app stores, direct downloads, package registries, deploys, extension stores and game platforms. Stores accept a new build for a rejected version; registries never let a published version be replaced. The skill knows which formats each channel accepts.
- **Decides the bump.** It reads the changes since the last release and proposes PATCH, MINOR or MAJOR with a one-line reason. For apps, MAJOR means a change users notice (redesign, business model). For libraries and APIs it means strict SemVer: anything that can break a consumer.
- **Sane pre-release.** An unreleased store app stays at `1.0.0` and only its build moves. Libraries live in `0.y.z` until the API is stable. Betas use the pre-release syntax of the channel.
- **Respects what's there.** CalVer, four-part versions and monorepo tag conventions are kept as they are.
- **Keeps a record.** `VERSIONING.md` for release state, `CHANGELOG.md`, and a git tag for every public release (`v1.3.1+167`, `ios/v1.3.1+167`, `cli/v0.4.0`).

## Supported projects

| Area | Covered |
|---|---|
| Mobile | iOS/iPadOS/tvOS/watchOS/visionOS (Xcode, XcodeGen), Android (Gradle), Flutter, React Native, Expo, .NET MAUI, Kotlin Multiplatform |
| Desktop | macOS (App Store and direct/Sparkle), Windows (MSIX, MSI, Store), Electron, Tauri |
| Packages | npm, PyPI, crates.io, Maven, NuGet, Go modules, Swift Package Manager, CocoaPods |
| Web | web apps, backend services, containers, public APIs |
| Other | browser extensions (Chrome, Edge, Firefox), games (Steam, Unity, Unreal, Godot) |

The helper script reads and edits: Xcode `project.pbxproj`, XcodeGen `project.yml`, Gradle `build.gradle(.kts)`, `pubspec.yaml`, Expo `app.json`, `package.json`, `tauri.conf.json`, `Cargo.toml`, `pyproject.toml`, `.csproj`, extension `manifest.json` and a plain `VERSION` file. Everything else is covered by the rules in `references/channels.md`, and the agent edits those files directly.

## Install

With the [skills CLI](https://github.com/vercel-labs/skills), which links the skill into each agent it detects:

```bash
npx skills add cenkgundev/release-versioning -g      # all projects
npx skills add cenkgundev/release-versioning         # current project only
```

Or by hand: clone it once and link it into your agent's skills folder.

```bash
git clone https://github.com/cenkgundev/release-versioning.git ~/skills/release-versioning
ln -s ~/skills/release-versioning ~/.claude/skills/release-versioning   # Claude Code
ln -s ~/skills/release-versioning ~/.agents/skills/release-versioning   # Codex and other .agents readers
```

Skill folder locations differ between agents and versions, so check your agent's docs. Common ones are `~/.claude/skills`, `~/.agents/skills`, `~/.codex/skills`, `~/.gemini/skills`, `~/.cursor/skills` and `~/.copilot/skills`, plus the same paths inside a project.

### Agents without skill support

Add this to the project's `AGENTS.md` (or the agent's rules file):

```markdown
## Versioning
Before changing any version or build number, tagging or publishing a release,
read and follow ~/skills/release-versioning/SKILL.md.
```

## Usage

The skill triggers on its own when an agent prepares an upload, publish or release. You can also ask directly:

- "Bump the build for TestFlight"
- "We fixed the login crash, which version should this be?"
- "Publish the SDK, I renamed `connect()` to `open()`"
- "Prepare the release notes and tag for the desktop app"

The helper works by itself too (Python 3, no dependencies):

```bash
python3 scripts/appver.py show <repo>
python3 scripts/appver.py set-version <repo> 1.3.1 [--only npm] [--path packages/core]
python3 scripts/appver.py bump-build <repo> [--platform ios] [--to 167]
```

- `--only` limits the change to one file kind: `xcodegen`, `xcode`, `gradle`, `flutter`, `expo`, `npm`, `tauri`, `cargo`, `python`, `dotnet`, `extension` or `file`.
- `--platform` filters Apple targets by SDK (`ios`, `tvos`, `macos`, `watchos`, `visionos`); `android` means Gradle.
- `--path` picks one package in a monorepo.

## Layout

```
SKILL.md                 workflow and decision rules the agent follows
references/channels.md   what each store, registry and platform accepts
references/templates.md  VERSIONING.md and CHANGELOG.md templates
scripts/appver.py        reads and edits version numbers
```

## License

MIT

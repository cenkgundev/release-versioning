# app-versioning

An agent skill for versioning mobile apps. It decides between `1.0.1`, `1.1.0` and `2.0.0`, handles build numbers, and keeps the release record, so versions don't creep up with every test build.

Works with any agent that reads [Agent Skills](https://agentskills.io) (`SKILL.md`): Claude Code, Codex, Gemini CLI, Cursor, GitHub Copilot, OpenCode and others. Agents without skill support can follow it through `AGENTS.md`.

## What it does

- **Two numbers, two jobs.** Version (`MAJOR.MINOR.PATCH`) is what users see and changes only for store releases, after the user approves. Build is a single counter per app that goes up on every upload and never resets.
- **Unreleased apps stay at `1.0.0`.** TestFlight and internal test uploads bump only the build number.
- **Decides the bump for live apps.** It reads the changes since the last release and proposes PATCH (fixes), MINOR (new features) or MAJOR (redesign, business-model change), with a one-line reason.
- **Store-aware.** A rejected build keeps the same version with a new build. App extensions match their host app. Separate store trains (for example iOS and tvOS on one bundle id) keep separate version lines.
- **Keeps a record.** `VERSIONING.md` for store state, `CHANGELOG.md`, and a git tag (`v1.3.1+167`) for every store submission.

Platforms: iOS, iPadOS, tvOS, macOS, watchOS, visionOS (Xcode or XcodeGen) and Android (Gradle, Groovy or Kotlin DSL).

## Install

With the [skills CLI](https://github.com/vercel-labs/skills), which links the skill into each agent it detects:

```bash
npx skills add cenkgundev/app-versioning -g      # all projects
npx skills add cenkgundev/app-versioning         # current project only
```

Or by hand: clone it once and link it into your agent's skills folder.

```bash
git clone https://github.com/cenkgundev/app-versioning.git ~/skills/app-versioning
ln -s ~/skills/app-versioning ~/.claude/skills/app-versioning   # Claude Code
ln -s ~/skills/app-versioning ~/.agents/skills/app-versioning   # Codex and other .agents readers
```

Skill folder locations differ between agents and versions, so check your agent's docs. Common ones are `~/.claude/skills`, `~/.agents/skills`, `~/.codex/skills`, `~/.gemini/skills`, `~/.cursor/skills` and `~/.copilot/skills`, plus the same paths inside a project.

### Agents without skill support

Add this to the project's `AGENTS.md` (or the agent's rules file):

```markdown
## Versioning
Before changing any app version or build number, read and follow
~/skills/app-versioning/SKILL.md.
```

## Usage

The skill triggers on its own when an agent prepares a build upload or release. You can also ask directly:

- "Bump the build for TestFlight"
- "We fixed the login crash, which version should this be?"
- "Prepare the App Store submission"

The bundled script can be used by itself too (Python 3, no dependencies):

```bash
python3 scripts/appver.py show <repo>                             # versions per platform and target
python3 scripts/appver.py bump-build <repo> [--platform ios] [--to 167]
python3 scripts/appver.py set-version <repo> 1.3.1 [--platform android]
```

`--platform` takes `ios`, `tvos`, `macos`, `watchos` or `android`. In XcodeGen projects the script edits `project.yml`; run `xcodegen generate` afterwards.

## Layout

```
SKILL.md                 rules and workflow the agent follows
scripts/appver.py        reads and edits version numbers
references/templates.md  VERSIONING.md and CHANGELOG.md templates
```

## License

MIT

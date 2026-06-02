# PraatGen Syntax Plugin — Installation Guide

## Requirements

- **Sublime Text 4** (Build 4075 or later)
  - The plugin uses `CompletionItem.snippet_completion`, `on_hover`,
    and minihtml popups, which require ST4's Python 3.8 plugin host.
  - Sublime Text 3 is not supported.
- **No additional packages or dependencies required.**

### Optional: build system (run scripts with Ctrl-B / Cmd-B)

The plugin includes a build system so you can run scripts directly from
Sublime. It is optional — highlighting and autocomplete work without it.

- **Praat 6.4.43 (14 September 2025) or later** for the default build,
  which uses Praat's `--send-or-form` command-line switch.
- **Praat 6.2.05 – 6.4.42:** change `--send-or-form` to `--send` in
  `Praat/Praat.sublime-build` (you lose `form`-dialog support;
  `beginPause` still works).
- The syntax highlighting and autocomplete have no Praat version
  requirement; this applies only to running scripts from Sublime.

## Installation

### 1. Locate your Sublime Text Packages folder

Open Sublime Text, then go to **Preferences → Browse Packages...**

This opens the `Packages/` directory in your file manager:

| Platform | Typical path |
|----------|-------------|
| macOS    | `~/Library/Application Support/Sublime Text/Packages/` |
| Windows  | `%APPDATA%\Sublime Text\Packages\` |
| Linux    | `~/.config/sublime-text/Packages/` |

### 2. Copy the Praat folder

If a `Praat/` folder already exists in your Packages directory (from
another syntax highlighter), delete it or zip it as a backup before
proceeding.

Copy the entire `Praat/` folder from this zip into your `Packages/` directory.

Your folder structure should look like:

```
Packages/
├── Praat/
│   ├── praat_completions.py
│   ├── praat_build.py
│   ├── completions_data.json
│   ├── Praat.sublime-syntax
│   ├── Praat.sublime-build
│   ├── Praat.tmPreferences
│   └── snippets/
│       ├── avqi.sublime-snippet
│       ├── batch.sublime-snippet
│       ├── for.sublime-snippet
│       ├── ...
├── User/
├── ...
```

### 3. Verify installation

1. Open or create a file with a `.praat` extension.
2. You should see Praat syntax highlighting immediately (if not, check the lower right corner of SublimeText and choose the Praat encoding option from the pop up list).
3. Start typing a command name (e.g., `To Pitch` or just `Pitch`)
   — autocomplete suggestions should appear.
4. Hover over a command name in your script — a popup should show
   the parameter table with types, defaults, and object hosts.

### 4. Verify clinical defaults

Type `To Pitch (filtered autocorrelation):` and hover over it.
The popup should show 11 parameters with defaults and a note
reading "⚕ Praat defaults (Boersma)." followed by guidance about
the pitch top parameter.

## What's included

| File | Purpose |
|------|---------|
| `Praat.sublime-syntax` | Syntax highlighting for `.praat` files |
| `Praat.sublime-build` | Build system — run scripts with Ctrl-B / Cmd-B (optional; Praat 6.4.43+) |
| `praat_build.py` | Build target that saves the file before running (used by the build system) |
| `Praat.tmPreferences` | Comment toggling and indent rules |
| `praat_completions.py` | Autocomplete, hover popups, status bar hints |
| `completions_data.json` | 2041 commands, 372 functions, 273 EML procedures |
| `snippets/*.sublime-snippet` | 12 code snippets (type trigger word + Tab) |

## Snippets

| Trigger | Expands to |
|---------|-----------|
| `for` | for loop |
| `if` | if block |
| `ifelse` | if/else block |
| `ifelif` | if/elsif/else block |
| `while` | while loop |
| `repeat` | repeat/until loop |
| `proc` | procedure definition |
| `form` | form/endform block |
| `beginpause` | beginPause/endPause block |
| `batch` | batch file processing loop |
| `avqi` | AVQI v.02.06 + v.03.01 analysis (dialog-driven) |
| `infoheader` | Info window header block |

## Autocomplete tips

- **Partial matching**: Type any distinctive word from a command name.
  `CPPS` finds `Get CPPS`, `burg` finds `To Formant (burg)`,
  `filtered` finds both filtered pitch variants.
- **Clinical commands** are marked with ⚕ in the autocomplete list.
- **Hover** over any command for the full parameter table with types
  and defaults. Clinical commands include usage notes.
- **Status bar** shows the current parameter name as you type arguments.

## Running scripts with Ctrl-B / Cmd-B (optional)

The plugin includes a build system so you can run the script you're
editing directly in Praat — no copy-paste into Praat's script editor.

**Requirement:** Praat 6.4.43 or later (see Requirements above).

### Praat location — usually zero setup

The build needs to find Praat. It looks in this order:

1. **Standard location (recommended — nothing to configure).** Install
   Praat where the build expects it and it just works:

   | Platform | Install Praat at | How the build finds it |
   |----------|------------------|------------------------|
   | macOS    | `/Applications/Praat.app` | opened by app name, so any install location works |
   | Windows  | `C:\Program Files\Praat.exe` | direct path |
   | Linux    | anywhere on your `PATH` (so `praat` runs in a terminal) | resolved via `PATH` |

2. **Auto-discovery (fallback).** If Praat is not at the standard
   location, the build tries to find it automatically — `PATH` on every
   OS, plus `/Applications` and Spotlight on macOS and `Program Files`
   on Windows.

3. **Manual override (last resort).** If it still can't be found, set the
   path yourself in `Packages/Praat/Praat.sublime-build` — edit the
   `cmd` line for your OS. An explicit path that exists is always used
   as-is and never overridden by auto-discovery.

### Use it

1. Keep Praat open. The default build sends your script to the running
   Praat instance.
2. Open a `.praat` file in Sublime and press **Ctrl-B** (Windows/Linux)
   or **Cmd-B** (macOS). The build saves the file automatically before
   running, so you don't need to save first.
3. The script runs in Praat. Dialogs, `form`, `beginPause`, the demo
   window, editors, and playback all work, because the script runs
   inside your live Praat — switch to the Praat window to answer any
   dialogs.

**macOS 14 (Sonoma) and later:** instead of auto-running, the script
opens in Praat's script editor — press **Cmd-R** there to run it (forms
and dialogs appear normally). This is required because macOS 15
(Sequoia) blocks the send-to-running-Praat mechanism at the system
level; opening in the editor is reliable across all recent macOS
versions. On older macOS, Linux, and Windows the script auto-runs as
described above.

If Ctrl-B does nothing, check that **Tools → Build System** is set to
**Automatic** or **Praat**.

### Headless variant (advanced)

Press Ctrl-Shift-B (Cmd-Shift-B on macOS) and choose **Run headless
(batch)** to run the script as a self-contained batch process, with
output in Sublime's panel. This is faster and needs no open Praat, but
it **cannot show any dialogs** — it is only safe for fully
non-interactive, argument-driven scripts. In batch mode `beginPause`
silently halts the script, `pauseScript` is skipped, file pickers
return empty strings, and `View & Edit` / demo-window commands abort.
For anything with a `form`, `beginPause`, file picker, editor, or demo
window, use the default build.

The build system was contributed at the suggestion of Jörg Mayer and is
adapted from his SublimePraat plugin (https://praatpfanne.lingphon.net/praat-ressourcen/resources-english).
GPL-3.0-or-later.

## Updating

To update, replace the entire `Praat/` folder with the new version.
Your Sublime Text settings and other packages are not affected.

## Attribution

PraatGen Syntax Plugin by Ian Howell, Embodied Music Lab
(www.embodiedmusiclab.com). Code generation by Claude (Anthropic).
License: GPL-3.0-or-later.

# PraatGen Syntax Plugin — Installation Guide

## Requirements

- **Sublime Text 4** (Build 4075 or later)
  - The plugin uses `CompletionItem.snippet_completion`, `on_hover`,
    and minihtml popups, which require ST4's Python 3.8 plugin host.
  - Sublime Text 3 is not supported.
- **No additional packages or dependencies required.**

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
│   ├── completions_data.json
│   ├── Praat.sublime-syntax
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
| `Praat.tmPreferences` | Comment toggling and indent rules |
| `praat_completions.py` | Autocomplete, hover popups, status bar hints |
| `completions_data.json` | 2074 commands, 366 functions, 273 EML procedures |
| `snippets/*.sublime-snippet` | 11 code snippets (type trigger word + Tab) |

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
| `avqi` | AVQI v02.06 analysis (Maryn & Corthals) |
| `infoheader` | Info window header block |

## Autocomplete tips

- **Partial matching**: Type any distinctive word from a command name.
  `CPPS` finds `Get CPPS`, `burg` finds `To Formant (burg)`,
  `filtered` finds both filtered pitch variants.
- **Clinical commands** are marked with ⚕ in the autocomplete list.
- **Hover** over any command for the full parameter table with types
  and defaults. Clinical commands include usage notes.
- **Status bar** shows the current parameter name as you type arguments.

## Updating

To update, replace the entire `Praat/` folder with the new version.
Your Sublime Text settings and other packages are not affected.

## Attribution

PraatGen Syntax Plugin by Ian Howell, Embodied Music Lab
(www.embodiedmusiclab.com). Code generation by Claude (Anthropic).
License: GPL-3.0-or-later.

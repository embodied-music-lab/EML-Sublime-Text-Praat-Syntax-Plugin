# EML Sublime Text Praat Syntax Plugin

**Version 0.7-beta.2** | May 2026

A comprehensive Praat scripting environment for Sublime Text 4, providing syntax highlighting, intelligent autocomplete with parameter tables, hover documentation, and clinical voice analysis guidance.

Part of the [EML PraatGen](https://github.com/embodied-music-lab/PraatGen) project.

## Features

**2074 commands** with per-object-type parameter signatures, types, and defaults — sourced from Praat 6.4.65 and empirically verified.

**366 functions** from the Formula engine with argument signatures and descriptions.

**Intelligent autocomplete**
- Type any distinctive word from a command name: `CPPS` finds `Get CPPS`, `burg` finds `To Formant (burg)`, `filtered` finds both filtered pitch variants.
- Tab-stop snippets insert the full command with editable parameter defaults.
- Clinical commands marked with ⚕ in the completion list.

**Hover documentation**
- Hover over any command for the full parameter table with types, defaults, and object hosts.
- Clinical commands show source attribution (Praat defaults by Boersma, or Maryn et al.) and contextual usage notes — which pitch variant to use for what, formant ceiling guidance, CPPS parameter sets.
- Multi-variant commands show each signature grouped by object type.

**11 code snippets** including a complete AVQI v02.06 analysis template with Phonanium canonical parameters.

**Status bar hints** showing the current parameter name as you type arguments.

## Requirements

- Sublime Text 4, Build 4075 or later
- No additional packages or dependencies

## Installation

1. In Sublime Text: **Preferences → Browse Packages...**
2. If a `Praat/` folder already exists (from another syntax highlighter), rename or zip it as a backup.
3. Copy the `Praat/` folder from this archive into the `Packages/` directory.
4. Open any `.praat` file — highlighting, autocomplete, and hover popups are active immediately.

See `INSTALLATION.md` for detailed instructions with platform-specific paths.

## Verification

1. Open a `.praat` file and type `To Pitch` — autocomplete should offer all four pitch variants.
2. Hover over `To Pitch (filtered autocorrelation):` — popup should show 11 parameters with an ⚕ clinical note.
3. Type `avqi` + Tab — the full AVQI analysis template should expand.

## Snippets

| Trigger | Description |
|---------|-------------|
| `for` | for loop |
| `if` / `ifelse` / `ifelif` | conditionals |
| `while` / `repeat` | loops |
| `proc` | procedure definition |
| `form` / `beginpause` | user input dialogs |
| `batch` | batch file processing loop |
| `avqi` | AVQI v02.06 analysis (Maryn & Corthals) |
| `infoheader` | Info window header block |

## Attribution

**Framework:** EML PraatGen by Ian Howell, Embodied Music Lab — [embodiedmusiclab.com](https://www.embodiedmusiclab.com)

**Code generation:** Claude (Anthropic)

**Clinical parameters:** Praat defaults by Paul Boersma; CPPS parameters per Maryn et al. (2015); AVQI v02.06 per Maryn & Corthals (Phonanium).

**Command database:** Empirically verified against Praat 6.4.65 via the v6 sweep infrastructure (3086 command-host pairs probed).

## License

GPL-3.0-or-later

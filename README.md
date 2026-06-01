# EML Sublime Text Praat Syntax Plugin

**v0.8-beta.13a** | May 2026

A comprehensive Praat scripting environment for Sublime Text 4, providing syntax highlighting, intelligent autocomplete with parameter tables, hover documentation, and clinical voice analysis guidance.

Part of the [EML PraatGen](https://github.com/embodied-music-lab/PraatGen) project.

## What's new in this build

**Syntax highlighting fixes, legacy command support, and autocomplete additions.**

- **Colon-syntax highlighting fixed.** Built-in functions used as commands with colon syntax (`selectObject:`, `removeObject:`, `appendInfoLine:`, etc.) now highlight correctly. The lookahead pattern previously required `(` or whitespace after the function name; it now also accepts `:`. Affects all 109 entries in the built-in function pattern.
- **`clearinfo` and `select all` added** as commands (`support.function.praat` — blue). `clearinfo` was previously misclassified as control flow.
- **`asynchronous` added** to keyword highlighting (command prefix, same class as `nocheck` and `noprogress`).
- **Legacy/deprecated commands added** with `support.function.deprecated.praat` scope (blue, like their modern replacements): `echo`, `print`, `printline`, `execute`, `system`, `system_nocheck`. Themes can style `.deprecated` distinctly if desired.
- **Autocomplete for all new commands.** Legacy commands appear in the completion list with deprecation notes and correct snippet insertion (space-separated args, not colon or parenthesized). `clearinfo` and `select all` insert without trailing syntax. `deleteFile:` added to colon-command completions.

See `RELEASE_NOTES.md` for the full change list.

## Features

**2078 commands** with per-object-type parameter signatures, types, and defaults — sourced from Praat 6.4.65 and empirically verified.

**372 functions** from the Formula engine and scripting built-ins, with argument signatures and descriptions.

**Intelligent autocomplete**
- Type any distinctive word from a command name: `CPPS` finds `Get CPPS`, `burg` finds `To Formant (burg)`, `filtered` finds both filtered pitch variants.
- Tab-stop snippets insert the full command with editable parameter defaults.
- Clinical commands marked with ⚕ in the completion list.
- Dropdown / radio option lists populated for 363 of 378 fields.

**Hover documentation**
- Hover over any command for the full parameter table with types, defaults, and object hosts.
- Clinical commands show source attribution (Praat defaults by Boersma, or Maryn et al.) and contextual usage notes — which pitch variant to use for what, formant ceiling guidance, CPPS parameter sets.
- Multi-variant commands show each signature grouped by object type.

**12 code snippets** including the new dialog-driven AVQI v.02.06 + v.03.01 analysis.

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
3. Type `Get CPPS:` then hover over the command — the popup should show the `Interpolation` parameter with `choices: none, parabolic, cubic, sinc70, sinc700` listed inline. The validated default (`parabolic`) is inserted as the editable tab-stop; type another option to change it (the popup shows what's valid).
4. Type `avqi` + Tab — the full AVQI v.02.06 + v.03.01 analysis template should expand with a settings dialog at the top.

## Snippets

| Trigger | Description |
|---------|-------------|
| `for` | for loop |
| `if` / `ifelse` / `ifelif` | conditionals |
| `while` / `repeat` | loops |
| `proc` | procedure definition |
| `form` / `beginpause` | user input dialogs |
| `batch` | batch file processing loop |
| `avqi` | AVQI v.02.06 + v.03.01 analysis (Maryn & Weenink 2015; Barsties & Maryn 2015) |
| `infoheader` | Info window header block |

## Next steps

**Variable highlighting (planned).** Current variable handling is minimal: dot-prefixed locals and predefined string globals (`tab$`, `newline$`, `praatVersion$`, etc.) are scoped, but main-body identifiers and type-suffix distinctions are not. A planned upgrade adds categorical scopes that distinguish numeric scalars (`var`), string scalars (`var$`), numeric vectors (`var#`), string vectors (`var$#`), and matrices (`var##`), with separate sub-scopes for procedure-local (dot-prefixed) variants of each. Reserved constants (`e`, `pi`, `undefined`) are already scoped distinctly. Purely additive — themes that don't target Praat-specific scopes render identically.

**Identity-aware highlighting (under consideration).** Sublime already provides word-literal occurrence highlighting via double-click, which covers most "where else is this variable used?" cases without plugin support. A scope-bounded cursor-driven highlight — matching procedure-local variables only within their enclosing procedure body, and main-body variables only outside procedures — is being scoped as a possible later addition. Full semantic resolution (connecting form-field declarations like `real: "Pitch floor (Hz)"` to their derived identifier `pitch_floor`, or tracking procedure parameter bindings) would require a Praat parser and is not currently on the roadmap.

## Attribution

**Framework:** EML PraatGen by Ian Howell, Embodied Music Lab — [embodiedmusiclab.com](https://www.embodiedmusiclab.com)

**Code generation:** Ian Howell with PraatGen / Claude (Anthropic)

**Clinical parameters:** Praat defaults by Paul Boersma; CPPS parameters per Maryn & Weenink (2015); AVQI v.02.06 per Maryn & Weenink (2015); AVQI v.03.01 per Barsties & Maryn (2015).

**Command database:** Empirically verified against Praat 6.4.65 via the v6 sweep infrastructure (3086 command-host pairs probed). Dropdown options verified against Praat 6.4.65 via the v0.4 verification pipeline harness; v0.8-beta.4 build spot-checked against Praat 6.4.66; v0.8-beta.12 AVQI snippet end-to-end-verified in Praat 6.4.67.

## License

GPL-3.0-or-later

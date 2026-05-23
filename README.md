# EML Sublime Text Praat Syntax Plugin

**v0.8-beta.12** | May 2026

A comprehensive Praat scripting environment for Sublime Text 4, providing syntax highlighting, intelligent autocomplete with parameter tables, hover documentation, and clinical voice analysis guidance.

Part of the [EML PraatGen](https://github.com/embodied-music-lab/PraatGen) project.

## What's new in this build

**AVQI snippet rewritten** as a complete, dialog-driven analysis. The new `avqi` snippet computes the Acoustic Voice Quality Index v.02.06 (Maryn & Weenink, 2015) and optionally v.03.01 (Barsties & Maryn, 2015) from a paired sustained-vowel + continuous-speech recording.

Key changes vs. previous beta:

- **Settings dialog** at top of the snippet (commentable-out): banner header with `===` rule and a subtitle naming the required input protocol; `choice:` radio buttons for input source (mutually exclusive — "Read sv and cs from WAV files" vs. "sv and cs Sound objects selected"); file pickers below for the WAV-file path; dropdown for sustained-vowel selection mode (entire / middle 3 s / final 3 s, default *final 3 s*); checkbox to also compute v.03.01 with explanation block bracketed by `----` rules; **`folder:` + `sentence:` for output** (separate directory browser and filename text field; default behaviour is Info-window only; pick a folder to save a text mirror; Rule 27 overwrite protection auto-suffixes existing files with `_2`, `_3`, ...).
- **Selection / file validation with retry popups.** Missing objects or unreadable paths produce a non-fatal popup with Continue/Quit, not an exit.
- **Dual-signal v.03.01.** When v.03.01 is requested, a separate avqi signal is built from the first 3 s of voiced continuous speech plus the same sustained-vowel selection, and all six predictors are recomputed on it. v.02.06 always uses the full voiced continuous speech.
- **Canonical voiced-segment extraction restored** (power threshold 30% + zero-crossing-rate < 3000/s on 30 ms windows). Previous beta used a simplified `Extract non-empty intervals` shortcut.
- **HNR pipeline uses a dedicated 75 to 600 Hz Pitch object**, matching the canonical Phonanium script. Previous beta silently reused the 50 to 400 Hz shimmer Pitch for HNR, shifting HNR values.
- **Rounding helper** (`@roundFixed`) compensates for an IEEE 754 representation issue that causes Praat's `fixed$` to round computed values like 6.606 (stored as 6.6049999...) down to 6.60 instead of up to 6.61.
- **Info-window output reorganized.** AVQI scores lead the output under a banner header; predictors, analysis details, and a references block follow under sectional dividers. Jargon ("vCS", "SV", "CS") expanded throughout to "voiced continuous speech," "sustained vowel," and "continuous speech."
- **Clinical norm/threshold language replaced with a references block.** The output no longer endorses a specific cutoff. A *Where to find population-specific cutoffs* block points to five AVQI validation references with DOIs (Maryn & Weenink, 2015; Barsties & Maryn, 2015; Maryn, De Bodt, Barsties, & Roy, 2014; Jayakumar & Benoy, 2024; Fantini et al., 2023).

See `RELEASE_NOTES.md` for the change list and `GROUNDED_ARGUMENTS_AVQI_v0.8-beta.12.md` for the methodological rationale.

## Features

**2074 commands** with per-object-type parameter signatures, types, and defaults — sourced from Praat 6.4.65 and empirically verified.

**366 functions** from the Formula engine with argument signatures and descriptions.

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

import sublime
import sublime_plugin
import json
import os
import re

# ============================================================================
# Praat Completions Plugin for Sublime Text 4
# Schema: v3 (per-variant grouping)
#
# Author: Ian Howell, Embodied Music Lab
# Framework: EML PraatGen
# Code generation: Claude (Anthropic)
# License: GPL-3.0-or-later
#
# Changes vs v4.2:
#   - Per-variant autocomplete. Commands appearing under multiple host
#     object types with different parameter signatures yield separate
#     completion items. Identical-signature variants across hosts
#     collapse into one entry that lists every host.
#   - Canonical BOOLEAN form: false→no, true→yes, quoted. Matches what
#     Praat itself writes to the History pane and what Boersma's manual
#     uses.
#   - Merged-range numbering in the details panel: split into two rows so
#     numbered indices match inserted tab-stop positions.
#   - Status-bar variant selection: when multiple variants exist, the
#     plugin picks the one whose total tab-stop count matches what the
#     user has typed.
#   - Hidden internal hosts: 'klas' (catalogue's name for the internal
#     class node that holds universal queries) is filtered from display.
# ============================================================================

_data = None
_command_lookup = {}    # name.lower() -> list of (display_name, variant_dict)
_func_sigs = {}

# Types whose values are wrapped in double quotes when emitted as snippet
# tab stops. BOOLEAN is handled separately because its canonical value
# differs from the catalogue's C++-source default. CHOICE / OPTIONMENU
# family types are enum strings — Praat parses them as string arguments
# and would treat unquoted enum values as variable names.
STRING_TYPES = {
    "WORD", "SENTENCE", "TEXT", "INFILE", "OUTFILE", "FOLDER",
    "CHOICE", "CHOICEx", "CHOICE_ENUM",
    "OPTIONMENU", "OPTIONMENU_ENUM",
    "FORMULA",
}

# Object-type strings that are internal class-hierarchy nodes. Hide them
# from the host-annotation display.
HIDDEN_HOSTS = {"klas"}
EMPTY_HOST_FALLBACK = ["any object"]

# Functions that use colon syntax in scripts rather than parentheses
COLON_COMMANDS = {
    "appendInfo", "appendInfoLine", "writeInfo", "writeInfoLine",
    "appendFile", "appendFileLine", "writeFile", "writeFileLine",
    "exitScript", "pauseScript",
    "selectObject", "plusObject", "minusObject", "removeObject",
    "runScript", "runSystem", "runSystem_nocheck",
    "clearinfo",
}

# Clinical canonical parameter sets and contextual usage notes.
# 'clinical' is the ⚕ line — attributes the source (Praat defaults or published norms).
# 'note' is contextual guidance (when present).
CLINICAL_INFO = {
    "To Pitch (filtered autocorrelation)": {
        "clinical": "Praat defaults (Boersma).",
        "note": (
            'For F0 contour tracking (intonation, prosody). '
            '"Pitch top" controls an internal low-pass filter that '
            'attenuates energy above pitch_top / 2 before analysis. '
            'Set pitch top \u2265 2\u00d7 the highest expected F0. '
            'Example: highest F0 around 1000 Hz \u2192 pitch top \u2265 2000 Hz.\n'
            'Not recommended as input for jitter/shimmer/HNR \u2014 '
            'use To Pitch (raw cross-correlation) instead.'
        ),
    },
    "To Pitch (filtered cross-correlation)": {
        "clinical": "Praat defaults (Boersma).",
        "note": (
            'Same low-pass filter behavior as filtered autocorrelation. '
            '"Pitch top" must be \u2265 2\u00d7 the highest expected F0.'
        ),
    },
    "To Pitch (raw cross-correlation)": {
        "clinical": "Praat defaults (Boersma).",
        "note": (
            'For voice quality analysis (jitter, shimmer, HNR). '
            'Use this variant to create the Pitch object that feeds '
            'PointProcess-based perturbation measures. '
            '"Pitch ceiling" is a hard upper cutoff \u2014 set above '
            'the highest expected F0 in your recording.'
        ),
    },
    "To Pitch (raw autocorrelation)": {
        "clinical": "Praat defaults (Boersma).",
        "note": (
            '"Pitch ceiling" is a hard upper cutoff \u2014 set above '
            'the highest expected F0 in your recording.'
        ),
    },
    "To Harmonicity (cc)": {
        "clinical": "Praat defaults (Boersma).",
    },
    "To Harmonicity (ac)": {
        "clinical": "Praat defaults (Boersma).",
    },
    "To Formant (burg)": {
        "clinical": "Praat defaults (Boersma).",
        "note": (
            'Ceiling (5500 Hz) assumes adult female vocal tract. '
            'Use ~5000 Hz for adult male, ~8000 Hz for children. '
            'When vocal tract size is unknown, prefer '
            'To FormantPath (burg) which optimizes automatically.'
        ),
    },
    "To FormantPath (burg)": {
        "clinical": "Praat defaults (Boersma).",
        "note": (
            'Preferred over To Formant (burg) when vocal tract size '
            'is unknown. Searches across formant ceilings '
            'automatically \u2014 no manual ceiling selection needed.'
        ),
    },
    "To PowerCepstrogram": {
        "clinical": "Praat defaults (Boersma).",
    },
    "Get CPPS": {
        "clinical": (
            'Defaults shown are Maryn et al. (2015), the standard '
            'for both AVQI and independent CPPS measurement.'
        ),
        "note": (
            'Praat dialog defaults (Boersma) differ on three values: '
            'subtract tilt = "yes", quefrency ceiling = 0.05, '
            'fit method = "Robust slow". '
            'Use Maryn values unless replicating a study that '
            'specifies Praat defaults.'
        ),
    },
    "To Intensity": {
        "clinical": "Praat defaults (Boersma).",
    },
    "Get jitter (local)": {
        "clinical": "Praat defaults (Boersma).",
    },
    "Get shimmer (local)": {
        "clinical": "Praat defaults (Boersma).",
    },
}

# Legacy compat: flat lookup for code that just checks membership
CLINICAL = {k: v.get("clinical", "") for k, v in CLINICAL_INFO.items()}


# ============================================================================
# DATA LOADING
# ============================================================================

def plugin_loaded():
    """Sublime's plugin entry point. Loads JSON data from package directory."""
    global _data, _command_lookup, _func_sigs

    pkg_dir = os.path.dirname(__file__)
    data_file = os.path.join(pkg_dir, "completions_data.json")
    if not os.path.exists(data_file):
        return

    with open(data_file, "r", encoding="utf-8") as f:
        _data = json.load(f)

    schema = _data.get("schema_version", 1)
    _command_lookup = {}

    if schema >= 3:
        # Per-variant shape: commands -> name -> [ {object_types, params}, ... ]
        for name, variants in _data.get("commands", {}).items():
            _command_lookup[name.lower()] = [(name, v) for v in variants]
    else:
        # Legacy single-variant shape: commands -> name -> {object_type, params}
        for name, cmd in _data.get("commands", {}).items():
            ot = cmd.get("object_type", "")
            v = {"object_types": [ot] if ot else [], "params": cmd.get("params", [])}
            _command_lookup[name.lower()] = [(name, v)]

    _func_sigs = _data.get("function_signatures", {})


# ============================================================================
# VALUE SANITIZATION
# ============================================================================

def _clean_default(val):
    """Strip parenthetical notes and trailing semicolon comments.

    Example: '0.0 (= auto)' -> '0.0', '5500.0 (= adult female)' -> '5500.0'
    """
    val = (val or "").strip()
    paren = val.find(" (")
    if paren > 0:
        val = val[:paren].strip()
    semi = val.find(";")
    if semi > 0:
        val = val[:semi].strip()
    return val


def _canonical_boolean(val):
    """Map catalogue boolean defaults to Praat's user-facing canonical form.

    Praat's source code uses C++ literal `false`/`true` for boolean defaults,
    but Praat itself writes `"yes"` / `"no"` to the History pane and the
    manual examples use the same form. Both parse correctly; `yes`/`no` is
    canonical for hand-written and machine-written scripts alike.
    """
    v = (val or "").strip().lower()
    if v == "false":
        return "no"
    if v == "true":
        return "yes"
    return val


def _filter_hosts(host_types):
    """Drop internal-only class nodes (e.g., 'klas') from display lists.

    If filtering empties the list, fall back to EMPTY_HOST_FALLBACK so the
    user still sees a meaningful host annotation. After the 18 May 2026
    Fix A in extract_pkb_v1.py, the catalogue's 'klas' node is renamed to
    'Universal' at parse time, so this fallback should not fire in normal
    operation. It remains as a defensive guard against future catalogue
    artifacts that introduce hidden hosts.
    """
    filtered = [h for h in (host_types or []) if h not in HIDDEN_HOSTS]
    return filtered if filtered else list(EMPTY_HOST_FALLBACK)


# ============================================================================
# SNIPPET GENERATION
# ============================================================================

def _param_snippet(params):
    """Build the snippet portion after the colon.

    BOOLEAN values are emitted as quoted `"yes"` / `"no"`. STRING_TYPES are
    quoted with the default unchanged. Other types pass through cleaned.
    Merged left/right ranges split into two tab stops.
    """
    if not params:
        return ""
    parts = []
    idx = 1
    for p in params:
        ptype = p.get("type", "")
        if p.get("_merged"):
            parts.append("${%d:%s}" % (idx, _clean_default(p.get("_left_default", ""))))
            parts.append("${%d:%s}" % (idx + 1, _clean_default(p.get("_right_default", ""))))
            idx += 2
        elif ptype == "BOOLEAN":
            val = _canonical_boolean(_clean_default(p.get("default", "no")))
            parts.append('"${%d:%s}"' % (idx, val))
            idx += 1
        elif ptype == "REALVECTOR" or ptype == "NUMVEC":
            # REALVECTOR defaults are space-separated numbers; Praat needs
            # them wrapped as a vector literal {a, b, c} or zero# for empty.
            raw = _clean_default(p.get("default", "")).strip()
            if raw:
                nums = [n for n in re.split(r'[\s,]+', raw) if n]
                val = "{" + ", ".join(nums) + "}"
            else:
                val = "zero# (3)"
            parts.append("${%d:%s}" % (idx, val))
            idx += 1
        elif ptype == "STRINGVECTOR" or ptype == "STRVEC":
            raw = _clean_default(p.get("default", "")).strip()
            if raw:
                items = [s.strip() for s in raw.split(",") if s.strip()]
                val = "{" + ", ".join('"%s"' % s.strip('"') for s in items) + "}"
            else:
                val = '{"", "", ""}'
            parts.append("${%d:%s}" % (idx, val))
            idx += 1
        elif ptype == "FORMULA":
            # FORMULA params are Praat expressions evaluated against the
            # selected object. Catalogue uses C-style \" for embedded
            # quotes; Praat scripts use "" (double-double). Convert.
            raw = _clean_default(p.get("default", "")).strip().strip('"')
            raw = raw.replace('\\"', '""')
            val = raw if raw else "1"
            parts.append('"${%d:%s}"' % (idx, val))
            idx += 1
        elif ptype in STRING_TYPES:
            opts = p.get("options")
            default = _clean_default(p.get("default", ""))
            # Note: Sublime's native CompletionItem snippet format does NOT
            # support LSP-style choice tab-stops ${N|opt1,opt2|}. The choice
            # syntax parses as an unrecognized tab-stop and Sublime inserts
            # empty text. So we emit a plain default tab-stop here — users
            # see the validated default pre-selected and can edit in place;
            # the full choice list is shown in the hover popup.
            if opts and default and default not in opts:
                # Catalogue default isn't one of the options (e.g. raw C++
                # expression). Substitute the first valid option as the
                # pre-selected default for the snippet.
                default = opts[0]
            elif opts and not default:
                default = opts[0]
            parts.append('"${%d:%s}"' % (idx, default))
            idx += 1
        else:
            parts.append("${%d:%s}" % (idx, _clean_default(p.get("default", ""))))
            idx += 1
    return ": " + ", ".join(parts)


def _expand_params_for_display(params):
    """Yield (display_label, type, display_default, options) tuples.

    Splits merged left/right pairs into two rows so numbered indices in
    the details panel match the inserted tab-stop positions. BOOLEAN
    defaults are shown in canonical yes/no form. The 4th element is the
    options list for CHOICE/OPTIONMENU fields, or None for other types
    and for synthesized rows from merged ranges.
    """
    for p in params:
        if p.get("_merged"):
            left_label = p.get("_left_label") or p.get("label", "")
            right_label = p.get("_right_label") or p.get("label", "")
            ld = _clean_default(p.get("_left_default", ""))
            rd = _clean_default(p.get("_right_default", ""))
            if left_label == right_label:
                # Catalogue stores identical left/right bodies; surface
                # the shared label qualified with min/max
                yield (left_label + " (min)", p.get("type", ""), ld, None)
                yield (right_label + " (max)", p.get("type", ""), rd, None)
            else:
                yield (left_label, p.get("type", ""), ld, None)
                yield (right_label, p.get("type", ""), rd, None)
        elif p.get("type") == "BOOLEAN":
            yield (p.get("label", ""), p.get("type", ""),
                   _canonical_boolean(_clean_default(p.get("default", ""))),
                   None)
        else:
            yield (p.get("label", ""), p.get("type", ""),
                   _clean_default(p.get("default", "")),
                   p.get("options"))


def _field_count(params):
    """Count actual tab-stop positions for a param list (merged ranges = 2)."""
    return sum(2 if p.get("_merged") else 1 for p in params)


def _details_html(name, variant, include_clinical=True):
    """Build HTML details for the completion panel.

    Numbered rows match inserted tab-stop positions (merged ranges count
    as two rows). Clinical canonical signature appears at the bottom if
    one is registered for this command name and include_clinical is True.
    """
    params = variant.get("params", [])
    rows = []
    for i, (label, ptype, default, opts) in enumerate(_expand_params_for_display(params), 1):
        row = "%d. <b>%s</b> (%s) = %s" % (i, label, ptype, default)
        if opts:
            choices = ", ".join(_esc(o) for o in opts)
            row += '<br>&nbsp;&nbsp;&nbsp;&nbsp;<span class="opts">choices: %s</span>' % choices
        rows.append(row)

    body = "<br>".join(rows) if rows else ""

    hosts = _filter_hosts(variant.get("object_types", []))
    if hosts:
        host_line = "<i>Object: %s</i>" % ", ".join(hosts)
        body = (host_line + "<br><br>" + body) if body else host_line

    if include_clinical and name in CLINICAL_INFO:
        info = CLINICAL_INFO[name]
        if body:
            body += "<br><br>"
        body += '<span class="clinical">⚕ %s</span>' % _esc(info.get("clinical", ""))
        note = info.get("note")
        if note:
            # Convert \n in note to <br> for multi-line notes
            note_html = _esc(note).replace("\n", "<br>")
            body += "<br><br>" + note_html

    return body


# ============================================================================
# COMPLETION ITEMS
# ============================================================================

def _annotation_for_variant(variant):
    """Build the right-aligned annotation text in the completion list."""
    params = variant.get("params", [])
    n = _field_count(params)
    hosts = _filter_hosts(variant.get("object_types", []))
    if hosts:
        # Compact host list for display; show first 2, summarize the rest
        if len(hosts) <= 2:
            host_str = ", ".join(hosts)
        else:
            host_str = "%s, +%d" % (", ".join(hosts[:2]), len(hosts) - 2)
        if n:
            return "%d args · %s" % (n, host_str)
        return host_str
    return "%d args" % n if n else ""


# ============================================================================
# STATUS BAR
# ============================================================================

def _get_param_labels(params):
    """Flat list of short parameter labels matching tab-stop order.

    Merged ranges produce two labels (min/max or left/right body). Output
    length matches `_field_count(params)`.
    """
    labels = []
    for label, ptype, _default, _opts in _expand_params_for_display(params):
        # Strip units in parens for status-bar brevity
        clean = label.split(" (")[0].strip()
        labels.append(clean)
    return labels


def _count_commas(text):
    """Count commas not inside quotes or nested parens."""
    in_quote = False
    depth = 0
    commas = 0
    for ch in text:
        if ch == '"':
            in_quote = not in_quote
        elif not in_quote:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif ch == ',' and depth == 0:
                commas += 1
    return commas


def _pick_variant(variants, typed_commas):
    """Choose the best variant for status-bar display.

    `variants` is the list of (name, variant_dict) entries.
    `typed_commas` is the number of commas the user has typed after the
    colon (0 = on first arg, 1 = on second, etc.). The chosen variant is
    the one whose field count is the smallest that still accommodates the
    typed position. Falls back to the variant with the most fields when
    none accommodate.
    """
    if len(variants) == 1:
        return variants[0]
    typed_arg_index = max(0, typed_commas)
    # Variants that have room for the typed position, sorted by field count
    fits = sorted(
        ((name, v, _field_count(v.get("params", []))) for name, v in variants),
        key=lambda t: t[2],
    )
    for name, v, n in fits:
        if n > typed_arg_index:
            return (name, v)
    # No variant accommodates — return the one with most fields
    fits.sort(key=lambda t: -t[2])
    name, v, _ = fits[0]
    return (name, v)


def _find_command_and_position(view, point):
    """Locate the command or function on the current line and the param index."""
    line_region = view.line(point)
    full_line = view.substr(line_region)
    cursor_in_line = point - line_region.begin()
    line_text = full_line.lstrip()

    if line_text.lower().startswith("noprogress "):
        line_text = line_text[len("noprogress "):]

    # Strip leading assignment (var = ...)
    work_text = line_text
    eq_pos = line_text.find("=")
    if eq_pos > 0 and eq_pos < 50:
        after = line_text[eq_pos + 1:].lstrip()
        if after:
            work_text = after

    # --- Command (colon syntax) ---
    colon_pos = work_text.find(":")
    if colon_pos > 0:
        cmd_text = work_text[:colon_pos].strip()
        cmd_lower = cmd_text.lower()
        if cmd_lower in _command_lookup:
            variants = _command_lookup[cmd_lower]
            full_colon = full_line.find(":")
            if full_colon >= 0 and cursor_in_line > full_colon:
                typed_commas = _count_commas(full_line[full_colon + 1:cursor_in_line])
            else:
                typed_commas = -1
            name, variant = _pick_variant(variants, typed_commas if typed_commas >= 0 else 0)
            params = variant.get("params", [])
            if params:
                return name, params, typed_commas
            return name, params, -1

    # --- Function (parenthesis syntax) ---
    paren_pos = full_line.find("(")
    if paren_pos > 0 and cursor_in_line > paren_pos:
        before_paren = full_line[:paren_pos].rstrip()
        tokens = before_paren.split()
        if tokens:
            fn_name = tokens[-1]
            sig = _func_sigs.get(fn_name, {})
            args_str = sig.get("args", "")
            # New-style signatures list: take the first signature's args
            # for the status-bar hint (canonical primary form).
            if not args_str:
                sig_list = sig.get("signatures") or []
                if sig_list:
                    args_str = sig_list[0].get("args", "")
            if args_str:
                arg_list = [a.strip() for a in args_str.split(",")]
                params = [{"label": a, "type": "arg"} for a in arg_list]
                commas = _count_commas(full_line[paren_pos + 1:cursor_in_line])
                return fn_name, params, commas

    return None, None, -1


class PraatStatusBarHints(sublime_plugin.EventListener):
    """Show all parameter names in the status bar, marking the current one."""

    def on_selection_modified_async(self, view):
        if not view.match_selector(0, "source.praat"):
            view.erase_status("praat_param")
            return

        if len(view.sel()) != 1:
            view.erase_status("praat_param")
            return

        point = view.sel()[0].begin()
        name, params, param_idx = _find_command_and_position(view, point)

        if name is None or param_idx < 0:
            view.erase_status("praat_param")
            return

        labels = _get_param_labels(params)

        if param_idx < len(labels):
            parts = []
            for i, label in enumerate(labels):
                if i == param_idx:
                    parts.append("\u25b8 %s \u25c2" % label)
                else:
                    parts.append(label)
            hint = " \u00b7 ".join(parts)
        elif param_idx >= len(labels) and labels:
            hint = " \u00b7 ".join(labels) + " \u00b7 \u26a0 extra"
        else:
            view.erase_status("praat_param")
            return

        view.set_status("praat_param", hint)


# ============================================================================
# POST-COMPLETION CASE FIX
# ============================================================================
# ST4 completions can only replace the current word (prefix), not text before
# it. When the user types "to Pi" and selects "To Pitch (...)", the lowercase
# "to " stays. This TextCommand fixes the case after completion.

class PraatFixCaseCommand(sublime_plugin.TextCommand):
    """Fix command name case on the current line after completion."""

    def run(self, edit):
        if _command_lookup is None:
            return
        for region in self.view.sel():
            line_region = self.view.line(region)
            line_text = self.view.substr(line_region)
            stripped = line_text.lstrip()
            indent = len(line_text) - len(stripped)

            # Strip noprogress/nocheck prefix
            effective = stripped
            skip = 0
            for kw in ("noprogress ", "nocheck "):
                if effective.lower().startswith(kw):
                    skip = len(kw)
                    effective = effective[skip:]
                    break

            # Extract command portion (before first colon, or whole line)
            cmd_part = effective.split(":")[0].strip() if ":" in effective else effective.strip()
            cmd_lower = cmd_part.lower()

            # Look up in command registry
            if cmd_lower in _command_lookup:
                correct_name = _command_lookup[cmd_lower][0][0]
                typed_name = effective[:len(correct_name)]
                if typed_name != correct_name:
                    start = line_region.begin() + indent + skip
                    end = start + len(correct_name)
                    self.view.replace(
                        edit,
                        sublime.Region(start, end),
                        correct_name
                    )


# ============================================================================
# COMPLETIONS
# ============================================================================

def _get_line_prefix(view, point):
    """Get text on current line before cursor, stripped."""
    line_start = view.line(point).begin()
    text = view.substr(sublime.Region(line_start, point))
    stripped = text.lstrip()
    if stripped.lower().startswith("noprogress "):
        stripped = stripped[len("noprogress "):]
    return stripped


class PraatCompletionListener(sublime_plugin.EventListener):
    """Emit one completion per command-variant; merge identical-signature ones."""

    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(locations[0], "source.praat"):
            return None
        if _data is None:
            plugin_loaded()
            if _data is None:
                return None

        point = locations[0]
        line_prefix = _get_line_prefix(view, point)
        line_prefix_lower = line_prefix.lower()
        if not line_prefix_lower:
            return None

        if prefix:
            pre_text = line_prefix[:-len(prefix)]
        else:
            pre_text = line_prefix
        pre_text_lower = pre_text.lower().rstrip()

        results = []

        # --- Commands (per-variant) ---
        schema = _data.get("schema_version", 1)
        commands = _data.get("commands", {})
        for name, variants_data in commands.items():

            # Match from line start — case-insensitive so "to Pi" finds
            # "To Pitch". Note: if the user typed the verb prefix in wrong
            # case (e.g. "to" instead of "To"), the wrong-case prefix stays
            # on the line after completion. Praat is case-sensitive, so the
            # user will need to fix it — but at least they see the options.
            if name.lower().startswith(line_prefix_lower):
                remaining_name = name[len(pre_text):]
                trigger = remaining_name
            elif not pre_text.strip():
                # Word-boundary match: ONLY when cursor is at line start
                # (no partial command already typed). Lets "CPPS" match
                # "Get CPPS", "Pitch" match "To Pitch (...)", etc.
                # The full command name is inserted, replacing the prefix.
                # Strip parens so "filtered" matches "(filtered" in
                # "To Pitch (filtered autocorrelation)".
                words = name.lower().split()
                matched = False
                for wi in range(1, len(words)):
                    suffix = " ".join(w.strip("(),") for w in words[wi:])
                    if suffix.startswith(line_prefix_lower):
                        remaining_name = name
                        trigger = name
                        matched = True
                        break
                if not matched:
                    continue
            else:
                continue
            # Normalize legacy single-variant entries
            if schema >= 3:
                variant_list = variants_data
            else:
                ot = variants_data.get("object_type", "")
                variant_list = [{
                    "object_types": [ot] if ot else [],
                    "params": variants_data.get("params", []),
                }]

            for variant in variant_list:
                params = variant.get("params", [])
                snippet = remaining_name + _param_snippet(params)
                annotation = _annotation_for_variant(variant)
                details = _details_html(name, variant)

                # Surface clinical-canonical commands with a marker
                kind_letter = "c"
                kind_label = "Command"
                if name in CLINICAL:
                    kind_letter = "\u269a"
                    kind_label = "Clinical command"

                item = sublime.CompletionItem.snippet_completion(
                    trigger=trigger,
                    snippet=snippet,
                    annotation=annotation,
                    kind=(sublime.KIND_ID_FUNCTION, kind_letter, kind_label),
                    details=details,
                )
                results.append(item)

        # --- Functions and colon-syntax commands ---
        # v5 fix (18 May 2026): iterate _func_sigs (dict, keyed by function
        # name) rather than _data["functions"], whose shape changed from a
        # dict-of-lists in v4.3.1 to a list-of-dicts in v5. The legacy
        # iteration silently crashed with AttributeError on .items().
        #
        # Match against `prefix` (the trailing word Sublime supplies), not
        # `line_prefix_lower` (the whole line). Functions live in expression
        # positions — `x = abs(...)`, `Formula: ~sin(...)` — where the line
        # before the cursor includes assignment operators, parens, and other
        # non-name text. Matching by `line_prefix_lower` would require
        # function names to start with that whole line, which they never do.
        # This was the latent bug the `if not pre_text_lower:` gate masked
        # in v4.3.1.
        prefix_lower = prefix.lower() if prefix else ""
        if prefix_lower:
            for fn, sig in _func_sigs.items():
                if not fn.lower().startswith(prefix_lower):
                    continue
                if fn in COLON_COMMANDS:
                    item = sublime.CompletionItem.snippet_completion(
                        trigger=fn,
                        snippet=fn + ": $0",
                        annotation="command",
                        kind=(sublime.KIND_ID_FUNCTION, "c", "Command"),
                    )
                else:
                    args = (sig or {}).get("args", "")
                    desc = (sig or {}).get("desc", "")
                    # If this entry uses the new `signatures` list (3+
                    # overloads), draw args/desc from the first
                    # signature — the canonical primary form. The hover
                    # popup still iterates and shows all signatures.
                    if not args and sig:
                        sig_list = sig.get("signatures") or []
                        if sig_list:
                            args = sig_list[0].get("args", "")
                            desc = sig_list[0].get("desc", "")
                    # Sublime's snippet parser treats $ as a sigil for tab-stops
                    # ($0, $1, ${1:default}) and variables ($BLOCK_COMMENT_START).
                    # Function names like fixed$, length$, fileNames$# contain
                    # a literal $ that must be escaped as \$ in snippet content.
                    # Without this, insertion produces undefined behavior — most
                    # destructively, clearing the surrounding line.
                    # The `trigger` field is not parsed as a snippet, so fn
                    # stays unescaped there.
                    fn_snip = fn.replace("$", "\\$")
                    if args:
                        arg_list = [a.strip() for a in args.split(",")]
                        # Argument labels may also contain $ (e.g. "matrix##",
                        # "vector#" are fine, but "string$" needs escaping
                        # because it lands inside the placeholder default).
                        tab_args = ", ".join(
                            "${%d:%s}" % (i + 1, a.replace("$", "\\$"))
                            for i, a in enumerate(arg_list)
                        )
                        snip = "%s (%s)" % (fn_snip, tab_args)
                    else:
                        snip = fn_snip + " ($0)"
                    ann = "function" if not desc else ("function \u2014 " + desc[:40])
                    item = sublime.CompletionItem.snippet_completion(
                        trigger=fn,
                        snippet=snip,
                        annotation=ann,
                        kind=(sublime.KIND_ID_FUNCTION, "f", "Function"),
                    )
                results.append(item)

            # --- Types ---
            for ot in _data.get("object_types", []):
                if ot.lower().startswith(prefix_lower):
                    item = sublime.CompletionItem(
                        trigger=ot,
                        annotation="type",
                        completion=ot,
                        kind=(sublime.KIND_ID_TYPE, "t", "Type"),
                    )
                    results.append(item)

            # --- Constants ---
            for c in _data.get("constants", []):
                if c.lower().startswith(prefix_lower):
                    item = sublime.CompletionItem(
                        trigger=c,
                        annotation="const",
                        completion=c,
                        kind=(sublime.KIND_ID_VARIABLE, "v", "Const"),
                    )
                    results.append(item)

        if not results:
            return None

        return sublime.CompletionList(results, flags=sublime.INHIBIT_WORD_COMPLETIONS)

    def on_post_text_command(self, view, command_name, args):
        """After a completion is committed, fix wrong-case command prefixes.
        Catches commit_completion, insert_best_completion, and auto_complete."""
        if command_name not in ('commit_completion', 'insert_best_completion',
                                'auto_complete', 'insert_completion'):
            return
        if not view.sel():
            return
        if not view.match_selector(view.sel()[0].begin(), "source.praat"):
            return
        view.run_command('praat_fix_case')

    def on_modified_async(self, view):
        """Fallback: fix case on any modification (catches completions that
        don't fire as named text commands). Guarded to only act when the
        line looks like a just-completed command with wrong case."""
        if not view.sel() or len(view.sel()) != 1:
            return
        if not view.match_selector(view.sel()[0].begin(), "source.praat"):
            return
        if _command_lookup is None:
            return

        region = view.sel()[0]
        line_region = view.line(region)
        line_text = view.substr(line_region)
        stripped = line_text.lstrip()

        # Only act if line has a colon (looks like a completed command)
        if ":" not in stripped:
            return

        cmd_part = stripped.split(":")[0].strip()
        # Strip noprogress/nocheck
        for kw in ("noprogress ", "nocheck "):
            if cmd_part.lower().startswith(kw):
                cmd_part = cmd_part[len(kw):]
                break

        cmd_lower = cmd_part.lower()
        if cmd_lower in _command_lookup:
            correct_name = _command_lookup[cmd_lower][0][0]
            if cmd_part != correct_name:
                view.run_command('praat_fix_case')


# ============================================================================
# Hover popup
# ============================================================================
# CompletionItem.details doesn't render in some ST4 configurations — verified
# 18 May 2026 in user's environment: details HTML is sent but never surfaces,
# only the annotation column is visible (clipped in dropdown, expanded on
# hover). To deliver the parameter table, host info, and clinical-canonical
# note as a usable depth-view, this listener renders the same content via
# view.show_popup() when the user hovers over a command, function, type, or
# procedure call in the editor text.
#
# Scope detection uses Praat.sublime-syntax tags:
#   support.function.command.praat       — multi-word command (Get start time)
#   support.function.{matrix,vector,
#     string,string-array,praat}         — single-token functions
#   support.type.praat                   — object types (Sound, TextGrid, ...)
#                                          renamed from entity.name.type in
#                                          v0.8-beta.11 to suppress ST's
#                                          auto-symbol-indexing on these.
#   entity.name.function.procedure-call  — @procName calls

POPUP_CSS = """
<style>
    body { font-size: 1.0rem; padding: 0.3rem 0.5rem; line-height: 1.4; }
    h3   { margin: 0 0 0.4rem 0; font-size: 1.05rem; color: var(--bluish); }
    b    { color: var(--orangish); }
    i    { color: var(--greenish); }
    code { font-family: monospace; color: var(--bluish); }
    .head { font-size: 1.05rem; font-weight: bold; color: var(--bluish);
            margin-bottom: 0.3rem; }
    .sep { margin: 0.4rem 0; border-top: 1px solid var(--foreground); opacity: 0.25; }
    .clinical { color: var(--purplish); margin-top: 0.5rem; }
    .section { margin-top: 0.3rem; }
    .opts { color: var(--bluish); font-family: monospace; font-size: 0.9em; }
</style>
"""

_SEP = '<div class="sep"></div>'


def _esc(s):
    """Minimal HTML escape for popup text content."""
    if s is None:
        return ""
    return (str(s).replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;"))


def _popup_show(view, point, body, max_width=720, max_height=480):
    """Open a popup at point with the standard CSS wrapper."""
    view.show_popup(
        POPUP_CSS + body,
        flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
        location=point,
        max_width=max_width,
        max_height=max_height,
    )


class PraatHoverListener(sublime_plugin.EventListener):
    """Show a rich popup with parameter details when the user hovers over a
    Praat command, function, type, or procedure call in the editor."""

    def _try_line_command(self, view, point):
        """Extract the command name from the line text at point.

        Handles the case where the cursor is on a word (like 'Pitch')
        that is part of a multi-word command (like 'To Pitch (filtered
        cross-correlation)'). Returns the matched command name or None.
        """
        line_region = view.line(point)
        line_text = view.substr(line_region).strip()
        # Strip leading dots (continuation lines)
        if line_text.startswith("..."):
            return None
        # Extract the command portion (before the colon, if any)
        cmd_part = line_text.split(":")[0].strip() if ":" in line_text else line_text.strip()
        # Also strip leading noprogress / nocheck
        for prefix in ("noprogress ", "nocheck "):
            if cmd_part.lower().startswith(prefix):
                cmd_part = cmd_part[len(prefix):].strip()
        # Try exact match first
        if cmd_part.lower() in _command_lookup:
            return cmd_part
        # Try progressively shorter prefixes (handles trailing args on
        # no-colon commands like "select all")
        words = cmd_part.split()
        for n in range(len(words), 0, -1):
            candidate = " ".join(words[:n])
            if candidate.lower() in _command_lookup:
                return candidate
        return None

    def on_hover(self, view, point, hover_zone):
        if hover_zone != sublime.HOVER_TEXT:
            return
        if _data is None:
            return
        if not view.match_selector(point, "source.praat"):
            return

        # ALWAYS try line-level command extraction first, regardless of scope.
        # This prevents ST4's native "Go to Definition" from hijacking the
        # hover on words like "Pitch" that are both part of a command name
        # and a defined symbol in other open files.
        cmd_name = self._try_line_command(view, point)
        if cmd_name:
            self._popup_command(view, point, cmd_name)
            return

        scope = view.scope_name(point)

        # Multi-word commands: extract the full scoped region (the syntax file
        # tags the whole command name as one support.function.command span).
        if "support.function.command" in scope:
            region = view.extract_scope(point)
            name = view.substr(region).rstrip(":").strip()
            self._popup_command(view, point, name)
            return

        # Single-token functions: any other support.function.* scope.
        # Use extract_scope (not view.word) because view.word splits on
        # `$` and `#`, returning 'mul' instead of 'mul##' and 'fixed'
        # instead of 'fixed$'. The wordCharacters="$#" setting in
        # Praat.tmPreferences is supposed to fix this but is ignored
        # by ST4 on macOS — empirically confirmed 2026-05-22.
        # The syntax file tags the entire function name (suffixes
        # included) as a single scoped region, so extract_scope
        # returns the correct span.
        if "support.function" in scope:
            region = view.extract_scope(point)
            # .strip() because the plain-function syntax rule consumes
            # trailing whitespace into the match (\s*(?=\(|\s|$)),
            # so extract_scope returns 'ceiling ' instead of 'ceiling'.
            # The ##/#/$/$# rules use pure lookaheads and don't have
            # this issue, but .strip() is defensive against future
            # syntax-file changes.
            name = view.substr(region).strip()
            self._popup_function(view, point, name)
            return

        # Object types — scope is `support.type.praat` (not entity.name.*).
        # Renamed from entity.name.type in v0.8-beta.11 so Sublime no longer
        # auto-indexes Praat object types as symbols, which prevents ST's
        # "Show Definitions" hover from firing on `Table`, `Sound`, `Pitch`,
        # etc. wherever they appear in a buffer (including inside multi-word
        # commands like `Create Table with column names:` where the bare-word
        # indexing was firing despite the surrounding scope being a command).
        if "support.type" in scope:
            region = view.extract_scope(point)
            name = view.substr(region).strip()
            self._popup_type(view, point, name)
            return

        # Procedure calls (@procName ...)
        if "entity.name.function.procedure-call" in scope:
            region = view.extract_scope(point)
            text = view.substr(region).strip()
            self._popup_procedure(view, point, text)
            return

        # ---- Scope-agnostic fallback ----
        # The scope-based dispatch above misses several cases:
        #   1. tab$, newline$ and other predefined string variables — syntax
        #      tags these as constant.language.praat, not support.function.
        #   2. Buffers that aren't fully recognized as source.praat (e.g.
        #      untitled buffers, syntax-assignment edge cases) may have weaker
        #      scope coverage on individual tokens.
        # We use a manual word extractor (not view.word) because view.word
        # splits on `$` and `#` regardless of tmPreferences wordCharacters
        # setting — empirically confirmed 2026-05-22 on macOS ST4.
        #
        # IMPORTANT: only fire popups here for zero-argument entries. If a
        # function takes arguments, the syntax file's regex requires `(`
        # to follow the name before assigning the function scope. If we
        # reach this fallback with a multi-arg function name in hand, that
        # means the syntax did NOT classify it as a function call — the
        # user wrote `string$` in a position like `index (string$, part$)`
        # where `string$` is a parameter placeholder, not a function call.
        # Firing the function popup there is misleading. Restrict the
        # fallback to true constants like `tab$` and `newline$` whose
        # `args` field is empty.
        region = self._extract_token_at(view, point)
        name = view.substr(region)
        if name in _func_sigs:
            sig = _func_sigs[name]
            takes_args = bool(sig.get("args") or sig.get("signatures"))
            if not takes_args:
                self._popup_function(view, point, name)
                return
        if name in _data.get("object_types", []):
            self._popup_type(view, point, name)
            return

    def _extract_token_at(self, view, point):
        """Extract a token at `point`, treating `$` and `#` as word characters.

        Sublime Text's `view.word(point)` uses the platform default word
        definition, which splits on `$` and `#`. The `wordCharacters="$#"`
        setting in Praat.tmPreferences is intended to extend this but is
        not reliably applied by ST4 on macOS (empirically confirmed
        2026-05-22). This helper does the extraction manually so the
        plugin is host-independent and settings-independent.
        """
        line_region = view.line(point)
        line_text = view.substr(line_region)
        line_start = line_region.begin()
        col = point - line_start
        # Extend left while character is alnum or in {_, $, #}
        start = col
        while start > 0:
            ch = line_text[start - 1]
            if ch.isalnum() or ch in "_$#":
                start -= 1
            else:
                break
        # Extend right
        end = col
        while end < len(line_text):
            ch = line_text[end]
            if ch.isalnum() or ch in "_$#":
                end += 1
            else:
                break
        return sublime.Region(line_start + start, line_start + end)

    def _popup_command(self, view, point, name):
        variants = _command_lookup.get(name.lower(), [])
        if not variants:
            return

        # Split into parameterized and zero-param variants
        with_params = []
        zero_param_hosts = []
        for display_name, variant in variants:
            params = variant.get("params", [])
            hosts = _filter_hosts(variant.get("object_types", []))
            if params:
                with_params.append((display_name, variant))
            else:
                zero_param_hosts.extend(hosts)

        # Build the popup
        head = '<div class="head">%s</div>' % _esc(name)
        sections = []
        for display_name, variant in with_params:
            html = _details_html(display_name, variant, include_clinical=False)
            if html:
                sections.append(html)

        body = head
        if sections:
            body += _SEP.join(sections)

        # Collapse zero-param variants into plain English
        if zero_param_hosts:
            if sections:
                body += _SEP
            body += ("<i>Object: %s</i><br>"
                     "This command takes no arguments for these objects."
                     % ", ".join(zero_param_hosts))

        if not sections and not zero_param_hosts:
            return

        # Clinical annotation and contextual notes: once at the bottom
        info = CLINICAL_INFO.get(name)
        if info:
            clinical = info.get("clinical", "")
            note = info.get("note")
            body += _SEP + '<div class="clinical">\u2695 %s</div>' % _esc(clinical)
            if note:
                note_html = _esc(note).replace("\n", "<br>")
                body += "<br>" + note_html

        _popup_show(view, point, body)

    def _popup_function(self, view, point, name):
        sig = _func_sigs.get(name)
        if not sig:
            return
        # New-style: a `signatures` list of {args, desc} dicts, one per
        # overload. Used when a function has 3+ overloads (e.g. fixed$
        # accepting scalar/vector/matrix). Takes precedence over the
        # legacy args+alt_args path.
        signatures = sig.get("signatures")
        if signatures:
            body = ""
            for i, sg in enumerate(signatures):
                head_parts = ["<code>%s</code>" % _esc(name)]
                if sg.get("args"):
                    head_parts.append("<code>(%s)</code>" % _esc(sg["args"]))
                if i > 0:
                    body += '<div class="sep"></div>'
                body += '<div class="head">%s</div>' % " ".join(head_parts)
                if sg.get("desc"):
                    body += "<br/>" + _esc(sg["desc"])
            _popup_show(view, point, body, max_height=320)
            return
        # Legacy path: args + optional alt_args/alt_desc (2 overloads).
        args = sig.get("args", "")
        desc = sig.get("desc", "")
        alt_args = sig.get("alt_args", "")
        alt_desc = sig.get("alt_desc", "")
        head_parts = ["<code>%s</code>" % _esc(name)]
        if args:
            head_parts.append("<code>(%s)</code>" % _esc(args))
        head = '<div class="head">%s</div>' % " ".join(head_parts)
        body = head
        if desc:
            body += "<br/>" + _esc(desc)
        if alt_args or alt_desc:
            body += '<div class="sep"></div>'
            alt_head_parts = ["<code>%s</code>" % _esc(name)]
            if alt_args:
                alt_head_parts.append("<code>(%s)</code>" % _esc(alt_args))
            body += '<div class="head">%s</div>' % " ".join(alt_head_parts)
            if alt_desc:
                body += "<br/>" + _esc(alt_desc)
        _popup_show(view, point, body, max_height=320)

    def _popup_type(self, view, point, name):
        if name not in _data.get("object_types", []):
            return
        body = ('<div class="head">%s</div>'
                '<i>Praat object type</i>') % _esc(name)
        _popup_show(view, point, body, max_width=400, max_height=120)

    def _popup_procedure(self, view, point, text):
        # text is like "@emlMean: .data#" — pull the bare @name token
        head_token = text.split("(", 1)[0].split(":", 1)[0].strip()
        for p in _data.get("procedures", []) or []:
            if not isinstance(p, dict):
                continue
            if p.get("name") == head_token:
                params = p.get("params", "")
                purpose = p.get("purpose", "")
                scope_tag = p.get("scope", "")
                head_parts = ["<code>%s</code>" % _esc(p["name"])]
                if params:
                    head_parts.append("<code>%s</code>" % _esc(params))
                head = '<div class="head">%s</div>' % " ".join(head_parts)
                body = head
                if purpose:
                    body += "<br/>" + _esc(purpose)
                if scope_tag:
                    body += "<br/><br/><i>Scope: %s</i>" % _esc(scope_tag)
                _popup_show(view, point, body, max_height=320)
                return

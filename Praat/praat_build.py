# ============================================================================
# EML PraatGen — build target: save-before-run + macOS run-mode branch
#                + Praat auto-discovery
# ============================================================================
# Three jobs:
#
# 1. SAVE BEFORE RUN
#    Praat receives the script path via Sublime's $file variable. For an
#    UNSAVED buffer $file is empty, and Praat resolves the empty path against
#    the process working directory (Sublime's own program folder), producing a
#    confusing "Cannot open file ... /Contents/MacOS/" error. This target saves
#    the active view first, so $file is always a real path:
#      - A saved-but-dirty file is saved silently, then runs.
#      - A never-saved buffer gets the save dialog; if it is dismissed, the
#        build aborts with a clear status message instead of the cryptic error.
#
# 2. macOS RUN-MODE BRANCH
#    On macOS 15 (Sequoia), --send / --send-or-form to an already-running Praat
#    is silently refused by TCC (the same-bundle org.praat.Praat Apple Event is
#    blocked). So on macOS >= 14 we instead open the script in Praat's editor
#    via `open -a Praat <file>`; the user presses Cmd-R to run it, and forms
#    present natively. open -a addresses Praat by name, so LaunchServices finds
#    it wherever it is installed — no path needed. Earlier macOS, Linux, and
#    Windows keep the --send-or-form auto-run path from Praat.sublime-build.
#
#    The open-in-editor path triggers on a detected major >= 14 AND when the
#    version cannot be determined. macOS reports "10.16" to processes not built
#    against the 11.0+ SDK (the SYSTEM_VERSION_COMPAT shim); _macos_major works
#    around this by querying sw_vers with SYSTEM_VERSION_COMPAT=0 and by mapping
#    a "10.16" reading to the modern path. Real macOS <= 10.15 (Catalina) and
#    11-13 keep the --send-or-form auto-run path. To force auto-run on
#    undetectable macOS instead, change `major is None or major >= 14` back to
#    `major is not None and major >= 14`.
#
# 3. PRAAT AUTO-DISCOVERY (non-open-a paths)
#    For the --send-or-form paths, the build file ships the standard Praat
#    location per OS. If Praat is installed there, nothing happens. If it is
#    NOT there, we try to discover it before giving up (PATH on every OS;
#    /Applications and Spotlight on macOS; Program Files on Windows) so the
#    build still works. An explicitly-configured path that exists is always
#    respected and never overridden.
#
# Wired in via "target": "praat_build" in Praat.sublime-build.
# ============================================================================

import os
import platform
import shutil
import subprocess

import sublime
from Default.exec import ExecCommand

# macOS major version at/above which the open-in-editor path is used.
MACOS_OPEN_THRESHOLD = 14


def _parse_macos_major(ver):
    """'15.6' -> 15. The shim value '10.16' is reported to processes not built
    against the 11.0+ SDK and means 'Big Sur or later'; map it to a value that
    takes the modern (open-in-editor) path. Real 10.x (<= 10.15 Catalina)
    passes through unchanged."""
    parts = ver.split(".")
    major = int(parts[0])
    if major == 10 and len(parts) > 1 and int(parts[1]) >= 16:
        return 16
    return major


def _macos_major():
    """macOS major version as an int, or None if it cannot be determined.

    Prefers `sw_vers` with SYSTEM_VERSION_COMPAT=0, which returns the true
    product version (e.g. "15.6") even from a process that would otherwise be
    handed the "10.16" compatibility shim — the cause of the open-in-editor
    branch silently not firing on Sequoia."""
    try:
        env = dict(os.environ)
        env["SYSTEM_VERSION_COMPAT"] = "0"
        ver = subprocess.check_output(
            ["sw_vers", "-productVersion"], env=env).decode().strip()
        if ver:
            return _parse_macos_major(ver)
    except Exception:
        pass
    try:
        ver = platform.mac_ver()[0]          # e.g. "15.6" (may be shimmed)
        if ver:
            return _parse_macos_major(ver)
    except Exception:
        pass
    return None


def _exe_available(exe):
    """True if the build file's configured executable can be located."""
    if not exe:
        return False
    if os.path.isabs(exe):
        return os.path.exists(exe)
    return shutil.which(exe) is not None     # bare name -> resolve on PATH


def _discover_praat():
    """Best-effort locate Praat when the configured path is missing.
    Returns an executable path string, or None."""
    found = shutil.which("praat")            # PATH, any OS
    if found:
        return found
    plat = sublime.platform()
    if plat == "osx":
        cand = "/Applications/Praat.app/Contents/MacOS/Praat"
        if os.path.exists(cand):
            return cand
        try:                                 # ask Spotlight/LaunchServices
            base = subprocess.check_output(
                ["osascript", "-e",
                 'POSIX path of (path to application "Praat")'],
                stderr=subprocess.DEVNULL).decode().strip()
            exe = os.path.join(base, "Contents/MacOS/Praat") if base else ""
            if exe and os.path.exists(exe):
                return exe
        except Exception:
            pass
    elif plat == "windows":
        for cand in (r"C:\Program Files\Praat.exe",
                     r"C:\Program Files (x86)\Praat.exe"):
            if os.path.exists(cand):
                return cand
    return None


class PraatBuildCommand(ExecCommand):
    def run(self, **kwargs):
        # Cancel requests (Tools -> Cancel Build) arrive as kill=True and must
        # pass straight through to the running process.
        if kwargs.get("kill"):
            super().run(**kwargs)
            return

        view = self.window.active_view()

        # Save first so $file is a real path. Saving a named file is
        # synchronous; a never-saved buffer opens the save dialog.
        if view is not None and (view.is_dirty() or view.file_name() is None):
            view.run_command("save")

        # If there is still no path on disk (never saved, or save cancelled),
        # do not hand Praat a bogus path — abort with a clear message.
        if view is None or view.file_name() is None:
            self.window.status_message(
                "Praat build: save the file first, then build again.")
            return

        # macOS >= 14: open the script in Praat's editor (TCC blocks the
        # --send Apple Event on Sequoia); the user runs it with Cmd-R. open -a
        # locates Praat by name, so this also serves as discovery on macOS.
        if sublime.platform() == "osx":
            major = _macos_major()
            if major is None or major >= MACOS_OPEN_THRESHOLD:
                kwargs["cmd"] = ["open", "-a", "Praat", view.file_name()]
                super().run(**kwargs)
                return

        # All other paths use the --send-or-form cmd from Praat.sublime-build.
        # If its configured executable can't be found, auto-discover Praat
        # before giving up. An existing, explicitly-set path is left as-is.
        cmd = kwargs.get("cmd")
        if cmd and not _exe_available(cmd[0]):
            found = _discover_praat()
            if found:
                kwargs["cmd"] = [found] + list(cmd[1:])

        super().run(**kwargs)

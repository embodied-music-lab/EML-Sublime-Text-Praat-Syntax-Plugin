# ============================================================================
# EML PraatGen — build target with save-before-run hardening
# ============================================================================
# Praat's --send-or-form switch receives the script path via Sublime's $file
# variable. For an UNSAVED buffer $file is empty, and Praat resolves the empty
# path against the process working directory (Sublime's own program folder),
# producing a confusing "Cannot open file ... /Contents/MacOS/" error.
#
# This build target saves the active view before delegating to the default
# exec command, so $file is always a real path:
#   - A saved-but-dirty file is saved silently, then runs.
#   - A never-saved buffer gets the save dialog; if it is dismissed, the build
#     aborts with a clear status message instead of the cryptic Praat error.
#
# Wired in via "target": "praat_build" in Praat.sublime-build.
# ============================================================================

from Default.exec import ExecCommand


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

        super().run(**kwargs)

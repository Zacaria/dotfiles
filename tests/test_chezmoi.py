"""Exercise the actual chezmoi binary in isolated homes and state directories."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest


REPO = Path(__file__).resolve().parents[1]
CHEZMOI = shutil.which("chezmoi")


@unittest.skipUnless(CHEZMOI, "Install chezmoi before running these tests")
class ChezmoiTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="chezmoi-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.home = self.root / "home with spaces"
        self.home.mkdir()
        self.cwd = self.root / "another directory"
        self.cwd.mkdir()
        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        for key in tuple(self.env):
            if key.startswith(("CHEZMOI_", "XDG_")):
                self.env.pop(key)
        self.config = self.root / "chezmoi.toml"

    def chez(self, *args, source=REPO):
        command = [
            CHEZMOI,
            "--destination", str(self.home),
            "--config", str(self.config),
            "--persistent-state", str(self.root / "state.boltdb"),
            "--cache", str(self.root / "cache"),
            "--no-pager",
            "--no-tty",
        ]
        if source is not None:
            command += ["--source", str(source)]
        return subprocess.run(
            [*command, *args], cwd=self.cwd, env=self.env,
            text=True, capture_output=True, check=False,
        )

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def fake_command(self, name, body):
        directory = self.root / "fake commands"
        directory.mkdir(exist_ok=True)
        executable = directory / name
        executable.write_text("#!/bin/sh\nset -eu\n" + body + "\n")
        executable.chmod(0o755)
        self.env["PATH"] = str(directory) + os.pathsep + self.env["PATH"]

    def copy_source(self):
        copy = self.root / "repository with spaces"
        shutil.copytree(
            REPO, copy,
            ignore=shutil.ignore_patterns(".git", "fonts", ".history", "__pycache__"),
        )
        return copy

    def test_source_root_limits_managed_files(self):
        result = self.chez("managed", "--include=files")
        self.assert_success(result)
        self.assertEqual(set(result.stdout.splitlines()), {
            ".aliases", ".Brewfile", ".bunfig.toml", ".npmrc",
            ".config/ghostty/config.ghostty", ".config/zed/settings.json",
            ".config/mise/config.toml",
            ".config/starship.toml", ".config/uv/.python-version",
            ".config/uv/uv.toml", ".gitconfig", ".gitignore_global",
            ".zprofile", ".zshrc",
        })

    def test_dry_run_never_executes_scripts_or_changes_home(self):
        self.fake_command("brew", "exit 91")
        self.fake_command("git", "exit 92")
        self.assert_success(self.chez("apply", "--dry-run", "--verbose"))
        self.assertEqual(list(self.home.iterdir()), [])

    def test_apply_copies_files_is_idempotent_and_preserves_local_settings(self):
        personal = self.home / ".zshrc.local"
        personal.write_text("personal settings\n")
        self.assert_success(self.chez("apply", "--exclude=scripts"))
        target = self.home / ".config/mise/config.toml"
        self.assertFalse(target.is_symlink())
        self.assertEqual(
            target.read_text(), (REPO / "home/dot_config/mise/config.toml").read_text()
        )
        self.assertEqual(
            (self.home / ".config/uv/.python-version").read_text().strip(), "3.13.3"
        )
        self.assertEqual(personal.read_text(), "personal settings\n")
        self.assert_success(self.chez("apply", "--exclude=scripts"))
        result = self.chez("diff", "--exclude=scripts")
        self.assert_success(result)
        self.assertEqual(result.stdout, "")

    def test_conflicting_local_changes_fail_without_overwriting(self):
        self.assert_success(self.chez("apply", "--exclude=scripts"))
        target = self.home / ".zshrc"
        target.write_text("changed outside chezmoi\n")
        result = self.chez("apply", "--exclude=scripts", "--error-on-conflict")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_text(), "changed outside chezmoi\n")

    def test_init_remembers_repository_not_source_subdirectory(self):
        source = self.copy_source()
        self.assert_success(self.chez("init", source=source))
        result = self.chez("source-path", str(self.home / ".zshrc"), source=None)
        self.assert_success(result)
        self.assertEqual(Path(result.stdout.strip()), source / "home/dot_zshrc")

    def test_repository_and_destination_paths_can_contain_spaces(self):
        source = self.copy_source()
        self.assert_success(self.chez("apply", "--exclude=scripts", source=source))
        self.assertEqual(
            (self.home / ".aliases").read_text(),
            (source / "home/dot_aliases").read_text(),
        )

    @unittest.skipUnless(sys.platform == "darwin", "Package scripts target macOS")
    def test_failed_packages_do_not_replace_existing_files(self):
        original = self.home / ".zshrc"
        original.write_text("original\n")
        self.fake_command("brew", "printf 'controlled package failure\\n' >&2; exit 23")
        result = self.chez("apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("controlled package failure", result.stderr)
        self.assertEqual(original.read_text(), "original\n")

    @unittest.skipUnless(sys.platform == "darwin", "Package scripts target macOS")
    def test_scripts_run_once_and_rerun_when_manifest_changes(self):
        source = self.copy_source()
        prefix = self.root / "fake Homebrew"
        (prefix / "bin").mkdir(parents=True)
        mise = prefix / "bin/mise"
        mise.write_text(
            "#!/bin/sh\nset -eu\n"
            'if [ "$1" = install ]; then\n'
            '  test -f "$MISE_GLOBAL_CONFIG_FILE"\n'
            '  printf "mise\\n" >> "$TEST_CALLS"\n'
            "fi\n"
        )
        mise.chmod(0o755)
        uv = prefix / "bin/uv"
        uv.write_text(
            "#!/bin/sh\nset -eu\n"
            'if [ "$3" = --help ]; then printf "%s\\n" --default; exit 0; fi\n'
            '[ "$*" = "python install 3.13.3 --default" ] || exit 21\n'
            'printf "uv\\n" >> "$TEST_CALLS"\n'
        )
        uv.chmod(0o755)
        codex = prefix / "bin/codex"
        codex.write_text(
            f"#!{shutil.which('node')}\n" + r'''
const fs = require("node:fs");
if (process.argv[2] !== "app-server") {
  fs.appendFileSync(process.env.TEST_CALLS,
    process.argv[3] === "marketplace" ? "codex-marketplace\n" : "codex-add\n");
} else {
  require("node:readline").createInterface({ input: process.stdin }).on("line", line => {
    const message = JSON.parse(line);
    if (!message.id) return;
    let result = {};
    if (message.method === "initialize") result = { codexHome: process.env.HOME + "/.codex" };
    else if (message.method === "hooks/list") result = { data: [{ hooks: [{
      key: process.env.HOME + "/.codex/hooks.json:pre_tool_use:0:0",
      source: "user", command: "rtk hook codex", trustStatus: "untrusted",
      currentHash: "sha256:" + "a".repeat(64),
    }] }] };
    else if (message.method === "config/value/write") {
      if (message.params.value.trusted_hash !== "sha256:" + "a".repeat(64)) process.exit(26);
      fs.appendFileSync(process.env.TEST_CALLS, "codex-trust\n");
    } else process.exit(27);
    console.log(JSON.stringify({ id: message.id, result }));
  });
}
'''
        )
        codex.chmod(0o755)
        rtk = prefix / "bin/rtk"
        rtk.write_text(
            "#!/bin/sh\nset -eu\n"
            'if [ "$2" = --help ]; then printf "%s\\n" "- omp:"; exit 0; fi\n'
            'case "$*" in\n'
            '  *--codex*) printf "rtk-codex\\n" >> "$TEST_CALLS" ;;\n'
            '  *"agent omp"*) printf "rtk-omp\\n" >> "$TEST_CALLS" ;;\n'
            "  *) exit 22 ;;\n"
            "esac\n"
        )
        rtk.chmod(0o755)
        calls = self.root / "calls.txt"
        self.env.update(TEST_BREW_PREFIX=str(prefix), TEST_CALLS=str(calls))
        data = tomllib.loads((source / "home/.chezmoidata.toml").read_text())
        self.env["TEST_CONTEXT_VERSION"] = data["contextModeVersion"]
        self.fake_command(
            "brew",
            'case "$1" in\n'
            '  --prefix) printf "%s\\n" "$TEST_BREW_PREFIX" ;;\n'
            '  bundle) printf "brew\\n" >> "$TEST_CALLS" ;;\n'
            "  list) exit 1 ;;\n"
            "  *) exit 24 ;;\n"
            "esac",
        )
        self.fake_command(
            "git",
            'mkdir -p "$5"\ntouch "$5/oh-my-zsh.sh"\n'
            'printf "ohmyzsh\\n" >> "$TEST_CALLS"',
        )
        self.fake_command("npm", r'''
mkdir -p "$HOME/.local/lib/node_modules/context-mode"
printf '{"name":"context-mode","version":"%s","type":"module"}\n' "$TEST_CONTEXT_VERSION" > "$HOME/.local/lib/node_modules/context-mode/package.json"
cat > "$HOME/.local/lib/node_modules/context-mode/cli.mjs" <<'NODE'
import fs from "node:fs";
fs.appendFileSync(process.env.TEST_CALLS, "context-setup\n");
NODE
printf "npm\n" >> "$TEST_CALLS"
''')
        self.fake_command(
            "omp",
            'case "$*" in\n'
            '  "plugin install "*) printf "omp-install\\n" >> "$TEST_CALLS" ;;\n'
            '  "plugin doctor") printf "omp-doctor\\n" >> "$TEST_CALLS" ;;\n'
            "  *) exit 25 ;;\n"
            "esac",
        )
        self.assert_success(self.chez("apply", source=source))
        first = calls.read_text().splitlines()
        self.assertEqual(first, [
            "brew", "mise", "uv", "ohmyzsh", "npm", "codex-marketplace",
            "codex-add", "context-setup", "omp-install", "rtk-codex",
            "codex-trust", "rtk-omp", "omp-doctor",
        ])
        self.assert_success(self.chez("apply", source=source))
        self.assertEqual(calls.read_text().splitlines(), first)
        manifest = source / "home/dot_Brewfile"
        manifest.write_text(manifest.read_text() + '\nbrew "tree"\n')
        self.assert_success(self.chez("apply", source=source))
        self.assertEqual(calls.read_text().splitlines(), first + ["brew", "mise", "uv"])


if __name__ == "__main__":
    unittest.main()

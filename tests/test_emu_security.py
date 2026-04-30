import ast
import os

import pytest

yaml = pytest.importorskip("yaml")

PLUGIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REQUIREMENTS_PATH = os.path.join(PLUGIN_DIR, 'requirements.txt')
HOOK_PATH = os.path.join(PLUGIN_DIR, 'hook.py')
CONF_DIR = os.path.join(PLUGIN_DIR, 'conf')
DATA_DIR = os.path.join(PLUGIN_DIR, 'data')


class TestRequirementsSecurity:
    """Test that requirements.txt documents known CVE risks."""

    def test_pyminizip_has_cve_warning_comment(self):
        """pyminizip has known CVEs; requirements.txt should document this.

        pyminizip uses zlib and has had vulnerabilities reported. A comment
        in requirements.txt should warn maintainers about this risk so it
        is not overlooked during dependency reviews.
        """
        with open(REQUIREMENTS_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify pyminizip is listed
        assert 'pyminizip' in content, (
            "pyminizip not found in requirements.txt"
        )

        # Check for a CVE-related comment near the pyminizip line
        lines = content.splitlines()
        found_cve_comment = False
        for i, line in enumerate(lines):
            if 'pyminizip' in line.lower():
                # Check this line and surrounding lines for CVE warning
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 3)
                context = '\n'.join(lines[context_start:context_end])
                if 'cve' in context.lower() or 'vulnerab' in context.lower():
                    found_cve_comment = True
                    break
        assert found_cve_comment, (
            "requirements.txt should have a comment warning about known "
            "CVEs for pyminizip (e.g., '# WARNING: pyminizip has known "
            "CVE vulnerabilities')"
        )


class TestHookParseable:
    """Verify that hook.py is syntactically valid."""

    def test_hook_file_exists(self):
        """hook.py must exist as the plugin entry point."""
        assert os.path.isfile(HOOK_PATH), (
            f"hook.py not found at {HOOK_PATH}"
        )

    def test_hook_can_be_parsed(self):
        """hook.py should be valid Python parseable by ast.parse."""
        with open(HOOK_PATH, 'r', encoding='utf-8') as f:
            source = f.read()
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"hook.py has a syntax error: {e}")
        assert tree is not None

    def test_hook_defines_enable_function(self):
        """hook.py must define an async 'enable' function."""
        with open(HOOK_PATH, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        enable_funcs = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef) and node.name == 'enable'
        ]
        assert len(enable_funcs) > 0, (
            "hook.py must define an 'async def enable(...)' function"
        )

    def test_hook_defines_plugin_name(self):
        """hook.py should define a 'name' variable."""
        with open(HOOK_PATH, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        name_assignments = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == 'name'
                for target in node.targets
            )
        ]
        assert len(name_assignments) > 0, (
            "hook.py should define a 'name' variable for the plugin"
        )


class TestAbilitiesYAML:
    """Validate YAML configuration files are well-formed."""

    def _get_yaml_files(self, directory):
        """Recursively collect all YAML files from a directory."""
        yaml_files = []
        if not os.path.isdir(directory):
            return yaml_files
        for root, _dirs, files in os.walk(directory):
            for fname in files:
                if fname.endswith('.yml') or fname.endswith('.yaml'):
                    yaml_files.append(os.path.join(root, fname))
        return sorted(yaml_files)

    def test_conf_yaml_files_are_valid(self):
        """All YAML files in conf/ should be parseable."""
        yaml_files = self._get_yaml_files(CONF_DIR)
        assert len(yaml_files) > 0, (
            f"No YAML files found in {CONF_DIR}"
        )
        for fpath in yaml_files:
            with open(fpath, 'r', encoding='utf-8') as f:
                try:
                    data = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Failed to parse {fpath}: {e}")
                assert data is not None, (
                    f"YAML file is empty: {fpath}"
                )

    def test_data_yaml_files_are_valid_if_present(self):
        """If data/ contains YAML files (post-setup), they should be parseable."""
        yaml_files = self._get_yaml_files(DATA_DIR)
        if not yaml_files:
            pytest.skip(
                "No YAML files in data/ — run plugin setup to populate"
            )
        for fpath in yaml_files:
            with open(fpath, 'r', encoding='utf-8') as f:
                try:
                    data = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Failed to parse {fpath}: {e}")
                assert data is not None, (
                    f"YAML file is empty: {fpath}"
                )

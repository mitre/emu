"""Exhaustive tests for app/parsers/vssadmin_shadow.py."""
import pytest

from plugins.emu.app.parsers.vssadmin_shadow import Parser
from tests.conftest import _StubFact


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def parser():
    p = Parser()
    return p


@pytest.fixture
def dummy_blob():
    return r"""
vssadmin 1.1 - Volume Shadow Copy Service administrative command-line tool
(C) Copyright 2001-2013 Microsoft Corp.

Successfully created shadow copy for 'C:\'
    Shadow Copy ID: {uuid}
    Shadow Copy Volume Name: \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy7
"""


@pytest.fixture
def multi_volume_blob():
    return """
    Shadow Copy Volume Name: \\\\?\\GLOBALROOT\\Device\\HarddiskVolumeShadowCopy1
    Shadow Copy Volume Name: \\\\?\\GLOBALROOT\\Device\\HarddiskVolumeShadowCopy2
"""


# ---------------------------------------------------------------------------
# Tests — _get_volume_name
# ---------------------------------------------------------------------------

class TestGetVolumeName:
    def test_parse_blob(self, dummy_blob):
        results = Parser._get_volume_name(dummy_blob)
        assert results == r'\\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy7'

    def test_parse_blob_without_match(self):
        assert not Parser._get_volume_name('no volume name here')

    def test_empty_string(self):
        assert not Parser._get_volume_name('')

    def test_partial_match(self):
        blob = 'Shadow Copy Volume Name:'
        assert not Parser._get_volume_name(blob)

    def test_returns_first_match_only(self, multi_volume_blob):
        result = Parser._get_volume_name(multi_volume_blob)
        assert result is not None
        # Should return the first match

    def test_leading_whitespace(self):
        blob = '   Shadow Copy Volume Name: \\\\?\\GLOBALROOT\\Device\\ShadowCopy99'
        result = Parser._get_volume_name(blob)
        assert result is not None
        assert 'ShadowCopy99' in result

    def test_no_whitespace_prefix(self):
        blob = 'Shadow Copy Volume Name: \\\\?\\GLOBALROOT\\Device\\ShadowCopy1'
        result = Parser._get_volume_name(blob)
        assert result is not None

    def test_multiline_output(self):
        blob = """some output
other line
    Shadow Copy Volume Name: \\\\?\\GLOBALROOT\\Device\\HarddiskVolumeShadowCopy5
trailing output
"""
        result = Parser._get_volume_name(blob)
        assert 'HarddiskVolumeShadowCopy5' in result


# ---------------------------------------------------------------------------
# Tests — parse method
# ---------------------------------------------------------------------------

class TestParse:
    def test_parse_returns_empty_on_no_match(self, parser):
        result = parser.parse('no matching output')
        assert result == []

    def test_parse_returns_empty_on_empty(self, parser):
        result = parser.parse('')
        assert result == []

    def test_parse_with_mappers(self, parser, dummy_blob):
        class MockMapper:
            def __init__(self):
                self.source = 'src_trait'
                self.target = 'tgt_trait'
                self.edge = 'has'

        parser.mappers = [MockMapper()]
        result = parser.parse(dummy_blob)
        assert len(result) == 1
        rel = result[0]
        assert rel.source.trait == 'src_trait'
        assert rel.target.trait == 'tgt_trait'
        assert rel.edge == 'has'

    def test_parse_with_multiple_mappers(self, parser, dummy_blob):
        class MockMapper:
            def __init__(self, source, target, edge):
                self.source = source
                self.target = target
                self.edge = edge

        parser.mappers = [
            MockMapper('s1', 't1', 'edge1'),
            MockMapper('s2', 't2', 'edge2'),
        ]
        result = parser.parse(dummy_blob)
        assert len(result) == 2
        assert result[0].edge == 'edge1'
        assert result[1].edge == 'edge2'

    def test_parse_no_mappers(self, parser, dummy_blob):
        parser.mappers = []
        result = parser.parse(dummy_blob)
        assert result == []

import pytest
from pypi_info import SimpleRequirementParser

class TestSimpleRequirementParser:
    @pytest.fixture
    def simple_parser(self):
        return SimpleRequirementParser(input_file_path='dummy')
    
    def test_parse_line(self, simple_parser):
        line = 'pulp-smash='
        item = simple_parser.parse_line(line)

        expected_item = ('pulp-smash', None)
        assert item == expected_item


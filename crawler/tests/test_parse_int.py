"""
Tests for parse_int utility function (optimized version with 万/亿 support)
"""
import pytest
from novel_crawler.spiders.base import parse_int


class TestParseInt:
    def test_extracts_simple_number(self):
        assert parse_int("123") == 123

    def test_handles_wan_without_decimal(self):
        """"100万" -> 100 * 10000 = 1000000"""
        assert parse_int("100万") == 1_000_000
        assert parse_int("495万") == 4_950_000

    def test_handles_wan_with_decimal(self):
        """优化版: "1.2万" -> 12000, "3.6万" -> 36000"""
        assert parse_int("1.2万") == 12_000
        assert parse_int("3.6万") == 36_000
        assert parse_int("0.5万") == 5_000

    def test_handles_yi(self):
        assert parse_int("1.5亿") == 150_000_000
        assert parse_int("2亿") == 200_000_000
        assert parse_int("0.3亿") == 30_000_000

    def test_handles_qian(self):
        assert parse_int("5千") == 5_000
        assert parse_int("1.5千") == 1_500

    def test_handles_comma_thousands(self):
        assert parse_int("1,234,567") == 1234567
        assert parse_int("3,456") == 3456

    def test_returns_zero_for_empty(self):
        assert parse_int("") == 0
        assert parse_int(None) == 0

    def test_returns_zero_for_no_digit(self):
        assert parse_int("abc") == 0
        assert parse_int("--") == 0
        assert parse_int("万") == 0
        assert parse_int("亿") == 0

    def test_extracts_first_from_mixed(self):
        assert parse_int("view: 1234") == 1234

    def test_handles_spaces(self):
        assert parse_int("  100  ") == 100

    def test_handles_plus_prefix(self):
        assert parse_int("+100") == 100

    def test_handles_wan_with_tail(self):
        """"1.2万 收藏" -> 12000"""
        assert parse_int("1.2万 收藏") == 12_000

    def test_handles_combined(self):
        """混用单位: "1亿2000万" -> 120000000"""
        assert parse_int("1亿2000万") == 120_000_000

    def test_handles_large_number(self):
        assert parse_int("999999999") == 999_999_999

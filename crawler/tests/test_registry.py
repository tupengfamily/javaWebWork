"""
Tests for the spider registry / loader
"""
import pytest

from novel_crawler.spiders.registry import SITE_TO_SPIDER, load_spider_class


class TestSiteRegistry:
    def test_contains_all_known_sites(self):
        assert "qidian" in SITE_TO_SPIDER
        assert "fanqie" in SITE_TO_SPIDER
        assert "zongheng" in SITE_TO_SPIDER

    def test_class_paths_are_valid_format(self):
        """每个 class path 形如 'module.path.ClassName'"""
        for code, path in SITE_TO_SPIDER.items():
            assert path.count(".") >= 2, f"invalid path for {code}: {path}"
            assert path.split(".")[-1].endswith("Spider")

    def test_load_unknown_site_raises(self):
        with pytest.raises(ValueError, match="unknown site"):
            load_spider_class("not_exists_xxx")

    def test_load_known_site_returns_class(self):
        cls = load_spider_class("qidian")
        assert cls is not None
        assert cls.__name__ == "QidianSpider"

    def test_loaded_spider_has_required_attrs(self):
        cls = load_spider_class("qidian")
        assert hasattr(cls, "site_code")
        assert hasattr(cls, "name")
        assert hasattr(cls, "start_requests")
        assert hasattr(cls, "parse")
        assert cls.site_code == "qidian"
        assert cls.name == "qidian"

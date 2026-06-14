"""
Tests for BaseSpider and its make_novel / make_ranking helpers
"""
import pytest

from novel_crawler.spiders.base import BaseSpider
from novel_crawler.items import NovelData, RankingData


class ConcreteSpider(BaseSpider):
    """Minimal concrete subclass for testing base class behavior"""
    site_code = "test"
    name = "test"

    def start_requests(self):
        return iter([])

    def parse(self, response):
        return iter([])


class TestBaseSpider:
    def setup_method(self):
        self.spider = ConcreteSpider()
        self.spider.task_id = 42
        self.spider.ranking_type = "monthly"
        self.spider.category = "xuanhuan"

    def test_make_novel_fills_site_code(self):
        n = self.spider.make_novel(
            external_id="1", title="T", author="A", novel_url="u"
        )
        assert isinstance(n, NovelData)
        assert n.site_code == "test"

    def test_make_ranking_fills_all_inherited(self):
        r = self.spider.make_ranking(
            novel_external_id="1", rank=3, view_count=100, rec_count=10
        )
        assert isinstance(r, RankingData)
        assert r.site_code == "test"
        assert r.ranking_type == "monthly"
        assert r.category == "xuanhuan"

    def test_subclass_defaults(self):
        # ConcreteSpider sets site_code via class attribute
        assert self.spider.site_code == "test"
        assert self.spider.name == "test"

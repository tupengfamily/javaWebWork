"""
Tests for NovelData and RankingData dataclasses
"""
import pytest

from novel_crawler.items import NovelData, RankingData


class TestNovelData:
    def test_minimal_construction(self):
        n = NovelData(external_id="12345", site_code="qidian",
                      title="Test", author="Author", novel_url="https://x")
        assert n.external_id == "12345"
        assert n.site_code == "qidian"
        assert n.title == "Test"
        assert n.author == "Author"
        assert n.novel_url == "https://x"
        # defaults
        assert n.category == ""
        assert n.cover_url == ""
        assert n.word_count == 0
        assert n.status == "ongoing"

    def test_full_construction(self):
        n = NovelData(
            external_id="1", site_code="qd", title="T", author="A",
            novel_url="u", category="xuanhuan", cover_url="c",
            word_count=100, status="completed"
        )
        assert n.category == "xuanhuan"
        assert n.word_count == 100
        assert n.status == "completed"

    def test_to_dict_serialization(self):
        n = NovelData(external_id="1", site_code="x",
                      title="T", author="A", novel_url="u")
        d = n.to_dict()
        assert isinstance(d, dict)
        assert d["external_id"] == "1"
        assert d["title"] == "T"
        assert d["word_count"] == 0
        assert d["status"] == "ongoing"


class TestRankingData:
    def test_minimal_construction_auto_crawl_time(self):
        r = RankingData(novel_external_id="1", site_code="x",
                        ranking_type="daily", rank=1)
        assert r.novel_external_id == "1"
        assert r.site_code == "x"
        assert r.ranking_type == "daily"
        assert r.rank == 1
        # auto-generated crawl_time should be ISO-8601 string
        assert isinstance(r.crawl_time, str)
        assert "T" in r.crawl_time  # ISO format

    def test_full_construction(self):
        r = RankingData(
            novel_external_id="1", site_code="qd",
            ranking_type="monthly", category="xuanhuan",
            rank=5, view_count=100000, rec_count=500
        )
        assert r.category == "xuanhuan"
        assert r.view_count == 100000
        assert r.rec_count == 500

    def test_to_dict(self):
        r = RankingData(novel_external_id="1", site_code="x",
                        ranking_type="daily", rank=1)
        d = r.to_dict()
        assert d["rank"] == 1
        assert d["view_count"] == 0
        assert "crawl_time" in d

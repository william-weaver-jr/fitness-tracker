"""Unit tests for pagination helpers."""

from __future__ import annotations

import pytest

from fittrack.api.pagination import Page, Paginated


@pytest.mark.unit
class TestPage:
    def test_defaults(self) -> None:
        p = Page()
        assert p.page == 1
        assert p.limit == 20

    def test_custom_values(self) -> None:
        p = Page(page=3, limit=50)
        assert p.page == 3
        assert p.limit == 50

    def test_offset_property(self) -> None:
        p = Page(page=1, limit=20)
        assert p.offset == 0

        p2 = Page(page=2, limit=20)
        assert p2.offset == 20

        p3 = Page(page=5, limit=10)
        assert p3.offset == 40

    def test_page_must_be_positive(self) -> None:
        with pytest.raises(Exception):
            Page(page=0)

        with pytest.raises(Exception):
            Page(page=-1)

    def test_limit_max_100(self) -> None:
        with pytest.raises(Exception):
            Page(limit=101)

    def test_limit_min_1(self) -> None:
        with pytest.raises(Exception):
            Page(limit=0)


@pytest.mark.unit
class TestPaginated:
    def test_basic_construction(self) -> None:
        result: Paginated[int] = Paginated(
            items=[1, 2, 3],
            total=10,
            page=1,
            limit=3,
        )
        assert result.items == [1, 2, 3]
        assert result.total == 10
        assert result.page == 1
        assert result.limit == 3

    def test_pages_property(self) -> None:
        result: Paginated[str] = Paginated(items=[], total=95, page=1, limit=20)
        assert result.pages == 5  # ceil(95/20)

    def test_pages_exact_division(self) -> None:
        result: Paginated[str] = Paginated(items=[], total=100, page=1, limit=20)
        assert result.pages == 5

    def test_pages_zero_total(self) -> None:
        result: Paginated[str] = Paginated(items=[], total=0, page=1, limit=20)
        assert result.pages == 0

    def test_has_next(self) -> None:
        result: Paginated[int] = Paginated(items=[], total=50, page=1, limit=20)
        assert result.has_next is True

    def test_no_next_on_last_page(self) -> None:
        result: Paginated[int] = Paginated(items=[], total=40, page=2, limit=20)
        assert result.has_next is False

    def test_has_prev(self) -> None:
        result: Paginated[int] = Paginated(items=[], total=50, page=2, limit=20)
        assert result.has_prev is True

    def test_no_prev_on_first_page(self) -> None:
        result: Paginated[int] = Paginated(items=[], total=50, page=1, limit=20)
        assert result.has_prev is False

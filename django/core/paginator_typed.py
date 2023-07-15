import collections.abc
import inspect
import warnings
from math import ceil
from typing import Any, Dict, Generator, List, Optional, Union

from django.utils.functional import cached_property
from django.utils.inspect import method_has_no_args
from django.utils.translation import gettext_lazy as _


class UnorderedObjectListWarning(RuntimeWarning):
    pass


class InvalidPage(Exception):
    pass


class PageNotAnInteger(InvalidPage):
    pass


class EmptyPage(InvalidPage):
    pass


class Paginator:
    ELLIPSIS = _("…")
    default_error_messages: Dict[str, str] = {
        "invalid_page": _("That page number is not an integer"),
        "min_page": _("That page number is less than 1"),
        "no_results": _("That page contains no results"),
    }

    def __init__(
        self,
        object_list: Union[collections.abc.Sequence, collections.abc.Set],
        per_page: int,
        orphans: int = 0,
        allow_empty_first_page: bool = True,
        error_messages: Optional[Dict[str, str]] = None,
    ) -> None:
        self.object_list = object_list
        self._check_object_list_is_ordered()
        self.per_page = int(per_page)
        self.orphans = int(orphans)
        self.allow_empty_first_page = allow_empty_first_page
        self.error_messages = (
            self.default_error_messages
            if error_messages is None
            else self.default_error_messages | error_messages
        )

    def __iter__(self) -> Generator["Page", None, None]:
        for page_number in self.page_range:
            yield self.page(page_number)

    def validate_number(self, number: Union[int, float]) -> int:
        try:
            if isinstance(number, float) and not number.is_integer():
                raise ValueError
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger(self.error_messages["invalid_page"])
        if number < 1:
            raise EmptyPage(self.error_messages["min_page"])
        if number > self.num_pages:
            raise EmptyPage(self.error_messages["no_results"])
        return number

    def get_page(self, number: Union[int, float]) -> "Page":
        try:
            number = self.validate_number(number)
        except PageNotAnInteger:
            number = 1
        except EmptyPage:
            number = self.num_pages
        return self.page(number)

    def page(self, number: Union[int, float]) -> "Page":
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return self._get_page(self.object_list[bottom:top], number, self)

    def _get_page(self, *args: Any, **kwargs: Any) -> "Page":
        return Page(*args, **kwargs)

    @cached_property
    def count(self) -> int:
        c = getattr(self.object_list, "count", None)
        if callable(c) and not inspect.isbuiltin(c) and method_has_no_args(c):
            return c()
        return len(self.object_list)

    @cached_property
    def num_pages(self) -> int:
        if self.count == 0 and not self.allow_empty_first_page:
            return 0
        hits = max(1, self.count - self.orphans)
        return ceil(hits / self.per_page)

    @property
    def page_range(self) -> range:
        return range(1, self.num_pages + 1)

    def _check_object_list_is_ordered(self) -> None:
        ordered = getattr(self.object_list, "ordered", None)
        if ordered is not None and not ordered:
            obj_list_repr = (
                "{} {}".format(
                    self.object_list.model, self.object_list.__class__.__name__
                )
                if hasattr(self.object_list, "model")
                else "{!r}".format(self.object_list)
            )
            warnings.warn(
                "Pagination may yield inconsistent results with an unordered "
                "object_list: {}.".format(obj_list_repr),
                UnorderedObjectListWarning,
                stacklevel=3,
            )

    def get_elided_page_range(
        self, number: int = 1, on_each_side: int = 3, on_ends: int = 2
    ) -> Generator[Union[int, str], None, None]:
        number = self.validate_number(number)

        if self.num_pages <= (on_each_side + on_ends) * 2:
            yield from self.page_range
            return

        if number > (1 + on_each_side + on_ends) + 1:
            yield from range(1, on_ends + 1)
            yield self.ELLIPSIS
            yield from range(number - on_each_side, number + 1)
        else:
            yield from range(1, number + 1)

        if number < (self.num_pages - on_each_side - on_ends) - 1:
            yield from range(number + 1, number + on_each_side + 1)
            yield self.ELLIPSIS
            yield from range(self.num_pages - on_ends + 1, self.num_pages + 1)
        else:
            yield from range(number + 1, self.num_pages + 1)


class Page(collections.abc.Sequence):
    def __init__(
        self,
        object_list: Union[collections.abc.Sequence, collections.abc.Set],
        number: int,
        paginator: Paginator,
    ) -> None:
        self.object_list = object_list
        self.number = number
        self.paginator = paginator

    def __repr__(self) -> str:
        return f"<Page {self.number} of {self.paginator.num_pages}>"

    def __len__(self) -> int:
        return len(self.object_list)

    def __getitem__(self, index: Union[int, slice]) -> Any:
        if not isinstance(index, (int, slice)):
            raise TypeError(
                "Page indices must be integers or slices, not %s."
                % type(index).__name__
            )
        if not isinstance(self.object_list, list):
            self.object_list = list(self.object_list)
        return self.object_list[index]

    def has_next(self) -> bool:
        return self.number < self.paginator.num_pages

    def has_previous(self) -> bool:
        return self.number > 1

    def has_other_pages(self) -> bool:
        return self.has_previous() or self.has_next()

    def next_page_number(self) -> int:
        return self.paginator.validate_number(self.number + 1)

    def previous_page_number(self) -> int:
        return self.paginator.validate_number(self.number - 1)

    def start_index(self) -> int:
        if self.paginator.count == 0:
            return 0
        return (self.paginator.per_page * (self.number - 1)) + 1

    def end_index(self) -> int:
        if self.number == self.paginator.num_pages:
            return self.paginator.count
        return self.number * self.paginator.per_page

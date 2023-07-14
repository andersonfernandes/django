import copy
from collections.abc import Mapping, Iterable, Iterator
from typing import Any, Dict, List, Optional, Tuple


class OrderedSet:
    def __init__(self, iterable: Optional[Iterable] = None) -> None:
        self.dict: Dict[Any, None] = dict.fromkeys(iterable or ())

    def add(self, item: Any) -> None:
        self.dict[item] = None

    def remove(self, item: Any) -> None:
        del self.dict[item]

    def discard(self, item: Any) -> None:
        try:
            self.remove(item)
        except KeyError:
            pass

    def __iter__(self) -> Iterator:
        return iter(self.dict)

    def __reversed__(self) -> Iterator:
        return reversed(self.dict)

    def __contains__(self, item: Any) -> bool:
        return item in self.dict

    def __bool__(self) -> bool:
        return bool(self.dict)

    def __len__(self) -> int:
        return len(self.dict)

    def __repr__(self) -> str:
        data = repr(list(self.dict)) if self.dict else ""
        return f"{self.__class__.__qualname__}({data})"


class MultiValueDictKeyError(KeyError):
    pass


class MultiValueDict(dict):
    def __init__(self, key_to_list_mapping: Optional[Dict] = None) -> None:
        super().__init__(key_to_list_mapping)

    def __repr__(self) -> str:
        return "<%s: %s>" % (self.__class__.__name__, super().__repr__())

    def __getitem__(self, key: str) -> Any:
        try:
            list_ = super().__getitem__(key)
        except KeyError:
            raise MultiValueDictKeyError(key)
        try:
            return list_[-1]
        except IndexError:
            return []

    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key, [value])

    def __copy__(self) -> 'MultiValueDict':
        return self.__class__([(k, v[:]) for k, v in self.lists()])

    def __deepcopy__(self, memo: Dict[int, Any]) -> 'MultiValueDict':
        result = self.__class__()
        memo[id(self)] = result
        for key, value in dict.items(self):
            dict.__setitem__(
                result, copy.deepcopy(key, memo), copy.deepcopy(value, memo)
            )
        return result

    def __getstate__(self) -> Dict[str, Any]:
        return {**self.__dict__, "_data": {k: self._getlist(k) for k in self}}

    def __setstate__(self, obj_dict: Dict[str, Any]) -> None:
        data = obj_dict.pop("_data", {})
        for k, v in data.items():
            self.setlist(k, v)
        self.__dict__.update(obj_dict)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        try:
            val = self[key]
        except KeyError:
            return default
        if val == []:
            return default
        return val

    def _getlist(
        self, key: str, default: Optional[Any] = None, force_list: bool = False
    ) -> Any:
        try:
            values = super().__getitem__(key)
        except KeyError:
            if default is None:
                return []
            return default
        else:
            if force_list:
                values = list(values) if values is not None else None
            return values

    def getlist(self, key: str, default: Optional[Any] = None) -> List[Any]:
        return self._getlist(key, default, force_list=True)

    def setlist(self, key: str, list_: List[Any]) -> None:
        super().__setitem__(key, list_)

    def setdefault(self, key: str, default: Optional[Any] = None) -> Any:
        if key not in self:
            self[key] = default
        return self[key]

    def setlistdefault(
        self, key: str, default_list: Optional[List[Any]] = None
    ) -> List[Any]:
        if key not in self:
            if default_list is None:
                default_list = []
            self.setlist(key, default_list)
        return self._getlist(key)

    def appendlist(self, key: str, value: Any) -> None:
        self.setlistdefault(key).append(value)

    def items(self) -> Iterator[Tuple[str, Any]]:
        for key in self:
            yield key, self[key]

    def lists(self) -> Iterator[Tuple[str, List[Any]]]:
        return iter(super().items())

    def values(self) -> Iterator[Any]:
        for key in self:
            yield self[key]

    def copy(self) -> 'MultiValueDict':
        return copy.copy(self)

    def update(self, *args: Any, **kwargs: Any) -> None:
        if len(args) > 1:
            raise TypeError("update expected at most 1 argument, got %d" % len(args))
        if args:
            arg = args[0]
            if isinstance(arg, MultiValueDict):
                for key, value_list in arg.lists():
                    self.setlistdefault(key).extend(value_list)
            else:
                if isinstance(arg, Mapping):
                    arg = arg.items()
                for key, value in arg:
                    self.setlistdefault(key).append(value)
        for key, value in kwargs.items():
            self.setlistdefault(key).append(value)

    def dict(self) -> Dict[str, Any]:
        return {key: self[key] for key in self}


class ImmutableList(tuple):
    def __new__(
        cls, *args: Any, warning: str = "ImmutableList object is immutable.", **kwargs: Any
    ) -> 'ImmutableList':
        self = tuple.__new__(cls, *args, **kwargs)
        self.warning = warning
        return self

    def complain(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError(self.warning)

    __delitem__ = complain
    __delslice__ = complain
    __iadd__ = complain
    __imul__ = complain
    __setitem__ = complain
    __setslice__ = complain
    append = complain
    extend = complain
    insert = complain
    pop = complain
    remove = complain
    sort = complain
    reverse = complain


class DictWrapper(dict):
    def __init__(self, data: Dict, func: Any, prefix: str) -> None:
        super().__init__(data)
        self.func = func
        self.prefix = prefix

    def __getitem__(self, key: str) -> Any:
        use_func = key.startswith(self.prefix)
        key = key.removeprefix(self.prefix)
        value = super().__getitem__(key)
        if use_func:
            return self.func(value)
        return value


class CaseInsensitiveMapping(Mapping):
    def __init__(self, data: Any) -> None:
        self._store = {k.lower(): (k, v) for k, v in self._unpack_items(data)}

    def __getitem__(self, key: str) -> Any:
        return self._store[key.lower()][1]

    def __len__(self) -> int:
        return len(self._store)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Mapping) and {
            k.lower(): v for k, v in self.items()
        } == {k.lower(): v for k, v in other.items()}

    def __iter__(self) -> Iterator[str]:
        return (original_key for original_key, value in self._store.values())

    def __repr__(self) -> str:
        return repr({key: value for key, value in self._store.values()})

    def copy(self) -> 'CaseInsensitiveMapping':
        return self

    @staticmethod
    def _unpack_items(data: Any) -> Iterator[Tuple[str, Any]]:
        if isinstance(data, (dict, Mapping)):
            yield from data.items()
            return
        for i, elem in enumerate(data):
            if len(elem) != 2:
                raise ValueError(
                    "dictionary update sequence element #{} has length {}; "
                    "2 is required.".format(i, len(elem))
                )
            if not isinstance(elem[0], str):
                raise ValueError(
                    "Element key %r invalid, only strings are allowed" % elem[0]
                )
            yield elem

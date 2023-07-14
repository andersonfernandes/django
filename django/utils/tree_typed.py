"""
A class for storing a tree graph. Primarily used for filter constructs in the
ORM.
"""

import copy

from typing import List, Optional

from django.utils.hashable import make_hashable


class Node:
    default: str = "DEFAULT"

    def __init__(
        self,
        children: Optional[List['Node']] = None,
        connector: Optional[str] = None,
        negated: bool = False,
    ) -> None:
        self.children = children[:] if children else []
        self.connector = connector or self.default
        self.negated = negated

    @classmethod
    def create(
        cls,
        children: Optional[List['Node']] = None,
        connector: Optional[str] = None,
        negated: bool = False,
    ) -> 'Node':
        obj = Node(children, connector or cls.default, negated)
        obj.__class__ = cls
        return obj

    def __str__(self) -> str:
        template = "(NOT (%s: %s))" if self.negated else "(%s: %s)"
        return template % (self.connector, ", ".join(str(c) for c in self.children))

    def __repr__(self) -> str:
        return "<%s: %s>" % (self.__class__.__name__, self)

    def __copy__(self) -> 'Node':
        obj = self.create(connector=self.connector, negated=self.negated)
        obj.children = self.children
        return obj

    copy = __copy__

    def __deepcopy__(self, memodict) -> 'Node':
        obj = self.create(connector=self.connector, negated=self.negated)
        obj.children = copy.deepcopy(self.children, memodict)
        return obj

    def __len__(self) -> int:
        return len(self.children)

    def __bool__(self) -> bool:
        return bool(self.children)

    def __contains__(self, other: 'Node') -> bool:
        return other in self.children

    def __eq__(self, other: 'Node') -> bool:
        return (
            self.__class__ == other.__class__
            and self.connector == other.connector
            and self.negated == other.negated
            and self.children == other.children
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.__class__,
                self.connector,
                self.negated,
                *make_hashable(self.children),
            )
        )

    def add(self, data: 'Node', conn_type: str) -> 'Node':
        if self.connector != conn_type:
            obj = self.copy()
            self.connector = conn_type
            self.children = [obj, data]
            return data
        elif (
            isinstance(data, Node)
            and not data.negated
            and (data.connector == conn_type or len(data) == 1)
        ):
            self.children.extend(data.children)
            return self
        else:
            self.children.append(data)
            return data

    def negate(self) -> None:
        self.negated = not self.negated

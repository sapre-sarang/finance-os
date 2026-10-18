from collections.abc import Sequence


class StatementParseError(Exception):
    """A statement was rejected as a whole; no rows from it may be used."""

    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("; ".join(self.problems))

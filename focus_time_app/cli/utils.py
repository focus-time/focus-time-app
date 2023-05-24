import typing as t
from enum import EnumType
from gettext import ngettext

from click import Choice
from click import Context
from click import Parameter


class IntEnumChoice(Choice):
    def __init__(self, enum_type: EnumType, case_sensitive: bool = True) -> None:
        choices = [f"{value.value}: {value.name}" for value in enum_type]
        super().__init__(choices, case_sensitive)
        self._enum_type = enum_type

    def convert(
            self, value: t.Any, param: t.Optional["Parameter"], ctx: t.Optional["Context"]
    ) -> t.Any:
        try:
            return self._enum_type(int(value))
        except ValueError:
            choices_str = ", ".join(map(repr, self.choices))
            self.fail(
                ngettext(
                    "{value!r} is not {choice}.",
                    "{value!r} is not one of {choices}.",
                    len(self.choices),
                ).format(value=value, choice=choices_str, choices=choices_str),
                param,
                ctx,
            )

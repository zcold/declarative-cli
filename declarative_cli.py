"""Declarative command line interface parser
"""

import argparse
import ast
import inspect
from dataclasses import dataclass
from typing import Any, Union

from addict import Dict as AttrDict

@dataclass
class DeclarativeArgumentParser(argparse.ArgumentParser):
    """Command line options"""

    __shorts__: dict[str, Union[str, list[str]]]
    """Shortcuts for arguments, e.g.
    - `{"my_option": ["m", "y"]}`
    - `{"my_option": "y"}`
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Read data fields in `dataclass` and construct arguments."""
        super().__init__(*args, **kwargs)
        if (description := self.__class__.__doc__) and not self.description:
            self.description = description

        cls_def: ast.ClassDef = ast.parse(inspect.getsource(self.__class__)).body[0]  # type: ignore
        options = []
        shorts = AttrDict()
        for subtree in cls_def.body:
            if isinstance(subtree, (ast.AnnAssign, ast.Assign)):
                options.append(self._dap_get_option(subtree))
                if options[-1].name == "__shorts__":
                    shorts |= options[-1].default
            if not options:
                continue
            if isinstance(subtree, ast.Expr):
                if options[-1].name == "__shorts__":
                    options.pop(-1)
                    continue
                options[-1].help = subtree.value.value  # type: ignore
        for option in options:
            opt_string = [f"{self.prefix_chars}{self.prefix_chars}{option.name}"]
            opt_shorts = shorts.get(option.name, [])
            if not isinstance(opt_shorts, list):
                opt_shorts = [opt_shorts]
            opt_string += [f"{self.prefix_chars}{opt}" for opt in opt_shorts]
            action = "store"
            if option.dtype == "bool":
                if option.default == False:
                    action = "store_true"
                else:
                    action = "store_false"

            self.add_argument(*opt_string, help=option.help, action=action, default=option.default)

    def _dap_get_option(self, tree: Union[ast.AnnAssign, ast.Assign]) -> AttrDict:
        """Get option name and defaults from `tree`

        Args:
            tree (ast.AnnAssign): Subtree from class definition

        Returns:
            AttrDict: Attribute dict with `name` and optional `__default__`.
        """
        result = AttrDict()
        if isinstance(tree, ast.Assign):
            name = tree.targets[0].id  # type: ignore
        else:
            name = tree.target.id  # type: ignore
            result.dtype = tree.annotation.id  # type: ignore
        result.name = name
        if hasattr(self, name):
            result.default = getattr(self, name)
        elif tree.value is not None:
            result.default = tree.value.value  # type: ignore
        return result

    def parse_args(self, *args, **kwargs) -> AttrDict:
        """Override `parse_args` arguments to return `AttrDict`.

        Returns:
            AttrDict: Arguments
        """
        args = super().parse_args(*args, **kwargs)
        return AttrDict(vars(args))

  
# class MyParser(DeclarativeArgumentParser):
#     """Float module releasing helper"""

#     example: str = ""
#     """Example option"""

#     __shorts__ = {"example": "e"}
#     """Shortcuts of options
#     """


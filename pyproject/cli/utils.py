import re

import click
from click import Path
from click import option
from click import argument
from click import echo
from click import get_text_stream

from ..utils import namespace
from .. import settings


def short_command_name(module_name):
    """Convert a module name into a short command name."""
    tail = module_name.split('.')[-1].lower()
    name = ''.join(re.findall('(?:^|[-_])([a-z0-9])', module_name))
    return name or None


def group(*args, **kwds):
    """Automatically add @click.pass_context to groups."""
    def wrapper(fun):
        fun2 = click.pass_context(fun)
        fun3 = click.group(cls=AliasedGroup, *args, **kwds)(fun2)
        return fun3
    return wrapper


def command(*args, **kwds):
    """Automatically add @click.pass_context to commands."""
    def wrapper(fun):
        fun2 = click.pass_context(fun)
        fun3 = click.command(*args, **kwds)(fun2)
        return fun3
    return wrapper


class AliasedGroup(click.Group):
    """Automatically redirect calls like rlc -> really-long-command."""

    def get_command(self, ctx, name):
        # See if user called `really-long-command`.
        command = click.Group.get_command(self, ctx, name)
        if command is not None:
            return command

        commands = self.list_commands(ctx)

        # See if user called `re` instead of `really-long-command`.
        for c in commands:
            if c.startswith(name):
                command = click.Group.get_command(self, ctx, c)
                if command is not None:
                    return command

        # See if user called `rlc` instead of `really-long-command`.
        for c in commands:
            if name == short_command_name(c):
                command = click.Group.get_command(self, ctx, c)
                if command is not None:
                    return command

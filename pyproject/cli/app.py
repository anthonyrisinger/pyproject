from . import shell
from . import utils


def main():
    """Entrypoint."""
    command(obj=utils.namespace())


@utils.group(commands={shell.command.name: shell.command})
def command(ctx):
    """The Top."""

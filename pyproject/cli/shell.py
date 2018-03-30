from . import utils


@utils.command(name='shell')
def command(ctx):
    """Open a shell and explore!"""
    from IPython import embed
    embed(banner1='\nWelcome to Shell.\n')

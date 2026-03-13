import click

@click.command()
@click.argument('name', default='World')
def hello(name):
    """Greets the given name."""
    click.echo(f"Hello, {name}!")

if __name__ == '__main__':
    hello()
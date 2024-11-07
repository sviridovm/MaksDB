import click
from vectordb.coordinator.__main__ import main as coordinator_main



@click.group()  
def cli():
    pass

@cli.command()
def start():
    coordinator_main.main()


def main():
    pass


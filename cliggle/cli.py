from __future__ import absolute_import

import click

from .helpers import download
from .helpers import get_competition_list
from .helpers import login_user
from .helpers import shorten
from .helpers import submit

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
def cliggle():
    """Cliggle: a CLI for Kaggle competitions."""
    pass


@click.command('list')
def list_competitions():
    """List the current competition titles.

    Note: we use a shortened title for ease of use. Specifically,
    we use the first word, of the full title, lower cased and stripped
    of all non-alphanumeric characters.
    """
    comps = get_competition_list()
    titles = [c['competitionTitle'] for c in comps]
    titles = '\n'.join(shorten(t) for t in titles)
    click.echo(titles)


@click.command('download')
@click.argument('title')
@click.option('-u', '--username', prompt=True, help='Kaggle username.')
@click.option('-p', '--password', prompt=True, hide_input=True, help='Kaggle password.')
def download_files(title, username, password):
    """Download the data files for a competition."""
    titles = [shorten(c['competitionTitle']) for c in get_competition_list()]
    if title not in titles:
        raise click.ClickException('Invalid title.')

    competition_url = [c['competitionUrl'] for c in get_competition_list()][titles.index(title)]
    session = login_user(username, password)
    download(competition_url, session)


@click.command('submit')
@click.argument('title')
@click.argument('filename')
@click.option('-m', '--message', help='A description of the submission.')
@click.option('-u', '--username', prompt=True, help='Kaggle username.')
@click.option('-p', '--password', prompt=True, hide_input=True, help='Kaggle password.')
def submit_predictions(title, filename, message, username, password):
    """Submit predictions for a competition."""
    titles = [shorten(c['competitionTitle']) for c in get_competition_list()]
    if title not in titles:
        raise click.ClickException('Invalid title.')

    competition_url = [c['competitionUrl'] for c in get_competition_list()][titles.index(title)]
    session = login_user(username, password)
    submit(filename, message, competition_url, session)


cliggle.add_command(submit_predictions)
cliggle.add_command(download_files)
cliggle.add_command(list_competitions)

if __name__ == '__main__':
    cliggle()

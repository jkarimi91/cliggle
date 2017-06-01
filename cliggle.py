import click
import json
import re
import requests


BASE_URL = 'https://www.kaggle.com'


def get_competition_list():
    url = '/competitions'
    pattern = r'\"competitions\":(\[.+?\])'
    return get_json(url, pattern)

def get_json(url, pattern):
    pattern = re.compile(pattern)
    response = requests.get(BASE_URL + url)
    match = re.findall(pattern, response.text)[0]
    return json.loads(match)


def shorten(title):
    word = title.split()[0]
    return ''.join(ch for ch in word.lower() if ch.isalnum())


@click.group()
def cliggle():
    """Cliggle: a CLI for Kaggle competitions."""
    pass

@click.command('list')
def list_competitions():
    comps = get_competition_list()
    titles = [c['competitionTitle'] for c in comps]
    titles = '\n'.join(shorten(t) for t in titles)
    click.echo(titles)


cliggle.add_command(list_competitions)


if __name__ == '__main__':
    cliggle()

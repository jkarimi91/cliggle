import getpass
import json
import re
import sys

import click
import requests
import tqdm

BASE_URL = 'https://www.kaggle.com'


def get_competition_list():
    url = BASE_URL + '/competitions'
    response = requests.get(url)
    pattern = r'\"competitions\":(\[.+?\])'
    return get_json(response.text, pattern)


def get_file_list(competition_url, session):
    url = BASE_URL + competition_url + '/data'
    response = session.get(url)
    pattern = r'\"files\":(\[.+?\])'
    return get_json(response.text, pattern)


def get_json(text, pattern):
    pattern = re.compile(pattern)
    match = re.findall(pattern, text)[0]
    return json.loads(match)


def shorten(title):
    word = title.split()[0]
    return ''.join(ch for ch in word.lower() if ch.isalnum())


def login_user():
    session = requests.session()
    url = BASE_URL + '/account/login'
    data = {
        'UserName': raw_input('Username: '),
        'Password': getpass.getpass('Password: ')
    }
    response = session.post(url, data=data)

    if response.url == url:
        click.echo('Incorrect username/password.')
        sys.exit(0)

    return session


def has_accepted_rules(competition_url, session):
    url = BASE_URL + competition_url
    response = session.get(url)
    pattern = r'\"hasAcceptedRules\":(true|false)'
    return get_json(response.text, pattern)


def download(competition_file, session):
    url = BASE_URL + competition_file['url']
    response = session.get(url, stream=True)
    with open(competition_file['name'], 'wb') as f:
        kwargs = {
            'total': int(response.headers['content-length']),
            'unit': 'B',
            'unit_scale': True,
            'desc': competition_file['name']
        }
        progress_bar = tqdm.tqdm(**kwargs)

        chunk_size = 10**6  # 1 MB
        content = response.iter_content(chunk_size=chunk_size)
        for chunk in content:
            progress_bar.update(len(chunk))
            f.write(chunk)
        progress_bar.close()


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


@click.command('download')
@click.argument('title')
def download_files(title):
    comps = get_competition_list()
    titles = [c['competitionTitle'] for c in comps]
    titles = map(shorten, titles)
    if title in titles:
        i = titles.index(title)
        url = [c['competitionUrl'] for c in comps][i]
        session = login_user()

        if has_accepted_rules(url, session):
            files = get_file_list(url, session)
            for f in files:
                download(f, session)
        else:
            click.echo('Accept competition rules to continue.')
    else:
        click.echo('Invalid title.')


cliggle.add_command(download_files)
cliggle.add_command(list_competitions)


if __name__ == '__main__':
    cliggle()

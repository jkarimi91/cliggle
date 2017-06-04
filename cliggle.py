import getpass
import json
import os
import re

import click
import requests
import tqdm

BASE_URL = 'https://www.kaggle.com'
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


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
        raise click.ClickException('Incorrect username/password.')

    return session


def has_accepted_rules(competition_url, session):
    url = BASE_URL + competition_url
    response = session.get(url)
    pattern = r'\"hasAcceptedRules\":(true|false)'
    return get_json(response.text, pattern)


def has_remaining_daily_submissions(competition_url, session):
    url = BASE_URL + competition_url
    response = session.get(url)
    pattern = r'"remainingDailySubmissions":(\d+)'
    return get_json(response.text, pattern) > 0


def download(competition_url, session):
    if not has_accepted_rules(competition_url, session):
        raise click.ClickException('Accept competition rules to continue.')

    for cf in get_file_list(competition_url, session):
        url = BASE_URL + cf['url']
        response = session.get(url, stream=True)
        with open(cf['name'], 'wb') as f:
            kwargs = {
                'total': int(response.headers['content-length']),
                'unit': 'B',
                'unit_scale': True,
                'desc': cf['name']
            }
            progress_bar = tqdm.tqdm(**kwargs)

            chunk_size = 10**6  # 1 MB
            content = response.iter_content(chunk_size=chunk_size)
            for chunk in content:
                progress_bar.update(len(chunk))
                f.write(chunk)
            progress_bar.close()


def submit(filename, message, competition_url, session):
    if not has_accepted_rules(competition_url, session):
        raise click.ClickException('Accept competition rules to continue.')
    if not has_remaining_daily_submissions(competition_url, session):
        raise click.ClickException('Max number of daily submissions reached. Try again later.')

    data = {
        'fileName': filename,
        'contentLength': os.path.getsize(filename),
        'lastModifiedDateUtc': os.path.getmtime(filename)
    }
    response = session.post(BASE_URL + '/blobs/inbox/submissions', data=data)

    files = {'file': (filename, open(filename, 'rb'))}
    response = session.post(BASE_URL + response.json()['createUrl'], files=files)

    data = {
        'blobFileTokens': [response.json()['token']],
        'submissionDescription': message
    }
    session.post(BASE_URL + competition_url + '/submission.json', data=data)


@click.group(context_settings=CONTEXT_SETTINGS)
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
    if title not in titles:
        raise click.ClickException('Invalid title.')

    i = titles.index(title)
    url = [c['competitionUrl'] for c in comps][i]
    session = login_user()

    download(url, session)


@click.command('submit')
@click.argument('title')
@click.argument('filename')
@click.option('-m', '--message')
def submit_predictions(title, filename, message):
    comps = get_competition_list()
    titles = [c['competitionTitle'] for c in comps]
    titles = map(shorten, titles)
    if title not in titles:
        raise click.ClickException('Invalid title.')

    i = titles.index(title)
    url = [c['competitionUrl'] for c in comps][i]
    session = login_user()

    submit(filename, message, url, session)


cliggle.add_command(submit_predictions)
cliggle.add_command(download_files)
cliggle.add_command(list_competitions)


if __name__ == '__main__':
    cliggle()

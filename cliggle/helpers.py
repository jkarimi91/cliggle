import json
import os
import re

import click
import requests
import tqdm

BASE_URL = 'https://www.kaggle.com'


def get_competition_list():
    response = requests.get(BASE_URL + '/competitions')
    pattern = r'\"competitions\":(\[.+?\])'
    return get_json(response.text, pattern)


def get_file_list(competition_url, session):
    response = session.get(BASE_URL + competition_url + '/data')
    pattern = r'\"files\":(\[.+?\])'
    return get_json(response.text, pattern)


def get_team(competition_url, session):
    response = session.get(BASE_URL + competition_url)
    pattern = r'\"team\":({.+?}),'
    return get_json(response.text, pattern)


def get_json(text, pattern):
    pattern = re.compile(pattern)
    match = re.findall(pattern, text)[0]
    return json.loads(match)


def shorten(title):
    word = title.split()[0]
    return ''.join(ch for ch in word.lower() if ch.isalnum())


def login_user(username, password):
    session = requests.session()
    url = BASE_URL + '/account/login'
    data = {
        'UserName': username,
        'Password': password
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


def remaining_daily_submissions(competition_url, session):
    url = BASE_URL + competition_url
    response = session.get(url)
    pattern = r'"remainingDailySubmissions":(\d+)'
    return get_json(response.text, pattern)


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
            with tqdm.tqdm(**kwargs) as progress_bar:
                chunk_size = 10 ** 6  # 1 MB
                content = response.iter_content(chunk_size=chunk_size)
                for chunk in content:
                    progress_bar.update(len(chunk))
                    f.write(chunk)


def submit(filename, message, competition_url, session):
    if not has_accepted_rules(competition_url, session):
        raise click.ClickException('Accept competition rules to continue.')
    if remaining_daily_submissions(competition_url, session) == 0:
        raise click.ClickException('Max number of daily submissions reached. Try again later.')

    data = {
        'fileName': filename,
        'contentLength': os.path.getsize(filename),
        'lastModifiedDateUtc': os.path.getmtime(filename)
    }
    response = session.post(BASE_URL + '/blobs/inbox/submissions', data=data)
    file_upload_url = response.json()['createUrl']

    files = {'file': (filename, open(filename, 'rb'))}
    response = session.post(BASE_URL + file_upload_url, files=files)
    blob_file_token = response.json()['token']

    # Initialize status.json aka submission status check.
    # Note: must initialize status.json before making submission.
    team_id = get_team(competition_url, session)['id']
    api_version = 1
    submission_id = 'null'
    competition_id = [c for c in get_competition_list() if c['competitionUrl'] == competition_url][0]['competitionId']
    all_submissions_url = '{}/c/{}//submissions.json?sortBy=date&group=all&page=1'.format(BASE_URL, competition_id)
    last_submission_id = session.get(all_submissions_url).json()[0]['id']
    status_url_str = '{}{}/submissions/status.json?apiVersion={}&teamId={}&submissionId={}&greaterThanSubmissionId={}'
    status_url = status_url_str.format(BASE_URL, competition_url, api_version,
                                       team_id, submission_id, last_submission_id)
    session.get(status_url)

    data = {
        'blobFileTokens': [blob_file_token],
        'submissionDescription': message
    }
    session.post(BASE_URL + competition_url + '/submission.json', data=data)

    response = session.get(status_url)
    submission_id = response.json()['id']
    status_url = status_url_str.format(BASE_URL, competition_url, api_version,
                                       team_id, submission_id, last_submission_id)
    response = session.get(status_url)
    while response.json()['submissionStatus'] == 'pending':
        response = session.get(status_url)
    click.echo('Submission {}.'.format(response.json()['submissionStatus']))

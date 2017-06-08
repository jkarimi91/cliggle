import os

from click.testing import CliRunner

from cliggle.cli import cliggle
from credentials import PASSWORD
from credentials import USERNAME


os.chdir(os.path.dirname(__file__))


class TestList(object):
    def test_output(self):
        runner = CliRunner()
        result = runner.invoke(cliggle, args=['list'])
        assert result.exception is None
        assert 'digit' in result.output


class TestDownload(object):
    def test_incorrect_login(self):
        runner = CliRunner()
        result = runner.invoke(cliggle, args=['download', 'titanic', '-u foo', '-p bar'])
        assert result.exception is not None
        assert 'Incorrect username/password.' in result.output

    def test_invalid_title(self):
        runner = CliRunner()
        result = runner.invoke(cliggle, args=['download', 'foobar', '-u foo', '-p bar'])
        assert result.exception is not None
        assert 'Invalid title.' in result.output

    def test_not_accepted_rules(self):
        runner = CliRunner()
        result = runner.invoke(cliggle, args=['download', 'titanic'], input='\n'.join([USERNAME, PASSWORD]))
        assert result.exception is not None
        assert 'Accept competition rules to continue.' in result.output

    def test_successful_download(self):
        runner = CliRunner()
        result = runner.invoke(cliggle, args=['download', 'digit'], input='\n'.join([USERNAME, PASSWORD]))
        assert result.exception is None
        assert os.path.isfile('train.csv')
        assert os.path.getsize('train.csv') == 76775041

        files = ['sample_submission.csv', 'train.csv', 'test.csv']
        for f in files:
            os.remove(f)


class TestSubmit(object):
    def test_incorrect_login(self):
        runner = CliRunner()
        result = runner.invoke(cliggle, args=['submit', 'digit', 'foobar.txt', '-u foo', '-p bar'])
        assert result.exception is not None
        assert 'Incorrect username/password.' in result.output

    def test_invalid_title(self):
        runner = CliRunner()
        result = runner.invoke(cliggle, args=['submit', 'foobar', 'foobar.txt', '-u foo', '-p bar'])
        assert result.exception is not None
        assert 'Invalid title.' in result.output

    def test_not_accepted_rules(self):
        runner = CliRunner()
        args = ['submit', 'titanic', 'foobar.txt']
        result = runner.invoke(cliggle, args=args, input='\n'.join([USERNAME, PASSWORD]))
        assert result.exception is not None
        assert 'Accept competition rules to continue.' in result.output

    def test_no_remaining_submissions(self):
        filename = create_submission('ImageId', 'Label', (1, 28000))
        runner = CliRunner()
        args = ['submit', 'digit', filename, '-m testing cliggle']
        result = runner.invoke(cliggle, args=args, input='\n'.join([USERNAME, PASSWORD]))
        while result.exception is None:
            result = runner.invoke(cliggle, args=args, input='\n'.join([USERNAME, PASSWORD]))
        os.remove(filename)
        assert 'Max number of daily submissions reached. Try again later.' in result.output

    def test_unsuccessful_submission(self):
        filename = create_submission('ImageId', 'Label', (1, 28000))
        runner = CliRunner()
        args = ['submit', 'house', filename, '-m testing cliggle']
        result = runner.invoke(cliggle, args=args, input='\n'.join([USERNAME, PASSWORD]))
        os.remove(filename)
        assert result.exception is None
        assert 'Submission error.' in result.output

    def test_successful_submission(self):
        filename = create_submission('Id', 'SalePrice', (1461, 2919))
        runner = CliRunner()
        args = ['submit', 'house', filename, '-m testing cliggle']
        result = runner.invoke(cliggle, args=args, input='\n'.join([USERNAME, PASSWORD]))
        os.remove(filename)
        assert result.exception is None
        assert 'Submission complete.' in result.output


def create_submission(id_label, prediction_label, id_range):
    with open('submission.csv', 'wb') as f:
        f.write('{},{}\n'.format(id_label, prediction_label))
        prediction = 0
        min_id, max_id = id_range
        for data_id in xrange(min_id, max_id + 1):
            f.write('{},{}\n'.format(data_id, prediction))
    return 'submission.csv'

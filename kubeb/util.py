import json
from kubeb import file_util
from kubeb.command import Command


def run_docker_build(image, tag, path):
    command = "docker build -t {}:{} {}".format(image, tag, path)

    status, _, _ = Command(command).execute()

    return status


def run_docker_push(image, tag):
    command = "docker push {}:{}".format(image, tag)
    status, _, _ = Command(command).execute()

    return status


def run_helm_install(name, template, debug, options):
    helm_chart_path = file_util.get_helm_chart_path(template)
    command = "helm upgrade --install --force {} -f .kubeb/helm-values.yml {} --wait".format(name, helm_chart_path)

    if options:
        option_str = ','.join(['%s=%s' % (key, value) for (key, value) in options.items()])
        command += ' --set {}'.format(option_str)

    if debug:
        print(command)
        command += ' --dry-run --debug'

    status, _, _ = Command(command).execute()

    return status


def run_helm_uninstall(name):
    command = "helm delete --purge {}".format(name)
    status, _, _ = Command(command).execute()

    return status


def run_helm_history(image):
    command = "helm history {}".format(image)
    status, _, _ = Command(command).execute()

    return status


def run_helm_rollback(image, revision):
    command = "helm rollback {} {}".format(image, revision)
    status, _, _ = Command(command).execute()

    return status


def get_last_working_revision(name):
    command = "helm history {} --output json".format(name)

    exitcode, output, _ = Command(command).execute(printout=False)
    if exitcode != 0:
        return None

    revisions = json.loads(output)
    revs = [r['revision'] for r in revisions if r['status'] == 'SUPERSEDED']
    if len(revs) == 0:
        return None

    return max(revs)

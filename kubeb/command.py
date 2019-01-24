import os
import json
import subprocess
from kubeb import file_util


def run(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())

    p_status = process.wait()
    return p_status


def run2(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    output, err = process.communicate()

    return output, err


class Command(object):

    def __init__(self):
        pass

    def run_docker_build(self, image, tag, path):
        command = "docker build -t {}:{} {}".format(image, tag, path)
        return run(command)

    def run_docker_push(self, image, tag):
        command = "docker push {}:{}".format(image, tag)
        return run(command)

    def run_helm_install(self, name, template, debug, options):
        helm_chart_path = file_util.get_helm_chart_path(template)
        command = "helm upgrade --install --force {} -f .kubeb/helm-values.yml {} --wait".format(name, helm_chart_path)

        if options:
            option_str = ','.join(['%s=%s' % (key, value) for (key, value) in options.items()])
            command += ' --set {}'.format(option_str)

        if debug:
            print(command)
            command += ' --dry-run --debug'

        return run(command)

    def run_helm_uninstall(self, name):
        command = "helm delete --purge {}".format(name)
        return run(command)

    def run_helm_history(self, image):
        command = "helm history {}".format(image)
        return run(command)

    def run_helm_rollback(self, image, revision):
        command = "helm rollback {} {}".format(image, revision)
        return run(command)

    def get_last_working_revision(self, name):
        command = "helm history {} --output json".format(name)
        output, err = run2(command)

        revisions = json.loads(output)

        revs = [r['revision'] for r in revisions if r['status'] == 'SUPERSEDED']

        return max(revs)

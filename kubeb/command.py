import os
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


class Command(object):

    def __init__(self):
        pass

    def run_docker_build(self, image, tag, path):
        command = "docker build -t {}:{} {}".format(image, tag, path)
        return run(command)

    def run_docker_push(self, image, tag):
        command = "docker push {}:{}".format(image, tag)
        return run(command)

    def run_helm_install(self, name, template, debug):
        helm_chart_path = file_util.get_helm_chart_path(template)
        command = "helm upgrade --install --force {} -f .kubeb/helm-values.yml {} --wait".format(name, helm_chart_path)
        if debug:
            command += ' --dry-run --debug'
        return run(command)

    def run_helm_uninstall(self, name):
        command = "helm delete --purge {}".format(name)
        return run(command)

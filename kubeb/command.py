import os

import subprocess

from . import file_util as file


def docker_build_command(image, tag):
    return "docker build -t " + image + ':' + tag + ' ' + os.getcwd()


def docker_push_command(image, tag):
    return "docker push " + image + ':' + tag


def helm_install_command(name, template):
    return "helm upgrade --install --force " + name + " -f .kubeb/helm-values.yml .kubeb/" + template + " --wait"


def helm_uninstall_command():
    return "bash " + file.uninstall_script_file


def run(command):
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)

    (output, err) = p.communicate()

    p_status = p.wait()

    return p_status, output, err

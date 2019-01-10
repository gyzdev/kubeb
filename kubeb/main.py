import os
import time

import click
import click_spinner
spinner = click_spinner.Spinner()

# from dotenv import dotenv_values

from kubeb.core import Kubeb, pass_kubeb
from kubeb import file_util, config, command

@click.group()
@click.version_option('0.0.1')
@click.pass_context
def cli(ctx):
    ctx.obj = Kubeb()

@cli.command()
@click.option('--name', '-n',
              default=lambda: os.path.basename(os.getcwd()),
              prompt='Release name',
              help='Release name.')
@click.option('--user', '-n',
              default=lambda: os.environ.get('USER', ''),
              prompt='Maintainer name',
              help='Maintainer name.')
@click.option('--template', '-t',
              default='laravel|podder-task-bean',
              prompt='Release template',
              help='Release template name.')
@click.option('--image',
              default=lambda: os.environ.get('USER', '') + '/' + os.path.basename(os.getcwd()),
              prompt='Docker image name',
              help='Docker image name.')
@click.option('--env',
              default='local',
              prompt='Environment name',
              help='Environment name.')
@click.option('--force',
              is_flag=True,
              help='Overwrite config file.')
@pass_kubeb
def init(kubeb, name, user, template, image, env, force):
    """ Init kubeb configuration
        Generate config, script files
    """
    if file_util.config_file_exist() and force is False:
        kubeb.log('Kubeb config found. Please update config file or use --force option')
        return

    if not file_util.template_exist(template):
        kubeb.log('Kubeb template not found. Please check template name')
        return

    ext_template = file_util.is_ext_template(template)

    file_util.clean_up()
    file_util.generate_config_file(name, user, template, ext_template, image, env)
    file_util.generate_script_file(name, template)
    file_util.generate_environment_file(env, template)
    file_util.generate_docker_file(template)

    kubeb.log('Kubeb config file generated in %s', click.format_filename(file_util.config_file))

@cli.command()
@pass_kubeb
def info(kubeb):
    """ Show current configuration
    """
    if not file_util.config_file_exist():
        kubeb.log('Kubeb config file not found in %s', file_util.kubeb_directory)
        return

    config_data = config.load_config()
    print(config_data)

@cli.command()
@click.option('--message', '-m',
              multiple=True,
              help='Release note')
@pass_kubeb
def build(kubeb, message):
    """ Build current application
        Build Dockerfile image
        Add release note, tag to config file
    """
    if not file_util.config_file_exist():
        kubeb.log('Kubeb config file not found in %s', file_util.kubeb_directory)
        exit(1)

    if not message:
        marker = '# Add release note:'
        hint = ['', '', marker]
        message = click.edit('\n'.join(hint))
        msg = message.split(marker)[0].rstrip()
        if not msg:
            msg = ""
    else:
        msg = '\n'.join(message)

    image = config.get_image()
    tag = 'v' + str(int(round(time.time() * 1000)))

    kubeb.log('Building docker image ...')
    spinner.start()
    status, output, err = command.run(command.build_command(image, tag))
    if status != 0:
        kubeb.log('Docker image build failed', err)
        return
    spinner.stop()

    spinner.start()
    status, output, err = command.run(command.push_command(image, tag))
    if status != 0:
        kubeb.log('Docker image push failed', err)
        return
    spinner.stop()

    kubeb.log(output)
    kubeb.log('Docker image build succeed.')

    config.add_version(tag, msg)

@cli.command()
@click.option('--version', '-v',
              help='Install version.')
@pass_kubeb
def install(kubeb, version):
    """ Install current application to Kubernetes
        Generate Helm chart value file with docker image version
        If version is not specified, will get the latest version
    """
    if not file_util.config_file_exist():
        kubeb.log('Kubeb config file not found')
        return

    deploy_version = config.get_version(version)
    if not deploy_version:
        kubeb.log('No deployable version found')
        return

    kubeb.log('Deploying version: %s', deploy_version["tag"])
    file_util.generate_helm_file(config.get_template(), config.get_ext_template(), config.get_image(), deploy_version["tag"], config.get_current_environment())

    kubeb.log('Installing application ...')
    spinner.start()
    status, output, err = command.run(command.install_command())
    if status != 0:
        kubeb.log('Install application failed', err)
        file_util.clean_up_after_install(config.get_template())
        exit(1)

    file_util.clean_up_after_install(config.get_template())
    spinner.stop()

    kubeb.log(output)
    kubeb.log('Install application succeed.')

@cli.command()
@click.confirmation_option()
@pass_kubeb
def uninstall(kubeb):
    """Uninstall current application from Kubernetes
    """
    if not file_util.config_file_exist():
        kubeb.log('Kubeb config file not found')
        return

    status, output, err = command.run(command.uninstall_command())
    if status != 0:
        kubeb.log('Uninstall application failed', err)
        return

    kubeb.log(output)
    kubeb.log('Uninstall application succeed.')


@cli.command()
@pass_kubeb
def version(kubeb):
    """Show current application versions
    """
    if not file_util.config_file_exist():
        kubeb.log('Kubeb config file not found in %s', file_util.kubeb_directory)
        return

    versions = config.get_versions()
    if not versions or len(versions) == 0:
        kubeb.log('No version found in %s', file_util.kubeb_directory)
        return

    for version in versions:
        kubeb.log('- %s: %s', version['tag'], version['message'])


@cli.command()
@click.argument('env',
                default='local',
                type=str)
@pass_kubeb
def env(kubeb, env):
    """Use environment
        Example: kubeb env develop to use environment develop
    """
    if not file_util.config_file_exist():
        kubeb.log('Kubeb config file not found in %s', file_util.kubeb_directory)
        return

    environment = config.get_env(env)
    if not environment:
        kubeb.log('Environment not found')
        kubeb.log('Initiate environment %s in %s', env, file_util.kubeb_directory)
        file_util.generate_environment_file(env, config.get_template())

    config.set_current_environement(env)
    kubeb.log('Now use %s', env)


@cli.command()
@click.argument('name', required=True,
                default="sample",
                type=str)
@click.argument('path', required=True,
                default=".",
                type=click.Path(resolve_path=True))
@click.option('--force',
              is_flag=True,
              help='Overwrite template file.')

@pass_kubeb
def template(kubeb, name, path, force):
    """Add user template
        kubeb [template_name] [template_directory_path]
        Example: kubeb template example ./example
        Will add template to external template directory: ~/.kubeb/ext-templates/[template_name]
    """

    if file_util.template_exist(name) and not force:
        kubeb.log('Kubeb template found. Please change name or --force')
        return

    file_util.add_ext_template(name, path)

    kubeb.log('Kubeb template add to %s', click.format_filename(file_util.ext_template_directory))

@cli.command()
@click.confirmation_option()
@pass_kubeb
def destroy(kubeb):
    """Remove all kubeb configuration
    """
    file_util.clean_up()

    kubeb.log('Destroyed config directory %s' % file_util.kubeb_directory)



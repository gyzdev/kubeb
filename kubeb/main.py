import os

import click

from kubeb.kubeb import Kubeb
from kubeb import __version__


@click.group()
@click.version_option(__version__)
def cli():
    pass


@cli.command()
@click.option('--name', '-n',
              default=lambda: os.path.basename(os.getcwd()),
              prompt='Release name',
              help='Release name.')
@click.option('--user', '-u',
              default=lambda: os.environ.get('USER', ''),
              prompt='Maintainer name',
              help='Maintainer name.')
@click.option('--template', '-t',
              default='laravel|podder-pipeline|podder-task-bean',
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
def init(name, user, template, image, env, force):
    """ Init kubeb configuration
        Generate config, script files
    """
    Kubeb().initiate(name, user, template, image, env, force)


@cli.command()
def info():
    """ Show current configuration
    """
    Kubeb().info()


@cli.command()
@click.option('--message', '-m',
              multiple=True,
              help='Release note')
@click.option('--push',
              is_flag=True,
              default=False)
def build(message, push):
    """ Build current application
        Build Dockerfile image
        Add release note, tag to config file
    """
    Kubeb().build(message, push)


@cli.command()
@click.option('--version', '-v',
              help='Push version.')
def push(version):
    """ Push docker image to registry
    """
    Kubeb().push(version)


@cli.command()
@click.option('--version', '-v',
              help='Install version.')
@click.option('--set', 'options',
              type=str)
@click.option('--dry-run', 'dry_run',
              is_flag=True,
              default=False)
@click.option('--rollback',
              is_flag=True,
              default=True)
@click.confirmation_option()
def deploy(version, options, dry_run, rollback):
    """ Install current application to Kubernetes
        Generate Helm chart value file with docker image version
        If version is not specified, will get the latest version
    """
    deploy_options = dict()

    if options:
        for item in options.split(','):
            deploy_options.update([item.split('=')])

    Kubeb().deploy(version, deploy_options, dry_run, rollback)


@cli.command()
@click.confirmation_option()
def delete():
    """Uninstall current application from Kubernetes
    """
    Kubeb().delete()


@cli.command()
def version():
    Kubeb().version()


@cli.command()
def history():
    """Show current application deploy history
    """
    Kubeb().history()


@cli.command()
@click.argument('revision',
                default=0,
                type=int)
@click.confirmation_option()
def rollback(revision):
    """Rollback application to revision
        revision=0 is rollback to previous version
    """
    Kubeb().rollback(revision)


@cli.command()
@click.argument('env',
                default='local',
                type=str)
def env(env):
    """Use environment
        Example: kubeb env develop to use environment develop
    """
    Kubeb().env(env)


@cli.command()
@click.argument('variables',
                nargs=-1)
def setenv(variables):
    """Use environment
       Example: kubeb env develop to use environment develop
    """
    env_vars = dict()
    for item in variables:
        env_vars.update([item.split('=')])
    Kubeb().setenv(env_vars)


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
def template(name, path, force):
    """Add user template
        kubeb [template_name] [template_directory_path]
        Example: kubeb template example ./example
        Will add template to external template directory: ~/.kubeb/ext-templates/[template_name]
    """
    Kubeb().template(name, path, force)


@cli.command()
@click.confirmation_option()
def destroy():
    """Remove all kubeb configuration
    """
    Kubeb().destroy()

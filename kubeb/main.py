import os

import click

from kubeb.kubeb import Kubeb


@click.group()
def cli():
    pass


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
    Kubeb().initiate(name, user, template, image, env, force)


@cli.command()
def info():
    Kubeb().info()


@cli.command()
@click.option('--message', '-m',
              multiple=True,
              help='Release note')
@click.option('--push',
              is_flag=True,
              default=False)
def build(message, push):
    Kubeb().build(message, push)


@cli.command()
@click.option('--version', '-v',
              help='Push version.')
def push(version):
    Kubeb().push(version)


@cli.command()
@click.option('--version', '-v',
              help='Install version.')
@click.option('--dry-run', 'dry_run',
              is_flag=True,
              default=False)
def deploy(version, dry_run):
    Kubeb().deploy(version, dry_run)


@cli.command()
@click.confirmation_option()
def delete():
    Kubeb().delete()


@cli.command()
def version():
    Kubeb().version()


@cli.command()
@click.argument('env',
                default='local',
                type=str)
def env(env):
    Kubeb().env(env)


@cli.command()
@click.argument('variables',
                nargs=-1)
def setenv(variables):
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
    Kubeb().template(name, path, force)


@cli.command()
@click.confirmation_option()
def destroy():
    Kubeb().destroy()

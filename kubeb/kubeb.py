import sys
import os

import yaml
import time
import click
import click_spinner
spinner = click_spinner.Spinner()

from kubeb import file_util, config
from .generators import (PodderPipelineGenerator, PodderTaskBeanGenerator, LaravelGenerator)
from kubeb.command import Command


class Kubeb:

    def log(self, msg, *args):
        if args:
            msg %= args
        click.echo(msg, file=sys.stderr)

    def initiate(self, name, user, template, image, env, force):

        """ Init kubeb configuration
             Generate config, script files
        """
        if file_util.config_file_exist() and force is False:
            self.log('Kubeb config found. Please update config file or use --force option')
            return

        if not file_util.template_exist(template):
            self.log('Kubeb template not found. Please check template name')
            return

        ext_template = file_util.is_ext_template(template)

        generator = self._get_generator(template)
        if generator is None:
            self.log('Kubeb generator not found. Please check template name')
            return

        generator(data=dict(name=name,
                            user=user,
                            template=template,
                            ext_template=ext_template,
                            image=image,
                            env=env,
                            force=force
                            )
                  ).execute()

        self.log('Kubeb config file generated in %s', click.format_filename(file_util.config_file))

    def info(self):
        """ Show current configuration
        """
        if not file_util.config_file_exist():
            self.log('Kubeb config file not found in %s', file_util.kubeb_directory)
            return

        config_data = yaml.dump(config.load_config(), default_flow_style=False)
        print(config_data)

    def build(self, message, push):
        """ Build current application
            Build Dockerfile image
            Add release note, tag to config file
        """
        if not file_util.config_file_exist():
            self.log('Kubeb config file not found in %s', file_util.kubeb_directory)
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

        self.log('Building docker image {}:{}...'.format(image, tag))

        spinner.start()
        status = Command().run_docker_build(image, tag, os.getcwd())
        spinner.stop()
        if status != 0:
            self.log('Docker image build failed')
            return
        else:
            self.log('Docker image build succeed.')

        if push:
            spinner.start()
            status = Command().run_docker_push(image, tag)
            spinner.stop()
            if status != 0:
                self.log('Docker image push failed')
                return
            else:
                self.log('Docker image push succeed.')

        config.add_version(tag, msg)

    def push(self, version=None):
        """ Push docker image to registry
        """
        if not file_util.config_file_exist():
            self.log('Kubeb config file not found')
            return

        deploy_version = config.get_version(version)
        if not deploy_version:
            self.log('No deploy version found')
            return

        image = config.get_image()
        self.log('docker push {}:{}'.format(image, deploy_version["tag"]))

        spinner.start()
        status = Command().run_docker_push(image, deploy_version["tag"])
        spinner.stop()
        if status != 0:
            self.log('Docker image push failed')
        else:
            self.log('Docker image push succeed.')

    def deploy(self, version, options, dry_run, rollback=False):
        """ Install current application to Kubernetes
            Generate Helm chart value file with docker image version
            If version is not specified, will get the latest version
        """
        if not file_util.config_file_exist():
            self.log('Kubeb config file not found')
            return

        deploy_version = config.get_version(version)
        if not deploy_version:
            self.log('No deployable version found')
            return

        self.log('Deploying version: %s', deploy_version["tag"])
        file_util.generate_helm_file(config.get_template(), config.get_ext_template(), config.get_image(),
                                     deploy_version["tag"], config.get_current_environment())

        if options and not dry_run:
            self.log('Saving deploy options ...')
            file_util.save_deploy_options(options)

        self.log('Installing application ...')
        spinner.start()
        status = Command().run_helm_install(config.get_name(), config.get_template(), dry_run, options)
        spinner.stop()
        if status != 0:
            self.log('Install application failed.')

            if not dry_run and not rollback:
                self.log('Rollback application to previous version')
                self.deploy(config.get_last_deploy_version(), options, False, True)
        else:

            config.update_last_deploy_version(deploy_version["tag"])
            self.log('Install application succeed.')

    def rollback(self, version, options):

        rollback_version = config.get_previous_version(version)

        self.deploy(rollback_version["tag"], options, False)

    def delete(self):
        """Uninstall current application from Kubernetes
        """
        if not file_util.config_file_exist():
            self.log('Kubeb config file not found')
            return

        status = Command().run_helm_uninstall(config.get_name())
        if status != 0:
            self.log('Delete application failed')
            return

        self.log('Uninstall application succeed.')

    def version(self):
        """Show current application versions
        """
        if not file_util.config_file_exist():
            self.log('Kubeb config file not found in %s', file_util.kubeb_directory)
            return

        versions = config.get_versions()
        if not versions or len(versions) == 0:
            self.log('No version found in %s', file_util.kubeb_directory)
            return

        for version in versions:
            self.log('- %s: %s', version['tag'], version['message'])

    def env(self, env):
        """Use environment
           Example: kubeb env develop to use environment develop
        """
        if not file_util.config_file_exist():
            self.log('Kubeb config file not found in %s', file_util.kubeb_directory)
            return

        environment = config.get_env(env)
        if not environment:
            self.log('Environment not found')
            self.log('Initiate environment %s in %s', env, file_util.kubeb_directory)
            file_util.generate_environment_file(env, config.get_template())

        config.set_current_environement(env)
        self.log('Now use %s', env)

    def setenv(self, env_vars):
        """Use environment
           Example: kubeb env develop to use environment develop
        """
        if not file_util.config_file_exist():
            self.log('Kubeb config file not found in %s', file_util.kubeb_directory)
            return

        env = config.get_current_environment()
        config.set_environment_variable(env, env_vars)

    def template(self,name, path, force):
        """Add user template
            kubeb [template_name] [template_directory_path]
            Example: kubeb template example ./example
            Will add template to external template directory: ~/.kubeb/ext-templates/[template_name]
        """
        if file_util.template_exist(name) and not force:
            self.log('Kubeb template found. Please change name or --force')
            return

        file_util.add_ext_template(name, path)

        self.log('Kubeb template add to %s', click.format_filename(file_util.ext_template_directory))

    def destroy(self):
        """Remove all kubeb configuration
        """
        file_util.clean_up()

        self.log('Destroyed config directory %s' % file_util.kubeb_directory)

    def _get_generator(self, template):
        generators = {
            'laravel': LaravelGenerator,
            'podder-pipeline': PodderPipelineGenerator,
            'podder-task-bean': PodderTaskBeanGenerator,
        }

        return generators.get(template, None)

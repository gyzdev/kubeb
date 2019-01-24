import sys
import os

import yaml
import time
import click
import click_spinner
spinner = click_spinner.Spinner()

from kubeb import file_util, config, util
from .generators import (PodderPipelineGenerator, PodderTaskBeanGenerator, LaravelGenerator)


class Kubeb:

    def log(self, msg, *args):
        if args:
            msg %= args
        click.echo(msg, file=sys.stderr)

    def initiate(self, name, user, template, image, env, force):

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

        if not file_util.config_file_exist():
            self.log('Kubeb config file not found in %s', file_util.kubeb_directory)
            return

        config_data = yaml.dump(config.load_config(), default_flow_style=False)
        print(config_data)

    def build(self, message, push):

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
        status = util.run_docker_build(image, tag, os.getcwd())
        spinner.stop()
        if status != 0:
            self.log('Docker image build failed')
            return
        else:
            self.log('Docker image build succeed.')

        if push:
            spinner.start()
            status = util.run_docker_push(image, tag)
            spinner.stop()
            if status != 0:
                self.log('Docker image push failed')
                return
            else:
                self.log('Docker image push succeed.')

        config.add_version(tag, msg)

    def push(self, version=None):

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
        status = util.run_docker_push(image, deploy_version["tag"])
        spinner.stop()
        if status != 0:
            self.log('Docker image push failed')
        else:
            self.log('Docker image push succeed.')

    def deploy(self, version, options, dry_run, rollback=True):

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
        status = util.run_helm_install(config.get_name(), config.get_template(), dry_run, options)
        spinner.stop()
        if status != 0:
            self.log('Install application failed.')

            if dry_run is False and rollback:
                last_working_revision = util.get_last_working_revision(config.get_name())
                if not last_working_revision:
                    self.log('Last working revision not found. Skip rollback')
                    return

                self.log('Rollback application to last working revision {}'.format(last_working_revision))
                self.rollback(last_working_revision)
        else:
            self.log('Install application succeed.')

    def delete(self):

        if not file_util.config_file_exist():
            self.log('Kubeb config file not found')
            return

        status = util.run_helm_uninstall(config.get_name())
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

    def history(self):

        if not file_util.config_file_exist():
            self.log('Kubeb config file not found in %s', file_util.kubeb_directory)
            return

        self.log('Get application deploy history ...')
        spinner.start()
        status = util.run_helm_history(config.get_name())
        spinner.stop()
        if status != 0:
            self.log('Get application deploy history failed.')
        else:
            self.log('Get application deploy history succeed.')

    def rollback(self, revision):

        if not file_util.config_file_exist():
            self.log('Kubeb config file not found in %s', file_util.kubeb_directory)
            return

        self.log('Rollback application to revision {} ...'.format(revision))
        spinner.start()
        status = util.run_helm_rollback(config.get_name(), revision)
        spinner.stop()
        if status != 0:
            self.log('Rollback application to revision failed.')
        else:
            self.log('Rollback application to revision succeed.')

    def env(self, env):

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

        if not file_util.config_file_exist():
            self.log('Kubeb config file not found in %s', file_util.kubeb_directory)
            return

        env = config.get_current_environment()
        config.set_environment_variable(env, env_vars)

    def template(self,name, path, force):

        if file_util.template_exist(name) and not force:
            self.log('Kubeb template found. Please change name or --force')
            return

        file_util.add_ext_template(name, path)

        self.log('Kubeb template add to %s', click.format_filename(file_util.ext_template_directory))

    def destroy(self):

        file_util.clean_up()

        self.log('Destroyed config directory %s' % file_util.kubeb_directory)

    def _get_generator(self, template):
        generators = {
            'laravel': LaravelGenerator,
            'podder-pipeline': PodderPipelineGenerator,
            'podder-task-bean': PodderTaskBeanGenerator,
        }

        return generators.get(template, None)

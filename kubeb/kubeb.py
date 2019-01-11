import sys

import time
import click
import click_spinner
spinner = click_spinner.Spinner()

from kubeb import file_util, config, command


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
        file_util.clean_up()
        file_util.generate_config_file(name, user, template, ext_template, image, env)
        file_util.generate_script_file(name, template)
        file_util.generate_environment_file(env, template)
        file_util.generate_docker_file(template)

        self.log('Kubeb config file generated in %s', click.format_filename(file_util.config_file))

    def info(self):
        """ Show current configuration
        """
        if not file_util.config_file_exist():
            self.log('Kubeb config file not found in %s', file_util.kubeb_directory)
            return

        config_data = config.load_config()
        print(config_data)

    def build(self, message):
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

        self.log('Building docker image ...')
        spinner.start()
        status, output, err = command.run(command.docker_build_command(image, tag))
        if status != 0:
            self.log('Docker image build failed', err)
            return
        spinner.stop()

        spinner.start()
        status, output, err = command.run(command.docker_push_command(image, tag))
        if status != 0:
            self.log('Docker image push failed', err)
            return
        spinner.stop()

        self.log(output)
        self.log('Docker image build succeed.')

        config.add_version(tag, msg)

    def deploy(self, version):
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

        self.log('Installing application ...')
        spinner.start()
        status, output, err = command.run(command.helm_install_command(config.get_name(), config.get_template()))
        if status != 0:
            self.log('Install application failed', err)
            file_util.clean_up_after_install(config.get_template())
            exit(1)

        file_util.clean_up_after_install(config.get_template())
        spinner.stop()

        self.log(output)
        self.log('Install application succeed.')

    def delete(self):
        """Uninstall current application from Kubernetes
        """
        if not file_util.config_file_exist():
            self.log('Kubeb config file not found')
            return

        status, output, err = command.run(command.helm_uninstall_command(config.get_name()))
        if status != 0:
            self.log('Uninstall application failed', err)
            return

        self.log(output)
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
from . import file_util


def load_config():
    return file_util.get_yaml_dict(file_util.config_file)


def get_name():
    return file_util.get_value('name', file_util.config_file)


def get_image():
    return file_util.get_value("image", file_util.config_file)


def add_version(tag, message=""):
    version = file_util.get_value('version', file_util.config_file)
    if not version:
        version = []

    version.append(dict(
        tag=tag,
        message=message
    ))

    file_util.set_value("version", version, file_util.config_file)


def get_versions():
    return file_util.get_value('version', file_util.config_file)


def get_version(version=None):
    versions = get_versions()
    if not versions or len(versions) == 0:
        return None

    found_version = None
    if not version:
        found_version = versions[-1]
    else:
        try:
            found_version = next((ver for ver in versions if ver["tag"] == version))
        except StopIteration:
            pass
    return found_version


def get_previous_version(version):

    versions = get_versions()
    if not versions or len(versions) == 0:
        return None

    previous_version = None
    versions.sort(key=lambda r: r["tag"])
    i = 0
    ver = dict({"tag": ""})
    while ver["tag"] == version:
        ver = versions[i]
        i += 1

    if i < len(versions):
        previous_version = versions[i + 1]

    return previous_version


def get_template():
    return file_util.get_value('template', file_util.config_file)


def get_local():
    return file_util.get_value('local', file_util.config_file)


def get_env(name):
    environments = file_util.get_value('env', file_util.config_file)
    if not environments:
        return None

    environment = None
    try:
        environment = environments.name
    except KeyError:
        pass

    return environment


def set_current_environement(env):
    file_util.set_value("current_environment", env, file_util.config_file)


def get_current_environment():
    return file_util.get_value('current_environment', file_util.config_file)


def get_ext_template():
    return file_util.get_value('ext_template', file_util.config_file)


def set_environment_variable(env, env_vars):
    environments = file_util.get_value("environments", file_util.config_file)

    variables = dict()
    try:
        variables = environments[env]['variables']
    except KeyError:
        pass

    variables = { **variables, **env_vars }

    print(variables)
    environments[env]['variables'] = variables
    file_util.set_value("environments", environments, file_util.config_file)


def get_environment_variables(env):
    environments = file_util.get_value("environments", file_util.config_file)

    variables = dict()
    try:
        variables = environments[env]['variables']
    except KeyError:
        pass
    return variables


def update_last_deploy_version(version_tag):
    file_util.set_value("last_deploy_version", version_tag, file_util.config_file)


def get_last_deploy_version():
    return file_util.get_value("last_deploy_version", file_util.config_file)

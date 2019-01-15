import os
import shutil
import codecs
import yaml

from jinja2 import Environment, FileSystemLoader

kubeb_directory = '.kubeb' + os.path.sep
config_file = kubeb_directory + "config.yml"
helm_value_file = kubeb_directory + "helm-values.yml"

docker_file = os.path.join(os.getcwd(), "Dockerfile")
docker_directory = os.path.join(os.getcwd(), "docker")

template_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), './templates/')) + os.path.sep
ext_template_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '../ext_templates/')) + os.path.sep
helm_template_directory = template_directory + "helm"

_marker = object()

def config_file_exist():
    return os.path.isfile(config_file)


def docker_file_exist():
    return os.path.isfile(docker_file)


def init_config_dir():
    directory = os.path.join(os.getcwd(), kubeb_directory)
    if not os.path.isdir(directory):
        os.makedirs(directory)


def remove_config_dir():
    directory = os.path.join(os.getcwd(), kubeb_directory)
    if os.path.isdir(directory):
        shutil.rmtree(directory)


def get_template_directory(template, external):
    if external:
        return ext_template_directory + template
    else:
        return template_directory + template

def get_helm_chart_dir(template):
    return kubeb_directory + template

def generate_config_file(name, user, template, ext_template, image, env):
    init_config_dir()

    values = dict(
        name=name,
        template=template,
        ext_template=ext_template,
        user=user,
        image=image,
    )

    with open(config_file, "w") as fh:
        fh.write(yaml.dump(values,
                           default_flow_style=False,
                           line_break=os.linesep))

    environments = dict()
    environments[env] = dict(
        name=env
    )

    set_value('environments', environments, config_file)
    set_value('current_environment', env, config_file)

def generate_docker_file(template):
    work_dir = os.getcwd()
    template_dir = template_directory + template

    docker_file_src = os.path.join(template_dir, 'Dockerfile')
    if os.path.isfile(docker_file_src):
        docker_file_dst = os.path.join(work_dir, 'Dockerfile')
        shutil.copy(docker_file_src, docker_file_dst)

    ignore_src = os.path.join(template_dir, '.dockerignore')
    if os.path.isfile(ignore_src):
        ignore_dst = os.path.join(work_dir, '.dockerignore')
        shutil.copy(ignore_src, ignore_dst)

    if os.path.isdir(os.path.join(template_dir, template)):
        shutil.copytree(os.path.join(template_dir, template), get_helm_chart_dir(template))


def generate_helm_file(template, ext_template, image, tag, env):
    if not ext_template:
        template_dir = template_directory + template
    else:
        template_dir = ext_template_directory + template

    dotenv_path = get_environment_file(env)
    if not os.path.exists(dotenv_path):
        print("can't read %s - it doesn't exist." % dotenv_path)
        return None

    env_file_dst = os.path.join(get_helm_chart_dir(template), 'app.env')
    shutil.copy(dotenv_path, env_file_dst)

    # parsed_dict = dotenv_values(dotenv_path)
    #
    # env_vars = dict()
    # for key, value in parsed_dict.items():
    #     if value and value != '' and value != 'null':
    #         env_vars[key] = value

    values = dict(
        image=image,
        tag=tag
    )

    jinja2_env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True)
    content = jinja2_env.get_template('helm-values.yaml').render(values)
    with open(helm_value_file, "w") as fh:
        fh.write(content)

    print("generated helm-values.yaml in %s" % helm_value_file)


def clean_up():
    remove_config_dir()


def set_value(key_name, value, file):
    config = get_yaml_dict(file)
    if not config:
        config = {}

    if type(value) is dict:
        for key in value.keys():
            config.setdefault(key_name, {})[key] = value[key]
    else:
        config[key_name] = value

    with codecs.open(file, 'w', encoding='utf8') as f:
        f.write(yaml.dump(config, default_flow_style=False,
                          line_break=os.linesep))


def get_value(key_name, file, default=_marker):
    value = None
    config = get_yaml_dict(file)
    if config:
        try:
            value = config[key_name]
        except KeyError:
            value = None

    if value is None and default != _marker:
        return default

    return value

def get_yaml_dict(filename):
    try:
        with codecs.open(filename, 'r', encoding='utf8') as f:
            return yaml.load(f)
    except IOError:
        return {}

def get_environment_file(env):
    work_dir = os.getcwd()
    return os.path.join(work_dir, '.env.' + env)

def generate_environment_file(env, template):
    work_dir = os.getcwd()
    template_dir = template_directory + template

    docker_file_src = os.path.join(template_dir, 'dotenv')
    docker_file_dst = os.path.join(work_dir, '.env.' + env)
    shutil.copy(docker_file_src, docker_file_dst)


def template_exist(template):
    return os.path.isdir(template_directory + template) \
           or os.path.isdir(ext_template_directory + template)


def is_ext_template(template):
    return os.path.isdir(ext_template_directory + template)


def add_ext_template(name, path):
    template_dir = ext_template_directory + name
    if os.path.isdir(template_dir):
        shutil.rmtree(template_dir)

    shutil.copytree(path, template_dir)


def clean_up_after_install(template):
    try:
        env_file = os.path.join(get_helm_chart_dir(template), 'app.env')
        if os.path.isfile(env_file):
            shutil.rmtree(env_file)
    except:
        pass

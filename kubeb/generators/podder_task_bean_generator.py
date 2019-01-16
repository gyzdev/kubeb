from kubeb import file_util

from .base_generator import BaseGenerator


class PodderTaskBeanGenerator(BaseGenerator):
    def execute(self):
        file_util.clean_up()
        file_util.generate_config_file(self.data["name"],
                                       self.data["user"],
                                       self.data["template"],
                                       self.data["ext_template"],
                                       self.data["image"],
                                       self.data["env"])
        file_util.generate_environment_file(self.data["env"], self.data["template"])
        file_util.generate_docker_file(self.data["template"])
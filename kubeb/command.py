import subprocess


class Command(object):

    def __init__(self, command):
        self._command = command

    def execute(self, shell=True, executable=None, printout=True):
        return self._call(self._command, shell=shell, executable=executable, printout=printout)

    def _call(self, command, shell=True, executable=None, printout=True):
        process = subprocess.Popen(command,
                                   stdout=subprocess.PIPE,
                                   shell=shell,
                                   executable=executable,
                                   universal_newlines=True)

        if printout:
            while True:
                stdout = process.stdout.readline()
                if stdout == '' and process.poll() is not None:
                    break
                if stdout:
                    print(stdout.strip())

        output, error = process.communicate()
        exitcode = process.returncode

        return exitcode, output, error

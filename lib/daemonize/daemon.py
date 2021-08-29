import sys
import os
import time
import atexit

from signal import SIGTERM
from signal import SIGHUP

DEFAULT_STD_IN = '/dev/null'
DEFAULT_STD_OUT = '/dev/null'
DEFAULT_STD_ERR = '/dev/null'


class Daemon(object):

    def __init__(self, pid_file, std_in=DEFAULT_STD_IN, std_out=DEFAULT_STD_OUT, std_err=DEFAULT_STD_ERR):

        self.std_in = std_in
        self.stdout = std_out
        self.stderr = std_err
        self.pid_file = pid_file

    def daemonize(self):

        try:

            pid = os.fork()

            if pid > 0:
                sys.exit(0)

        except OSError:

            sys.exit(1)

        os.setsid()
        os.umask(0)

        try:

            pid = os.fork()

            if pid > 0:
                sys.exit(0)

        except OSError:

            sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.std_in, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        atexit.register(self.remove_process_id)
        pid = str(os.getpid())

        try:

            open(self.pid_file, 'w+').write("%s\n" % pid)

        except IOError:

            sys.exit(1)

    def remove_process_id(self):

        os.remove(self.pid_file)

    def get_process_id(self):

        try:

            pf = open(self.pid_file, 'r')
            pid = int(pf.read().strip())
            pf.close()

        except IOError:

            pid = None

        return pid

    def start(self, daemon=True):

        if self.get_process_id():

            message = "pid file %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pid_file)
            sys.exit(1)

        if daemon:
            self.daemonize()

        self.run()

    def stop(self):

        pid = self.get_process_id()

        if not pid:

            message = "pid file %s does not exist. Daemon not running?"
            sys.stderr.write((message + '\n') % self.pid_file)
            return

        try:

            while 1:

                os.kill(pid, SIGTERM)
                time.sleep(0.1)

        except OSError as err:

            err = str(err)

            if err.find("No such process") > 0:

                if os.path.exists(self.pid_file):
                    os.remove(self.pid_file)

            else:

                sys.exit(1)

    def signal_process(self):

        pid = self.get_process_id()

        if pid:

            try:

                os.kill(pid, SIGHUP)

            except OSError:

                pass

        else:

            pass

    def restart(self):

        self.stop()
        self.start()

    def run(self):

        raise NotImplemented()

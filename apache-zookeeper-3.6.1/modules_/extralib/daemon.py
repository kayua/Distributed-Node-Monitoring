#
#	@program: daemon
#	@author: Matthew Vliet
#	@source: https://gist.github.com/mvliet/7649806
#	@date: (DD/MM/YYYY) 25/11/2013

# Based off of code written by Sander Marechal, which was released into public
# domain.
# http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
#

import sys, os, time, atexit
import logging
from signal import SIGTERM
from signal import SIGHUP

log = logging.getLogger(__name__)


class Daemon(object):
    """A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    # def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):

        log.debug('Created daemon. stdin=%s, stdout=%s, stderr=%s' %
                  (stdin, stdout, stderr))
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        log.debug("Attempting to daemonize.")
        try:
            pid = os.fork()
            if pid > 0:
                log.debug("First fork suceeded.  New pid: %s" % pid)
                sys.exit(0)
        except OSError as e:
            log.debug("fork #1 failed: %d (%s)" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        #os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                log.debug("Second fork suceeded.  New pid: %s" % pid)
                sys.exit(0)
        except OSError as e:
            log.debug("fork #2 failed: %d (%s)" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard open descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+') #TODO check file(self.stderr, 'a+', 0)

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        try:
            open(self.pidfile,'w+').write("%s\n" % pid)
            log.debug("pid written to: '%s'" % self.pidfile)

        except IOError:
            log.error("unable to write pid to open '%s'" % self.pidfile)
            log.error("Aborting")
            sys.exit(1)

        log.debug("done.")

    def delpid(self):
        os.remove(self.pidfile)

    def getpid(self):
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
            log.debug("Found pid in open.  pid: %s" % pid)
        except IOError:
            pid = None
            log.debug("No pid found.")
        return pid

    def start(self, daemon=True):
        if self.getpid():
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        if daemon:
            self.daemonize()

        self.run()


    def stop(self):
        log.debug("Attempting to stop daemon")
        pid = self.getpid()
        if not pid:
            message = "pidfile %s does not exist. Daemon not running?"
            log.debug(message % self.pidfile)
            sys.stderr.write((message+'\n') % self.pidfile)
            return # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
            log.debug("Daemon killed successfully")
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                log.debug("Failed to kill daemon")
                log.debug(err)
                sys.exit(1)

    def signal(self, signal):
        pid = self.getpid()
        if pid:
            try:
                os.kill(pid, SIGHUP)
            except Exception as err:
                err = str(err)
                log.error("Failed signaling process with pid=%s" % pid)
                log.error(err)
        else:
            log.error("pidfile %s does not exist. Daemon not running?" %
                      self.pidfile)

    def restart(self):
        log.debug("Restarting the daemon")
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon.
        It will be called after the process has been daemonized by start()
        or restart().
        """
        raise NotImplemented()
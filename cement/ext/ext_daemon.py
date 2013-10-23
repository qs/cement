"""Daemon Framework Extension"""

import os
import sys
import io
import pwd
import grp
from ..core import handler, hook, backend, exc
from ..utils.misc import minimal_logger

Log = minimal_logger(__name__)
Log = minimal_logger(__name__)
CEMENT_DAEMON_ENV = None
CEMENT_DAEMON_APP = None


class Environment(object):
    """
    This class provides a mechanism for altering the running processes
    environment.

    Optional Arguments:

        stdin
            A file to read STDIN from.  Default: /dev/null

        stdout
            A file to write STDOUT to.  Default: /dev/null

        stderr
            A file to write STDERR to.  Default: /dev/null

        dir
            The directory to run the process in.

        pid_file
            The filesystem path to where the PID (Process ID) should be
            written to.  Default: None

        user
            The user name to run the process as.  Default: os.environ['USER']

        group
            The group name to run the process as.  Default: The primary group
            of os.environ['USER'].

        umask
            The umask to pass to os.umask().  Default: 0

    """

    def __init__(self, **kw):
        self.stdin = kw.get('stdin', '/dev/null')
        self.stdout = kw.get('stdout', '/dev/null')
        self.stderr = kw.get('stderr', '/dev/null')
        self.dir = kw.get('dir', os.curdir)
        self.pid_file = kw.get('pid_file', None)
        self.umask = kw.get('umask', 0)
        self.user = kw.get('user', os.environ['USER'])

        # clean up
        self.dir = os.path.abspath(os.path.expanduser(self.dir))
        if self.pid_file:
            self.pid_file = os.path.abspath(os.path.expanduser(self.pid_file))

        try:
            self.user = pwd.getpwnam(self.user)
        except KeyError as e:
            raise exc.FrameworkError("Daemon user '%s' doesn't exist." %
                                     self.user)

        try:
            self.group = kw.get('group',
                                grp.getgrgid(self.user.pw_gid).gr_name)
            self.group = grp.getgrnam(self.group)
        except KeyError as e:
            raise exc.FrameworkError("Daemon group '%s' doesn't exist." %
                                     self.group)

    def _write_pid_file(self):
        """
        Writes os.getpid() out to self.pid_file.
        """
        pid = str(os.getpid())
        Log.debug('writing pid (%s) out to %s' % (pid, self.pid_file))

        # setup pid
        if self.pid_file:
            f = open(self.pid_file, 'w')
            f.write(pid)
            f.close()
            os.chown(os.path.dirname(self.pid_file),
                     self.user.pw_uid, self.group.gr_gid)

    def switch(self):
        """
        Switch the current process's user/group to self.user, and
        self.group.  Change directory to self.dir, and write the
        current pid out to self.pid_file.
        """
        # set the running uid/gid
        Log.debug('setting process uid(%s) and gid(%s)' %
                 (self.user.pw_uid, self.group.gr_gid))
        os.setgid(self.group.gr_gid)
        os.setuid(self.user.pw_uid)
        os.environ['HOME'] = self.user.pw_dir
        os.chdir(self.dir)
        if self.pid_file and os.path.exists(self.pid_file):
            raise exc.FrameworkError("Process already running (%s)" %
                                     self.pid_file)
        else:
            self._write_pid_file()

    def daemonize(self):
        """
        Fork the current process into a daemon.

        References:

        UNIX Programming FAQ
            1.7 How do I get my program to act like a daemon?
            http://www.unixguide.net/unix/programming/1.7.shtml
            http://www.faqs.org/faqs/unix-faq/programmer/faq/

        Advanced Programming in the Unix Environment
            W. Richard Stevens, 1992, Addison-Wesley, ISBN 0-201-56317-7.

        """
        Log.debug('attempting to daemonize the current process')
        # Do first fork.
        try:
            pid = os.fork()
            if pid > 0:
                Log.debug('successfully detached from first parent')
                os._exit(os.EX_OK)
        except OSError as e:
            sys.stderr.write("Fork #1 failed: (%d) %s\n" %
                            (e.errno, e.strerror))
            sys.exit(1)

        # Decouple from parent environment.
        os.chdir(self.dir)
        os.umask(int(self.umask))
        os.setsid()

        # Do second fork.
        try:
            pid = os.fork()
            if pid > 0:
                Log.debug('successfully detached from second parent')
                os._exit(os.EX_OK)
        except OSError as e:
            sys.stderr.write("Fork #2 failed: (%d) %s\n" %
                            (e.errno, e.strerror))
            sys.exit(1)

        # Redirect standard file descriptors.
        stdin = open(self.stdin, 'r')
        stdout = open(self.stdout, 'a+')
        stderr = open(self.stderr, 'a+')

        if hasattr(sys.stdin, 'fileno'):
            try:
                os.dup2(stdin.fileno(), sys.stdin.fileno())
            except io.UnsupportedOperation as e:
                # FIXME: ?
                pass
        if hasattr(sys.stdout, 'fileno'):
            try:
                os.dup2(stdout.fileno(), sys.stdout.fileno())
            except io.UnsupportedOperation as e:
                # FIXME: ?
                pass
        if hasattr(sys.stderr, 'fileno'):
            try:
                os.dup2(stderr.fileno(), sys.stderr.fileno())
            except io.UnsupportedOperation as e:
                # FIXME: ?
                pass

        # Update our pid file
        self._write_pid_file()


def daemonize():
    """
    This function switches the running user/group to that configured in
    config['daemon']['user'] and config['daemon']['group'].  The default user
    is os.environ['USER'] and the default group is that user's primary group.
    A pid_file and directory to run in is also passed to the environment.

    It is important to note that with the daemon extension enabled, the
    environment will switch user/group/set pid/etc regardless of whether
    the --daemon option was passed at command line or not.  However, the
    process will only 'daemonize' if the option is passed to do so.  This
    allows the program to run exactly the same in forground or background.

    """
    # We want to honor the runtime user/group/etc even if --daemon is not
    # passed... but only daemonize if it is.
    global CEMENT_DAEMON_ENV
    global CEMENT_DAEMON_APP

    app = CEMENT_DAEMON_APP
    CEMENT_DAEMON_ENV = Environment(
        user=app.config.get('daemon', 'user'),
        group=app.config.get('daemon', 'group'),
        pid_file=app.config.get('daemon', 'pid_file'),
        dir=app.config.get('daemon', 'dir'),
        umask=app.config.get('daemon', 'umask'),
    )

    CEMENT_DAEMON_ENV.switch()

    if '--daemon' in app.argv:
        CEMENT_DAEMON_ENV.daemonize()


def extend_app(app):
    """
    Adds the '--daemon' argument to the argument object, and sets the default
    [daemon] config section options.

    """
    global CEMENT_DAEMON_APP
    CEMENT_DAEMON_APP = app

    app.args.add_argument('--daemon', dest='daemon',
                          action='store_true', help='daemonize the process')

    # Add default config
    user = pwd.getpwnam(os.environ['USER'])
    group = grp.getgrgid(user.pw_gid)

    defaults = dict()
    defaults['daemon'] = dict()
    defaults['daemon']['user'] = user.pw_name
    defaults['daemon']['group'] = group.gr_name
    defaults['daemon']['pid_file'] = None
    defaults['daemon']['dir'] = '/'
    defaults['daemon']['umask'] = 0
    app.config.merge(defaults, override=False)
    app.extend('daemonize', daemonize)


def cleanup(app):
    """
    After application run time, this hook just attempts to clean up the
    pid_file if one was set, and exists.

    """
    global CEMENT_DAEMON_ENV

    if CEMENT_DAEMON_ENV and CEMENT_DAEMON_ENV.pid_file:
        if os.path.exists(CEMENT_DAEMON_ENV.pid_file):
            Log.debug('Cleaning up pid_file...')
            pid = open(CEMENT_DAEMON_ENV.pid_file, 'r').read().strip()

            # only remove it if we created it.
            if int(pid) == int(os.getpid()):
                os.remove(CEMENT_DAEMON_ENV.pid_file)


def load():
    hook.register('post_setup', extend_app)
    hook.register('pre_close', cleanup)

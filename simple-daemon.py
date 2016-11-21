#!/usr/bin/env python3

import sys, os, time, atexit, signal, socketserver


class DaemonServer:

    def __init__(self):
        self.pidfile = '/tmp/' + sys.argv[0].split('/')[-1].replace('.py', '.pid')
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum, frame):
        raise SigtermException('SIGTERM')
	
    def daemonize(self):
        try: 
            pid = os.fork() 
            if pid > 0:
                sys.exit(0) 
        except OSError as err: 
            sys.stderr.write('fork #1 failed: {0}\n'.format(err))
            sys.exit(1)
	
        os.chdir('/') 
        os.setsid() 
        os.umask(0) 
	
        try: 
            pid = os.fork() 
            if pid > 0:
                sys.exit(0) 
        except OSError as err: 
            sys.stderr.write('fork #2 failed: {0}\n'.format(err))
            sys.exit(1) 
	
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
	
        atexit.register(self.delpid)
        pid = str(os.getpid())
        with open(self.pidfile,'w+') as f:
            f.write(pid + '\n')
	
    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        try:
            with open(self.pidfile,'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None
	
        if pid:
            message = "pidfile {0} already exist. Daemon already running?\n"
            sys.stderr.write(message.format(self.pidfile))
            sys.exit(1)
		
        self.daemonize()
        self.run()

    def stop(self):
        try:
            with open(self.pidfile,'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None
	
        if not pid:
            message = "pidfile {0} does not exist. Daemon not running?\n"
            sys.stderr.write(message.format(self.pidfile))
            return # not an error in a restart

        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            e = str(err.args)
            if e.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print (str(err.args))
                sys.exit(1)

    def restart(self):
        """Restart the daemon."""
        self.stop()
        self.start()

    def run(self):
        socketserver.TCPServer.allow_reuse_address = True
        server = socketserver.TCPServer(('', 9999), SmallServer)
        try:
            server.serve_forever()
        except SigtermException:
            server.shutdown()
            server.server_close()


class SmallServer(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024)
        print("input:", data.decode('utf-8').strip())
        self.request.sendall('ok\r\n'.encode('utf-8'))


class SigtermException(Exception):
    '''
    '''
    pass


if __name__ == '__main__':
    server = DaemonServer()
    if len(sys.argv) == 2:
        if sys.argv[1] == 'start':
            server.start()
        elif sys.argv[1] == 'stop':
            server.stop()
        elif sys.argv[1] == 'restart':
            server.restart()
        else:
            print('usage: {} start|stop|restart'.format(sys.argv[0]))
    else:
        print('usage: {} start|stop|restart'.format(sys.argv[0]))

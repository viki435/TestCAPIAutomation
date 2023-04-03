import paramiko
import logging
import select
import subprocess
import os
import sys
import time
import datetime
from scp import SCPClient
#from paramiko_expect import SSHClientInteraction

_logger = logging.getLogger(__name__)

class SSH(object):

    def __init__(self, remote_ip, user_name, passwd, port = 22):
        """
        Constructs all the necessary attributes for the SSH object.

            :param remote_ip: Remote ESXi host IP Address
            :type remote_ip: string e.g. '10.223.246.8'
            :param user_name: Remote machine Username
            :type user_name: string e.g. 'root'
            :param passwd: Remote machine Password
            :type passwd: string e.g. 'intel@123'
        """
        self.connection = None

        self.remote_ip = remote_ip
        self.user_name = user_name
        self.passwd = passwd
        self.port = port

        self.ssh_status_connected = False

        self._nbytes = 1048576

    def connect(self):
        """
        Function to connect to Remote Machine
        """
        self.ssh_status_connected = False
        try:
            self.connection = paramiko.SSHClient()
            self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.connection.connect(hostname=self.remote_ip, port=self.port, username=self.user_name, password=self.passwd, look_for_keys = False, allow_agent = False)
            self.transport = self.connection.get_transport()
            self.transport.set_keepalive(30)
            _logger.info('Connected to remote machine {}.'.format(self.remote_ip))
            self.ssh_status_connected = True
        except paramiko.AuthenticationException:
            _logger.info("Authentication failed, please verify your credentials")        
        except paramiko.SSHException as sshException:
            _logger.info("Unable to establish SSH connection: %s" % sshException)
        except paramiko.BadHostKeyException as badHostKeyException:
            _logger.info("Unable to verify server's host key: %s" % badHostKeyException)
        except paramiko.ssh_exception.NoValidConnectionsError as NoValidConnectionsError:
            _logger.info("Unable to Connect: %s" % NoValidConnectionsError)

        return self.ssh_status_connected

    def execute_cmd(self, cmd, exec_path, timeout):
        """
        Function to execute the command on Remote Machine from ssh connection

            :param cmd: Command to execute
            :type cmd: string e.g. 'ls -al'
            :param exec_path: Path where to execute the command
            :type exec_path: string e.g. '/root/scratch'
            :param timeout: Waiting time to complete the command execution
            :type timeout: integer
            :return: Output of the command executed on remote machine
            :rtype: string
        """
        if exec_path != '':
            cmd_exec = 'cd ' + exec_path + ';' + cmd
        else:
            cmd_exec = cmd
        try:
            _logger.info('[Remote command $:] {}'.format(cmd_exec))
            stdin, stdout, stderr = self.connection.exec_command(cmd_exec, timeout=timeout)
        except AttributeError as e:
            _logger.info('SSH connection broke! %s' % e)
            return -1
        buffer = '' # Initializing buffer        
        while not stdout.channel.exit_status_ready():
            ''' Only print data if there is data to read in the channel'''
            if stdout.channel.recv_ready():
                rl, wl, xl = select.select([ stdout.channel ], [ ], [ ], 0.0)
                if len(rl) > 0:
                    tmp = stdout.channel.recv(self._nbytes)
                    buffer = tmp.decode()

                #_logger.info(buffer)

        error = stderr.read().decode('utf-8')
        #_logger.info("Remote error",error)
        if str(error) is '':
            #_logger.info("Buffer",buffer)
            return buffer
        elif 'warning' in str(error):
            return buffer
        elif 'calgary' in str(error):
            return buffer
        elif 'WARNING' in str(error):
            return buffer
        else:
            '''print(cmd + ' Failed to run')'''
            _logger.info("ERRORRRRRR....",error)
            return -1

    def is_remote_machine_alive(self, timeout):
        """
        Function to check whether the remote machine is alive or not

            :param timeout: Waiting time
            :type timeout: integer
            :return: True if alive else False
            :rtype: Boolean
        """
        _logger.info('Checking remote IP {} is reachable or not...'.format(self.remote_ip))
        wait_time = timeout
        while wait_time > 0:
            try:
                response = subprocess.check_output(['ping', '-c', '3', self.remote_ip], stderr = subprocess.STDOUT, universal_newlines=True)
            except subprocess.CalledProcessError:
                response = None
                sys.stdout.write('\r'+'Waiting for '+str(wait_time)+' Seconds...')
                sys.stdout.flush()
            if response:
                _logger.info('\nRemote IP {} is reachable.'.format(self.remote_ip))
                _logger.info('Waiting for 30 seconds for system to configure services after boot (if fresh boot)')
                time.sleep(30) # Buffer of 30 seconds for system to configure services after boot
                return True
            wait_time=wait_time-3
        _logger.info('\nEven after {} seconds, remote IP {} is not reachable'.format(timeout, self.remote_ip))
        return False

    def remote_reboot(self):
        """Function to reboot the remote machine

            :param remote_ip: Remote ESXi host IP Address
            :type remote_ip: string e.g. '10.223.246.8'
            :param user_name: Remote machine Username
            :type user_name: string e.g. 'root'
            :param passwd: Remote machine Password
            :type passwd: string e.g. 'intel@123'
            :return: 0 on success, -1 on failure
            :rtype: integer
        """
        if self.is_remote_machine_alive(300) == True:
            self.connect()
        else:
            return -1   

        _logger.info('Executing reboot command...')
        self.execute_cmd('reboot', '', 100 )

        self.ssh_disconnect()

        _logger.info('Waiting for 120 seconds to reboot command to complete.')
        time.sleep(40) #Give 40 seconds for reboot command execution to complete    

        if self.is_remote_machine_alive(120) == True:
            self.connect()
        else:
            return -1

        """
        out = self.execute_cmd('uptime', '', 100 )
        _logger.info ("here is a n error:::", out )

        self.ssh_disconnect()

        if out != '':
            _logger.info ("here is a n error:::", out )
            uptime = out.strip().split()[2].strip(',').split(':')
            if datetime.time(int(uptime[0]), int(uptime[1]), int(uptime[2])) < datetime.time(00,2,0):
                _logger.info("Reboot is successful")
                return 0
            else:
                _logger.info('Looks like reboot failed!')
                _logger.info('System uptime is {}'.format(datetime.time(int(uptime[0]), int(uptime[1]), int(uptime[2]))))
                return -1
        _logger.info('The command "uptime" failed to print output')  
        """
        return 0

    def ssh_disconnect(self):
        """Function to disconnect from the remote machine connected using ssh

            :param ssh_instance: return value from ssh_connect(,,)
            :type ssh_instance: hex integer e.g. '10.223.246.8'
        """
        self.connection.close()

    def scp_remote_to_local(self, dst_path):
        """Function to copy remote file or directory to local current execution directory path

            :param dst_path: Remote destination directory path
            :type dst_path: string e.g. '/root/home/user'
            :return: 0 on success
            :rtype: integer
        """
        scp = SCPClient(self.connection.get_transport())
        scp.get(dst_path, recursive=True)
        _logger.info('SCP Remote to Local is Successful. Remote_path: {}, Local_path: {}'.format(dst_path, os.getcwd()))
        scp.close()
        return 0

    def scp_local_to_remote(self, src_path, dst_path):
        """Function to copy local file to remote destination

            :param src_path: Local source directory path
            :type src_path: string e.g. '/root/home/user'
            :param dst_path: Remote destination directory path
            :type dst_path: string e.g. '/root/home/user'
            :return: 0 on success
            :rtype: integer
        """
        # SCPCLient takes a paramiko transport as an argument
        scp = SCPClient(self.connection.get_transport())
        if os.path.isfile(src_path) == True:
            scp.put(src_path, dst_path)
        # Uploading the 'test' directory with its content in the
        # '/home/user/dump' remote directory
        else:
            scp.put(src_path, recursive=True, remote_path=dst_path)
        _logger.info('SCP Local to Remote is Successful. Local_path: {}, Remote_path: {}'.format(src_path, dst_path))
        scp.close()
        return 0

    def is_remote_machine_alive(self, timeout):
        """Function to check whether the remote machine is alive or not

            :param remote_ip: Remote machine IP Address
            :type remote_ip: string e.g. '10.223.246.8'
            :param timeout: Waiting time
            :type timeout: integer
            :return: True if alive else False
            :rtype: Boolean
        """
        print('Checking remote IP {} is reachable or not...'.format(self.remote_ip))
        wait_time = timeout
        while wait_time > 0:
            try:
                response = subprocess.check_output(['ping', '-c', '3', self.remote_ip], stderr = subprocess.STDOUT, universal_newlines=True)
            except subprocess.CalledProcessError:
                response = None
                sys.stdout.write('\r'+'Waiting for '+str(wait_time)+' Seconds...')
                sys.stdout.flush()
            if response:
                print('\nRemote IP {} is reachable.'.format(self.remote_ip))
                print('Waiting for 30 seconds for system to configure services after boot (if fresh boot)')
                time.sleep(30) # Buffer of 30 seconds for system to configure services after boot
                return True
            wait_time=wait_time-3
        print('\nEven after {} seconds, remote IP {} is not reachable'.format(timeout, self.remote_ip))
        return False

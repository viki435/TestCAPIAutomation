#!/usr/bin/env python

import paramiko
import select
import os
import sys
import time
import stat
import datetime
from scp import SCPClient
import fileinput

nbytes = 1048576


repo = "https://ubit-artifactory-or.intel.com/artifactory/list/vmware_os-or-local/ESXi_8.0_RC1/Release/"
sourece_file_name = 'VMware-VMvisor-Installer-8.0-RC1-10238925-2.x86_64.iso'
destination_file_name = 'VMware-VMvisor-Installer-8.0-RC1-10238925-2.x86_64.iso'
boot_cfg_efi_dir='/gfs/group/VCE/shared/extract_data/efi/boot'

def ssh_connect(remote_ip, user_name, passwd):
    """Function to connect to Remote Machine

        :param remote_ip: Remote ESXi host IP Address
        :type remote_ip: string e.g. '10.223.246.8'
        :param user_name: Remote machine Username
        :type user_name: string e.g. 'root'
        :param passwd: Remote machine Password
        :type passwd: string e.g. 'intel@123'
        :return: ssh instance
        :rtype: hex
    """
    ssh = None
    for iterations in range(3):
        try:
            ssh = paramiko.SSHClient()  # ??ssh??
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=remote_ip, port=22, username=user_name, password=passwd, look_for_keys = False, allow_agent = False)
            print('Connected to remote machine {}.'.format(remote_ip))
            return ssh        
        except paramiko.AuthenticationException:
            print("Authentication failed, please verify your credentials")        
        except paramiko.SSHException as sshException:
            print("Unable to establish SSH connection: %s" % sshException)
        except paramiko.BadHostKeyException as badHostKeyException:
            print("Unable to verify server's host key: %s" % badHostKeyException)
        except paramiko.ssh_exception.NoValidConnectionsError as NoValidConnectionsError:
            print("Unable to Connect: %s" % NoValidConnectionsError)
    return ssh

def ssh_cmd_execute(ssh_instance, cmd, exec_path, timeout):
    """Function to execute the command on Remote Machine from ssh_instance

        :param ssh_instance: return value from ssh_connect(,,)
        :type ssh_instance: hex integer
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
        print('[Remote command $:] {}'.format(cmd_exec))
        stdin, stdout, stderr = ssh_instance.exec_command(cmd_exec, timeout=timeout)
    except AttributeError as e:
        print('SSH connection broke! %s' % e)
        return -1
    buffer = '' # Initializing buffer        
    while not stdout.channel.exit_status_ready():
        ''' Only print data if there is data to read in the channel'''
        if stdout.channel.recv_ready():
            rl, wl, xl = select.select([ stdout.channel ], [ ], [ ], 0.0)
            if len(rl) > 0:
                tmp = stdout.channel.recv(nbytes)
                buffer = tmp.decode()

def scp_local_to_remote(ssh_instance, src_path, dst_path):
    """Function to copy local file to remote destination

        :param ssh_instance: return value from ssh_connect(,,)
        :type ssh_instance: hex integer
        :param src_path: Local source directory path
        :type src_path: string e.g. '/root/home/user'
        :param dst_path: Remote destination directory path
        :type dst_path: string e.g. '/root/home/user'
        :return: 0 on success
        :rtype: integer
    """
    # SCPCLient takes a paramiko transport as an argument
    scp = SCPClient(ssh_instance.get_transport())
    if os.path.isfile(src_path) == True:
        scp.put(src_path, dst_path)
    # Uploading the 'test' directory with its content in the
    # '/home/user/dump' remote directory
    else:
        scp.put(src_path, recursive=True, remote_path=dst_path)
    print('SCP Local to Remote is Successful. Local_path: {}, Remote_path: {}'.format(src_path, dst_path))
    scp.close()
    return 0

def replace_line_bystr(cfg_dir, pref_str,pref_replace,file_stwith, file_endwith):
    print("called function")
    print(cfg_dir)
    print(file_stwith)
    print(file_endwith)
    print(pref_str)
    print(pref_replace)
    cfg_dir = os.getcwd()
    print(cfg_dir)
    cfg = os.listdir(cfg_dir)
    print(cfg)
    for filename in cfg:
        if filename.startswith(file_stwith) and filename.endswith(file_endwith):
            for line in fileinput.input(filename, inplace = 1):
                if pref_str in line:
                    print (line.replace(line,pref_replace))
                else:
                    print(line)

def download_file(user, password):
    ssh_instance = ssh_connect('capi-shell.intel.com',  user, password)
    print(ssh_instance)
    cmd="wget --user={0} --password={1} -O".format(user, password)+ " "+ destination_file_name+" " + repo + sourece_file_name
    exec_path='/gfs/group/VCE/shared'
    ssh_cmd_execute(ssh_instance, cmd, exec_path, 300)

def extract_iso(user, password):
    ssh_instance = ssh_connect('capi-shell.intel.com',   user, password)
    iso_extract_path="/gfs/group/VCE/update_iso_tools"

    remove_content ="/gfs/group/VCE/shared/extract_data"
    ssh_cmd_execute(ssh_instance, "rm -r %s/*" % remove_content , remove_content, 300)

    ssh_cmd_execute(ssh_instance, 'cd', iso_extract_path, 300)
    ssh_cmd_execute(ssh_instance, 'pwd', iso_extract_path, 300)

    cmd_extract="./unpack_iso.sh  -no-directory -output-directory /gfs/group/VCE/shared/extract_data/ /gfs/group/VCE/shared/%s" % destination_file_name
    ssh_cmd_execute(ssh_instance, cmd_extract, iso_extract_path, 300)


if __name__ == '__main__':
    # execute only if run as the entry point into the program
    #E.g. 
    #>> down_copy_iso.py 'username' 'password' 'fl31ca105gs1301'
    user = sys.argv[1]
    password = sys.argv[2]
    platform = sys.argv[3]

    #print(user,password,platform)
    #download_file(user, password)
    
    extract_iso(user, password)
    ssh_instance = ssh_connect('capi-shell.intel.com', user, password)

    rm_spce="sed -i 's/\///g' boot.cfg"
    ssh_cmd_execute(ssh_instance, rm_spce, boot_cfg_efi_dir, 300)

    scp_local_to_remote(ssh_instance,'change_str_line.py', boot_cfg_efi_dir)
    output =ssh_cmd_execute(ssh_instance, 'python change_str_line.py "{0}"'.format(platform), boot_cfg_efi_dir, 300)
    print(output)

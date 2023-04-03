#!/usr/bin/env python
"""This module contains various functions related to VM"""

from avocado.utils import ssh
from avocado import Test

import os
import sys
import datetime
import time
from subprocess import call
from subprocess import call
from tools import cli, tasks, service_instance, pchelper, tasks, task
from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnectNoSSL, SmartConnect
from wait_for import TimedOutError, wait_for
import re
from utils.ssh_utils import SSH
#from remote_utility import ssh_cmd_execute
import requests

def set_reserved_mem_to_max(self, host, user, pwd, vm_name):
    '''
    Description: This function is used to set the reserved memory of the VM to maximum 
    :param host: The IP of the ESXi
    :type: str
    :param user: User name of the ESXi
    :type: str
    :param pwd: Password of the ESXi
    :type: str
    :param vm_name: Name of the VM to set memory reservation
    :type: str
    :return True, False: Returns True if it sets the memReservation to Max else returns False
    :return type: bool

    '''
    self.log.debug('Connecting to the host...')
    si = SmartConnectNoSSL(host=host, user=user, pwd=pwd)
    self.log.debug('Successfully connected to host')

    content = si.RetrieveContent()
    self.log.debug('Finding the object of the VM ', vm_name)
    vm_obj = pchelper.get_obj(content, [vim.VirtualMachine], vm_name)

    summary = vm_obj.summary
    self.log.debug('The configuration summary of the VM {} is {}'.format(vm_name, summary))

    assigned_memory = vm_obj.summary.config.memorySizeMB
    self.log.debug('The memory assigned to the VM is ', assigned_memory)

    reserved_memory = vm_obj.summary.config.memoryReservation
    self.log.debug('The memory reserved in the VM is ', reserved_memory)

    if assigned_memory == reserved_memory:
        self.log.debug('Memory reservation is already set to max')
        return True

    self.log.debug('Lets set the MemoryReservation to Max...')
    specification = vim.vm.ConfigSpec()
    self.log.debug('Specification of the VM is ',specification)
    specification.memoryReservationLockedToMax = True
    task.WaitForTask(vm_obj.Reconfigure(specification))

    self.log.debug('Checking the memory reservation now..')

    if assigned_memory == reserved_memory:
        self.log.debug('Memory reservation is set to max')
        return True

    else:
        self.log.debug('Could not set the memory reservation to Maximum.. Please check manually')
        return False


def set_mac_addr(self, host, user, pwd, vm_name, addr_type, mac_addr):
    '''
    Author: nithin2x
    E-Mail: nithinx.krishnamurthy@intel.com
    Description: This function is used to set the reserved memory of the VM to maximum 
    :param host: The IP of the ESXi
    :type: str
    :param user: User name of the ESXi
    :type: str
    :param pwd: Password of the ESXi
    :type: str
    :param vm_name: Name of the VM to set memory reservation
    :type: str
    :param addr_type: This parameter allows only 3 values: 'Manual', 'Assigned', 'Generated'
    :type: str
    :param mac_addr: A Valid MAC address
    :type: str
    :param ethernet_name: The name of the adapter you want to change
    :type: str
    :return True, False: Returns True if it sets the memReservation to Max else returns False
    :return type: bool
    '''
    si = SmartConnectNoSSL(host=host, user=user, pwd=pwd)
    content = si.RetrieveContent()

    vm_obj = pchelper.get_obj(content, [vim.VirtualMachine], vm_name)

    if not vm_obj:
        self.fail('Unable to locate the virtual machine ', vm_name)
        return False

    deviceToChange = []
    for device in vm_obj.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                deviceToChange = device

    self.log.debug(deviceToChange)

    nic = vim.vm.device.VirtualDeviceSpec()
    nic.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
    nic.device = deviceToChange

    try:        
        nic.device.addressType = addr_type
        nic.device.macAddress = mac_addr

    except:
        raise Exception('Please enter the Valid MAC address or valid Address Type')

    # Create an empty spec object
    spec = vim.vm.ConfigSpec()
    self.log.debug('After editing, the ethernet files is:')
    self.log.debug(nic)

    deviceToChange = [nic]
    spec.deviceChange = deviceToChange
    task = vm_obj.ReconfigVM_Task(spec=spec)
    tasks.wait_for_tasks(si, [task])
    self.log.debug('Modified the NIC successfully')

    return True

def set_reserved_mem_to_maximum(self, host, user, pwd, vm_name):
    '''
    Description: This function is used to set the reserved memory of the VM to maximum 
    :param host: The IP of the vCenter
    :type: str
    :param user: User name of the vCenter
    :type: str
    :param pwd: Password of the vCenter
    :type: str
    :param vm_name: Name of the VM to set memory reservation
    :type: str
    :return True, False: Returns True if it sets the memReservation to Max else returns False
    :return type: bool

    '''
    self.log.debug('Connecting to the host...')
    si = SmartConnectNoSSL(host=host, user=user, pwd=pwd)
    self.log.debug('Successfully connected to host')

    content = si.RetrieveContent()
    self.log.debug('Finding the object of the VM ', vm_name)
    vm_obj = pchelper.get_obj(content, [vim.VirtualMachine], vm_name)

    summary = vm_obj.summary
    self.log.debug('The configuration summary of the VM {} is {}'.format(vm_name, summary))

    self.log.debug('Lets set the MemoryReservation to Max...')
    spec = vim.vm.ConfigSpec()
    self.log.debug('Specification of the VM is ',spec)
    spec.memoryReservationLockedToMax = True
    task = vm_obj.ReconfigVM_Task(spec=spec)
    tasks.wait_for_tasks(si, [task])

    self.log.debug('The reserved memory in the VM is:',spec.memoryReservationLockedToMax)

    if spec.memoryReservationLockedToMax:
        return True
    else:
        return False


def clone_VM(self, host, user, pwd, src_vmname, clone_vmname, clone_spec):
    """
    Author: nithin2x
    E-Mail: nithinx.krishnamurthy@intel.com
    Description: This function is used to clone the VM
    :param host: The IP of the vCneter
    :type: str
    :param user: User name of the vCneter
    :type: str
    :param pwd: Password of the vCneter
    :type: str
    :param:src_vmname: Name of the source vm to be cloned
    :type: String
    :param:clone_vmname: Name of the newly cloned VM
    :type: String
    :param:clone_spec: Specification/Configurations of the clone
    :type: PlacementSpec, CustomizationSpec, VirtualMachineConfigSpec, VirtualMachineRelocateSpec
    """
    si = SmartConnectNoSSL(host=host, user=user, pwd=pwd)
    content = si.RetrieveContent()

    vm_obj = pchelper.get_obj(content, [vim.VirtualMachine], src_vmname)
    folder_obj = vm_obj.parent

    if not vm_obj:
        self.fail('Unable to locate the virtual machine ', src_vmname)
        return False

    task = vm_obj.CloneVM_Task(folder_obj, clone_vmname, clone_spec)
    tasks.wait_for_tasks(si, [task])

    return True

    
def execute_program_in_vm(si, vm_name, vm_user_name, vm_passwd, path_to_program, program_arguments):
    """
    Author: sriramrx
    API for executing a process in the VM without the
    network requirement to actually access it.
    :param si: si object
    :param vm_name: VM name of VMs inside which program execution is to be done
    :type vm_name: string
    :param vm_user_name: user name for vm
    :type vm_user_name: string
    :param vm_passwd: passwd of the vm
    :type vm_passwd: string
    :param path_to_program: path of program bin in VM
    :type path_to_program: string
    :param program_arguments: program arguments if any
    :type program_arguments: string
    :return: True if program executed successfully
    """
    try:
        content = si.RetrieveContent()
        vm = None
        if vm_name:
            vm = pchelper.get_obj(content, [vim.VirtualMachine], vm_name)

        if not vm:
            raise SystemExit("Unable to locate the virtual machine.")
            return -1

        creds = vim.vm.guest.NamePasswordAuthentication(
            username=vm_user_name, password=vm_passwd)

        try:
            profile_manager = content.guestOperationsManager.processManager

            program_spec = vim.vm.guest.ProcessManager.ProgramSpec(
                programPath=path_to_program,
                arguments=program_arguments)

            res = profile_manager.StartProgramInGuest(vm, creds, program_spec)

            if 'reboot' in path_to_program:
                print("Successfully rebooted the VM {}".format(vm_name))
                return 0

            if '/proc/sysrq-trigger' in program_arguments:
                print("Successfully executed crash command inside the VM {}".format(vm_name))
                return 0     
                
            if res > 0:
                print("Program submitted, PID is %d" % res)
                pid_exitcode = \
                    profile_manager.ListProcessesInGuest(vm, creds, [res]).pop().exitCode
                while re.match('[^0-9]+', str(pid_exitcode)):
                    print("Program running, PID is %d" % res)
                    print("The VM is {}".format(vm_name))
                    time.sleep(5)
                    pid_exitcode = \
                        profile_manager.ListProcessesInGuest(vm, creds, [res]).pop().exitCode
                    if pid_exitcode == 0:
                        print("Program %d completed with success" % res)
                        print("The VM is {}".format(vm_name))
                        return 0
                    elif re.match('[1-9]+', str(pid_exitcode)):
                        print("ERROR: Program %d completed with Failure" % res)
                        print("  tip: Try running this on guest %r to debug"
                              % vm.summary.guest.ipAddress)
                        print("ERROR: More info on process")
                        print(profile_manager.ListProcessesInGuest(vm, creds, [res]))
                        return -1

        except IOError as ex:
            print(ex)
            return -1
    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1    


def add_virtual_disk(self, si, vm_name, disk_size, disk_type):
    """
    Author: sriramrx
    API for attaching a virtual disk to the VM 
    :param si: si object
    :param vm_name: VM name of VM to which disk has to be attached
    :type vm_name: string
    :param disk_size: size if the disk to be attached
    :type disk_size: string
    :param disk_type: type of the disk e.g: thin, thick
    :type disk_type: string
    :return: unit_number of the attached disk 
    :rtype: int
    """
    try:
        content = si.RetrieveContent()
        vm = None
        vm = pchelper.get_obj(content, [vim.VirtualMachine], vm_name)
        spec = vim.vm.ConfigSpec()
        # get all disks on a VM, set unit_number to the next available
        unit_number = 0
        controller = None

        for device in vm.config.hardware.device:
            if hasattr(device.backing, 'fileName'):
                unit_number = int(device.unitNumber) + 1
                # unit_number 7 reserved for scsi controller
                if unit_number == 7:
                    unit_number += 1
                if unit_number >= 16:
                    self.log.debug("Too many disks")
                    self.fail("Failed to add virtual disk to {}".format(vm_name))
            if isinstance(device, vim.vm.device.VirtualSCSIController):
                controller = device
        if controller is None:
            self.log.debug("Disk SCSI controller not found!")
            self.fail("Failed to add virtual disk to {}".format(vm_name))
        # add disk here
        dev_changes = []
        new_disk_kb = int(disk_size) * 1024 * 1024
        disk_spec = vim.vm.device.VirtualDeviceSpec()

        disk_spec.fileOperation = "create"
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.backing = \
            vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        if disk_type == 'thin':
            disk_spec.device.backing.thinProvisioned = True
        disk_spec.device.backing.diskMode = 'persistent'
        disk_spec.device.unitNumber = unit_number
        disk_spec.device.capacityInKB = new_disk_kb
        disk_spec.device.controllerKey = controller.key
        dev_changes.append(disk_spec)
        spec.deviceChange = dev_changes
        task = vm.ReconfigVM_Task(spec=spec)
        tasks.wait_for_tasks(si, [task])
        self.log.debug("{} GB disk added to {}".format(str(disk_size), str(vm.config.name)))
        return unit_number

    except Exception as e:
        self.log.debug("Caught exception: %s" % str(e))
        self.fail("Failed to add the virtual disk to {}".format(vm_name))


def delete_virtual_disk(self, si, ssh_session, vm_path, vm_name, disk_number):
    """
    Author: sriramrx
    API for removing a virtual disk from the VM and deleting the virtual disk files
    from datastore
    :param si: si object
    :param ssh_session: paramiko session object to the host
    :param vm_path: datastore path to the vm
    :type vm_path: string
    :param vm_name: VM name of VM to which disk has to be attached
    :type vm_name: string
    :param disk_number: disk number(unit_number + 1) of the disk to be removed
    :type disk_number: int
    """
    try:
        content = si.RetrieveContent()
        vm = None
        vm_obj = pchelper.get_obj(content, [vim.VirtualMachine], vm_name)
        spec = vim.vm.ConfigSpec()

        hdd_prefix_label = 'Hard disk '
        hdd_label = hdd_prefix_label + str(disk_number)
        virtual_hdd_device = None
        for dev in vm_obj.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualDisk) \
                    and dev.deviceInfo.label == hdd_label:
                virtual_hdd_device = dev
        if not virtual_hdd_device:
            self.fail('Virtual {} could not '
                            'be found.'.format(virtual_hdd_device))

        virtual_hdd_spec = vim.vm.device.VirtualDeviceSpec()
        virtual_hdd_spec.operation = \
            vim.vm.device.VirtualDeviceSpec.Operation.remove
        virtual_hdd_spec.device = virtual_hdd_device

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [virtual_hdd_spec]
        task = vm_obj.ReconfigVM_Task(spec=spec)
        tasks.wait_for_tasks(si, [task])
        self.log.debug("Removed the disk from {}".format(vm_name))
        dst_disk = vm_path + vm_name + "/" + vm_name + "_" + str(disk_number-1) + ".vmdk"
        dst_disk_flat = vm_path + vm_name + "/" + vm_name + "_" + str(disk_number-1) + "-flat.vmdk"
        rm_dst_disk_cmd = "rm -rf " + dst_disk
        rm_dst_disk_flat_cmd = "rm -rf " + dst_disk_flat
        out = ssh_cmd_execute(ssh_session, rm_dst_disk_cmd, '', 30)
        if out == -1:
            self.fail("Failed to delete virtual disk file")
        out = ssh_cmd_execute(ssh_session, rm_dst_disk_flat_cmd, '', 30)
        if out == -1:
            self.fail("Failed to delete virtual flat disk file")
        self.log.debug("Deleted the virtual disk")        

    except Exception as e:
        self.log.debug("Caught exception: %s" % str(e))
        self.fail("Failed to remove the virtual disk from {}".format(vm_name))


def upload_file_to_vm(si, remote_esxi_ip, vm_name, vm_user_name, vm_passwd, remote_file_path, local_file_path):
    """
    API for Uploading a file from host to guest
    :param remote_esxi_ip: ip of ESXi host
    :type remote_esxi_ip: string
    :param vm_name: VM name for VMs for which file upload is to be done
    :type vm_name: string
    :param vm_user_name: user name for vm
    :type vm_user_name: string
    :param vm_passwd: passwd of the vm
    :type vm_passwd: string
    :param remote_file_path: path of file inside VM
    :type remote_file_path: string
    :param local_file_path: path of file inside automation server
    :type local_file_path: string
    :return: True if file is uploaded successfully
    """
    vm_path = remote_file_path
    try:
        content = si.RetrieveContent()

        if vm_name:
            content = si.RetrieveContent()
            vm = pchelper.get_obj(content, [vim.VirtualMachine], vm_name)

        if not vm:
            raise SystemExit("Unable to locate VirtualMachine.")
            return -1

        print("Found: {0}".format(vm.name))

        tools_status = vm.guest.toolsStatus
        if (tools_status == 'toolsNotInstalled' or
                tools_status == 'toolsNotRunning'):
            raise SystemExit(
                "VMwareTools is either not running or not installed. "
                "Rerun the script after verifying that VMWareTools "
                "is running")
            return -1

        creds = vim.vm.guest.NamePasswordAuthentication(
            username=vm_user_name, password=vm_passwd)
        with open(local_file_path, 'rb') as myfile:
            data_to_send = myfile.read()

        try:
            file_attribute = vim.vm.guest.FileManager.FileAttributes()
            url = content.guestOperationsManager.fileManager. \
                InitiateFileTransferToGuest(vm, creds, vm_path,
                                            file_attribute,
                                            len(data_to_send), True)

            url = re.sub(r"^https://\*:", "https://"+str(remote_esxi_ip)+":", url)
            resp = requests.put(url, data=data_to_send, verify=False)
            if not resp.status_code == 200:
                print("Error while uploading file")
                return -1
            else:
                print("Successfully uploaded file")
                return 0
        except IOError as ex:
            print(ex)
            return -1
    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0

def download_file_from_vm(si, remote_esxi_ip, vm_name, vm_user_name, vm_passwd, remote_file_path, local_file_path, port_no=443):
    """
    API for downloading a file from host to guest
    :param remote_esxi_ip: ip of ESXi host
    :type remote_esxi_ip: string
    :param vm_name: VM name for VMs from which file download is to be done
    :type vm_name: string
    :param vm_user_name: user name for vm
    :type vm_user_name: string
    :param vm_passwd: passwd of the vm
    :type vm_passwd: string
    :param remote_file_path: path of file inside VM
    :type remote_file_path: string
    :param local_file_path: path of file inside automation server
    :type local_file_path: string
    :param port_no: port to be used for url
    :type port_no: int
    :return: True if file is uploaded successfully
    """
    vm_path = remote_file_path
    try:
        content = si.RetrieveContent()

        if vm_name:
            content = si.RetrieveContent()
            vm = pchelper.get_obj(content, [vim.VirtualMachine], vm_name)

        if not vm:
            raise SystemExit("Unable to locate VirtualMachine.")
            return -1

        print("Found: {0}".format(vm.name))

        tools_status = vm.guest.toolsStatus
        if (tools_status == 'toolsNotInstalled' or
                tools_status == 'toolsNotRunning'):
            raise SystemExit(
                "VMwareTools is either not running or not installed. "
                "Rerun the script after verifying that VMWareTools "
                "is running")
            return -1

        creds = vim.vm.guest.NamePasswordAuthentication(
            username=vm_user_name, password=vm_passwd)

        try:
            fti = content.guestOperationsManager.fileManager. \
                InitiateFileTransferFromGuest(vm, creds, vm_path)
            
            url = fti.url
            
            url = re.sub(':443', ':'+str(port_no), url)
            url = re.sub(r"^https://\*:", "https://"+str(remote_esxi_ip)+":", url)

            resp=requests.get(url, verify=False)

            with open(local_file_path, 'wb') as f:
                    f.write(resp.content)

        except IOError as ex:
            print(ex)
            return -1
    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0



from tools.tasks import wait_for_tasks
from pyVmomi import vim, vmodl
from tools import pchelper, tasks
from pyVim.connect import SmartConnectNoSSL
from pyVim.connect import SmartConnect
from pyVim.connect import Disconnect
from utils.ssh_utils import SSH
import ssl
import time
import logging
import os
import re

_logger = logging.getLogger(__name__)

class VM_Actions(object):

    def __init__(self, remote_ip, user_name, passwd):
        """
        Constructs all the necessary attributes for the VM_Actions object.
        """
        self.remote_ip =  remote_ip
        self.user_name = user_name
        self.passwd = passwd

    def get_VM_names(self, VM_name, Start_VM_Index, VM_Count):
        """
        """
        if VM_Count > 1:
            src_vm_name = VM_name[:len(VM_name)-1]
            VMs = [src_vm_name+str(i) for i in range(Start_VM_Index, Start_VM_Index+VM_Count)]
        else:
            VMs = [VM_name]
        return VMs

    def connect_vcenter_client(self, vc_name, vc_username, vc_password):
        """
        :param vc_name: vCenter server IP Address
        :type vc_name: string e.g. '10.223.246.8'
        :param vc_username: vCenter server Username
        :type vc_username: string e.g. 'xyz@vsphere.local'
        :param vc_password: vCenter server Password
        :type vc_password: string e.g. 'intel@123'
        :return: service instance si
        :rtype: class
        """
        try:
            si = SmartConnectNoSSL(host=vc_name, user=vc_username, pwd=vc_password)
            return si

        except ConnectionRefusedError:
            print("Invalid vCenter IP")

        except vim.fault.InvalidLogin:
            print("Invalid login")        

    def enable_vmkernel_service(self, vc_name, vc_username, vc_password, host_ip, service_type):
        """
        Function to enable given service on vmkernel NIC of ESXi host
        :param vc_name: vCenter server IP Address
        :param vc_username: vCenter server Username
        :param vc_password: vCenter server Password
        :param host_ip: IP if the ESXi host
        :param service_type: type of service to be enabled on the vmkernel
        :return: success/fail
        :rtype: int
        """         
        try:
            si = self.connect_vcenter_client(vc_name, vc_username, vc_password)
            content = si.RetrieveContent()
            host_obj =  pchelper.get_obj(content, [vim.HostSystem], host_ip)
            vmkernel_nic_obj = self.get_vmkernel_by_ip(host_obj, host_ip)
            vnic_manager = host_obj.configManager.virtualNicManager
            ret_val = self.set_service_type(vnic_manager, vmkernel_nic_obj, service_type, operation='select')
            return ret_val
        except Exception as e:
            print("Caught exception: %s" % str(e))
            return -1        

    def get_vmkernel_by_ip(self, host_obj, ip_address):
        """
        Function to return vnic object of host
        :param host_obj: Host object
        :param ip_address: ip of the ESXi host
        """
        for vnic in host_obj.config.network.vnic:
            if vnic.spec.ip.ipAddress == ip_address:
                return vnic
        return None

    def set_service_type(self, vnic_manager, vmk, service_type, operation='select'):
        """
        Function to set/unset particular service on vmkernel NIC
        :param vnic_manager: virtual nic manager of host
        :param vmk: vnic object of host
        :param service_type: type of service to be set/unset on the vmkernel
        :param operation: set/unset the particular service
        :return: success/fail
        :rtype: int   
        """
        try:
            if operation == 'select':
                vnic_manager.SelectVnicForNicType(service_type, vmk.device)
                return 0
            elif operation == 'deselect':
                vnic_manager.DeselectVnicForNicType(service_type, vmk.device)
                return 0
        except vmodl.fault.InvalidArgument as invalid_arg:
                msg="Failed to {} VMK service type {} on {}".format(operation, service_type, vmk.device)
                print(msg)
                return -1

    def vmotion(self, vc_name, vc_username, vc_password, vm_name, destination_host, mode, wait='yes', destination_datastore='', storage_vmotion=False):
        """
        Function to perform vMotion
        :param vc_name: vCenter server IP Address
        :param vc_username: vCenter server Usernamess
        :param vc_password: vCenter server Password
        :param vm_name: Test VMs name
        :param destination_host: Target host IP to migrate VM
        :param mode: shard/non-shared determines if compute vMotion or xvMotion is to be performed
        :param wait: if set waits for vMotion to complete else perform vMotion and return task object of the migration
        :return: success/fail if wait is set. task object if wait is not set
        :rtype:
        """
        print(destination_datastore)
        try:
            si = self.connect_vcenter_client(vc_name, vc_username, vc_password)
            content = si.RetrieveContent()
            vm =  pchelper.get_obj(content, [vim.VirtualMachine], vm_name)
            destination_host_obj =  pchelper.get_obj(content, [vim.HostSystem], destination_host)
            
            print("Check #####A")
            resource_pool = vm.resourcePool
            print (resource_pool)
            print("Check #####B")            

            if vm.runtime.powerState != 'poweredOn':
                print("The given VM is not powered ON")
                return -1
            msg = "Migrating {} to destination host {}".format(vm_name, destination_host)
            print(msg)            
            vm_relocate_spec = vim.vm.RelocateSpec()
            vm_relocate_spec.host = destination_host_obj
            vm_relocate_spec.pool = resource_pool
            print(mode)
            if storage_vmotion:
                print('src host', vm.summary.runtime.host)
                vm_relocate_spec.host = vm.summary.runtime.host
            if mode == "non-shared":
                datastores = destination_host_obj.datastore 
                for datastore in datastores:
                    if destination_datastore:
                        print(datastore.summary.name)
                        print(datastore.summary.type)
                        if datastore.summary.name == destination_datastore:                                       
                            vm_relocate_spec.datastore = datastore
                            print(vm_relocate_spec.datastore)
                            break
                    else:
                        if datastore.summary.type == 'VMFS':
                            vm_relocate_spec.datastore = datastore
                            break
                else:
                    print("Given datastore name cant be found in the host")
                    return -1
            migrate_priority = vim.VirtualMachine.MovePriority.highPriority
            task = vm.Relocate(spec=vm_relocate_spec, priority=migrate_priority)
            
            if wait == 'yes':
                
                tasks.wait_for_tasks(si, [task])
                print("Successfully migrated the VM {} to host {}".format(vm_name,destination_host))
                Disconnect(si)
                return 0
            else:
                print("Successfully initiated the vMotion")
                return task
        except vmodl.MethodFault as e:
            print("Caught vmodl fault: %s" % e.msg)
            return -1
        except Exception as e:
            print("Caught exception: %s" % str(e))
            return -1

    def power_off_vm(self, vmnames):
        """
        API for powering off virtual machines on a system.
        :param vmnames: VM name for VMs for which power off is to be done
        :type vmnames: list of strings. e.g: ['vm_name_1', 'vm_name_2']
        :return: True if VMs powered OFF successfully
        """
        si = SmartConnectNoSSL(host=self.remote_ip, user=self.user_name, pwd=self.passwd)
        try:
            if not vmnames:
                print("No virtual machine specified for poweroff")
                return -1

            # Retreive the list of Virtual Machines from the inventory objects
            # under the rootFolder
            content = si.content
            obj_view = content.viewManager.CreateContainerView(content.rootFolder,
                                                            [vim.VirtualMachine],
                                                            True)
            vm_list = obj_view.view
            obj_view.Destroy()

            # and vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOff

            # Find the vm and power it on
            tasks = [vm.PowerOff() for vm in vm_list if (vm.name in vmnames and vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn)]

            # Wait for power on to complete
            if tasks:
                wait_for_tasks(si, tasks)

            print("Virtual Machine(s) have been powered off successfully")
            return 0
        except vmodl.MethodFault as error:
            print("Caught vmodl fault : " + error.msg)
            return -1
        except Exception as error:
            print("Caught Exception : " + str(error))
            return -1

    def power_on_vm(self, vmnames):
        """
        API for powering on virtual machines on a system.
        :param vmnames: VM name for VMs for which power on is to be done
        :type vmnames: list of strings. e.g: ['vm_name_1', 'vm_name_2']
        :return: True if VMs powered ON successfully
        """
        si = SmartConnectNoSSL(host=self.remote_ip, user=self.user_name, pwd=self.passwd)
        try:
            if not vmnames:
                print("No virtual machine specified for poweron")
                return -1

            # Retreive the list of Virtual Machines from the inventory objects
            # under the rootFolder
            content = si.content
            obj_view = content.viewManager.CreateContainerView(content.rootFolder,
                                                            [vim.VirtualMachine],
                                                            True)
            vm_list = obj_view.view
            obj_view.Destroy()

            # and vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOff

            # Find the vm and power it on
            tasks = [vm.PowerOn() for vm in vm_list if (vm.name in vmnames and vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOff)]

            # Wait for power on to complete
            if tasks:
                wait_for_tasks(si, tasks)

            print("Virtual Machine(s) have been powered on successfully")
            return 0
        except vmodl.MethodFault as error:
            print("Caught vmodl fault : " + error.msg)
            return -1
        except Exception as error:
            print("Caught Exception : " + str(error))
            return -1

    def get_ip(self, vm_name):
        """
        Author: Nithin Krishnamurthy
        E-Mail: nithinx.krishnamurthy@intel.com
        Description: This function is used to get Powerstate of the VM in the ESXi
        :param host: The IP of the ESXi
        :type: str
        :param user: User name of the ESXi
        :type: str
        :param pwd: Password of the ESXi
        :type: str
        :param: vm_name
        :type: str
        returns IP address else returns 'None'
        """
        try:
            si = SmartConnectNoSSL(host=self.remote_ip, user=self.user_name, pwd=self.passwd, port=443)
        except:
            raise Exception('Unable to connect to the the host {}'.format(self.remote_ip))
            return -1

        content = si.RetrieveContent()

        try:
            vm_obj = pchelper.get_obj(content, [vim.VirtualMachine], vm_name)
        except:
            raise Exception('The VM {} is not found in the host'.format(vm_name))
            return -1

        i = 0
        while(i<=3):
            ip = vm_obj.guest.ipAddress
            if not ip:
                i += 1
                print(f'The VM {vm_name} is not functional yet, please wait for 60 Seconds')
                time.sleep(60)
                continue
            else:
                break
        print('The IP address of the VM is {}'.format(vm_obj.guest.ipAddress))
        return ip

    def get_bootcfg(self, kernel_var, siov_value):

        esxi_session = SSH(self.remote_ip, self.user_name, self.passwd)
        esx_status = esxi_session.is_remote_machine_alive(remote_esxi_ip, 30)

        if not esx_status:
            print('ESXi {} is not reachable..'.format(remote_esxi_ip))
            return -1

        cmd = 'find / -name boot.cfg'
        esxi_session.connect()

        bootcfg_list = ['bootbank/boot.cfg', 'altbootbank/boot.cfg']
        print('boot.cfg file location is {}'.format(bootcfg_list))
        # del bootcfg_list[-1]

        # bootcfg_file = bootcfg_list[1]
        for bootcfg_file in bootcfg_list:
            print('SCP the boot.cfg file from the location {}'.format(bootcfg_file))
            esxi_session.scp_remote_to_local(bootcfg_file)

            test_fw = os.getcwd()
            file = test_fw + '/boot.cfg'
            print('The current working directory location is {}'.format(test_fw))
            bootcfg = test_fw + '/boot.cfg'
            print('boot.cfg file location is {}'.format(bootcfg))

            self.set_boot_option(bootcfg, kernel_var, siov_value)

            copy_location = bootcfg_file.rsplit('/', 1)[0]
            esxi_session.scp_local_to_remote( file, copy_location)
        return

    def set_boot_option(self, bootcfg, kernel_var, siov_value):
        regEx = kernel_var + '.*'

        # Options to enable SIOV in the variable siov_enable
        kernelopt_repl = '%s=%s'%(kernel_var, siov_value)

        with open(bootcfg, 'r') as f:
            content = f.read()
            kernel_options = re.search(regEx, content)

        with open(bootcfg, 'w') as f:
            new_content = re.sub(kernel_options[0], kernelopt_repl, content)
            f.write(new_content)

            return

    def L4_test_config_func(self, vm_name, VM_Start_Index, VM_Count, Accelerator, Accel_Start_index, Accel_Count):

        src_vm_name = vm_name[:len(vm_name)-1]

        if Accelerator == 'nic':

            passthru_id='0000:04:00.0'
            all_device_ids = ["0000:04:00.0", ]

            print("***" * 20)
            print(all_device_ids)    
            print("***" * 20)        
            print (Accel_Start_index, Accel_Start_index, Accel_Count)
            print("***" * 20)
            device_ids = all_device_ids[Accel_Start_index:Accel_Start_index+Accel_Count]

        elif Accelerator == 'ssd':
            passthru_id='0000:3b:00.0'
            all_device_ids = ["0000:3b:00.0"]
            device_ids = all_device_ids[Accel_Start_index:Accel_Start_index+Accel_Count]

        if VM_Count > 1:
            VMs = [src_vm_name+str(i) for i in range(VM_Start_Index,VM_Start_Index+VM_Count)]
        elif VM_Count == 1:
            Single_VM_name = src_vm_name+str(VM_Start_Index)
            VMs=[Single_VM_name]

        if self.power_off_vm(VMs) != 0:
            print('Failed to power OFF the VMs')
            return -1   

        if self.enable_passthru(passthru_id, Accel_Count, Accel_Start_index) != 0:
            print('Toggling passthru for {} failed'.format(str(passthru_id)))
            return -1

        if VM_Count == 1:
            for device_id in device_ids:

                print("#############")
                print(Single_VM_name)
         
                if self.add_vf_to_vm(Single_VM_name, device_id) != 0:
                    print('Failed to attach {} devices to the VM'.format(Accelerator))
                    return -1
        else:
            zip_obj = zip(VMs, device_ids)
            for VM, device_id in zip_obj:
                if self.add_vf_to_vm(VM, device_id) != 0:
                    print('Failed to attach {} device to the VM {}'.format(Accelerator,VM))
                    return -1

        return 0

    def L4_test_clean_func(self, vm_name, VM_Start_Index, VM_Count, Accelerator, Accel_Start_index, Accel_Count):

        src_vm_name = vm_name[:len(vm_name)-1]
        if Accelerator == 'nic':
                passthru_id='0000:04:00.0'
                all_device_ids = ["0000:04:00.0"]
                device_ids = all_device_ids[Accel_Start_index:Accel_Start_index+Accel_Count]

        elif Accelerator == 'ssd':
            passthru_id='0000:3b:00.0'
            all_device_ids = ["0000:3b:00.0"]
            device_ids = all_device_ids[Accel_Start_index:Accel_Start_index+Accel_Count]    

        if VM_Count > 1:
            VMs = [src_vm_name+str(i) for i in range(VM_Start_Index,VM_Start_Index+VM_Count)]
        elif VM_Count == 1:
            Single_VM_name = src_vm_name+str(VM_Start_Index)
            VMs = [Single_VM_name]

        if self.power_off_vm(VMs) != 0:
            print('Failed to power OFF the VMs')
            return -1   

        if VM_Count == 1:
            for device_id in device_ids:
                if self.del_vf_from_vm(Single_VM_name, device_id) != 0:
                    print('Failed to remove {} devices from the VM'.format(Accelerator))
                    return -1
        else:
            zip_obj = zip(VMs, device_ids)
            for VM, device_id in zip_obj:
                if self.del_vf_from_vm(VM, device_id) != 0:
                    print('Failed to remove {} devices from the VM {}'.format(Accelerator,VM))
                    return -1
                
        if self.disable_passthru(passthru_id, Accel_Count, Accel_Start_index) != 0:
            print('Disabling passthru for {} failed'.format(Accelerator))
            return -1

        return 0

    def enable_passthru(self, device_id, number, start_index=0):
        """Function to enable passthru for a given device

            :param device_id: device id for device that we want to enable passthru
            :type device_id: string e.g. '2710'
            :param number: Number of devices for which we want to enable passthru
            :type number: int e.g. 8
            :param esxi_session: paramiko object of ESXi host
            :param start index: device start index. ranges from 0 to accelerator count
            :return: 0:success or -1:fail
            :rtype: int
        """
        cmd = 'lspci -p | grep ' + str(device_id)

        esxi_session = SSH(self.remote_ip, self.user_name, self.passwd)
        esxi_session.connect()
        stdin, stdout, stderr = esxi_session.connection.exec_command(cmd, timeout=100)

        out = stdout.read().decode('utf-8')
        print(out)
        devices = out.splitlines()[start_index:start_index+number]
        for device in devices:
            if not 'pciPassthru' in device:
                dev_id = device.split(' ')[0]
                cmd = 'esxcli hardware pci pcipassthru set -a -d={} -e=true'.format(dev_id)
                out = esxi_session.execute_cmd(cmd, '', 100)
                if 'Failed' in out:
                    return -1
                print('Toggled passthru for dev {}'.format(dev_id))
        cmd = 'lspci -p | grep ' + str(device_id)
        out = esxi_session.execute_cmd(cmd, '', 100)    
        return 0
  
    def disable_passthru(self, device_id, number, start_index=0):
        """Function to disable passthru for a given device

            :param device_id: device id for device that we want to disable passthru
            :type device_id: string e.g. '2710'
            :param number: Number of devices for which we want to disable passthru
            :type number: int e.g. 8
            :param esxi_session: paramiko object of ESXi host
            :param start index: device start index. ranges from 0 to accelerator count
            :return: 0:success or -1:fail
            :rtype: int
        """
        cmd = 'lspci -p | grep ' + str(device_id)

        esxi_session = SSH(self.remote_ip, self.user_name, self.passwd)
        esxi_session.connect()
        stdin, stdout, stderr = esxi_session.connection.exec_command(cmd, timeout=100)

        out = stdout.read().decode('utf-8')
        print(out)
        devices = out.splitlines()[start_index:start_index+number]
        for device in devices:
            if 'pciPassthru' in device:
                dev_id = device.split(' ')[0]
                cmd = 'esxcli hardware pci pcipassthru set -a -d={} -e=false'.format(dev_id)
                out = esxi_session.execute_cmd(cmd, '', 100)
                if 'Failed' in out:
                    return -1
                print('Disabled passthru for dev {}'.format(dev_id))
        cmd = 'lspci -p | grep ' + str(device_id)
        out = esxi_session.execute_cmd(cmd, '', 100)    
        return 0

    def check_vf_connected(self, vm_name, vf_id):
        """
        Checking the presence of required VF required to be connected
        :param host_name: ESXi host server IP
        :param host_username: ESXi host user name
        :param host_pwd: ESXI host password
        :param vm_name: name of Virtual machine 
        :param vf_id: ESXi PCIe VF ID we want to add/remove to/from VM
        :return: True if VF is connected successfully
        """
        s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        s.verify_mode = ssl.CERT_NONE
        si = SmartConnect(host=self.remote_ip, user=self.user_name, pwd=self.passwd, sslContext=s, disableSslCertValidation=True)
        content = si.RetrieveContent()
        host_view = content.viewManager.CreateContainerView(content.rootFolder,
                                                            [vim.HostSystem],
                                                            True)
        hosts = list(host_view.view)
        _logger.debug("Hosts= ", hosts)
        if len(hosts) != 1:
            _logger.debug("ERROR : there are no/ more hosts!")
            return -1
        vm_exist = False
        vm_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
        vms = list(vm_view.view)
        for vm in vms:
            if vm.summary.config.name == vm_name:
                _logger.debug(vm_name, "present at host", self.remote_ip)
                vm_exist = True
                vm_object = vm
        if not vm_exist:
            _logger.debug(vm_name, "Exists = ", vm_exist)
            return vm_exist
        for device in vm_object.config.hardware.device:
            if device.backing != None:
                try:
                    if vf_id in device.backing.id:
                        _logger.debug(vf_id, "connected to VM: ", vm_name)
                        return True
                except AttributeError as error:
                    _logger.debug("Error: ", error)
                    continue        
        _logger.debug(vf_id, "is not connected to VM: ", vm_name)
        return False

    def add_vf_to_vm(self, vm_name, vf_id):
        """
        Adding VF to VM
        :param host_name: ESXi host IP
        :param host_username: ESXi host user name
        :param host_pwd: ESXi host password
        :param vm_name: Name of Virtual Machine
        :param vf_id: PCIe VF ID to be added
        :return: returns 0 if successfully added
        """
        if self.check_vf_connected(vm_name, vf_id):
            return 0
        s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        s.verify_mode = ssl.CERT_NONE
        si = SmartConnect(host=self.remote_ip, user=self.user_name, pwd=self.passwd, sslContext=s, disableSslCertValidation=True)
        content = si.RetrieveContent()
        host_view = content.viewManager.CreateContainerView(content.rootFolder,
                                                            [vim.HostSystem],
                                                            True)
        hosts = list(host_view.view)
        _logger.debug("Hosts= ", hosts)
        if len(hosts) != 1:
            _logger.debug("ERROR : there are no/ more hosts!")
            return -1
        vf_exist = False
        vm_exist = False
        for pci_device in hosts[0].hardware.pciDevice:
            if pci_device.id == vf_id:
                _logger.debug(vf_id, " exists at host", self.remote_ip)
                vf_exist = True
                host_pci_dev = pci_device
                vm_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
                vms = list(vm_view.view)
                for vm in vms:
                    if vm.summary.config.name == vm_name:
                        vm_exist = True
                        vm_object = vm
        if (vf_exist != True) or (vm_exist != True):
            _logger.debug(vf_id, "exists = ", vf_exist, ";",vm_name, "Exists = ", vm_exist)
            return -1
        pci_passthroughs = vm_object.environmentBrowser.QueryConfigTarget(host=None).pciPassthrough
        systemid_by_pciid = {item.pciDevice.id: item.systemId for item in pci_passthroughs}

        if host_pci_dev.id not in systemid_by_pciid:
            raise Exception("Not a passthrough device")

        # The deviceId is a signed short but the server expects the PCI device ID to be unsigned.
        spec = vim.vm.ConfigSpec()
        dev_changes = []
        new_device_spec = vim.vm.device.VirtualDeviceSpec()
        new_device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        deviceId = hex(host_pci_dev.deviceId % 2**16).lstrip('0x')  # Converting to unsigned short
        new_device_spec.device = vim.vm.device.VirtualPCIPassthrough()
        new_device_spec.device.backing = vim.VirtualPCIPassthroughDeviceBackingInfo(deviceId=deviceId, 
                                                                                    id=host_pci_dev.id, 
                                                                                    systemId=systemid_by_pciid[host_pci_dev.id],
                                                                                    vendorId=host_pci_dev.vendorId,
                                                                                    deviceName=host_pci_dev.deviceName)

        new_device_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        dev_changes.append(new_device_spec)
        spec.deviceChange = dev_changes

        task = vm_object.ReconfigVM_Task(spec=spec)
        _logger.debug(task)
        _logger.debug(vf_id, "Successfully added to VM: ", vm_name) 
        return 0

    def del_vf_from_vm(self, vm_name, vf_id):
        """
        Removing VF from VM
        :param host_name: ESXi host IP
        :param host_username: ESXi host user name
        :param host_pwd: ESXi host password
        :param vm_name: Name of Virtual Machine
        :param vf_id: PCIe VF ID to be removed
        :return: returns 0 if successfully added
        """
        if not self.check_vf_connected(vm_name, vf_id):
            return 0

        s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        s.verify_mode = ssl.CERT_NONE
        si = SmartConnect(host=self.remote_ip, user=self.user_name, pwd=self.passwd, sslContext=s, disableSslCertValidation=True)
        content = si.RetrieveContent()
        host_view = content.viewManager.CreateContainerView(content.rootFolder,
                                                            [vim.HostSystem],
                                                            True)
        hosts = list(host_view.view)
        _logger.debug("Hosts= ", hosts)
        if len(hosts) != 1:
            _logger.debug("ERROR : there are no/ more hosts!")
            return -1
        vm_exist = False
        vm_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
        vms = list(vm_view.view)
        for vm in vms:
            if vm.summary.config.name == vm_name:
                vm_exist = True
                vm_object = vm
        if not vm_exist:
            _logger.debug(vm_name, "Exists = ", vm_exist)
            return vm_exist    
        
        spec = vim.vm.ConfigSpec()
        dev_changes = []
        new_device_spec = vim.vm.device.VirtualDeviceSpec()
        new_device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        
        vf_device = None 
        for device in vm_object.config.hardware.device:
            if device.backing != None:
                try:
                    if vf_id in device.backing.id:
                        vf_device = device
                        break                    
                except AttributeError as error:
                    continue
        
        new_device_spec.device = vf_device
        dev_changes.append(new_device_spec)
        spec.deviceChange = [new_device_spec]
        task = vm_object.ReconfigVM_Task(spec=spec)

        _logger.debug(task)
        _logger.debug(vf_id, "Successfully removed from VM: ", vm_name)
        return 0

    def list_vms(self):
        """Function to list all the VMs on the given ESXi host
            :return: output of vim-cmd vmsvc/getallvms
            :rtype: string
        """
        ssh_instance = SSH(self.remote_ip, self.user_name, self.passwd)
        ssh_instance.connect()

        cmd = 'vim-cmd vmsvc/getallvms'        
        out = ssh_instance.execute_cmd(cmd, '', 30)

        if out == -1 or out == '':
            print('Failed to list vms')
            return -1    
        ssh_instance.ssh_disconnect()
        return out

    def get_vm_id(self, vm_name):
        """Function to return VM name if VM ID is given
            :param vm_name: Name of VM at ESXi host
            :type vm_name: string e.g. 'linked_clone_1'
            :return: VM ID
            :rtype: string
        """
        all_vms = self.list_vms()
        if all_vms == -1:
            return -1
        for vm_info in all_vms.split('\n'):
            if vm_name in vm_info:
                return re.sub(' +', ' ', vm_info).split(' ')[0] #Merging multiple spaces into one
        print(all_vms)
        print('The given VM {} not found in list of VMs'.format(vm_name))
        return -1

    def get_vm_name(self, vm_id):

        """Function to return VM ID if VM name is given
            :param vm_id: ID of VM at ESXi host
            :return: VM Name
            :rtype: string
        """
        all_vms = self.list_vms()
        if all_vms == -1:
            return -1
        for vm_info in all_vms.split('\n'):        
            if str(vm_id) in vm_info:
                return re.sub(' +', ' ', vm_info).split(' ')[1] #Merging multiple spaces into one
        print(all_vms)
        print('The given VM {} not found in list of VMs'.format(vm_id))
        return -1

from avocado import Test
from common.test_base import BaseContent_Test
from utils.vm_utils import VM_Actions
from utils.ssh_utils import SSH
from utils.pyvmomi_library import execute_program_in_vm, upload_file_to_vm, download_file_from_vm
from pyVim.connect import SmartConnectNoSSL
import threading
import pprint
import avocado
import logging
import time
import os

_logger = logging.getLogger(__name__)

class thread(threading.Thread):
    """Thread class customised for executing workload in VM.
       Also, it returns the result of execution in join method
    """
    def __init__(self, si, vm_name, vm_user_name, vm_passwd, path_to_program, program_arguments):
        threading.Thread.__init__(self)
        #self.content=content
        self.si=si
        self.vm_name = vm_name
        self.vm_user_name = vm_user_name
        self.vm_passwd = vm_passwd
        self.path_to_program = path_to_program
        self.program_arguments = program_arguments
        self._return = None

    def run(self):
        self._return = execute_program_in_vm(self.si, self.vm_name, self.vm_user_name, self.vm_passwd, self.path_to_program, '')

    def join(self):
        threading.Thread.join(self)
        return self._return

class VtCode_Test(BaseContent_Test):
    """
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(VtCode_Test, self).setUp()

        self.list_esxi_hosts = [
            {
            "platname": self.yaml_configuration['sut']['platform_name'],
            "esxi_host": self.yaml_configuration['sut']['esxi']['ip'],
            "esxi_user": self.yaml_configuration['sut']['esxi']['user'],
            "esxi_password": self.yaml_configuration['sut']['esxi']['password'],
            "nfs_datastore_name": self.yaml_configuration['sut']['esxi']['datastores']['nfs']['name'],
            "nfs_share_path": self.yaml_configuration['sut']['esxi']['datastores']['nfs']['nfs_share_path'],
            "vms_names":[                    
                    self.yaml_configuration['sut']['esxi']['vms']['vm1']['vm_name'],
                    self.yaml_configuration['sut']['esxi']['vms']['vm2']['vm_name'],
                    self.yaml_configuration['sut']['esxi']['vms']['vm3']['vm_name'],
                ],
            },           
        ]

        self.platforms_checkup(self.list_esxi_hosts)
        
    def test_vtmicros(self):
        """
        Test Cases: Include description

        :avocado: tags=demo
        """
        vm_name = self.yaml_configuration['sut']['esxi']['vms']['vm1']['vm_name']
        vm_name_1 = self.yaml_configuration['sut']['esxi']['vms']['vm2']['vm_name']
        vm_name_2 = self.yaml_configuration['sut']['esxi']['vms']['vm3']['vm_name']
        #vm_name = "SJ_WithUbuntu_VTMicros_3"
        print("first vm name is ", vm_name)
        print("second vm name is ", vm_name_1)
        print("third vm name is ", vm_name_2)
        _logger.info("TestCase.test_demo: init")
        time.sleep(60)

        esxi_ip = self.yaml_configuration['sut']['esxi']['ip'] 
        esxi_user = self.yaml_configuration['sut']['esxi']['user']
        esxi_password = self.yaml_configuration['sut']['esxi']['password']

        vm_actions = VM_Actions(esxi_ip, esxi_user, esxi_password)

        VMs = vm_actions.get_VM_names(vm_name, 1, 1)
        VMs_1 = vm_actions.get_VM_names(vm_name_1, 1, 1)
        VMs_2 = vm_actions.get_VM_names(vm_name_2, 1, 1)

        print(VMs)
        print(VMs_1)
        print(VMs_2)
        vms_list=VMs+VMs_1+VMs_2
        print("Vms list is ", vms_list)

        for VM in vms_list:
            if vm_actions.power_on_vm(VM) != 0:
                self.fail('powering on VM failed in iteration')
                
        _logger.info('VM Power-ON - Command Completed (machine is booting)')
        
        time.sleep(60)
        for VM in vms_list: 
            vm_ip = vm_actions.get_ip(VM)
            _logger.info('IP ADDRESS = %s' % vm_ip)
               
        
        ##############################################################
        #Create tunnel for interacting with the platform
        ##############################################################
        sut_name = self.yaml_configuration['sut']['platform_name']
        hostname_capi_server = self.capi.targets[sut_name].rtb.parsed_url.hostname

        port = self.capi.targets[sut_name].tunnel.add(22, vm_ip )

        vm_username = self.yaml_configuration['sut']['esxi']['vms']['vm1']['vm_username']
        vm_password = self.yaml_configuration['sut']['esxi']['vms']['vm1']['vm_password']

        si = SmartConnectNoSSL(host=esxi_ip, user=esxi_user, pwd=esxi_password, port=443)
        for VM in vms_list:
            print("vmname inside loop", VM)
            upload_file_to_vm(si,esxi_ip,VM,vm_username,vm_password,"/home/root1/vtmicros", '/drivers.io.vmware.validation.capi-automation/vtmicros')        
            time.sleep(20)
            upload_file_to_vm(si,esxi_ip,VM,vm_username,vm_password,"/home/root1/inputFile.config", '/drivers.io.vmware.validation.capi-automation/inputFile.config')        
            time.sleep(10)
            cmd_chng_permission = '777 vtmicros'
            cmd_chng_permission_1 = '777 inputFile.config'

            execute_program_in_vm(si, VM, vm_username, vm_password, "/usr/bin/chmod", cmd_chng_permission)  
            execute_program_in_vm(si, VM, vm_username, vm_password, "/usr/bin/chmod", cmd_chng_permission_1)

        _logger.info("establish SSH connection")
       
        
        cmd_to_vm_session = './vtmicros'
        _logger.info("Executing vtmicros...")
        #execute_program_in_vm(si, vm_name, vm_username, vm_password, "/home/root1/vtmicros", cmd_to_vm_session)  
            
        thread_list = []
        for VM in vms_list:
                output = thread(si, VM, vm_username, vm_password, '/home/root1/vtmicros', cmd_to_vm_session)
                thread_list.append(output)
    
        for i in range(0,len(thread_list)):
            thread_list[i].start()

        for i in range(0,len(thread_list)):
            rval = thread_list[i].join()
            print("Returned Value for script execution in VM {} = {}".format(i, rval))
            if rval != 0 :
                print("Script execution failed in VM {}".format(i+1))
                return -1
        
        time.sleep(60*22)

        for VM in vms_list:
            download_file_from_vm(si, esxi_ip, VM, vm_username, vm_password, '/home/root1/output.txt', "/drivers.io.vmware.validation.capi-automation/testcases/output_"+ VM +".txt", port_no=443)
            time.sleep(10)
                
        for VM in vms_list:
            if vm_actions.power_off_vm(VM) != 0:
                self.fail('powering on VM failed in iteration')
            
            _logger.info('VM Power-OFF - Completed')

        time.sleep(30)

        _logger.info("TestCase.test_demo: completed")

from avocado import Test
from common.test_base import BaseContent_Test
from utils.ssh_utils import SSH
from utils.vm_utils import VM_Actions

import avocado
import subprocess
import logging
import time

_logger = logging.getLogger(__name__)

class GetVM_PowerCli_Test(BaseContent_Test):
    """
    TODO
    
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(GetVM_PowerCli_Test, self).setUp()

        self.list_esxi_hosts = [
                {
                "platname": self.capi.suts[0],
                "esxi_host": self.ESXI_IP,
                "esxi_user": self.ESXI_USERNAME,
                "esxi_password": self.ESXI_PASSWORD,
                "nfs_datastore_name": "vce_nfs_server",
                "nfs_share_path": "/var/vce/virtual_machines_repository",
                "vms_names":[                    
                    "vm_clean_machine",                    
                    ],
                },

                {
                "platname": self.capi.suts[1],
                },
            ]
        self.platforms_checkup(self.list_esxi_hosts)


    def test_getVM_powercli(self):
        """
        Test to execute Virtualization - VMware - Cores per Socket

        :avocado: tags=18014072501  
        """
        sut = self.list_esxi_hosts[0]
        vm_actions = VM_Actions(sut.get("esxi_host"), sut.get("esxi_user"), sut.get("esxi_password"))
        #self.ESXI_IP, self.ESXI_USERNAME, self.ESXI_PASSWORD)

        vmname = sut.get("vms_names")[0]
        VMs = vm_actions.get_VM_names(vmname, 1, 1)
        #VMs = vm_actions.get_VM_names(self.ESXI_VM1_NAME, 1, 1)       

        list_value=['4','16', '2', '12']
        l=len(list_value)
        for i in range(0,l,2):
            if vm_actions.power_off_vm(VMs) != 0:
                self.fail('powering on VM failed in iteration {}'.format(i))
            time.sleep(20)

            p = subprocess.Popen(['pwsh', 'powershell_scripts/test_getVM_powercli.ps1', sut.get("esxi_host"), sut.get("esxi_user"), sut.get("esxi_password"), vmname, list_value[i], list_value[i+1]]) 
            #p = subprocess.Popen(['pwsh', 'powershell_scripts/test_getVM_powercli.ps1', self.ESXI_IP, self.ESXI_USERNAME, self.ESXI_PASSWORD, self.ESXI_VM1_NAME, list_value[i], list_value[i+1]])
            p.wait()  

            if vm_actions.power_on_vm(VMs) != 0:
                self.fail('powering on VM failed in iteration {}'.format(i))
            time.sleep(80)

            vm_ip = vm_actions.get_ip(VMs[0])
            
            print("IP address of the virtual machine", vm_ip)

            ##############################################################
            #Create tunnel for interacting with the platform
            ##############################################################
            hostname_capi = self.capi.targets[sut.get("platname")].rtb.parsed_url.hostname
            port = self.capi.targets[sut.get("platname")].tunnel.add(22, vm_ip )
            
            #esxi_vm_session = SSH(hostname_capi, "root", "intel@123", port)
            #esxi_vm_session.connect()
            #esxi_session = SSH(vm_ip, self.ESXI_VM1_USERNAME, self.ESXI_VM1_PASSWORD)

            esxi_session = SSH(hostname_capi, "root", "intel@123", port)
            esxi_session.connect()
            cmd1 = "lscpu | grep 'socket'"
            cmd2 = 'cat /proc/cpuinfo | grep processor | wc -l'
            time.sleep(10)
            corespersock_info = esxi_session.execute_cmd(cmd1, '', 30)
            time.sleep(10)
            corespersock_info=corespersock_info.strip()
            corespersock_info = corespersock_info.split(' ')
            coresper_sock = corespersock_info[-1]

            print("*****cores per socket infor after****", coresper_sock )         
            process_info=esxi_session.execute_cmd(cmd2, '', 30)
            time.sleep(10)
            process_info=process_info.rstrip()
            print("*******processors infor********", process_info)
            print(process_info.rstrip())

            if vm_actions.power_off_vm(VMs) != 0:
                self.fail('powering on VM failed in iteration {}'.format(i))
    

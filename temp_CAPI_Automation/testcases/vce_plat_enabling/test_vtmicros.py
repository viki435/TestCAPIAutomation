from avocado import Test
from common.test_base import BaseContent_Test
from utils.vm_utils import VM_Actions
from utils.ssh_utils import SSH
import pprint
import avocado
import logging
import time

_logger = logging.getLogger(__name__)

class VTMicros_Test(BaseContent_Test):
    """
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(VTMicros_Test, self).setUp()
        #First element always is the SUT(ESXi host).

        self.list_esxi_hosts = [
                {
                "platname": self.capi.suts[0],
                "esxi_host": self.ESXI_IP,
                "esxi_user": self.ESXI_USERNAME,
                "esxi_password": self.ESXI_PASSWORD,
                "nfs_datastore_name": "vce_nfs_server",
                "nfs_share_path": "/var/vce/virtual_machines_repository",
                "vms_names":[                    
                    "SJ_WithUbuntu_1_EMR",
                    ],
                },
                {
                "platname": self.capi.suts[1],
                },
            ]

        self.platforms_checkup(self.list_esxi_hosts)

    def test_vtmicros(self):
        """
        Test Cases: Include description

        :avocado: tags=demo
        """

        _logger.info("TestCase.test_demo: init")

        vm_name = "SJ_WithUbuntu_1_EMR (1)" #"SJ_WithUbuntu_1_EMR"

        time.sleep(15)

        vm_actions = VM_Actions(self.ESXI_IP, self.ESXI_USERNAME, self.ESXI_PASSWORD)
        VMs = vm_actions.get_VM_names(vm_name, 1, 1)


        if vm_actions.power_on_vm(VMs) != 0:
            self.fail('powering on VM failed in iteration')
        
        time.sleep(60*2)
        _logger.info('VM Power-ON - Completed')
        
        vm_ip = vm_actions.get_ip(vm_name)
        _logger.info('IP ADDRESS = %s' % vm_ip)
        ##############################################################
        #Create tunnel for interacting with the platform
        ##############################################################
        hostname_capi = self.capi.targets["fl31ca105gs1404"].rtb.parsed_url.hostname
        port = self.capi.targets["fl31ca105gs1404"].tunnel.add(22, vm_ip )

        print (  "ssh -p %s jwolf4@%s" % (port, hostname_capi) )

        esxi_vm_session = SSH(hostname_capi, "jwolf4", "intel@123", port)
        esxi_vm_session.connect()
        cmd_to_vm_session = './vtmicros'  
        execution = esxi_vm_session.execute_cmd(cmd_to_vm_session, '', 600)
        _logger.info("ifconfig result/n: %s" % execution)

        time.sleep(60 * 30)

        if vm_actions.power_off_vm(VMs) != 0:
            self.fail('powering on VM failed in iteration')

        _logger.info('VM Power-OFF - Completed')
        time.sleep(30)

        _logger.info("TestCase.test_demo: completed")

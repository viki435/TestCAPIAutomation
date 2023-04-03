from avocado import Test
from common.test_base import BaseContent_Test
from utils.vm_utils import VM_Actions
from utils.ssh_utils import SSH
import pprint
import avocado
import logging
import time
import os

_logger = logging.getLogger(__name__)

class NewCode_Test(BaseContent_Test):
    """
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(NewCode_Test, self).setUp()

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
                ],
            },           
        ]

        self.platforms_checkup(self.list_esxi_hosts)

    def test_vtmicros(self):
        """
        Test Cases: Include description

        :avocado: tags=demo
        """
        #self.yaml_configuration['sut']['esxi']['vms']['vm1']['vm_name']
        vm_name = "SJ_WithUbuntu_1_EMR (1)"

        _logger.info("TestCase.test_demo: init")
        time.sleep(15)

        esxi_ip = self.yaml_configuration['sut']['esxi']['ip'] 
        esxi_user = self.yaml_configuration['sut']['esxi']['user']
        esxi_password = self.yaml_configuration['sut']['esxi']['password']

        vm_actions = VM_Actions(esxi_ip, esxi_user, esxi_password)

        VMs = vm_actions.get_VM_names(vm_name, 1, 1)

        if vm_actions.power_on_vm(VMs) != 0:
            self.fail('powering on VM failed in iteration')
        
        _logger.info('VM Power-ON - Command Completed (machine is booting)')
        
        time.sleep(60*2)
        vm_ip = vm_actions.get_ip(vm_name)
        _logger.info('IP ADDRESS = %s' % vm_ip)

        ##############################################################
        #Create tunnel for interacting with the platform
        ##############################################################
        sut_name = self.yaml_configuration['sut']['platform_name']
        hostname_capi_server = self.capi.targets[sut_name].rtb.parsed_url.hostname

        port = self.capi.targets[sut_name].tunnel.add(22, vm_ip )

        vm_username = self.yaml_configuration['sut']['esxi']['vms']['vm1']['vm_username']
        vm_password = self.yaml_configuration['sut']['esxi']['vms']['vm1']['vm_password']

        _logger.info( "ssh -p %s %s@%s" % (port, vm_username, hostname_capi_server) )
        _logger.info( "scp -P %s FILENAME %s@%s:/PATH" % (port, vm_username, hostname_capi_server) )

        esxi_vm_session = SSH(hostname_capi_server, vm_username, vm_password, port)
        esxi_vm_session.connect()

        _logger.info("Executing vtmicros...")
        cmd_to_vm_session = './vtmicros'
        execution = esxi_vm_session.execute_cmd(cmd_to_vm_session, '', 600)
        _logger.info("Command sent...")

        time.sleep(60 * 22) #22 min execution
        os.system("sshpass -p '%s' scp -P %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null %s@%s:/root/output.txt /root" % (vm_password, port, vm_username, hostname_capi_server))
        time.sleep(5)
        os.system("mv /root/output.txt /root/vtmicro_%s.txt" % sut_name)
        
        if vm_actions.power_off_vm(VMs) != 0:
            self.fail('powering on VM failed in iteration')

        _logger.info('VM Power-OFF - Completed')
        time.sleep(30)

        _logger.info("TestCase.test_demo: completed")

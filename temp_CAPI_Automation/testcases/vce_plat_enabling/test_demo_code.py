from avocado import Test
from common.test_base import BaseContent_Test
from utils.vm_utils import VM_Actions
from utils.ssh_utils import SSH
import pprint
import avocado
import logging
import time

_logger = logging.getLogger(__name__)

class Demo_Test(BaseContent_Test):
    """
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """
        super(Demo_Test, self).setUp()

        #First element always is the SUT(ESXi host).
        self.platform_name = self.yaml_configuration['sut']['platform_name']
        self.esxi_ip = self.yaml_configuration['sut']['esxi']['ip']
        self.esxi_username = self.yaml_configuration['sut']['esxi']['user']
        self.esxi_password = self.yaml_configuration['sut']['esxi']['password']
        self.platform_vm_name = self.yaml_configuration['sut']['esxi']['vms']['vm1']['vm_name']

        self.list_esxi_hosts = [
                {
                "platname": self.platform_name,
                "esxi_host": self.esxi_ip,
                "esxi_user": self.esxi_username,
                "esxi_password": self.esxi_password,
                "nfs_datastore_name": self.yaml_configuration['sut']['esxi']['datastores']['nfs']['name'],
                "nfs_share_path": self.yaml_configuration['sut']['esxi']['datastores']['nfs']['nfs_share_path'],
                "vms_names":[
                    self.platform_vm_name,
                    ],
                },
            ]

        self.health_check(self.platform_name, self.esxi_ip, self.esxi_username, self.esxi_password)
        self.platforms_checkup(self.list_esxi_hosts)

    def test_demo(self):
        """
        Test Cases: Include description

        :avocado: tags=demo_capi
        """

        _logger.info("TestCase.test_demo: init")

        vm_actions = VM_Actions(self.esxi_ip, self.esxi_username, self.esxi_password)

        VMs = vm_actions.get_VM_names(self.platform_vm_name, 1, 1)
        
        if vm_actions.power_on_vm(VMs) != 0:
            self.fail('powering on VM failed in iteration')
        
        time.sleep(20)
        _logger.info('VM Power-ON - Completed')
        
        vm_ip = vm_actions.get_ip(self.platform_vm_name)

        ##############################################################
        #Create tunnel for interacting with the platform
        ##############################################################
        hostname_capi = self.capi.targets[self.platform_name].rtb.parsed_url.hostname
        port = self.capi.targets[self.platform_name].tunnel.add(22, vm_ip )

        esxi_vm_session = SSH(hostname_capi,
            self.yaml_configuration['sut']['esxi']['vms']['vm1']['vm_username'],
            self.yaml_configuration['sut']['esxi']['vms']['vm1']['vm_password'],
            port
        )

        esxi_vm_session.connect()
        
        _logger.info('******************************')
        _logger.info('ssh -p %s %s@%s' % (port, self.yaml_configuration['sut']['esxi']['vms']['vm1']['vm_username'], hostname_capi))
        _logger.info('******************************')

        cmd_to_vm_session = 'ifconfig'
        output = esxi_vm_session.execute_cmd(cmd_to_vm_session, '', 600)
        _logger.info("ifconfig result/n: %s" % output)

        time.sleep(60*1)

        if vm_actions.power_off_vm(VMs) != 0:
            self.fail('powering on VM failed in iteration')

        _logger.info('VM Power-OFF - Completed')
        time.sleep(30)

        _logger.info("TestCase.test_demo: completed")

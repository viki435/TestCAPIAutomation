from avocado import Test
from common.test_base import BaseContent_Test
from utils.ssh_utils import SSH
from utils.vm_utils import VM_Actions

import avocado
import logging

_logger = logging.getLogger(__name__)

class Nic_Passthru_Test(BaseContent_Test):
    """
    TODO
    
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(Nic_Passthru_Test, self).setUp()

    def test_nic_passthru(self):
        """
        Test to execute test_nic_passthru
        Enables passthru for NIC devices
        Assigns NIC device to a single VM
        Removes NIC devices from the VM
        Disables passthru for devices
        If there is failure in any of the above operations, test fails

        #self.ESXI_IP, self.ESXI_USERNAME, self.ESXI_PASSWORD
        #self.ESXI_VM1_NAME
        #Config_VM_name = "VM_92"
        """
        _logger.info('Starting NIC pass through test')

        ############## IOMMU_Legacy_Status starts #############

        _logger.info('Checking the IOMMU status in the SUT...')

        esxi_session = SSH(self.ESXI_IP, self.ESXI_USERNAME, self.ESXI_PASSWORD)
        esxi_session.connect()

        cmd = "esxcli system settings kernel list | grep iovPasidMode | awk '{print $4}'"

        iommu_status = esxi_session.execute_cmd(cmd, '', 30)
        _logger.info('Status of IOMMU is {}'.format(iommu_status))

        if 'FALSE' in iommu_status:
            _logger.info('SUT is in Legacy Mode; continuing the test')
        else:
            _logger.info('SUT is in Scalable Mode; switch to Legacy mode')

            KERNEL_VAR = 'kernelopt'
            LEGACY_MODE = 'autoPartition=FALSE iovPasidMode=FALSE'

            vm_actions = VM_Actions(self.ESXI_IP, self.ESXI_USERNAME, self.ESXI_PASSWORD)
            res = vm_actions.get_bootcfg(KERNEL_VAR, LEGACY_MODE) 
            if res == -1:
                self.fail('Failed to change IOMMU Mode to Legacy')

            if esxi_session.remote_reboot() != 0:
                self.fail('Reboot failed after changing IOMMU Mode')  

            esxi_session = SSH(self.ESXI_IP, self.ESXI_USERNAME, self.ESXI_PASSWORD)
            esxi_session.connect()

            iommu_status = esxi_session.execute_cmd(cmd, '', 30)    

            if 'TRUE' in iommu_status:
                self.fail("Failed to change IOMMU Mode to Legacy")

        ############## IOMMU_Legacy_Status ends #############
        
        vm_actions = VM_Actions(self.ESXI_IP, self.ESXI_USERNAME, self.ESXI_PASSWORD)

        if vm_actions.L4_test_config_func(self.ESXI_VM1_NAME, 2, 1, 'nic', 0, 1) != 0:
            self.fail("test_nic_passthru config failed")
    
        VMs = vm_actions.get_VM_names(self.ESXI_VM1_NAME, 1, 1)     
                
        if vm_actions.power_on_vm(VMs) != 0:
                self.fail('powering on VM failed in iteration {}'.format(i))
            
        if vm_actions.L4_test_clean_func(self.ESXI_VM1_NAME, 2, 1, 'nic', 0, 1) != 0:
            self.fail("test_nic_passthru clean failed")
        
        _logger.info('NIC passthrough test completed successfully')
  
from avocado import Test
from common.test_base import BaseContent_Test
from utils.ssh_utils import SSH
from utils.vm_utils import VM_Actions
from threading import Thread

import avocado
import logging
import time

_logger = logging.getLogger(__name__)

class OverCommit_Memory_and_CPU_Allocation_Test(BaseContent_Test):
    """
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(OverCommit_Memory_and_CPU_Allocation_Test, self).setUp()

    def stress_generation(self):
        """
        """
        vm_actions = VM_Actions(self.ESXI_IP, self.ESXI_USERNAME, self.ESXI_PASSWORD)
        VMs = vm_actions.get_VM_names(self.ESXI_VM1_NAME, 1, 1)  
        vm_ip = vm_actions.get_ip(VMs[0])

        vm_session = SSH(vm_ip, self.ESXI_VM1_USERNAME, self.ESXI_VM1_PASSWORD)
        vm_session.connect()
        command = "stress-ng --cpu 128 --cpu-method all --verify -t 1m --metrics-brief"
        vm_session.execute_cmd(command, '', 30)

    def track_memory(self):
        """
        """
        esxi_session = SSH(self.ESXI_IP, self.ESXI_USERNAME, self.ESXI_PASSWORD)
        esxi_session.connect()
        time.sleep(5)        
        #command = "/usr/sbin/esxtop  -b -d 5 -n 50 >> /vmfs/volumes/datastore1/esxtop-batch.txt"
        command = "/usr/sbin/esxtop  -b -d 5 -n 50"
        print ( esxi_session.execute_cmd(command, '', 30) )

    def test_demo(self):
        """
        Test Cases: Include description

        :avocado: tags=18014073349,16013374726
        """

        _logger.info("TestCase.test_demo: init")

        Thread(target = self.stress_generation).start()
        time.sleep(5)
        Thread(target = self.track_memory).start()
        time.sleep(15)
        _logger.info("TestCase.test_demo: completed")       

from avocado import Test
from common.test_base import BaseContent_Test
from utils.ssh_utils import SSH
from utils.yaml_utils import convert_yaml_to_dictionary

import avocado
import time
import logging


_logger = logging.getLogger(__name__)

class VmTools_LinuxInstall_Test(BaseContent_Test):
    """
    TODO
    
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(VmTools_LinuxInstall_Test, self).setUp()

    def test_vmtools_linux_install(self):
        """
        ToDO
        """   
        _logger.info( "TestCase.test_vmtools_linux_install: Init" )

        esxi_session = SSH(self.ESXI_VM1_IP, self.ESXI_VM1_USERNAME, self.ESXI_VM1_PASSWORD)
        esxi_session.connect()

        str_cmd = "cat /etc/os-release"
        vm_os_version = esxi_session.execute_cmd(str_cmd, '', 30)
        
        _logger.info("going to install vmtools")

        if 'Fedora' in vm_os_version:            

            cmd_installation = "sudo yum install open-vm-tools-desktop -y"
            out = esxi_session.execute_cmd(cmd_installation, '', 30)

            time.sleep(100)
            if out == -1 or out == '':
                raise Exception('Failed to execute cmd: {}'.format(cmd_installation))

            cmd_status_installation = "systemctl status vmtoolsd.service"
            out = esxi_session.execute_cmd(cmd_status_installation, '', 30)
            if "active (running)" not in out:
                raise Exception('Failed to install VM Tools. Process not running')

            esxi_session.ssh_disconnect()
            _logger.info("Executed open-vm-tools in %s (%s)" % (self.ESXI_VM1_NAME, self.ESXI_VM1_IP))

        else:
            ###
            #Include new OS support
            ###
            pass

        _logger.info( "TestCase.test_vmtools_linux_install: Completed" )        
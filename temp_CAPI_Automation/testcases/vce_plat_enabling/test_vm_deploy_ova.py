from avocado import Test
from common.test_base import BaseContent_Test
from utils.yaml_utils import convert_yaml_to_dictionary
from utils import deploy_ova_utils
import avocado
import time
import logging


_logger = logging.getLogger(__name__)

class VmDeployment_WithVC_Test(BaseContent_Test):
    """
    TODO
    
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(VmDeployment_WithVC_Test, self).setUp()

    def test_vm_deployment_with_ova_file(self):
        """
        ToDO
        """   
        _logger.info( "TestCase.test_vm_deployment_with_ova_file: Init" )

        deploy_ova_utils.deploy_vm(self.VCENTER_IP, 
                                   self.VCENTER_USERNAME, 
                                   self.VCENTER_PASSWORD, 
                                   self.VCENTER_DEPLOY_VM_OVA_FILE_PATH, 
                                   self.VCENTER_DATACENTER, 
                                   self.VCENTER_DATASTORE)

        _logger.info( "TestCase.test_vm_deployment_with_ova_file: Completed" )        
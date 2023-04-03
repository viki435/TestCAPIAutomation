from avocado import Test
from common.test_base import BaseContent_Test

import avocado
import logging
from datetime import datetime
import time

_logger = logging.getLogger(__name__)

class Flash_BMC_Test(BaseContent_Test):
    """
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(Flash_BMC_Test, self).setUp()
        #Code from previos interation. it will be removed soon.
        #self.BMC = self.params.get( "BMC", default = None )
        #self.UPLOAD = self.params.get( "UPLOAD", default = False )
        self.UPLOAD = True
        self.BMC = self.yaml_configuration['sut']['bmc']

        self.target_name = self.yaml_configuration['sut']['platform_name']

    def test_flash_bmc(self):
        """
        Test Cases: Include description
        
        :avocado: tags=bkc,bmc
        """        
        if self.BMC is None:
            self.cancel("Missing BMC file parameter. Please include next argument (e.g.): -p BMC='file1'")

        _logger.info("TestCase.test_flash_bmc: Executing BMC flashing")

        #-------------------------------------------------------------------
        #Call Upload Image API action
        #-------------------------------------------------------------------
        console = "log-flash-bmc"
        self.capi.targets[self.target_name].console.disable(console=console)
        self.capi.targets[self.target_name].console.enable(console=console)

        initial_time = datetime.now()
        try:
            self.capi.targets[self.target_name].images.flash(
                {
                    "bmc": self.BMC
                },
                upload = self.UPLOAD,
                timeout = 2000
            )
            final_time = datetime.now()
        except:
            final_time = datetime.now()
            delta = int((final_time - initial_time).total_seconds())
            self.capi.targets[self.target_name].expect("Verification OK",
                                        console=console,
                                        timeout = self.capi.targets[self.target_name].kws["interfaces"]["images"]["bmc"]["estimated_duration"] - delta
            )

        _logger.info( "TestCase.test_flash_bmc: BMC Flashing DONE" )

    def tearDown(self):
        """
        TODO
        """
        #Loop items and skip network component
        _logger.info("TestCase.tearDown: Test Completed at %s" % self.capi.suts)
        self.capi.release_sut()

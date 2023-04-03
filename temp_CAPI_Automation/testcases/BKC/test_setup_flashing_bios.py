from avocado import Test
from common.test_base import BaseContent_Test

import avocado
import logging
from datetime import datetime
import time

_logger = logging.getLogger(__name__)

class Flash_BIOS_Test(BaseContent_Test):
    """
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(Flash_BIOS_Test, self).setUp()
        
    def test_flash_bios(self):
        """
        Test Cases: Include description

        :avocado: tags=bkc,bios
        """
        if self.BIOS is None:
            self.cancel("Missing BIOS file parameter. Please include next argument (e.g.): -p BIOS='file1'")

        _logger.info("TestCase.test_flash_bios: Executing BIOS flashing")
        
        #-------------------------------------------------------------------
        #Call Upload Image API action
        #-------------------------------------------------------------------
        console = "log-flash-bios"
        #First element of targets contains the SUT object
        self.capi.targets[self.target_name].console.disable(console=console)
        self.capi.targets[self.target_name].console.enable(console=console)

        initial_time = datetime.now()
        try:
            self.capi.targets[self.target_name].images.flash(
                {
                    "bios": self.BIOS
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
                                        timeout = self.capi.targets[self.target_name].kws["interfaces"]["images"]["bios"]["estimated_duration"] - delta
            )

        _logger.info( "TestCase.test_flash_bios: BIOS Flashing DONE" )

    def tearDown(self):
        """
        TODO        
        """
        #Loop items and skip network component
        _logger.info("TestCase.tearDown: Test Completed at %s" % self.capi.suts)
        self.capi.release_sut()

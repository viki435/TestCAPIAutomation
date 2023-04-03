from avocado import Test
from common.test_base import BaseContent_Test

import avocado
import logging
from datetime import datetime
import time

_logger = logging.getLogger(__name__)

class Flash_CPLDs_Test(BaseContent_Test):
    """
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(Flash_CPLDs_Test, self).setUp()

        self.CPLD_Files = []
        
        #Code from previos interation. it will be removed soon.
        #cplds = [ key for key in self.capi.targets[self.target_name].kws["interfaces"]["images"].keys() if "cpld" in key ]
        #for cpld in cplds:
        #    self.CPLD_Files.append(self.params.get( cpld.upper(), default = None ))
        #self.UPLOAD = self.params.get( "UPLOAD", default = False )

        print(self.yaml_configuration['sut']['cplds'])
        for cpld_name in self.yaml_configuration['sut']['cplds']:
            self.CPLD_Files.append(self.yaml_configuration['sut']['cplds'][cpld_name])

        self.target_name = self.yaml_configuration['sut']['platform_name']
        self.UPLOAD = True

    def test_flash_cplds(self):
        """
        Test Cases: Include description

        :avocado: tags=bkc,cpld
        """
        if None in self.CPLD_Files:
            self.cancel("Missing one (or more) CPLD file(s). Please include next argument (e.g.): -p CPLD1='file1' -p CPLD2='file2'")

        _logger.info("TestCase.test_flash_cplds: Executing CPLDs flashing")
        
        for index, cpld_name in enumerate(self.CPLD_Files, start = 1):

            #-------------------------------------------------------------------
            #Call Upload Image API action
            #-------------------------------------------------------------------
            self.capi.targets[self.target_name].images.flash(
                {
                    "cpld%s" % index: cpld_name
                }, 
                upload = self.UPLOAD
            )
            _logger.info( "TestCase.test_flash_cpld: CPLD%s Flashing DONE" % index )

        _logger.info( "TestCase.test_flash_cplds: CPLDs Flashing DONE" )

    def tearDown(self):
        """
        TODO
        """
        #Loop items and skip network component
        _logger.info("TestCase.tearDown: Test Completed at %s" % self.capi.suts)
        self.capi.release_sut()

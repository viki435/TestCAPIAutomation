from api.capi_api_requests import HTTP_Requests as http_requests
import logging
import requests
import tcfl.tc
import time

_logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO)

class CAPI_Connection( object ):

    def __init__(self, suts = [], username = None, password = None ):
        """
        Constructs all the necessary attributes for the CAPI_Interaction object.
        Includes flashing, serial and instruments methods.

        Parameters
        ----------
            suts : list
                Platform short names using list format. 
                E.g. ['fl31ca105gs1301', 'fl31ca105gs1302']
            username : str
                Username contains information based on your intel email account
                E.g. username = 'juan.wolf.maqueda@intel.com'
            password : str
                Password stores password used by your personal intel account
        """
        self.suts = suts
        self.username = username
        self.password = password
        self.targets = {}

        tcfl.config.setup()
        self.api_http_call = http_requests(self.username, self.password, self.suts)
        self.api_http_call.get_cookie_http_request()

        #Reserve systems for testing
        self.is_sut_reserved(self.suts)
        time.sleep(1)
        status = self.reserve_sut(self.suts)

    def is_sut_reserved(self, sut_names):
        """
        Method evaluate whether specific platform/sut is already reserved.

        Parameters
        ----------
            sut_names : list
                Platform name. E.g. 'fl31ca105gs1301'
        """
        status = self.reserve_sut(sut_names)
        if status == "busy" or status == "active":
            for name in self.targets:
                self.targets[name].release()            

    def reserve_sut(self, sut_names):
        """
        Method try to reserve a platform/sut based on availability.
        returns a tuple with target (tcfl.tc.target_c) object and 
        reservation status

        Parameters
        ----------
            sut_name : str
                Platform name. E.g. 'fl31ca105gs1301'
        """
        for sut_name in sut_names:
            self.targets[sut_name] = tcfl.tc.target_c.create( self.api_http_call.server_shortname + "/" + sut_name)
      
        allocid, state, targetids = tcfl.target_ext_alloc._alloc_targets(
                self.targets[self.suts[0]].rtb,
                { "group": sut_names },
        )
        return state

    def release_sut(self):
        """
        Method will release platform/sut where test case is being performed.
        """
        for name in self.targets:
            self.targets[name].release()
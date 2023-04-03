import logging
import urllib3
import requests
import subprocess
import json
import time
import re

_logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO)

class HTTP_Requests(object):
    """
    TBD
    """
    #INFORMATION HERE NEEDS TO BE INCLUDED BASED ON PLATFORM AVAILABILITY
    CAPI_SERVERS_PLATFORMS = {
        "fl31ca105gc1401_5000": "https://fl31ca105gc1401.deacluster.intel.com:5000"
    }

    CAPI_SERVER_URL = None
    REQUEST_OK_STATUS = 200

    def __init__(self, username, password, sut):
        """
        TBD
        """
        self.server_shortname = "fl31ca105gc1401_5000"
        HTTP_Requests.CAPI_SERVER_URL = HTTP_Requests.CAPI_SERVERS_PLATFORMS.get(self.server_shortname) + "/ttb-v2"
        
        if HTTP_Requests.CAPI_SERVER_URL is None:
            raise ValueError('SUT name is accessible')


        self.server_url = HTTP_Requests.CAPI_SERVER_URL
        self.username = username
        self.password = password
        self.sut = sut
        self.cookie = None

    def _execute_api_request(self, http_method_type, url_command, **http_api_kwargs):
        """
        TBD
        """
        assert http_method_type in ["PUT", "GET", "POST"], "%s not supported" % http_method_type
        response = None
        try:        
            response = requests.request(http_method_type, url_command, **http_api_kwargs)
            response.raise_for_status()
            _logger.info("HTTP.request: Performed successfully")
        except requests.exceptions.HTTPError as errh:
            _logger.info(errh)
        except requests.exceptions.ConnectionError as errc:
            _logger.info(errc)
        except requests.exceptions.Timeout as errt:
            _logger.info(errt)
        except requests.exceptions.RequestException as err:
            _logger.info(err)
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            _logger.info(message)

        return response

    def get_cookie_http_request(self):
        """
        TDB
        """
        _logger.info("Function.get_cookie_http_request: Create Auth cookie from Server (%s)" % self.server_url)
        loggin_api_call = self.server_url + "/login"

        response = self._execute_api_request( "PUT", 
                                                loggin_api_call, 
                                                verify = False,
                                                data = { 
                                                    "username": self.username, 
                                                    "password": self.password 
                                                }
                                            )
        self.cookie = response.cookies
        return self.cookie

    def allocate_platform(self, sut):
        """
        TBD
        """
        _logger.info("Function.allocate_platform: Reserving SUT (%s)" % sut)
        allocation_api_call = self.server_url + "/allocation"

        if self.cookie == None:
            self.get_cookie_http_request()
        
        response = self._execute_api_request("PUT",
                                                allocation_api_call,
                                                cookies = self.cookie,
                                                verify = False,
                                                json = {
                                                    "queue": False,
                                                    "groups": { "mygroup": [ sut ] },
                                                })

        if HTTP_Requests.REQUEST_OK_STATUS != response.status_code:
            _logger.info("Function.allocate_platform: Reservation failed for %s" % sut)            
            raise Exception('Failure: %s' % response) 

        json_response = json.loads(response.text)

        if json_response.get("state") == "busy":
            raise Exception('System is busy, Please select another option: %s' % json_response)

        elif json_response.get("state") == "active":
            self.sut = sut
            _logger.info("Function.allocate_platform: SUT (%s) reserved - Allocation status: Active" % self.sut)
            return json_response
        else:
            raise Exception('System status: %s, Please select another option' % json_response.get("state"))

        return response
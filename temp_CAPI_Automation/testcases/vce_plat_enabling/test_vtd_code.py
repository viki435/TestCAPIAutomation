from avocado import Test
from common.test_base import BaseContent_Test
from utils.ssh_utils import SSH
from utils.vm_utils import VM_Actions

import avocado
import subprocess
import logging
import time
import json

_logger = logging.getLogger(__name__)

class SetVTd_Test(BaseContent_Test):
    """
    TODO
    
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(SetVTd_Test, self).setUp()

        self.list_esxi_hosts = [
                {
                "platname": self.capi.suts[0],
                "esxi_host": self.ESXI_IP,
                "esxi_user": self.ESXI_USERNAME,
                "esxi_password": self.ESXI_PASSWORD,
                "nfs_datastore_name": "vce_nfs_server",
                "nfs_share_path": "/var/vce",
                "vms_names":[                  
                    ],
                },
                {
                "platname": self.capi.suts[1],
                },
            ]
        self.platforms_checkup(self.list_esxi_hosts)

    def test_active_bios_vtd(self):
        """
        Test to execute Virtualization - VMWare ESXi - BIOS VT options

        :avocado: tags=18014072277  
        """
        sut = self.list_esxi_hosts[0]
        esxi_session = SSH( sut.get("esxi_host"), 
                            sut.get("esxi_user"), 
                            sut.get("esxi_password"))
        esxi_session.connect()

        datastore_cmd = 'esxcli --debug --formatter=json  storage filesystem list'
        lst_datastores = json.loads(esxi_session.execute_cmd(datastore_cmd, '', 30))
        datastore_path = None
        for datastore in lst_datastores:
            if "datastore" in datastore.get("VolumeName"):
                datastore_path = datastore.get("UUID")
                break
        if datastore_path is None:
            self.fail("Datastore was not found")
        
        #Copy xmlcli tool to default datastore
        datastore_cmd = 'cp -rf /vmfs/volumes/vce_nfs_server/auto/xmlcli_2_0_0 /vmfs/volumes/%s' % datastore_path
        esxi_session.execute_cmd(datastore_cmd, '', 30)
        
        #Execute xmlcli commands
        #Note: it takes huge time be patient (~10 min) 
        execute_script = 'python3 /vmfs/volumes/%s/xmlcli_2_0_0/enable_vtd_script.py %s' % (datastore_path, datastore_path)
        output = esxi_session.execute_cmd(execute_script, '', 1200)
        print(output)
        #Verification if all ok then will reboot platform and wait for sanity check
        #if "Verify Passed" in output:
        self.capi.targets[sut.get("platname")].power.cycle()
        time.sleep(15)

        self.health_check(sut.get("platname"), 
            sut.get("esxi_host"), 
            sut.get("esxi_user"), 
            sut.get("esxi_password"),
            )

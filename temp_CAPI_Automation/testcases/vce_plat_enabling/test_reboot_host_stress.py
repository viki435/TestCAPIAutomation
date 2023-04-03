from avocado import Test
from common.test_base import BaseContent_Test
from utils.ssh_utils import SSH
from utils.yaml_utils import convert_yaml_to_dictionary

import avocado
import subprocess
import logging
import time
import json

_logger = logging.getLogger(__name__)

class Stress_Test(BaseContent_Test):
    """
    TODO
    
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(Stress_Test, self).setUp()

        self.list_esxi_hosts = [
                {
                "platname": self.capi.suts[0],
                "esxi_host": self.ESXI_IP,
                "esxi_user": self.ESXI_USERNAME,
                "esxi_password": self.ESXI_PASSWORD,
                "nfs_datastore_name": "vce_nfs_server",
                "nfs_share_path": "/var/vce",
                "vms_names":[],
                },
                {
                "platname": self.capi.suts[1],
                },
            ]
        self.platforms_checkup(self.list_esxi_hosts)

    def test_reboot_host_stress(self):
        """
        :avocado: tags=16012889909

        Virtualization - VMware/ESXi Stress host Reboot Cycles.
        Purpose of this test case is to continuously perform reboot cycles on host for Stress.
        Precondition: Enable the VT-x and VT-d in BIOS ,  Full memory population
        capture the VM verions before power cycle and perform power cycle
        after power ON host perform ping operation on host and capture the VM varision
        compare the version, repeat this step for 100 times
        Capture vmkernel, boot and vmware logs when test fails.
        """
        test_case_number = "16012889909"

        _logger.info( "TestCase.test_reboot_host_stress: Init" )

        _logger.info('Checking status of SUT...')

        sut = self.list_esxi_hosts[0]
        esxi_session = SSH( sut.get("esxi_host"),
                            sut.get("esxi_user"),
                            sut.get("esxi_password"))

        esxi_session.connect()

        str_cmd = "vmware -v"
        stdin, stdout, stderr = esxi_session.connection.exec_command(str_cmd, timeout=30)
        esxi_os_ver_bf_power_cycle = stdout.read().decode('utf-8').strip()
        _logger.info("ESXI OS version before power cycle", esxi_os_ver_bf_power_cycle)

        for i in range(1, 6):
            self.capi.targets[sut.get("platname")].send("Serial Report Variable Counter #%s" % i )

            _logger.info("iteration value is : ", i)

            if esxi_session.remote_reboot() != 0:
                self.store_logs(sut, test_case_number)
                self.fail('Reboot operation is failed ')

            self.health_check(sut.get("platname"),
                sut.get("esxi_host"),
                sut.get("esxi_user"),
                sut.get("esxi_password"),
                )

            esxi_session = SSH( sut.get("esxi_host"),
                                sut.get("esxi_user"),
                                sut.get("esxi_password"))
            esxi_session.connect()

            stdin, stdout, stderr = esxi_session.connection.exec_command(str_cmd, timeout=30)
            esxi_os_ver_af_ppower_cycle = stdout.read().decode('utf-8').strip()

            _logger.info("ESXI OS version after power cycle", esxi_os_ver_af_ppower_cycle)
            if (esxi_os_ver_bf_power_cycle!=esxi_os_ver_af_ppower_cycle):
                self.store_logs(sut, test_case_number)
                self.fail('Reboot opration is failed')

        _logger.info( "TestCase.test_reboot_host_stress: DONE" )

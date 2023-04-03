from avocado import Test
from common.test_base import BaseContent_Test
from utils.ssh_utils import SSH

import commonl
import tcfl.biosl
import avocado
import logging
from datetime import datetime
import time
import re
import os


_logger = logging.getLogger(__name__)

class ESXI_Installer_Test(BaseContent_Test):
    """
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(ESXI_Installer_Test, self).setUp()
        self.IDSID = self.params.get( "IDSID", default= None )

    def test_esxi_installation(self):
        """
        Test Cases: Include description

        :avocado: tags=bkc,esxi 
        """   
        _logger.info( "TestCase.test_esxi_installation: Init" )

        dict_vmnic_config_file ={
            "fl31ca105gs1401": "KS2.CFG",
            "fl31ca105gs1301": "KS0.CFG",
            "fl31ca105gs1403": "KS2.CFG",            
        }        
        
        self.capi.targets[self.capi.suts[0]].power.cycle()

        boot_ic = self.capi.targets[self.capi.suts[0]].kws['pos_boot_interconnect']
        mac_addr = self.capi.targets[self.capi.suts[0]].kws['interconnects'][boot_ic]['mac_addr']
        tcfl.biosl.boot_network_pxe(self.capi.targets[self.capi.suts[0]], r"UEFI PXEv4 \(MAC:%s\)" % mac_addr.replace(":", "").upper().strip())

        self.capi.targets[self.capi.suts[0]].expect("iPXE initialising devices...")

        self.capi.targets[self.capi.suts[0]].console.write("\x02\x02")	# use this iface so expecter
        time.sleep(0.3)
        self.capi.targets[self.capi.suts[0]].console.write("\x02\x02")	# use this iface so expecter
        time.sleep(0.3)
        self.capi.targets[self.capi.suts[0]].console.write("\x02\x02")	# use this iface so expecter
        time.sleep(0.3)
        self.capi.targets[self.capi.suts[0]].expect("Ctrl-B", timeout = 250)
        self.capi.targets[self.capi.suts[0]].console.write("\x02\x02")	# use this iface so expecter
        time.sleep(0.3)
        self.capi.targets[self.capi.suts[0]].console.write("\x02\x02")	# use this iface so expecter
        time.sleep(0.3)
        self.capi.targets[self.capi.suts[0]].expect("iPXE>")
        prompt_orig = self.capi.targets[self.capi.suts[0]].shell.shell_prompt_regex

        self.capi.targets[self.capi.suts[0]].shell.shell_prompt_regex = "iPXE>"
        kws = dict(self.capi.targets[self.capi.suts[0]].kws)
        boot_ic = self.capi.targets[self.capi.suts[0]].kws['pos_boot_interconnect']
        mac_addr = self.capi.targets[self.capi.suts[0]].kws['interconnects'][boot_ic]['mac_addr']
        ipv4_addr = self.capi.targets[self.capi.suts[0]].kws['interconnects'][boot_ic]['ipv4_addr']
        ipv4_prefix_len = self.capi.targets[self.capi.suts[0]].kws['interconnects'][boot_ic]['ipv4_prefix_len']
        kws['ipv4_netmask'] = commonl.ipv4_len_to_netmask_ascii(ipv4_prefix_len)

        ifstat = self.capi.targets[self.capi.suts[0]].shell.run("ifstat", output = True, trim = True)
        regex = re.compile("(?P<ifname>net[0-9]+): %s using" % mac_addr.lower(),re.MULTILINE)
        m = regex.search(ifstat)

        ifname = m.groupdict()['ifname']

        # static is much faster and we know the IP address already
        # anyway; but then we don't have DNS as it is way more
        # complicated to get it
        self.capi.targets[self.capi.suts[0]].shell.run("set %s/ip %s" % (ifname, ipv4_addr))
        self.capi.targets[self.capi.suts[0]].shell.run("set %s/netmask %s" % (ifname, kws['ipv4_netmask']))
        self.capi.targets[self.capi.suts[0]].shell.run("ifopen " + ifname)

        self.capi.targets[self.capi.suts[0]].shell.run("dhcp")
        time.sleep(25)

        command = "sshpass -p '%s' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -t %s@fl31ca105gc1308.deacluster.intel.com 'cat /var/vce/esxi_installers_automation/esxi_8.0.0-1.0.20513097/efi/boot/boot.cfg'" % (self.PASSWORD, self.IDSID)
        output= self.sshpass_execution(command)
        ks_file = re.search("KS.*CFG", output)
        output = str(output).replace(ks_file.group(), dict_vmnic_config_file.get(self.capi.suts[0], "KS0.CFG"))
        boot_file = open("boot.cfg", "w")
        boot_file.write(output)
        boot_file.close()

        command = "sshpass -p '%s' ssh -t %s@fl31ca105gc1308.deacluster.intel.com 'rm /var/vce/esxi_installers_automation/esxi_8.0.0-1.0.20513097/efi/boot/boot.cfg'" % (self.PASSWORD, self.IDSID)
        output= self.sshpass_execution(command)

        command = "sshpass -p '%s' scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null boot.cfg %s@fl31ca105gc1308.deacluster.intel.com:/var/vce/esxi_installers_automation/esxi_8.0.0-1.0.20513097/efi/boot/" % (self.PASSWORD, self.IDSID)
        output= self.sshpass_execution(command)


        #NFS Server
        self.capi.targets[self.capi.suts[0]].shell.run(f"module nfs://10.45.252.220/var/vce/esxi_installers_automation/esxi_8.0.0-1.0.20513097/efi/boot/boot.cfg","ok")

        self.capi.targets[self.capi.suts[0]].shell.run(f"kernel nfs://10.45.252.220/var/vce/esxi_installers_automation/esxi_8.0.0-1.0.20513097/efi/boot/bootx64.efi","ok")

        self.capi.targets[self.capi.suts[0]].send("boot")

        """
        max_minutes_for_waiting = 20
        counter = 0        
        esxi_session = SSH(self.ESXI_IP, self.ESXI_USERNAME, self.ESXI_PASSWORD)
        is_esxi_host_online =  False
        while counter < max_minutes_for_waiting:
            try:            
                is_esxi_host_online = esxi_session.connect()
            except:
                is_esxi_host_online = False
            if is_esxi_host_online == True:
                break
            _logger.info( "Checking ESXI host is online (%s of %s)" % (counter + 1, max_minutes_for_waiting))
            counter = counter + 1
            self.capi.targets[self.capi.suts[0]].send("Serial Report Variable Counter #%s" % counter )
            time.sleep(60)


        if not is_esxi_host_online:
            self.fail("ESXI Host is not reachable: %s" % self.ESXI_IP)
        else:
            _logger.info( "ESXI host is online: %s" % self.ESXI_IP )
        """

        _logger.info( "TestCase.test_esxi_installation: Completed" )

    def sshpass_execution(self, command):
        counter = 0
        max_iteration = 5
        while counter < max_iteration:
            counter = counter + 1
            stream = os.popen(command)    
            output = stream.read()
            if output == '': 
                continue
            if not "Permission denied" in str(output) :
                break
            time.sleep(4)
        return output

    def tearDown(self):
        """
        TODO        
        """
        #Loop items and skip network component
        _logger.info("TestCase.tearDown: Test Completed at %s" % self.capi.suts)
        self.capi.release_sut()

from api.capi_tcfl_requests import CAPI_Connection
from utils.yaml_utils import convert_yaml_to_dictionary
from utils.ssh_utils import SSH
from avocado import Test
import logging
import urllib3
import time
import json
import pprint
import os

_logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO)
urllib3.disable_warnings()

class BaseContent_Test(Test):
    """
    BaseContent_Test class uses Common API framework for getting access to the 
    SUT using HTTP requests and tcfl library. Also enabled Test cases setup and release platform when done
    """

    def setUp(self):
        """
        TODO
        """ 
        _logger.info("TestCase.SetUp: Initialization")

        self.CONFIG_FILE = self.params.get("CONFIG_FILE", default = None)

        if self.CONFIG_FILE is not None:

            self.yaml_configuration = None
            if os.path.exists(self.CONFIG_FILE):
                self.yaml_configuration = convert_yaml_to_dictionary(self.CONFIG_FILE)
            else:
                raise Exception("Configuration file is not found: %s" % self.CONFIG_FILE)

            self.TARGET_NAMES = [ 
                self.yaml_configuration['sut']['platform_name'],
                self.yaml_configuration['nut']['name'],
                ]
            self.USERNAME = self.yaml_configuration['capi_server']['capi_username']
            self.PASSWORD = self.yaml_configuration['capi_server']['capi_password']

            #BKC variables
            self.UPLOAD = True
            self.BIOS = self.yaml_configuration['sut']['bios']
            self.target_name = self.yaml_configuration['sut']['platform_name']

            """
            sut_yaml_structure = yaml_configuration.get('sut')

            if "esxi" in sut_yaml_structure:
                self.ESXI_IP = sut_yaml_structure['esxi']['ip']
                self.ESXI_USERNAME = sut_yaml_structure['esxi']['user']
                self.ESXI_PASSWORD = sut_yaml_structure['esxi']['password']

                if sut_yaml_structure['esxi'].get("vms", None):                    
                    self.ESXI_VM1_NAME = sut_yaml_structure['esxi']['vms']['vm1']['vm_name']
                    self.ESXI_VM1_IP = sut_yaml_structure['esxi']['vms']['vm1']['vm_ip']
                    self.ESXI_VM1_USERNAME = sut_yaml_structure['esxi']['vms']['vm1']['vm_username']
                    self.ESXI_VM1_PASSWORD = sut_yaml_structure['esxi']['vms']['vm1']['vm_password']

            if "vcenter" in yaml_configuration:
                vcenter_yaml_structure = yaml_configuration.get('vcenter')
                self.VCENTER_IP = vcenter_yaml_structure['ip_address']
                self.VCENTER_USERNAME = vcenter_yaml_structure['username']
                self.VCENTER_PASSWORD = vcenter_yaml_structure['password']
                self.VCENTER_DATACENTER = vcenter_yaml_structure['datacenter_name']
                self.VCENTER_DATASTORE = vcenter_yaml_structure['datastore_name']
                self.VCENTER_DEPLOY_VM_OVA_FILE_PATH = vcenter_yaml_structure['vm_ova_file_path']
            """

        else:
            # ============ Variables used by Reserve a platform with CAPI =======            
            self.TARGET_NAMES = self.params.get("SUTS", default = [])
            self.TARGET_NAMES = [ x.strip() for x in self.TARGET_NAMES[1:-1].split(",") ]

            self.USERNAME = self.params.get( "USERNAME", default= None )
            self.PASSWORD = self.params.get( "PASSWORD", default = None )
            # ============ Variables used by Reserve a platform with CAPI =======

            """            
            # ============ Variables used by ESXI OS content (or virtual machines)
            self.ESXI_IP = self.params.get( "ESXI_IP", default = None )
            self.ESXI_USERNAME = self.params.get( "ESXI_USERNAME", default = None )
            self.ESXI_PASSWORD = self.params.get( "ESXI_PASSWORD", default = None )

            # ---- Virtual Machine data list   
            self.ESXI_VM1_NAME = self.params.get( "ESXI_VM1_NAME", default = None )
            self.ESXI_VM1_IP = self.params.get( "ESXI_VM1_IP", default = None )
            self.ESXI_VM1_USERNAME = self.params.get( "ESXI_VM1_USERNAME", default = None )
            self.ESXI_VM1_PASSWORD = self.params.get( "ESXI_VM1_PASSWORD", default = None )
            # ---- 

            # ============ Variables used by ESXI OS content (or virtual machines)

            # ============ Variables used by VCENTER content
            self.VCENTER_IP = self.params.get( "VCENTER_IP", default = None )
            self.VCENTER_USERNAME = self.params.get( "VCENTER_USERNAME", default = None )
            self.VCENTER_PASSWORD = self.params.get( "VCENTER_PASSWORD", default = None )
            self.VCENTER_DATACENTER = self.params.get( "VCENTER_DATACENTER", default = None )
            self.VCENTER_DATASTORE = self.params.get( "VCENTER_DATASTORE", default = None )
            self.VCENTER_DEPLOY_VM_OVA_FILE_PATH = self.params.get( "VCENTER_DEPLOY_VM_OVA_FILE_PATH", default = None )
            # ============ Variables used by VCENTER content
            """

            #Variables used by BKC Test cases
            self.UPLOAD = self.params.get( "UPLOAD", default = True )
            self.BIOS = self.params.get( "BIOS", default = None )
            
            self.target_name = self.TARGET_NAMES[0]


        # ============ Variables used by Network under Test
        self.PLATFORM_NETWORK_DICT = {}
        self.ESXI_HOST_VIRTUAL_SWITCH_NAME = "vHighSpeed"
        self.ESXI_HOST_PORT_GROUP = "pgHighSpeed"
        # ======================================================

        self.capi = CAPI_Connection(self.TARGET_NAMES, self.USERNAME, self.PASSWORD)

        _logger.info("TestCase.SetUp: Completed")

    def health_check(self, platform_name, esxi_ip, esxi_user, esxi_password):
        """
        Confirm ESXI OS is working and platform is reachable with static IP address (ssh) 
        """        
        if dict(dict(self.capi.targets[platform_name].power.list()[2])["AC"])["state"] is False:
            self.capi.targets[platform_name].power.cycle()
            _logger.info("Activating Power Supply and waiting for platform boot...")

        max_minutes_for_waiting = self.capi.targets[platform_name].kws['bios.boot_time']/60
        counter = 0
        is_esxi_host_online =  False
        esxi_session = SSH(esxi_ip, esxi_user, esxi_password)
        while counter < max_minutes_for_waiting:
            try:            
                is_esxi_host_online = esxi_session.connect()
            except:
                is_esxi_host_online = False

            if is_esxi_host_online:
                esxi_session.ssh_disconnect()
                time.sleep(60)
                _logger.info("Platform is online")
                break

            _logger.info( "Checking ESXI host is online (%s of %s)" % (counter + 1, max_minutes_for_waiting))
            counter = counter + 1
            self.capi.targets[platform_name].send("Serial Report Variable Counter #%s" % counter )
            time.sleep(60)
            
        if not is_esxi_host_online:
            raise ValueError('Platform is not available. Plese confirm serial/power status and static ip address is assigned')

    def enable_private_network(self, private_network_name):
        """
        Enable NUT feature whether required
        """        
        self.private_network_name = private_network_name
        _logger.info("Activating NUT (%s)..." % self.private_network_name)
        self.capi.targets[self.private_network_name].power.on()
        _logger.info("NUT online (%s)..." % self.private_network_name)

    def disable_private_network(self):
        """
        Disable NUT feature whether required
        """        
        _logger.info("Disabling NUT (%s)..." % self.private_network_name)
        self.capi.targets[self.private_network_name].power.off()
        self.PLATFORM_NETWORK_DICT = {}
        _logger.info("NUT disconnected (%s)..." % self.private_network_name)

    def get_vmnic_card_name(self, platform_name, connection_details):
        """
        Obtain nic card name using mac address for identiying card with right mac address
        """
        cmd_show_nic_list = "esxcli --debug --formatter=json network nic list"

        esxi_session = SSH( connection_details.get("esxi_host"),
            connection_details.get("esxi_user"), 
            connection_details.get("esxi_password")
            )
        esxi_session.connect()
        output_show_nic_list_status = json.loads(esxi_session.execute_cmd(cmd_show_nic_list, '', 30))
        for nic_detail in output_show_nic_list_status:
            if nic_detail.get('MACAddress').lower() == self.PLATFORM_NETWORK_DICT[platform_name].get("PRIVATE_NETWORK_MAC_ADDRESS"):
                self.PLATFORM_NETWORK_DICT[platform_name]["ESXI_HOST_VMNIC_NAME"] = nic_detail.get('Name').lower()
                return nic_detail.get('Name').lower()  
        return False

    def set_esxi_network_settings(self, platform_name, connection_details):
        """
        Configure virtual switch, port group and vmkernel
        """
        wait_addconfig_x_seconds = 4

        self.PLATFORM_NETWORK_DICT[ connection_details.get("platname") ] = {
            "PRIVATE_NETWORK_MAC_ADDRESS": self.capi.targets[platform_name].kws["interconnects"][self.private_network_name]["mac_addr"].lower(),
            "PRIVATE_NETWORK_SUBNET": ".".join(self.capi.targets[platform_name].kws["interconnects"][self.private_network_name]["ipv4_addr"].split(".")[0:2]) 
        }        

        esxi_session = SSH( connection_details.get("esxi_host"),
            connection_details.get("esxi_user"), 
            connection_details.get("esxi_password")
            )
        esxi_session.connect()
        
        esxi_host_vmnic_name = self.get_vmnic_card_name(platform_name, connection_details)
        #Configure virtual switch
        ########
        cmd_configure_virtual_switch = "esxcfg-vswitch -a %s" % self.ESXI_HOST_VIRTUAL_SWITCH_NAME
        esxi_session.execute_cmd(cmd_configure_virtual_switch, '', 30)                
        time.sleep(wait_addconfig_x_seconds)

        cmd_configure_virtual_switch = "esxcfg-vswitch --link=%s %s" % (esxi_host_vmnic_name, self.ESXI_HOST_VIRTUAL_SWITCH_NAME)
        esxi_session.execute_cmd(cmd_configure_virtual_switch, '', 30)
        time.sleep(wait_addconfig_x_seconds)

        #Enable/Create uplink (if not assigned to vswitch)
        cmd_check_uplink_from_virtual_switch = "esxcli --debug --formatter=json network vswitch standard list"
        output_cmd_check_uplink_from_virtual_switch = json.loads(esxi_session.execute_cmd(cmd_check_uplink_from_virtual_switch, '', 30))

        for vswitch in output_cmd_check_uplink_from_virtual_switch:
            if vswitch.get("Name") == self.ESXI_HOST_VIRTUAL_SWITCH_NAME:
                if esxi_host_vmnic_name not in vswitch.get("Uplinks"):
                    cmd_create_uplink_from_virtual_switch = "esxcli network vswitch standard uplink add --uplink-name=%s --vswitch-name=%s" % (
                        esxi_host_vmnic_name,
                        self.ESXI_HOST_VIRTUAL_SWITCH_NAME
                        ) 
                    esxi_session.execute_cmd(cmd_create_uplink_from_virtual_switch, '', 30)
                    time.sleep(wait_addconfig_x_seconds)   

        #Configure port groups
        cmd_create_new_portgroup_to_vswitch = "esxcfg-vswitch -A %s %s" % (self.ESXI_HOST_PORT_GROUP, self.ESXI_HOST_VIRTUAL_SWITCH_NAME)
        esxi_session.execute_cmd(cmd_create_new_portgroup_to_vswitch, '', 30)
        time.sleep(wait_addconfig_x_seconds)

        #Configure vmkernel
        wait_addconfig_x_seconds = 10
        cmd_set_vmkernel_to_portgroup = "esxcfg-vmknic -a -i DHCP -p %s" % self.ESXI_HOST_PORT_GROUP
        esxi_session.execute_cmd(cmd_set_vmkernel_to_portgroup, '', 30)
        time.sleep(wait_addconfig_x_seconds)

        #Confirm private address is correctly configured
        cmd_show_net_interace_list = "esxcli --debug --formatter=json network ip interface ipv4 address list"
        output_show_nic_list_status = json.loads(esxi_session.execute_cmd(cmd_show_net_interace_list, '', 30))
        pprint.pprint(output_show_nic_list_status)

    def remove_esxi_network_settings(self, connection_details):
        """
        Remove virtual switch, port group and vmkernel configurations
        """
        wait_to_removeconfig_x_seconds = 4

        esxi_session = SSH( connection_details.get("esxi_host"),
            connection_details.get("esxi_user"), 
            connection_details.get("esxi_password")
            )
        esxi_session.connect()

        #Delete vmkernel configuration
        cmd_remove_vmkernel_to_portgroup = "esxcfg-vmknic -d %s" % self.ESXI_HOST_PORT_GROUP
        esxi_session.execute_cmd(cmd_remove_vmkernel_to_portgroup, '', 30)
        time.sleep(wait_to_removeconfig_x_seconds)        

        #Remove port group configuration        
        cmd_remove_portgroup_to_vswitch = "esxcfg-vswitch --del-pg=%s %s" % (self.ESXI_HOST_PORT_GROUP, self.ESXI_HOST_VIRTUAL_SWITCH_NAME)
        esxi_session.execute_cmd(cmd_remove_portgroup_to_vswitch, '', 30)
        time.sleep(wait_to_removeconfig_x_seconds)

        #Delete virtual switch configuration
        cmd_delete_virtual_switch = "esxcli network vswitch standard remove --vswitch-name=%s" % self.ESXI_HOST_VIRTUAL_SWITCH_NAME
        esxi_session.execute_cmd(cmd_delete_virtual_switch, '', 30)                
        time.sleep(wait_to_removeconfig_x_seconds)        

    def platforms_checkup(self, platforms_details):
        """
        ToDO
        """
        #Loop items and skip network component
        platform_list = [ plat for plat in platforms_details if "-nw" not in plat.get("platname") ]
        #Loop items for getting network name
        network = self.yaml_configuration['nut']['name']

        #Checking all platforms/network are online
        self.enable_private_network(network)

        for esxi_host in platform_list:            
            self.health_check(esxi_host.get("platname"), 
                esxi_host.get("esxi_host"), 
                esxi_host.get("esxi_user"), 
                esxi_host.get("esxi_password"),
                )
    
            self.set_esxi_network_settings(esxi_host.get("platname"), esxi_host)
            self.mount_nfs_datastore(esxi_host)
            self.register_vms(esxi_host)            

    def mount_nfs_datastore(self, platforms_details):
        """
        Use private network for mounting NFS Data Storage        
        """
        esxi_session = SSH( platforms_details.get("esxi_host"),
            platforms_details.get("esxi_user"), 
            platforms_details.get("esxi_password")
            )
        esxi_session.connect()

        _logger.info( "Mounting data storage (%s)" % platforms_details.get("esxi_host") )
        #Create new datastorage
        cmd_show_nfs_list = "esxcli --debug --formatter=json storage nfs list"
        nfs_status = json.loads(esxi_session.execute_cmd(cmd_show_nfs_list, '', 30))
        if nfs_status == []:
            cmd_mount_nfs_server = "esxcli storage nfs add -H %s.0.3 -s %s -v %s" % (
                self.PLATFORM_NETWORK_DICT[ platforms_details.get("platname") ]["PRIVATE_NETWORK_SUBNET"], 
                platforms_details.get("nfs_share_path"), 
                platforms_details.get("nfs_datastore_name") 
            )
            esxi_session.execute_cmd(cmd_mount_nfs_server, '', 30)        
            time.sleep(15)                

        #Get real volume name
        cmd_show_nfs_list = "esxcli --debug --formatter=json storage nfs list"
        nfs_status = json.loads(esxi_session.execute_cmd(cmd_show_nfs_list, '', 30))
        nfs_datastore_name = nfs_status[0].get("VolumeName")
        self.PLATFORM_NETWORK_DICT[ platforms_details.get("platname")]["nfs_name"] = nfs_datastore_name
        _logger.info( "NFS Data storage mounted (%s)" % platforms_details.get("esxi_host") )
        return nfs_datastore_name

    def unmount_nfs_datastore(self, platforms_details):
        """
        Use private network for unmounting NFS Data Storage
        """
        esxi_session = SSH( platforms_details.get("esxi_host"),
            platforms_details.get("esxi_user"), 
            platforms_details.get("esxi_password")
            )
        esxi_session.connect()
        _logger.info( "Unmounting data storage (%s)" % platforms_details.get("esxi_host") )        
        #Remove datastorage        
        nfs_volume_name =  self.PLATFORM_NETWORK_DICT[ platforms_details.get("platname")]["nfs_name"]        
        cmd_remove_datastore = 'esxcli storage nfs remove -v "%s"' % nfs_volume_name
        esxi_session.execute_cmd(cmd_remove_datastore, '', 600)
        time.sleep(5)
        _logger.info( "NFS Data storage unmounted (%s)" % platforms_details.get("esxi_host") )

    def register_vms(self, platforms_details):
        """
        Create new group port for accessing to the high speed network with the vmname
        """        
        esxi_session = SSH( platforms_details.get("esxi_host"),
            platforms_details.get("esxi_user"), 
            platforms_details.get("esxi_password")
            )
        esxi_session.connect()
        nfs_volume_name =  self.PLATFORM_NETWORK_DICT[ platforms_details.get("platname")]["nfs_name"]

        _logger.info("Registering VM (host: %s)" %  platforms_details.get("platname") )
        self.PLATFORM_NETWORK_DICT[ platforms_details.get("platname")]["vms"] = {}

        print(self.PLATFORM_NETWORK_DICT)

        for vm_name in platforms_details.get("vms_names"):

            #Create port group for specific VM (using VM name)
            cmd_create_new_portgroup_to_vswitch = "esxcfg-vswitch -A pg_%s %s" % (vm_name, self.ESXI_HOST_VIRTUAL_SWITCH_NAME)
            esxi_session.execute_cmd(cmd_create_new_portgroup_to_vswitch, '', 30)

            #Register VM
            cmd_register_vm_from_datastore = 'vim-cmd solo/registervm "/vmfs/volumes/%s/%s/%s.vmx"' %(nfs_volume_name, vm_name, vm_name)
            vm_number = esxi_session.execute_cmd(cmd_register_vm_from_datastore, '', 600).replace('\n',"")
            self.PLATFORM_NETWORK_DICT[ platforms_details.get("platname")]["vms"][vm_name] = vm_number
            time.sleep(5)
            _logger.info("VMs %s registered (vm number #%s)" % (vm_name, vm_number) )    

        _logger.info("VMs registered (host: %s)" %  platforms_details.get("platname") )

    def unregister_vms(self, platforms_details):
        """
        Remove group port for accessing to the high speed network with the vmname and unregister vm
        """
        esxi_session = SSH( platforms_details.get("esxi_host"),
            platforms_details.get("esxi_user"), 
            platforms_details.get("esxi_password")
            )
        esxi_session.connect()
        _logger.info("Unregistering VM (host: %s)" %  platforms_details.get("platname") )

        for vm_name in platforms_details.get("vms_names"):
            vm_number = self.PLATFORM_NETWORK_DICT[ platforms_details.get("platname")]["vms"][vm_name]

            #Unregister VM
            cmd_register_vm_from_datastore = 'vim-cmd /vmsvc/unregister %s' % vm_number
            esxi_session.execute_cmd(cmd_register_vm_from_datastore, '', 600)

            cmd_remove_new_portgroup_to_vswitch = "esxcfg-vswitch --del-pg=pg_%s %s" % (vm_name, self.ESXI_HOST_VIRTUAL_SWITCH_NAME)
            esxi_session.execute_cmd(cmd_remove_new_portgroup_to_vswitch, '', 30)
            _logger.info("VM %s unregistered (#%s)" % (vm_name, vm_number))

        time.sleep(10)
        _logger.info("VMs unregistered (host: %s)" %  platforms_details.get("platname") )

    def store_logs(self, platforms_details, test_case_number):
        """
        Store vmkernel and boot logs in local datastore
        """
        esxi_session = SSH( platforms_details.get("esxi_host"),
            platforms_details.get("esxi_user"),
            platforms_details.get("esxi_password")
            )
        esxi_session.connect()

        datastore_path = self._get_local_uuid_datastore(platforms_details)

        path_log = "/vmfs/volumes/%s/automation_logs" % datastore_path
        str_cmd = "mkdir %s" % path_log
        esxi_session.execute_cmd(str_cmd, '', 30)

        time_file_str = "vmkernel_%s_%s.log" % (test_case_number, time.strftime("%Y%m%d-%H%M%S") )
        path_file = "%s/%s" % (path_log ,time_file_str)
        source_path = '/var/log/vmkernel.log'
        str_cmd = "cp %s %s" % (source_path, path_file)
        print (str_cmd)
        esxi_session.execute_cmd(str_cmd, '', 30)

        time_file_str = "boot_%s_%s.gz" % (test_case_number, time.strftime("%Y%m%d-%H%M%S") )
        path_file = "%s/%s" % (path_log ,time_file_str)
        source_path = '/var/log/boot.gz'

        str_cmd = "cp %s %s" % (source_path, path_file)
        print (str_cmd)
        esxi_session.execute_cmd(str_cmd, '', 30)

    def _get_local_uuid_datastore(self, platforms_details, nfs = False):
        esxi_session = SSH( platforms_details.get("esxi_host"),
            platforms_details.get("esxi_user"),
            platforms_details.get("esxi_password")
            )
        esxi_session.connect()

        datastore_cmd = 'esxcli --debug --formatter=json  storage filesystem list'
        lst_datastores = json.loads(esxi_session.execute_cmd(datastore_cmd, '', 30))
        datastore_path = None
        for datastore in lst_datastores:
            if not nfs:
                if "datastore" in datastore.get("VolumeName"):
                    datastore_path = datastore.get("UUID")
                    break
            else:
                if "NFS" in datastore.get("Type"):
                    datastore_path = datastore.get("UUID")
                    break
        if datastore_path is None:
            self.fail("Datastore was not found")
        return datastore_path

    def _get_volumename_datastore(self, platforms_details, nfs = False):
        esxi_session = SSH( platforms_details.get("esxi_host"),
            platforms_details.get("esxi_user"),
            platforms_details.get("esxi_password")
            )
        esxi_session.connect()

        datastore_cmd = 'esxcli --debug --formatter=json storage filesystem list'
        lst_datastores = json.loads(esxi_session.execute_cmd(datastore_cmd, '', 30))
        datastore_name = None
        for datastore in lst_datastores:
            if not nfs:
                if "datastore" in datastore.get("VolumeName"):
                    datastore_name = datastore.get("VolumeName")
                    break
            else:
                if "NFS" in datastore.get("Type"):
                    datastore_name = datastore.get("VolumeName")
                    break
        if datastore_name is None:
            self.fail("Datastore was not found")
        return datastore_name     

    def tearDown(self):
        """
        TODO        
        """
        #Loop items and skip network component
        platform_list = [ plat for plat in self.list_esxi_hosts if "-nw" not in plat.get("platname") ]

        for esxi_host in platform_list:
            self.unregister_vms(esxi_host)
            self.unmount_nfs_datastore(esxi_host)
            self.remove_esxi_network_settings(esxi_host)

        self.disable_private_network()

        _logger.info("TestCase.tearDown: Test Completed at %s" % self.capi.suts)
        self.capi.release_sut()

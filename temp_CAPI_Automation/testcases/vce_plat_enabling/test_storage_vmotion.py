from avocado import Test
from common.test_base import BaseContent_Test
from utils.ssh_utils import SSH
from utils.vm_utils import VM_Actions
from utils.yaml_utils import convert_yaml_to_dictionary

import avocado
import subprocess
import logging
import time
import json

_logger = logging.getLogger(__name__)

class StorageMotion_Test(BaseContent_Test):
    """
    TODO
    
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(StorageMotion_Test, self).setUp()

        self.list_esxi_hosts = [
                {
                "platname": "fl31ca105gs1303",  #capi.suts[0],
                "esxi_host": "10.45.134.100",   #capi.ESXI_IP,
                "esxi_user": "root",            #capi.ESXI_USERNAME,
                "esxi_password": "intel@123",   #capi.ESXI_PASSWORD,
                "nfs_datastore_name": "vce_nfs_server",
                "nfs_share_path": "/var/vce",
                "vms_names":[],
                "vcenter": ("172.25.222.20", "administrator@vsphere.local", "Intel@123"),
                },       
                {
                "platname": self.capi.suts[1],
                },
            ]
        self.platforms_checkup(self.list_esxi_hosts)

    def test_storage_motion(self):
        """
        :avocado: tags=18014073440

        Test to execute Virtualization - VMware Storage Migration 
        Checking the required VM is present in current host migrate to destination host
        enabling VM kernel service on host
        performing storage migration using non-shared mode from one datastore to another data store.

        Prerequirements: Platform needs to have extra SSD connected

        Notes: Test case requires to add host to the VCenter - Check next idea later
        https://github.com/tejaswi-bachu/wordpress_blog/blob/main/pyvmomi_add_esxi_vcenter/test_add_esxi_to_vcenter.py
        """
        VM = "vm_basic_machine"
        sut = self.list_esxi_hosts[0]        
        esxi_sut_session = SSH( sut.get("esxi_host"),
                                sut.get("esxi_user"),
                                sut.get("esxi_password"))        
        esxi_sut_session.connect()
        
        cmd = 'vim-cmd vmsvc/getallvms'
        stdin, stdout, stderr = esxi_sut_session.connection.exec_command(cmd, timeout=30)
        cmd_result = stdout.read().decode('utf-8').strip()
        print(cmd_result)

        if(VM not in cmd_result):
            print("VM %s is not Registered" % VM)
            uuid_name = self._get_local_uuid_datastore(sut)

            nfs_datastore_name = self._get_local_uuid_datastore(sut, True)
            cp_vm = "cp -rf /vmfs/volumes/%s/virtual_machines_repository/%s /vmfs/volumes/%s" % (nfs_datastore_name, VM, uuid_name)
            print(cp_vm)
            esxi_sut_session.execute_cmd(cp_vm, '', 250)
            time.sleep(250)

            #Register VM
            print("Registering VM")
            cmd_register_vm_from_datastore = 'vim-cmd solo/registervm "/vmfs/volumes/%s/%s/%s.vmx"' %(uuid_name, VM, VM)
            vm_number = esxi_sut_session.execute_cmd(cmd_register_vm_from_datastore, '', 600).replace('\n',"")
            print("VM %s Registered" % VM)
            time.sleep(20)

            vm_actions = VM_Actions(sut.get("esxi_host"),
                                    sut.get("esxi_user"),
                                    sut.get("esxi_password"))

            VMs = vm_actions.get_VM_names(VM, 1, 1)
            if vm_actions.power_on_vm(VMs) != 0:
                self.fail('Powering on VM failed in iteration')

            time.sleep(10)

        vc_name, vc_username, vc_password = sut.get("vcenter")
        vm_actions.enable_vmkernel_service(vc_name, vc_username, vc_password, sut.get("esxi_host"), 'vmotion')

        objective_datastore = "datastore_share" #self._get_volumename_datastore(sut, True)

        print("***" * 100)

        if vm_actions.vmotion(vc_name, vc_username, vc_password, VM, sut.get("esxi_host"), 'non-shared', 'yes', objective_datastore, False)==-1:
            self.fail("vmotion got failed")


        VMs = vm_actions.get_VM_names(VM, 1, 1)
        if vm_actions.power_off_vm(VMs) != 0:
            self.fail('Powering off VM failed in iteration')
        time.sleep(30)

        vm_number = vm_actions.get_vm_id(VM)
        print("Unregistering VM %s" % VM)
        esxi_sut_session = SSH( sut.get("esxi_host"),
                                sut.get("esxi_user"),
                                sut.get("esxi_password"))
        esxi_sut_session.connect()        
        cmd_register_vm_from_datastore = 'vim-cmd /vmsvc/unregister %s' % vm_number
        esxi_sut_session.execute_cmd(cmd_register_vm_from_datastore, '', 600)

        delete_vm_files = "rm -rf /vmfs/volumes/%s/%s" % (uuid_name, VM)
        esxi_sut_session.execute_cmd(delete_vm_files, '', 30)

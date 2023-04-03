import os
import sys
import fileinput
def replace_line_bystr(cfg_dir, pref_str,pref_replace,file_stwith, file_endwith):
    print("called function")
    print(cfg_dir)
    print(file_stwith)
    print(file_endwith)
    print(pref_str)
    print(pref_replace)
    cfg_dir = os.getcwd()
    print(cfg_dir)
    cfg = os.listdir(cfg_dir)
    print(cfg)
    for filename in cfg:
        if filename.startswith(file_stwith) and filename.endswith(file_endwith):
            for line in fileinput.input(filename, inplace = 1):
                if pref_str in line:
                    print (line.replace(line,pref_replace))
                else:
                    print(line)

if __name__ == '__main__':
    # execute only if run as the entry point into the program
    platform = sys.argv[1]
    dict_ks_file = {
        "fl31ca105gs1301": "_KS.CFG",
        "fl31ca105gs1302": "KS.CFG",
        "fl31ca105gs1303": "KS.CFG",
    }

    boot_cfg_efi_directory = '/gfs/group/VCE/shared/extract_data/efi/boot'
    pref_str_1 = "prefix="
    pref_replace_1 = "prefix=http://capi-shell.intel.com/gfs/group/VCE/shared/extract_data\n"
    kernal_str_1 = "kernelopt=runweasel cdromBoot"
    Kernal_repalce_1 = "kernelopt=ks=http://capi-shell.intel.com/gfs/group/VCE/auto/%s\n" % dict_ks_file.get( platform, "KS.CFG")

    file_stwith_1 = 'boot'
    file_endwith_1 = 'cfg'

    replace_line_bystr(boot_cfg_efi_directory, pref_str_1, pref_replace_1, file_stwith_1, file_endwith_1)
    replace_line_bystr(boot_cfg_efi_directory, kernal_str_1, Kernal_repalce_1, file_stwith_1, file_endwith_1)

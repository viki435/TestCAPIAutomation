from yaml.loader import SafeLoader

import yaml
import os

def convert_yaml_to_dictionary(path_to_file):
    """
    Method will load yml file and convert it to python dictionary 
    """
    data = None
    if os.path.exists(path_to_file):
        with open(path_to_file) as f:
            data = yaml.load(f, Loader=SafeLoader)
        return data

    else:
        raise Exception("File not found (%s)." % path_to_file  )

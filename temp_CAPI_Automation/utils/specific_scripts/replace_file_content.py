import sys
import os

def replace_file_content(file_path, original_line, new_line):
    # creating a variable and storing the text
    # that we want to search
    search_text = original_line
    
    # creating a variable and storing the text
    # that we want to add
    replace_text = new_line
    
    # Opening our text file in read only
    # mode using the open() function
    with open(r'{0}'.format(file_path), 'r') as file:
    
        # Reading the content of the file
        # using the read() function and storing
        # them in a new variable
        data = file.read()
    
        # Searching and replacing the text
        # using the replace() function
        data = data.replace(search_text, replace_text)
    
    # Opening our text file in write only
    # mode to write the replaced content
    with open(r'{0}'.format(file_path), 'w') as file:
    
        # Writing the replaced data in our
        # text file
        file.write(data)
    
    # Printing Text replaced
    print("Text replaced")

if __name__ == '__main__':
    # execute only if run as the entry point into the program
    #E.g. 
    #>> replace_file_content.py 'file_path' 'original_line'
    file_path = sys.argv[1]
    original_line = sys.argv[2]

    ghp_token = os.getenv('GHP_TOKEN')    
    str_link = "https://%s@github.com/intel-innersource/applications.infrastructure.capi.tcf-intel" % (ghp_token)
    print ("-----> %s" % str_link)

    #replace_file_content(file_path, original_line, str_link)

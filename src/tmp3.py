import io
import marshal
import time
import mysql
import sys
import importlib.util
import os   

# with open('mysql.py', 'r') as memfile:
#     # Read the current contents of the file
#     current_contents = memfile.read()
#     print("Current file contents:")
#     print(current_contents)

#     # Move the file pointer to the end of the file to append new content
#     memfile.write('MySQL().prepare_node()\n')  # Adding a newline for better formatting

#     # If you want to read again after writing, you can seek back to the start
#     memfile.seek(0)  # Move the pointer to the start of the file

#     # Read again after writing to see the updated contents
#     updated_contents = memfile.read()
#     print("Updated file contents:")
#     print(updated_contents)

# os.path.basename(__file__)
# source_code = "print('hi')" # "mysql.MySQL().prepare_node()"
with open('mysql.py', 'r') as memfile:
    code_object = compile(memfile.read() + 'MySQL().prepare_node()', filename="hello1.py", mode="exec")
    pyc_file = io.BytesIO()
    pyc_file.write(b'\xcb\r\r\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    # pyc_file.write(int(time.time()).to_bytes(4, byteorder='little'))
    marshal.dump(code_object, pyc_file)
    print(pyc_file.getvalue())
    print('---')
    with open('file1.pyc', 'wb') as f:
        pyc_file.seek(0)
    #     pyc_file.read(8)
        f.write(pyc_file.getvalue())

pyc_data = importlib._bootstrap_external._code_to_timestamp_pyc(code_object)
print(pyc_data)
with open('file.pyc', 'wb') as f:
    f.write(pyc_data)


import io
import marshal
import time
import mysql
import sys
import importlib.util
import os   
code_object = compile("print('hiq')", filename="hello1.py", mode="exec")
pyc_data = importlib._bootstrap_external._code_to_timestamp_pyc(code_object)
print(pyc_data)
with open('file.pyc', 'wb') as f:
    f.write(pyc_data)

code_object = compile("print('hiq')", filename="hello1.py", mode="exec")
pyc_file = io.BytesIO()
pyc_file.write(b'o\r\r\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
marshal.dump(code_object, pyc_file)
print(pyc_file.getvalue())
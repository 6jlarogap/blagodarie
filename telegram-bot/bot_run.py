#!./ENV/bin/python
import os
import sys

cur_dir = os.path.dirname(__file__)
activate_this = os.path.join(cur_dir, 'ENV', 'bin', 'activate_this.py')
if os.path.exists(activate_this):
    print("Activating %s" % activate_this)
    with open(activate_this) as activate_this_file:
        exec(activate_this_file.read(), dict(__file__=activate_this))

if __name__ == "__main__":
    exec(open(os.path.join(cur_dir, 'main.py')).read())

import os
import re
import shutil
import subprocess
import sys

if os.path.exists('./test/tmp'):
    shutil.rmtree('./test/tmp', ignore_errors=True)

# create temp directory if don't exists
os.makedirs('./test/tmp')

def getFlag(name):
    return name in sys.argv

def getOption(name, default):
    index = -1

    try:
        index = sys.argv.index(name)
    except:
        pass

    if index > 0 and len(sys.argv) > index + 1:
        return sys.argv[index + 1]

    return default


BLENDER_EXE = getOption('--blender', 'blender')


def trim_output(out):
    # trim the output to the last 10 lines
    out_lines = out.split('\n')
    end = out_lines[-10:]
    result = '\n'.join(end)

    return result

for root, dirs, files in os.walk('test'):
    for pyFile in files:
        pyFile = os.path.join(root, pyFile)
        if pyFile.endswith('.test.py'):
            blendFile = pyFile.replace('.py', '.blend')
            print ("Running file "+ pyFile)

            args = [
                BLENDER_EXE,
                '--addons',
                'wireless',
                '--factory-startup',
                '-noaudio',
                '-b',
            ]
            if os.path.exists(blendFile):
                args.append(blendFile)

            else:
                print(
                    'WARNING: Blend file ' +
                    blendFile + 'does not exists',
                )

            args.append('--python')
            args.append(pyFile)

            out = subprocess.check_output(args, stderr=subprocess.STDOUT)

            print(out)

import os
import sys
import json
import math
import time
import subprocess
from termcolor import colored
from prettytable import PrettyTable

# Print iterations progress
def printProgressBar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

args = sys.argv
os.system('color')

# check arguments
if len(args) != 4:
    print("\nError: Wrong arguments.\n")
    exit()
BLENDER_PATH = args[1]
JSON_PATH = args[2]
OUTPUT_FILE = args[3]
if os.path.splitext(BLENDER_PATH)[1] != ".exe" or \
    os.path.splitext(JSON_PATH)[1] != ".json" or \
        os.path.splitext(OUTPUT_FILE)[1] != ".mvs":
    print("\nError: Wrong arguments. Try again.")
    print("It must be \"path_to_blender\\blender.exe path_to_input_file.json pah_to_output.mvs\"")
    exit()

## read json and run export
with open(JSON_PATH, 'r') as f:
    data = json.load(f)

# #Color
R = "\033[0;31;40m"
G = "\033[0;32;40m" 
N = "\033[0m"

table = PrettyTable(['FileName', 'Export'])
table.align["FileName"] = "l" 

is_all_success = True
l = len(data)
print(colored('\nBLENDER EXPORT TESTS', 'yellow'))
printProgressBar(0, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
captured_log = "" 
edm_files = []
for i, block in enumerate(data):
    blend_path = block['filename']
    file_name, file_ext  = os.path.splitext(blend_path)
    dir_name = os.path.dirname(blend_path)
    edm_path = os.path.join(dir_name, f'{file_name}.edm')
    
    # run export
    try:
        out = subprocess.run([BLENDER_PATH, 
                        '--background', 
                        blend_path, 
                        '--python-expr', 
                        'import bpy;bpy.ops.edm.import_matrials();bpy.ops.edm.fast_export_dummy()'],
                        capture_output=True, text=True).stdout.strip("\n")
        
        if 'Info: Model successfully exported to' in out:
            table.add_row([blend_path, G + "Success" + N])
        else: 
            table.add_row([blend_path, R + "Failed" + N])
            captured_log += out
            is_all_success = False

    except:
        table.add_row([blend_path, R+"Failed"+N])
        captured_log += f'ERROR: could not export {file_name}'
        is_all_success = False

    if not os.path.exists(edm_path):
        table.add_row([blend_path, R+"Failed"+N])
        captured_log += f'ERROR: {file_name}.edm was not created'
        is_all_success = False
    
    edm_files.append(edm_path)
    printProgressBar(i + 1, l, prefix = 'Progress:', suffix = 'Complete', length = 50)

## print log
print(table)

if not is_all_success:
    print(colored('\nLogs of errors:', 'yellow'), captured_log)
    print(colored('\nNot all models were successfully exported. .mvs file was not created.', 'red'))
    exit()

## prepare .mvs file
delta = 8.0
        
objects_count = len(edm_files)
width = math.floor(math.sqrt(objects_count))
data = []
for i, filepath in enumerate(edm_files):
    x = i // width
    z = i - x * width

    data.append({
        'ModelPath': filepath,
        'position': {
            "ppx": x * delta,
            "ppy": 10001.349609375,
            "ppz": z * delta,
            "pxx": 1,
            "pxy": 0,
            "pxz": 0,
            "pyx": 0,
            "pyy": 1,
            "pyz": 0,
            "pzx": 0,
            "pzy": 0,
            "pzz": 1
        }        
    })
loaded_modules = {'LoadedModels': data}

with open(OUTPUT_FILE, 'w') as f:
    json.dump(loaded_modules, f, indent=2)

print(colored('Common .mvs was saved here', 'yellow'), colored(OUTPUT_FILE, 'white'))
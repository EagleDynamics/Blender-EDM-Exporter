## This script builds material graph from .pickle and save it in .dot format.
## Example cmd: python.exe script_build_material_graph.py "path_to_material\EDM_Default_Material.pickle".
## You will get "path_to_material\EDM_Default_Material.dot".
## To see the results insert data from .dot in https://edotor.net/.

import re
import os
import sys
from pathlib import Path
from operator import itemgetter
from typing import Dict, Set, List, Tuple

import pickle
import graphviz 

sys.path.append(str(Path(__file__).absolute().parent)+"\\..")
pattern_format_node = re.compile(r'[^\w"]')
BASE_NODE_NAME = 'Group Input'

def add_node(nodes: Dict, node: str, socket: str):
    full_s_name = pattern_format_node.sub('_', f'{node}_{socket}')

    s = (full_s_name, socket)
    if node in nodes:
        nodes[node].add(s)
    else:
        nodes[node] = {s}

    return f'{node}:{full_s_name}'


def from_dict_to_str(node: str, nodes: Dict):
    if node not in nodes:
        return ''
    return '{' + '|'.join([f'<{full_s}> {s}' for (full_s, s) in nodes[node]]) + '}'

## cast socket.default_value to string type
def to_str(default_value):
    if type(default_value) == tuple and type(default_value[0]) == float:
        res = "("
        for indx, i in enumerate(default_value):
            res = f"{res}, {i:.2f}" if indx != 0 else f"{res}{i:.2f}"
        res = f"{res})"
        return res
    else:
        return str(default_value)

## input hase type SInput
def create_drop_down_node(input, nodes_in: Dict, nodes_out: Dict, node_names: List, links: List):
    if not input.enum_values:
        print("error while processing drop-down lists. Fix script")
        exit()

    node_names.append(input.name)

    ## create node constisted from enum values of drop-down list
    instance_value_full: str = None
    for option in input.enum_values:
        full_to = add_node(nodes_in, input.name, option[0])
        if option[0] == input.instance_value:
            instance_value_full = full_to

    full_from = add_node(nodes_out, BASE_NODE_NAME, input.name)
    links.append((full_from, instance_value_full))

## check argument
args = sys.argv

if '--' in args:
    script_args = args[args.index('--') + 1:]
else:
    script_args = args[1:]

if len(script_args) < 1:
    print("\nError: Wrong arguments. Try again.\n It must be \"script_build_material_graph.py mat_desc_file.pickle\"")
    exit()

input_pickle_path = script_args[0]
if os.path.splitext(input_pickle_path)[1] != ".pickle":
    print("\nError: Wrong arguments. Try again.\n It must be \"script_build_material_graph.py mat_desc_file.pickle\"")
    exit()

#input_pickle_path = rf'e:\repos\trunk\Utils\EDMTools\io_scene_edm\data\EDM_Default_Material.pickle'
dir_path, file_name = os.path.dirname(input_pickle_path), os.path.splitext(os.path.basename(input_pickle_path))[0]
output_dot_file = os.path.join(dir_path, file_name + '.dot')

## run parsing
with open(input_pickle_path, 'rb') as f:
    mat_desc = pickle.load(f)

dot = graphviz.Digraph(file_name, node_attr={'shape': 'record'})

nodes_in: Dict[str, Set[Tuple[str, str]]] = {}
nodes_out: Dict[str, Set[Tuple[str, str]]] = {}
links: List[Tuple[str, str]] = []
node_names: List[str] = []

visited = set()
for link in mat_desc.links:
    from_socket = link.from_socket
    if link.from_node == BASE_NODE_NAME:            
        ## to check if all inputs were visited
        visited.add(link.from_socket)

        def_val = mat_desc.inputs[link.from_socket_idx].default_value
        from_socket = f'{from_socket}: {to_str(def_val)}'
    full_from = add_node(nodes_out, link.from_node, from_socket)
    full_to = add_node(nodes_in, link.to_node, link.to_socket)
    links.append((full_from, full_to))
    node_names.append(link.from_node)
    node_names.append(link.to_node)


## process drop-down lists and check if all sockets in BASE_NODE_NAME were added. (if not - fix it)
for input in mat_desc.inputs:
    if input.enum_values:
        create_drop_down_node(input, nodes_in, nodes_out, node_names, links)
    elif input.name not in visited:
        socket = f'{input.name}: {to_str(input.default_value)}'
        add_node(nodes_out, BASE_NODE_NAME, socket)

links = sorted(links,  key=itemgetter(0))
node_names = sorted(set(node_names),  key=itemgetter(0))  # убираем дубликаты

for node in node_names:
    sockets_in = from_dict_to_str(node, nodes_in)    
    sockets_out = from_dict_to_str(node, nodes_out)

    sockets = rf"{{{node}|{{{sockets_in}|{sockets_out}}}}}"
    dot.node(node, sockets)

dot.edges(links)

try:
    dot.render(filename=output_dot_file)
except:
    pass

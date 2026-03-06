import json
import os
import tkinter as tk
from tkinter import filedialog
import argparse
import re

forbidden_chars = ["@", "#", "$", "%", "&", "(", ")", ".", "+", "–", "*", "?", "[", "^", "~", ":", "-", "'", "`",
                   "/", "\\"]

def create_lua_entrances(json_file_path, base_path):
    with open(fr"{base_path}/manifest.json") as manifest_file:
        manifest = json.load(manifest_file)
        game_name = manifest["game_name"]
        game_name_lua = game_name.lower().replace(' ', '_')
        for char in forbidden_chars:
            game_name_lua = game_name_lua.replace(char, "_")
        game_name_lua = re.sub(r'(_)\1+', r'\1', game_name_lua)
    assert isinstance(game_name, str)

    with open(json_file_path) as json_file:
        entrance_data = json.load(json_file)

    if not os.path.exists(fr"{base_path}/scripts/logic/graph_logic/er_connections.lua"):
        with open(fr"{base_path}/scripts/logic/graph_logic/er_connections.lua", "w", encoding="utf-8") as er_lua:
            er_lua.write("a")
    with open(fr"{base_path}/scripts/logic/graph_logic/er_connections.lua", "w") as er_connection_lua:
        nodes = []
        for region in entrance_data.keys():
            region_lua = region.lower().replace(' ', '_')
            for char in forbidden_chars:
                region_lua = region_lua.replace(char, "_")
            region_lua = re.sub(r'(_)\1+', r'\1', region_lua)
            nodes.append(region_lua)
            for exit in entrance_data[region]:
                exit_lua = exit.lower().replace(' ', '_')
                for char in forbidden_chars:
                    exit_lua = exit_lua.replace(char, "_")
                exit_lua = re.sub(r'(_)\1+', r'\1', exit_lua)
                nodes.append(exit_lua)
        unique_nodes = list(set(nodes))
        er_connection_lua.write("-- these are the nodes for the graph is build from. \n"
                                "-- Add more if you like\n")
        for node in unique_nodes:
            er_connection_lua.write(f'local {node} = {game_name_lua}_location.new("{node}")\n')

        er_connection_lua.write("-- these are the connections betweens the nodes defined above.\n"
                                "-- those are all 2-way connections. please go ahead an make them one-way if needed.\n"
                                "-- the rules are what is needed to get from point A to B for this specific "
                                "connection.\n"
                                "-- only add whats actually needed. replace the 'return true' to 'return <whatever "
                                "you use to build your rules>'\n")
        for region in entrance_data:
            region_lua = region.lower().replace(' ', '_')
            for char in forbidden_chars:
                region_lua = region_lua.replace(char, "_")
            region_lua = re.sub(r'(_)\1+', r'\1', region_lua)
            for exit in entrance_data[region]:
                exit_lua = exit.lower().replace(' ', '_')
                for char in forbidden_chars:
                    exit_lua = exit_lua.replace(char, "_")
                exit_lua = re.sub(r'(_)\1+', r'\1', exit_lua)
                er_connection_lua.write(f'{region_lua}:connect_two_ways({exit_lua}, function() return true end)\n')



if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    print("Select the base-folder of the pack:")
    base_path = tk.filedialog.askdirectory()
    print("Path to base-folder of the pack: ", base_path)

    print("Select the ER.json file path:")
    er_json_file_path = tk.filedialog.askopenfilename()
    print("Path to ER.json file: ", er_json_file_path)

    create_lua_entrances(er_json_file_path, base_path)
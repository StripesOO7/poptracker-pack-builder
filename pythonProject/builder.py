import json
import os
import sys
import tkinter as tk
from tkinter import filedialog
import requests

import item_json
import location_json
import tracker_layout
import base_structure
import logic

lvls = set()
locations_dict = dict()
maps_names = []
logic = dict()
open_chest = "open.png"
close_chest = "close.png"

if __name__ == "__main__":
    import argparse
    cmd_parser = argparse.ArgumentParser(
        prog="PopTracker Builder.py",
        description="""This is the main script that builds all parts of a basic PopTracker pack
        the other scripts can be used to fine re-run/fine-tune specific parts of the pack or in case of 
        gimp_images.py to create images for text based options in bulk.""",

    )
    cmd_parser.add_argument("-dp", "--datapackage-host", type=str)
    cmd_parser.add_argument("-gn", "--game-name", type=str)
    cmd_parser.add_argument("-r", "--pack-root", type=str)
    # cmd_parser.add_argument("", "")
    # cmd_parser.add_argument("", "")
    # cmd_parser.add_argument("", "", )
    cmd_args = cmd_parser.parse_args()
    if len(sys.argv) == 1 or cmd_args.pack_root == None:
        root = tk.Tk()
        root.withdraw()

        read_file_path = tk.filedialog.askdirectory()
    else:
        read_file_path = cmd_args.pack_root
    if not os.path.exists(read_file_path + "/datapackage_url.json"):
        with open(read_file_path + "/datapackage_url.json", "w", encoding="utf-8") as base_file:
            url = (
                cmd_args.datapackage_host or input("datapackage source (url): ")
                or "https://archipelago.gg"
            )
            game_name = cmd_args.game_name or input("Game name from Datapackage: ")
            dp_json = {
                "url" : f"{url}/datapackage",
                "game_name" : f"{game_name}"
            }
            base_file.write(json.dumps(dp_json, indent=4))
    if cmd_args.datapackage_host and cmd_args.game_name:
        datapackage_path = f"{cmd_args.datapackage_host}/datapackage"
        game_name = cmd_args.game_name
    else:
        with open(f"{read_file_path}/datapackage_url.json") as args_json:
            dp_json = json.load(args_json)
            datapackage_path = dp_json["url"]
            game_name = dp_json["game_name"]
        # *other_options = (
        #     dp_json = json.load(read_file_path + "/datapackage_url.txt")
        #     # open(read_file_path + "/datapackage_url.txt").readline().split(", ")
        # )

    games_dict = requests.get(datapackage_path).json()["games"]

    base_structure.create_base_structure(
        path=read_file_path, game_name=game_name, game_dict=games_dict
    )

    item_json.create_items(path=read_file_path)
    read_input = []
    location_list = []
    temp = []
    lvls = set()
    locations_dict = dict()
    with open(read_file_path + "/scripts/autotracking/location_mapping.lua", encoding="utf-8") as mapping:
        while inputs := mapping.readline():
            if "]" in inputs:
                if not (inputs.strip()[0:2] == "--" or inputs.strip()[0:2] == "//"):
                    read_input.append(inputs.split("="))
            else:
                pass
    for k, _ in enumerate(read_input):
        read_input[k][1] = read_input[k][1][
            read_input[k][1].index("{") + 1 : read_input[k][1].index("}")
        ]
        location_list.append(
            read_input[k][1].replace("@", "").replace('"', "").split("/")
        )
    for i, _ in enumerate(location_list):
        if len(location_list[i][0]) > 1:
            temp.append(location_list[i][0])
    lvls = sorted(set(temp))

    location_json.create_locations(path=read_file_path)

    location_json.create_maps(path=read_file_path, maps_names=lvls)
    tracker_layout.create_broadcast_layout(path=read_file_path)
    tracker_layout.create_tracker_basic_layout(path=read_file_path)
    tracker_layout.create_tracker_tabs(path=read_file_path, maps_names=lvls)
    tracker_layout.create_item_layout(path=read_file_path)

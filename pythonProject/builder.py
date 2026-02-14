import json
import os
import sys
import tkinter as tk
from sys import exception
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
    cmd_parser.add_argument("-H", "--home", type=str)
    cmd_parser.add_argument("-G", "--game", type=str)
    cmd_parser.add_argument("-S", "--source", type=str)
    cmd_parser.add_argument("-T", "--test", action="store_true", default=False)
    # cmd_parser.add_argument("", "")
    # cmd_parser.add_argument("", "", )
    cmd_args = cmd_parser.parse_args()
    if cmd_args.home is None:
        root = tk.Tk()
        root.withdraw()

        read_file_path = tk.filedialog.askdirectory()
    else:
        read_file_path = cmd_args.home
    datapackage_path = cmd_args.source
    if not os.path.exists(read_file_path + "/datapackage_url.json"):
        with open(read_file_path + "/datapackage_url.json", "w", encoding="utf-8") as base_file:
            url = (
                cmd_args.source or input("datapackage source (url): ")
                or "https://archipelago.gg"
            )
            if "http" in url:
                if not "/datapackage" in url:
                    url = f"{url}/datapackage"
            elif "\\" in url:
                url = url.replace("\\", "/")
            game_name = cmd_args.game or input("Game name from Datapackage: ")
            dp_json = {
                "url" : f"{url}",
                "game_name" : f"{game_name}"
            }
            base_file.write(json.dumps(dp_json, indent=4))
    if cmd_args.source and cmd_args.game:
        datapackage_path = cmd_args.source
        if "http" in datapackage_path and not "/datapackage" in datapackage_path:
            datapackage_path = f"{datapackage_path}/datapackage"
        elif "\\" in datapackage_path:
            datapackage_path = datapackage_path.replace("\\", "/")
        game_name = cmd_args.game
    else:
        with open(f"{read_file_path}/datapackage_url.json") as args_json:
            dp_json = json.load(args_json)
            datapackage_path = dp_json["url"]
            game_name = dp_json["game_name"]
        # *other_options = (
        #     dp_json = json.load(read_file_path + "/datapackage_url.txt")
        #     # open(read_file_path + "/datapackage_url.txt").readline().split(", ")
        # )
    # if "http" in datapackage_path:
    try:
        games_dict = requests.get(datapackage_path).json()["games"]
    except:
        with open(rf"{datapackage_path}") as datapackage_export:
            loaded_json = json.load(datapackage_export)
            games_dict = loaded_json["games"]
    finally:
        if games_dict is None:
            raise(exception())
    assert isinstance(read_file_path, str)
    assert isinstance(game_name, str)
    assert isinstance(games_dict, dict)

    base_structure.create_base_structure(
        path=read_file_path, game_name=game_name, game_dict=games_dict, test_state=cmd_args.test
    )

    item_json.create_items(path=read_file_path)
    read_input = []
    location_list = []
    hosted_item_list = []
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
        if '",' in read_input[k][1]:
            read_input[k][1] = read_input[k][1][
                read_input[k][1].index("{") + 1: read_input[k][1].rindex("}")
            ].split('",')
        else:
            read_input[k][1] = read_input[k][1][
                read_input[k][1].index("{") + 1: read_input[k][1].rindex("}")
            ]

    if isinstance(read_input[k][1], list):
        for location in read_input[k][1]:
            if "@" in location:
                location_list.append(
                    location.replace("@", "").strip().replace('"', "").split("/")
                )
            else:
                hosted_item_list.append(
                    location.replace('"', "").strip().replace(" ", "")
                )
    else:
        if "@" in read_input[k][1]:
            location_list.append(
                read_input[k][1].replace("@", "").strip().replace('"', "").split("/")
            )
        else:
            hosted_item_list.append(
                read_input[k][1].replace('"', "").strip().replace(" ", "")
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

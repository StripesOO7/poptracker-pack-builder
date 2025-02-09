import os
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
    root = tk.Tk()
    root.withdraw()

    read_file_path = tk.filedialog.askdirectory()
    if not os.path.exists(read_file_path + "/datapackage_url.txt"):
        with open(read_file_path + "/datapackage_url.txt", "w") as base_file:
            url = (
                input("datapackage source (url): ")
                or "https://archipelago.gg/datapackage"
            )
            game = input("Game name from Datapackage: ")
            base_file.write(f"{url}, {game}, ")
    datapackage_path, game_name, *other_options = (
        open(read_file_path + "/datapackage_url.txt").readline().split(", ")
    )

    games_dict = requests.get(datapackage_path).json()["games"]

    base_structure.create_base_structure(
        path=read_file_path, game_name=game_name, game_dict=games_dict
    )

    location_json.create_hints(path=read_file_path)
    item_json.create_items(path=read_file_path)
    read_input = []
    location_list = []
    temp = []
    lvls = set()
    locations_dict = dict()
    with open(read_file_path + "/scripts/autotracking/location_mapping.lua") as mapping:
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

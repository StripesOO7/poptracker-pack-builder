import json
import os
import tkinter as tk
from tkinter import filedialog
from item_json import _item_toggle_preset
hint_item_list = []

def _collect_hint_item_names(hint_item_name):
    hint_item_list.append(hint_item_name)

def traverse_json(json_dict, offset:dict[str:int], fullpath:str):
    keys = json_dict.keys()
    if "name" not in keys:
        print("pause")
        return json_dict
    fullpath = fullpath + json_dict["name"].lower()
    json_dict["name"] = f'{json_dict["name"]} - hint'
    if "map_locations" in keys:

        for map_location in json_dict["map_locations"]:
            if "size" in map_location.keys():
                offset['x'] = map_location['size'] if offset['x'] > 0 else -map_location['size']
                offset['y'] = map_location['size'] if offset['y'] > 0 else -map_location['size']
            map_location["x"] = map_location['x'] = offset['x']
            map_location['y'] = map_location['y'] = offset['y']
            map_location["shape"] = "diamond"
    if "section" in keys:
        for section in json_dict["section"]:
            section = traverse_json(section, offset, fullpath)

    if "children" in keys:
        for children in json_dict["children"]:
            children = traverse_json(children, offset, fullpath)
    if not "children" in keys and not "section" in keys:
        fullpath = fullpath.replace("'", ' ').replace("'", ' ')
        final_fullpath = f"{fullpath.replace(' ', '_')}_hint"
        _collect_hint_item_names(final_fullpath)
        json_dict["visibility_rules"] = final_fullpath
    return json_dict

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    x_offset = 0
    y_offset = 0
    print("Select the folder of the locations to have hint_locations created for: ")
    path = tk.filedialog.askdirectory()
    print("where do you want your hints to be places?\n"
          "valid options:\n"
          "- letf\n"
          "- right\n"
          "- bottom\n"
          "- top\n"
          "ANY non conflicting combination is possible. i.e top left, bottom right or just left:")
    direction = input().lower()
    if "left" in direction:
        x_offset = -20
    elif "right" in direction:
        x_offset = 20

    if "top" in direction:
        y_offset = -20
    elif "bottom" in direction:
        y_offset = 20

    locations_files = os.listdir(path)
    for file in locations_files:
        print(file, path)
        if file == "lightworld.json":
            print("pause")
        with open(f'{path}/{file}','r') as location_json:
            file_list = location_json.readlines()
            file_str = "".join(file_list)
            file_json_list = json.loads(file_str)
            for json_obj in file_json_list:
                hint_json = traverse_json(json_obj, {"x":x_offset, "y":y_offset}, "")

        with open(f'{path}/{file.replace(".json","_hints.json")}', 'w') as new_location_json:
            new_location_json.write(json.dumps([hint_json, json_obj]))
    with open(f'{path.replace(path.split("/")[-1], "items")}/hints_items.json', "w") as hint_items_file:
        hint_item_json = []
        for hint_item in hint_item_list:
            hint_item_json.append(_item_toggle_preset(hint_item))
        hint_items_file.write(json.dumps(hint_item_json, indent=4))
    with open(f'{path.replace(path.split("/")[-1], "scripts")}/autotracking/hints_mapping.lua', "w") as hint_mapping:
        hint_mapping.write("HINTS_MAPPING = \u007b\n")

        for hint_item in hint_item_list:
            hint_mapping.write(
                f'\t[] = \u007b\u007b"{hint_item}", "toggle"\u007d\u007d,\n'
            )
        hint_mapping.write("\u007d")


import json
import os
import tkinter as tk
from tkinter import filedialog
from item_json import _item_toggle_preset


# hint_item_list = []

# def _collect_hint_item_names(hint_item_name):
#     hint_item_list.append(hint_item_name)

def traverse_json(json_dict, offset:dict[str:int], fullpath:str):
    keys = json_dict.keys()
    if "name" not in keys:
        print("pause")
        return json_dict
    if "access_rules" in keys:
        del(json_dict["access_rules"])
    if "visibility_rules" in keys:
        del(json_dict["visibility_rules"])
    if fullpath == "":
        fullpath = json_dict["name"].lower()
    else:
        fullpath = f'{fullpath}_{json_dict["name"].lower()}'
    json_dict["name"] = f'{json_dict["name"]} - hint'
    if "map_locations" in keys:

        for map_location in json_dict["map_locations"]:
            if "size" in map_location.keys():
                offset['x'] = map_location['size'] if offset['x'] > 0 else -map_location['size']
                offset['y'] = map_location['size'] if offset['y'] > 0 else -map_location['size']
            map_location["x"] = map_location['x'] = offset['x']
            map_location['y'] = map_location['y'] = offset['y']
            map_location["shape"] = "diamond"
    if "sections" in keys:
        for section in json_dict["sections"]:
            section = traverse_json(section, offset, fullpath)

    if "children" in keys:
        for children in json_dict["children"]:
            children = traverse_json(children, offset, fullpath)
    if not ("children" in keys) or not ("sections" in keys):
        fullpath = fullpath.replace("'", ' ').replace("'", ' ')
        final_fullpath = f"{fullpath.replace(' ', '_')}_hint"
        # _collect_hint_item_names(final_fullpath)
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
          "- left\n"
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
        hint_json = []
        if file == "lightworld.json":
            print("pause")
        with open(f'{path}/{file}','r', encoding="utf-8") as location_json:
            file_list = location_json.readlines()
            file_str = "".join(file_list)
            file_json_list = json.loads(file_str)
            for json_obj in file_json_list:
                hint_json.append(traverse_json(json_obj, {"x":x_offset, "y":y_offset}, ""))

        with open(f'{path}/{file.replace(".json","_hints.json")}', 'w', encoding="utf-8") as new_location_json:
            new_location_json.write(json.dumps(hint_json, indent=4))
    with open(f'{path.replace(path.split("/")[-1], "items")}/hints_items.json', "w", encoding="utf-8") as hint_items_file:
        hint_item_json = []
        for hint_item in hint_item_list:
            hint_item_json.append(_item_toggle_preset(hint_item))
        hint_items_file.write(json.dumps(hint_item_json, indent=4))
    with open(f'{path.replace(path.split("/")[-1], "scripts")}/autotracking/hints_mapping.lua', "w", encoding="utf-8") as hint_mapping:
        read_input = []
        location_list = []
        hosted_item_list = []

        hints_dict = {}
        temp = []
        with open(f'{path.replace(path.split("/")[-1], "scripts")}/autotracking/location_mapping.lua',
                  "r", encoding="utf-8") as location_mapping:
            while inputs := location_mapping.readline():
                if "]" in inputs:
                    if not (
                            inputs.strip()[0:2] == "--" or inputs.strip()[0:2] == "//"
                    ):
                        if "--" in inputs and inputs.rindex("--") > inputs.rindex("}"):
                            inputs = inputs[: inputs.rindex("--")]
                            read_input.append(inputs.split("="))
                        elif inputs.rindex("}") == inputs.rindex("{") + 1:
                            pass
                        else:
                            read_input.append(inputs.split("="))
                else:
                    pass

            for k, _ in enumerate(read_input):
                read_input[k][0] = int(
                    read_input[k][0][
                    read_input[k][0].find("[") + 1: read_input[k][0].rfind("]")
                    ]
                )
                hints_dict[read_input[k][0]] = []
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
                                location.replace("@", "").replace('"', "").split("/")
                            )
                            location = location.replace("@", ""
                                                    ).replace('"', ""
                                                    ).replace("/", "_"
                                                    ).replace("'", ' '
                                                    ).replace(" ", "_"
                                                    ).lower()
                            hints_dict[read_input[k][0]].append(
                                '_'.join([location, "hint"])
                            )
                        else:
                            hosted_item_list.append(
                                location.replace('"', "").strip().replace(" ", "")
                            )
                else:
                    if "@" in read_input[k][1]:
                        location_list.append(
                            read_input[k][1].replace("@", "").replace('"', "").split("/")
                        )
                    else:
                        hosted_item_list.append(
                            read_input[k][1].replace('"', "").strip().replace(" ", "")
                        )
                    read_input[k][1] = read_input[k][1][:
                                            ].replace("@", ""
                                            ).replace('"', ""
                                            ).replace("/", "_"
                                            ).replace("'", ' '
                                            ).replace(" ", "_"
                                            ).lower()
                    hints_dict[read_input[k][0]].append(
                        '_'.join([read_input[k][1][:], "hint"])
                    )

        hint_mapping.write("HINTS_MAPPING = \u007b\n")

        for hint_item in hint_item_list:
            text = ""
            for hint_dict_list in hints_dict:
                if hint_item in  hints_dict[hint_dict_list]:
                        # print("found")
                        for item_name in hints_dict[hint_dict_list]:
                            if text == "":
                                text = f'\u007b"{item_name}", "toggle"\u007d'
                            else:
                                text = text+f',\u007b"{item_name}", "toggle"\u007d'
                        hint_mapping.write(
                            f"""\t[{hint_dict_list}] = \u007b{text}\u007d,\n"""
                        )
        hint_mapping.write("\u007d")


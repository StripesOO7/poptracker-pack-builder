import os
import json
import random
import tkinter as tk
from tkinter import filedialog
import requests
import re
import shutil


def create_base_structure(path: str, game_name: str, game_dict: dict, test_state: bool = False):
    """
    creates every needed directory and file needed to get a basic poptracker pack working and loading if the needed
    file is not already present
    :param str path: Path to the root folder of the Trackerpack
    :param str game_name: Name of the Game the Tracker is Made for. needs to Match the name in the AP datapackage
    :param dict game_dict: the json formated part from the AP datapackage for the specified game
    :return:
    """
    internal_cwd = os.path.dirname(os.path.realpath(__file__))
    game_name_lua = game_name.lower().replace(' ', '_')
    game_name_lua = game_name_lua.replace(' ', '_').capitalize()
    if not os.path.exists(path + "/scripts"):
        os.mkdir(path + "/scripts")
        os.mkdir(path + "/scripts/autotracking")
        os.mkdir(path + "/scripts/logic")
        os.mkdir(path + "/scripts/logic/graph_logic")
    if not os.path.exists(path + "/scripts/autotracking/archipelago.lua"):
        shutil.copy2(f'{internal_cwd}/lua/archipelago.lua', f'{path}/scripts/autotracking/archipelago.lua')
    if not os.path.exists(path + "/scripts/init.lua"):
        shutil.copy2(f'{internal_cwd}/lua/init.lua', f'{path}/scripts/init.lua')
    if not os.path.exists(path + "/scripts/luaitems.lua"):
        shutil.copy2(f'{internal_cwd}/lua/luaitems.lua', f'{path}/scripts/luaitems.lua')

    if not os.path.exists(path + "/scripts/items_import.lua"):
        shutil.copy2(f'{internal_cwd}/lua/items_import.lua', f'{path}/scripts/items_import.lua')
    if not os.path.exists(path + "/scripts/layouts_import.lua"):
        shutil.copy2(f'{internal_cwd}/lua/layouts_import.lua', f'{path}/scripts/layouts_import.lua')
    if not os.path.exists(path + "/scripts/settings.lua"):
        shutil.copy2(f'{internal_cwd}/lua/settings.lua', f'{path}/scripts/settings.lua')
    if not os.path.exists(path + "/scripts/autotracking.lua"):
        shutil.copy2(f'{internal_cwd}/lua/autotracking.lua', f'{path}/scripts/autotracking.lua')
    if not os.path.exists(path + "/scripts/watches.lua"):
        shutil.copy2(f'{internal_cwd}/lua/watches.lua', f'{path}/scripts/watches.lua')
    if not os.path.exists(path + "/manifest.json"):
        game_name_lua = game_name.lower().replace(' ', '_')
        for char in ("@", "#", "$", "%", "&", "(", ")", ".", "+", "–", "*", "?", "[", "^", "~", ":", "-", "\\", "/"):
            game_name_lua = game_name_lua.replace(char, "_")
        game_name_lua = re.sub(r'(_)\1+', r'\1', game_name_lua)
        with open(path + "/manifest.json", "w", encoding="utf-8") as manifest:
            manifest_json = {
                "name": f"{game_name} Archipelago",
                "game_name": f"{game_name}",
                "package_version": "0.0.1",
                "package_uid": f"{game_name.lower()}_ap",
                "author": "builder_script",
                "variants": {
                    "Map Tracker": {"display_name": "Map Tracker", "flags": ["ap"]},
                    "Items Only": {"display_name": "Items Only", "flags": ["ap"]},
                },
                "min_poptracker_version": "0.31.0",
            }
            # manifest["platform"] = "snes"
            # manifest["versions_url"] = "https://raw.githubusercontent.com/<username>/<repo_name>/versions/versions.json"
            manifest.write(json.dumps(manifest_json, indent=4))
    if not os.path.exists(path + "/LICENSE"):
        with open(path + "/LICENSE", "w", encoding="utf-8") as LICENSE:
            LICENSE.write(f"""
MIT License

Copyright (c) 2025 Stripes007

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
        """)
    if not os.path.exists(path + "/scripts/logic/base_logic.lua"):
        shutil.copy2(f"{internal_cwd}/lua/base_logic.lua", f'{path}/scripts/logic/base_logic.lua')
        # with open(path + "/scripts/logic/base_logic.lua", "w", encoding="utf-8") as logic_lua:
        #     logic_lua.write(
        #         f"""
        #         """)
    if not os.path.exists(path + "/scripts/logic/graph_logic/logic_main.lua"):
        # shutil.copy2(f"{internal_cwd}/lua/logic_main.lua", f'{path}/scripts/logic/graph_logic/logic_main.lua')
        for char in ():
            game_name_lua
        with open(internal_cwd + "/lua/logic_main.lua", "r", encoding="utf-8") as logic_lua:
            # base_lua = logic_lua.read().format(game_name_lua=game_name_lua)
            base_lua = logic_lua.read().replace('{game_name_lua}', game_name_lua)

        with open(path + "/scripts/logic/graph_logic/logic_main.lua", "w", encoding="utf-8") as logic_lua:
            logic_lua.write(base_lua)
    if not os.path.exists(path + "/scripts/logic/logic_helper.lua"):
        shutil.copy2(f"{internal_cwd}/lua/logic_helper.lua", f'{path}/scripts/logic/logic_helper.lua')
#         with open(path + "/scripts/logic/logic_helper.lua", "w", encoding="utf-8") as logic_helper_lua:
#             logic_helper_lua.write(
#                 """
# """
#             )
    if not os.path.exists(path + "/images"):
        os.mkdir(path + "/images")
        os.mkdir(path + "/images/items")
        os.mkdir(path + "/images/maps")
        os.mkdir(path + "/images/settings")
    if not os.path.exists(path + "/items"):
        os.mkdir(path + "/items")
    if not os.path.exists(path + "/layouts"):
        os.mkdir(path + "/layouts")
    if not os.path.exists(path + "/locations"):
        os.mkdir(path + "/locations")
    if not os.path.exists(path + "/maps"):
        os.mkdir(path + "/maps")
    if not (
        os.path.exists(path + "/scripts/autotracking/item_mapping.lua")
        and os.path.exists(path + "/scripts/autotracking/location_mapping.lua")
    ):
        _create_mappings(path=path, game_data=game_dict[game_name], test_state=test_state)
        return exit()


def _create_mappings(path: str, game_data: dict[str, int], test_state: bool = False):
    """
    writes the 2 mapping files needed for location and item tracking via AP
    :param game_data:
    :return:
    """
    items_data = game_data["item_name_to_id"]
    locations_data = game_data["location_name_to_id"]
    item_name_data = {**items_data, **locations_data}
    _write_mapping(path=path, file_name="item_mapping", data=items_data, type="items", test_state=test_state)
    _write_mapping(
        path=path, file_name="location_mapping", data=locations_data, type="locations"
    )
    # _write_mapping(
    #     path=path, file_name="item_names", data=item_name_data, type="item_names"
    # )
    pass


def _write_mapping(path: str, file_name: str, data: dict[str, int], type: str, test_state: bool = False):
    """
    writes the corresponding mapping file if AP-ID's to names.
    searches for the most common delimiters used in locationnames to possibly preselect/-create some regions.
    Item-types need to be adjusted after that step.
    Defaults to "toggle", randomizes it if Test-flag is set
    :param path:
    :param file_name:
    :param data:
    :param type:
    :return:
    """
    delimiter = [" - ", ": ", ") "]
    replacement = ["/", "/", ")/"]
    escape = ["\\", "\'", "\""]
    forbidden = ["<", ">", ":", "|", "?", "*"]
    item_states = ["toggle", "consumable", "static", "progressive", "progressive_toggle"]

    with open(path + "/scripts/autotracking/" + file_name + ".lua", "w", encoding="utf-8") as mapping:
        mapping.write(f"{file_name.upper()} = \u007b\n")
        match type:
            case "items":
                for name, ids in data.items():
                    for escape_char in escape:
                        if escape_char in name:
                            # name = name.replace(f"{escape_char}", f"\\{escape_char}")
                            name = name.replace(f"{escape_char}", "")
                    mapping.write(
                        f'\t[{ids}] = \u007b\u007b"{name.replace(" ", "").lower()}", '
                        f'"{random.choice(item_states) if test_state else "toggle" }"\u007d\u007d,'
                        f'\n'
                    )
            case "locations":
                for name, ids in data.items():
                    br = "false"

                    for i, spacer in enumerate(delimiter):
                        if spacer in name:
                            opened = name.find("(")
                            closed = name.find(")")
                            check_inbetween = name.find(spacer)
                            if opened < check_inbetween and check_inbetween < closed:
                                name = name[:closed] + name[closed:].replace(
                                    f"{spacer}", replacement[i]
                                )
                                name = name.replace(f"{spacer}", " - ")
                            else:
                                name = name.replace(f"{spacer}", replacement[i])
                    for forbidden_char in forbidden:
                        name = name.replace(f"{forbidden_char}", "")
                    for escape_char in escape:
                        if escape_char in name:
                            # name = name.replace(f"{escape_char}", f"\\{escape_char}")
                            name = name.replace(f"{escape_char}", "")
                    mapping.write(f'\t[{ids}] = \u007b"@{name}"\u007d,\n')
            # case "item_names":
            #     for name, ids in data.items():
            #         for escape_char in escape:
            #             if escape_char in name:
            #                 # name = name.replace(f"{escape_char}", f"\\{escape_char}")
            #                 name = name.replace(f"{escape_char}", "")
            #         mapping.write(
            #             f'\t["{name.replace(" ", "").lower()}"] = "{name}",'
            #             f"\n"
            #         )
        mapping.write("\u007d")


if __name__ == "__main__":
    import argparse
    root = tk.Tk()
    root.withdraw()

    print(
        """
    Please select the Directory the pack should be created in
    If there is no file called 'datapackage_url.json' already present please provide the requested information.
    """
    )
    read_file_path = tk.filedialog.askdirectory()
    if not os.path.exists(read_file_path + "/datapackage_url.json"):
        with open(read_file_path + "/datapackage_url.json", "w", encoding="utf-8") as base_file:
            url = (
                    input("datapackage source (url): ")
                    or "https://archipelago.gg"
            )
            game_name = input("Game name from Datapackage: ")
            dp_json = {
                "url": f"{url}/datapackage",
                "game_name": f"{game_name}"
            }
            base_file.write(json.dumps(dp_json, indent=4))
    with open(f"{read_file_path}/datapackage_url.json") as args_json:
        dp_json = json.load(args_json)
        datapackage_path = dp_json["url"]
        game_name = dp_json["game_name"]

    games_dict = requests.get(datapackage_path).json()["games"]

    create_base_structure(
        path=read_file_path, game_name=game_name, game_dict=games_dict
    )

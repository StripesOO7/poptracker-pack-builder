import json
import random
import tkinter as tk
from tkinter import filedialog
from item_json import _item_consumable_preset


def _maps_json(map_name: str):
    """
    returns a JSON-compatible dict containing the basic option for a single map definition in poptracker
    :param str map_name: Name of the Region to create a map listing off of.
    :return dict: returns a JSON-compatible dict containing the basic option for a single map definition in poptracker
    """
    map_json_obj = {
        "name": f"{map_name}",
        "location_size": 6,
        "location_border_thickness": 1,
        "img": f"images/maps/{map_name}.png",
    }
    return map_json_obj


def _write_locations(
    loc_dict: dict,
    region: str,
    location_list: list,
    logic_dict: dict,
    overworld: dict,
    overworld_hints: dict,
    top_most_region: str,
    fullpath: str,
    fullpath_hint: str,
    hints_list: list,
    location_mapping_string: str,
):
    """
    Based on the created Locations-dictionary creates a JSON-compatible dict containing all the needed information
    for poptracker to read the respective fil;es as valid location-trees.
    Also adds references to all locations to an all-combining Overworlds file.

    JSON-compatible dict is build in place thus no return value

    To-Do: add logic-rules based on extracted information from logic file(s)

    :param dict loc_dict:
    :param str region: name of the current region you are in and add locations/check to
    :param dict location_list: contains a dict to be filled with either more dict-structures ("children") for more
    nesting of locations or gets "sections" added if this is the final stage for this specific location
    :param dict logic_dict: currently unused thus empty. will contain a full dict containing the special access rules for each location
    :param dict overworld: contains the dict for the overworld.json file to get filled with references
    :param str top_most_region: containes the Name of the topmost Region so the check will be displayed when a Map is created with the same name
    :param str fullpath: contains the full path to the specific location that's needed for the reference in the
    overworld.json to work
    :return: none
    """

    sub_region = loc_dict[region]

    temp_lists = []
    temp_dicts = []
    for i in sub_region.keys():
        if isinstance(sub_region[i], list):
            temp_lists.append(i)
        else:
            temp_dicts.append(i)
    location_list.append(
        {
            "name": f"{region}",
            "chest_unopened_img": f"/images/items/{close_chest}",
            "chest_opened_img": f"/images/items/{open_chest}",
            "overlay_background": "#000000",
            "access_rules": [" "],
        }
    )
    hints_list.append(
        {
            "name": f"{region} - hint",
            "chest_unopened_img": f"/images/items/{close_chest}",
            "chest_opened_img": f"/images/items/{open_chest}",
            "overlay_background": "#000000",
            "access_rules": ["{}"],
        }
    )
    if len(temp_dicts) > 0:
        location_list[-1]["children"] = []
        hints_list[-1]["children"] = []
        for index, location in enumerate(temp_dicts):
            _write_locations(
                sub_region,
                location,
                location_list[-1]["children"],
                logic_dict,
                overworld,
                overworld_hints,
                top_most_region,
                fullpath + "/" + location,
                fullpath_hint + " - hint/" + location,
                hints_list[-1]["children"],
                location_mapping_string,
            )
    if len(temp_lists) > 0:
        location_list[-1]["sections"] = []
        hints_list[-1]["sections"] = []
        for location in temp_lists:

            x = random.randint(10, 2500)
            y = random.randint(10, 2500)
            location_list[-1]["sections"].append(
                {
                    "name": f"{location}",
                    "access_rules": [],
                    "visibility_rules": [],
                    "item_count": 1,
                }
            )
            hints_list[-1]["sections"].append(
                {
                    "name": f"{location} - hint",
                    "access_rules": [],
                    "visibility_rules": [
                        f"{(fullpath+'/'+location).replace(' ', '_').replace('/', '_').lower()}"
                    ],
                    "item_count": location_mapping_string.count(
                        fullpath + "/" + location
                    ),
                }
            )
            overworld["sections"].append(
                {
                    "name": f"{region} - {location}",
                    "ref": f"{fullpath + '/' + location}",
                }
            )
            overworld_hints["sections"].append(
                {
                    "name": f"{region} - {location} - hint",
                    "ref": f"{fullpath_hint + ' - hint/' + location} - hint",
                }
            )
        location_list[-1]["map_locations"] = [
            {"map": f"{top_most_region}", "x": f"{x}", "y": f"{y}", "size": 6}
        ]
        hints_list[-1]["map_locations"] = [
            {"map": f"{top_most_region}", "x": f"{x}", "y": f"{y}", "size": 12}
        ]


def _location_dict_builder(
    locations_dict: dict,
    path: list,
    location_list: list,
    logic_dict: dict,
    building: bool,
):
    """
    This function builds recursive a multi-layered dictionary.
    As long as there are elements left in location_list to traverse downwards it will add the first entry of that
    list as key to a new dictionary layer. If the Key already exists ist just adds another entry to that.
    When the last item in location_list is reached it will add it the final stage of the dict containing an empty list.
    The empty list is currently unused but is intended to store logic information or this specific Check/location.
    :param dict locations_dict: contains the part of the dict that needs to still be traversed. get moved 1 stage
    deeper with each iteration
    :param list path: list of stages already traversed through the dict-structure
    :param list location_list: remaining stages to traverse/add to the dict-structure
    :param dict logic_dict: currently unused otherwise containing a dict of logic rules applicable for each check
    :param bool building:
    :return: returns a sorted dictionary of the currently added locations
    """
    location_dict = locations_dict
    if building:
        if not len(location_list) == 1:

            for part in path:
                location_dict = location_dict[part]
            # print(location_list[1:], location_list[1:][0])
            print(path)
            location_dict.setdefault(location_list[0], dict())
            path.append(location_list[0])
            _location_dict_builder(
                locations_dict, path, location_list[1:], logic_dict, True
            )
        else:
            for part in path:
                location_dict = location_dict[part]
            try:
                location_dict.setdefault(location_list[0], list())
            except AttributeError:
                print(
                    f"Script stopped at '{location_list[0]}' in:\n'@{'/'.join(path)}/{location_list[0]}'\n"
                    f"This is because another location already exists that ends at '@{'/'.join(path)}' but the "
                    f"current location has sections deeper down that path.\n"
                    f"To fix this you need to add another section past '{path[-1]}'. The most basic way "
                    f"would be to double the name of the last section such that it results in "
                    f"'@{'/'.join(path)}/{path[-1]}'"
                )
                exit()
    return dict(sorted(location_dict.items()))


def create_hints(path: str):
    read_input = []
    hints_dict = {}
    location_list = []
    with open(path + "/scripts/autotracking/location_mapping.lua") as mapping:
        while inputs := mapping.readline():
            if "]" in inputs:
                read_input.append(inputs.split("="))
            else:
                pass
    for k, _ in enumerate(read_input):
        read_input[k][0] = int(
            read_input[k][0][
                read_input[k][0].find("[") + 1 : read_input[k][0].rfind("]")
            ]
        )
        read_input[k][1] = read_input[k][1][
            read_input[k][1].index("{") + 1 : read_input[k][1].index("}")
        ]
        location_list.append(
            read_input[k][1].replace("@", "").replace('"', "").split("/")
        )

        hints_dict[read_input[k][0]] = (
            read_input[k][1],
            read_input[k][1]
            .replace("@", "")
            .replace('"', "")
            .replace("/", "_")
            .replace(" ", "_")
            .lower(),
        )

    with open(path + "/scripts/autotracking/hints_mapping.lua", "w") as hint_mapping:
        hint_mapping.write("HINTS_MAPPING = \u007b\n")

        for index in sorted(hints_dict.keys()):
            hint_mapping.write(
                f'\t[{index}] = \u007b\u007b"{hints_dict[index][1]}", "toggle"\u007d\u007d,\n'
            )
        hint_mapping.write("\u007d")


def create_locations(path: str):  # , logic: dict[str, str]):
    """
    creates the singled out location files according to the names found in the locations_mapping file.

    Also asks for 2 images for still closed and already opened chests/items if not already defined in the datapackage file
    :param str path: Path to the root folder of the Tracker. Used for loading of the mapping file and saving the
    resulting <location>.json files
    :param logic:
    :return: none
    """
    global open_chest, close_chest
    read_input = []
    location_list = []
    hosted_item_list = []

    hints_dict = {}
    temp = []
    forbidden = ["<", ">", ":", "/", "\\", "|", "?", "*"]
    # global lvls, locations_dict, maps_names
    with open(path + "/scripts/autotracking/location_mapping.lua") as mapping:
        while inputs := mapping.readline():
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
                read_input[k][0].find("[") + 1 : read_input[k][0].rfind("]")
            ]
        )
        if '",' in read_input[k][1]:
            read_input[k][1] = read_input[k][1][
                read_input[k][1].index("{") + 1 : read_input[k][1].rindex("}")
            ].split('",')
        else:
            read_input[k][1] = read_input[k][1][
                read_input[k][1].index("{") + 1 : read_input[k][1].rindex("}")
            ]

        if isinstance(read_input[k][1], list):
            for location in read_input[k][1]:
                if "@" in location:
                    location_list.append(
                        location.replace("@", "").replace('"', "").split("/")
                    )
                    hints_dict[read_input[k][0]] = (
                        location[: location.rfind("/")],
                        location[: location.rfind("/")]
                        .replace("@", "")
                        .replace('"', "")
                        .replace("/", "_")
                        .replace(" ", "_")
                        .lower(),
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

            hints_dict[read_input[k][0]] = (
                read_input[k][1][: read_input[k][1].rfind("/")],
                read_input[k][1][: read_input[k][1].rfind("/")]
                .replace("@", "")
                .replace('"', "")
                .replace("/", "_")
                .replace(" ", "_")
                .lower(),
            )

    hosted_item_list = list(set(hosted_item_list))
    for index, item in enumerate(hosted_item_list):
        hosted_item_list[index] = [item, "consumable"]

    with open(path + "/items/location_items.json", "w") as location_items:
        item_json_obj = []

        for item_name, item_types in hosted_item_list:
            item_json_obj.append(_item_consumable_preset(item_name))

        location_items.write(f"{json.dumps(item_json_obj, indent=4)}")

    for i, _ in enumerate(location_list):
        if len(location_list[i][0]) > 1:
            temp.append(location_list[i][0])
    lvls = sorted(set(temp))
    #

    with open(path + "/scripts/locations_import.lua", "w") as locations_file:
        for level_name in lvls:
            locations_file.write(
                f'Tracker:AddLocations("locations/{level_name}.json")\n'
            )
            open(path + f"/scripts/logic/{level_name}.lua", "w").close()
        locations_file.write(f'Tracker:AddLocations("locations/Overworld.json")\n')
        open(path + "/scripts/logic/location_definition.lua", "w").close()
    locations_dict = {e: {} for e in lvls}

    logic_dict = {}  # extract_logic()
    """
    Braucht nen rework.
    idealerweise rekursiv damit man nicht auf 2-3 ebene beschränkt ist.
    das gleiche für das eigentliche location building später
    """
    for location in location_list:
        locations_dict = _location_dict_builder(
            locations_dict, [], location, logic_dict, True
        )
    open_chest = "open.png"
    close_chest = "close.png"
    # open_chest = other_options[0]
    # close_chest = other_options[1]
    with open(path + r"\scripts\autotracking\location_mapping.lua") as mapping_file:
        location_mapping_string = mapping_file.read().replace("\n", "")
    with open(path + rf"\locations\Overworld.json", "w") as overworld:
        overworld_list = []
        overworld_json = {
            "name": "Overworld",
            "chest_unopened_img": f"/images/items/{close_chest}",
            "chest_opened_img": f"/images/items/{open_chest}",
            "overlay_background": "#000000",
            "access_rules": [" "],
            "children": [],
        }
        overworld_hints_json = {
            "name": "Overworld Hints",
            "chest_unopened_img": f"/images/items/{close_chest}",
            "chest_opened_img": f"/images/items/{open_chest}",
            "overlay_background": "#000000",
            "access_rules": [" "],
            "children": [],
        }

        for index, locations_region in enumerate(locations_dict.keys()):
            x = random.randint(10, 2500)
            y = random.randint(10, 2500)
            top_most_region = locations_region
            overworld_json["children"].append(
                {
                    "name": f"{locations_region}",
                    "chest_unopened_img": f"/images/items/{close_chest}",
                    "chest_opened_img": f"/images/items/{open_chest}",
                    "overlay_background": "#000000",
                    "access_rules": [" "],
                    "sections": [],
                    "map_locations": [
                        {"map": "Overworld", "x": f"{x}", "y": f"{y}", "size": 6}
                    ],
                }
            )
            overworld_hints_json["children"].append(
                {
                    "name": f"{locations_region} - hint",
                    "chest_unopened_img": f"/images/items/{close_chest}",
                    "chest_opened_img": f"/images/items/{open_chest}",
                    "overlay_background": "#000000",
                    "access_rules": ["{}"],
                    "sections": [],
                    "map_locations": [
                        {"map": "Overworld", "x": f"{x}", "y": f"{y}", "size": 12}
                    ],
                }
            )
            with open(
                path + rf"\locations\{locations_region}.json", "w"
            ) as locations_file:
                location_file_list = []
                location_hint_list = []

                _write_locations(
                    locations_dict,
                    locations_region,
                    location_file_list,
                    logic_dict,
                    overworld_json["children"][index],
                    overworld_hints_json["children"][index],
                    top_most_region,
                    top_most_region,
                    locations_region,
                    location_hint_list,
                    location_mapping_string,
                )

                locations_file.write(
                    json.dumps(location_hint_list + location_file_list, indent=4)
                )

        overworld_list.append(overworld_hints_json)
        overworld_list.append(overworld_json)
        overworld.write(json.dumps(overworld_list, indent=4))

        maps_names = ["Overworld"]
        for lvl in lvls:
            if len(locations_dict[lvl]) > 9:
                maps_names.append(lvl)


#


def create_maps(path: str, maps_names: list):
    """
    creates the maps used in the tabbed section in poptracker.
    uses only regions with more than 9 sections in it according to the sectioning in the locations_mapping
    :param str path: Path to the root folder of the Tracker. Used for loading of the mapping file and saving the
    resulting <map_name>.json files
    :param list maps_names: list of names to be used to create the corresponding map definitions. Based of the first
    stage in the locations_mapping for each location
    :return: none
    """
    with open(path + "/maps/maps.json", "w") as maps:
        maps_json = []
        for map in maps_names:
            maps_json.append(_maps_json(map))

        maps.write(json.dumps(maps_json, indent=4))


# #


if __name__ == "__main__":
    """
    - Askes for the root folder of the Trackerpack.
    - Loades the locations_mapping.lua file that should have been created previously.
    - Creates Map-definitions for the first stage of each location if there are more then 9 locations total inside of
    that stage
    - Creates nested location-definitions for all the first stages of each location.
    """
    root = tk.Tk()
    root.withdraw()
    #
    print("Select the base-folder of the pack:")
    base_path = tk.filedialog.askdirectory()
    print("Path to base-folder of the pack: ", base_path)

    read_input = []
    location_list = []
    temp = []
    lvls = set()
    locations_dict = dict()
    # maps_names = []
    with open(base_path + "/scripts/autotracking/location_mapping.lua") as mapping:
        while inputs := mapping.readline():
            if "]" in inputs:
                if "--" in inputs and inputs.rindex("--") > inputs.rindex("}"):
                    inputs = inputs[: inputs.rindex("--")]
                    read_input.append(inputs.split("="))
                elif inputs.rindex("}") == inputs.rindex("{") - 1:
                    pass
                elif not (inputs.strip()[0:2] == "--" or inputs.strip()[0:2] == "//"):
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

    create_maps(base_path, lvls)
    create_locations(base_path)
    # print("finished")

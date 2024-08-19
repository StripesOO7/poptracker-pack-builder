import json
import random
import tkinter as tk
from tkinter import filedialog

def _maps_json(map_name):
    map_json_obj = {
        "name": f"{map_name}",
        "location_size": 6,
        "location_border_thickness": 1,
        "img": f"images/maps/{map_name}.png"
    }
    return map_json_obj

def _write_locations(loc_dict, region, location_list:list, logic_dict, overworld:dict, top_most_region, fullpath):
    '''
    if the logic form the rules-file could get split the location name into 3 sets (region, location, item) this
    function gets called.
    the set images for still closed and already opened items are set here, defaults to the poptracker provided
    open/closed images.
    Also try's to find matching region/location/items rules in the logicfile and writes them in the corresponding
    section. if nothing gets found access_rules get skipped and need to be added later. A file of the extracked rules is saved in the packs directory
    :param loc_dict:
    :param region:
    :param location_list:
    :param logic_dict:
    :param overworld:
    :param top_most_region:
    :param fullpath:
    :return:
    '''

    # regions = region
    well = False
    sub_region = loc_dict[region]

    # print(sorted(sub_region), sub_region)
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
            "chest_unopened_img": f"/images/Items/{close_chest}",
            "chest_opened_img": f"/images/Items/{open_chest}",
            "overlay_background": "#000000",
            "access_rules": [" "],
        }
    )
    if len(temp_dicts) > 0:
        location_list[-1]["children"] = []
        for index, location in enumerate(temp_dicts):
            _write_locations(sub_region, location, location_list[-1]["children"], logic_dict, overworld,
                                 top_most_region, fullpath + '/' + location)
    if len(temp_lists) > 0:
        location_list[-1]["sections"] = []
        # overworld["sections"] = []
        for i, location in enumerate(temp_lists):
            location_list[-1]["sections"].append(
                {
                    "name": f"{location}",
                    "access_rules": [],
                    "visibility_rules": [],
                    "item_count": 1
                }
            )
            overworld["sections"].append(
                {
                    "name": f"{region} - {location}",
                    "ref": f"{fullpath + '/' + location}"
                }
            )
        location_list[-1]["map_locations"] = [
            {
            "map": f"{top_most_region}",
            "x": random.randint(10, 2500),
            "y": random.randint(10, 1500),
            "size": 6
            }
        ]


def _location_dict_builder(locations_dict: dict, path: list, location_list: list, logic_dict: dict, building: bool):
    # print(location_list)
    location_dict = locations_dict
    if building:
        if not len(location_list) == 1:

            for part in path:
                location_dict = location_dict[part]
            # print(location_list[1:], location_list[1:][0])
            print(path)
            location_dict.setdefault(location_list[0], dict())
            # location_dict[location_list[0]].update({location_list[1:][0]: dict()})
            path.append(location_list[0])
            _location_dict_builder(locations_dict, path, location_list[1:], logic_dict, True)
        else:
            for part in path:
                location_dict = location_dict[part]
                # print(location_dict)
            # print(location_list[0])
            location_dict.setdefault(location_list[0], list())
            # location_dict[location_list[0]].update({location_list[0]: list()})
    # else:
    #     if len(location_list[1:]) > 1:
    #         location_dict[location_list[0]][location_list[1:][0]].append(location_list[1:][1])
    #         location_dict_builder(location_dict[location_list[0]], location_list[1:],logic_dict, False)
    #     elif len(location_list[1:]) == 1:
    #         location_dict[location_list[0]][location_list[1:][0]].append(location_list[1:][0])
    #     else:
    #         try:
    #             location_dict[location_list[0]][location_list[0]].append(logic_dict[location_list[0]])
    #         except:
    #             pass
    # print(location_dict.items())
    return dict(sorted(location_dict.items()))

def create_locations(path: str): #, logic: dict[str, str]):
    '''
    creates the singled out location files according to the names found in the locations_mapping file.
    distinct handling of 2 and 3 segment location splitting.
    Also asks for 2 images for still closed and already opened chests/items if not already defined in the datapackage file
    :param path:
    :param logic:
    :return:
    '''
    global open_chest, close_chest
    read_input = []
    location_list = []
    temp = []
    # global lvls, locations_dict, maps_names
    with open(path+'/scripts/autotracking/location_mapping.lua') as mapping:
        while inputs := mapping.readline():
            if "]" in inputs:
                read_input.append(inputs.split("="))
            else:
                pass
    for k, _ in enumerate(read_input):
        read_input[k][1] = read_input[k][1][read_input[k][1].index('{')+1: read_input[k][1].index('}')]
        location_list.append(read_input[k][1].replace('@', '').replace('"', '').split("/"))
    for i, _ in enumerate(location_list):
        if len(location_list[i][0]) > 1:
            temp.append(location_list[i][0])
    lvls = sorted(set(temp))
    #

    with open(path+"/scripts/locations_import.lua", 'w') as locations_file:
        for level_name in lvls:
            locations_file.write(f'Tracker:AddLocations("locations/{level_name}.json")\n')
            open(path + f"/scripts/logic/{level_name}.lua", "w").close()
        locations_file.write(f'Tracker:AddLocations("locations/Overworld.json")\n')
        open(path + "/scripts/logic/location_definition.lua", "w").close()
    locations_dict = {e: {} for e in lvls}

    logic_dict =  {} # extract_logic()
    """
    Braucht nen rework.
    idealerweise rekursiv damit man nicht auf 2-3 ebene beschränkt ist.
    das gleiche für das eigentliche location building später
    """
    for location in location_list:
        locations_dict = _location_dict_builder(locations_dict, [], location, logic_dict, True)
        # if not len(location) == 1:
        #     locations_dict[location[0]].update({location[1:][0]: list()})
        # else:
        #     locations_dict[location[0]].update({location[0]: list()})
    # for location in location_list:
    #     locations_dict = location_dict_builder(locations_dict, location, logic_dict, False)
    #     # if len(location[1:]) > 1:
    #     #     locations_dict[location[0]][location[1:][0]].append(location[1:][1])
    #     # elif len(location[1:]) == 1:
    #     #     locations_dict[location[0]][location[1:][0]].append(location[1:][0])
    #     # else:
    #     #     try:
    #     #         locations_dict[location[0]][location[0]].append(logic_dict[location[0]])
    #     #     except:
    #     #         pass

    # if other_options[0] in ["", " ", "\n"]:
    #     print(other_options)
    #     open_chest = tk.filedialog.askopenfilename().split('/')[-1]
    #     close_chest = tk.filedialog.askopenfilename().split('/')[-1]
    #     with open(path + '/datapacke_url.txt', 'a') as file:
    #         file.write(f"{open_chest}, {close_chest}")
    # else:
    open_chest = "open.png"
    close_chest = "close.png"
        # open_chest = other_options[0]
        # close_chest = other_options[1]
    with open(path+fr"\locations\Overworld.json", "w") as overworld:
        overworld_list = []
        overworld_json = {
            "name": "Overworld",
            "chest_unopened_img": f"/images/Items/{close_chest}",
            "chest_opened_img": f"/images/Items/{open_chest}",
            "overlay_background": "#000000",
            "access_rules": [" "],
            "children": []
        }

        for index, locations_region in enumerate(locations_dict.keys()):
            top_most_region = locations_region
            # print(city, lvl_locations[city])
            overworld_json["children"].append(
                {
                    "name": f"{locations_region}",
                    "chest_unopened_img": f"/images/Items/{close_chest}",
                    "chest_opened_img": f"/images/Items/{open_chest}",
                    "overlay_background": "#000000",
                    "access_rules": [" "],
                    "sections": [],
                    "map_locations": [
                        {
                            "map": f"{locations_region}",
                            "x": random.randint(10, 2500),
                            "y": random.randint(10, 1500),
                            "size": 6
                        }
                    ]
                }
            )
            with open(path+fr"\locations\{locations_region}.json", "w") as locations_file:
                location_file_list = []

                _write_locations(locations_dict, locations_region, location_file_list, logic_dict,
                                 overworld_json["children"][index], top_most_region, locations_region)
                locations_file.write(json.dumps(location_file_list, indent=4))

        overworld_list.append(overworld_json)
        overworld.write(json.dumps(overworld_list, indent=4))

        maps_names = ["Overworld"]
        for lvl in lvls:
            if len(locations_dict[lvl]) > 9:
                maps_names.append(lvl)
        # overworld.write('''
        #         }
        # ]''')
    # with open(path + fr"\locations\Overworld.json", "r+") as overworld:
    #     json_obj = json.loads(overworld)
    #     pretty_json = json.dumps(json_obj, indent=4)
    #     overworld.write(json_obj)
#

def create_maps(path: str, maps_names:list):
    '''
    creates the maps used in the tabbed section in poptracker.
    uses only regions with more than 9 sections in it according to the sectioning in the locations_mapping
    :param path:
    :param maps_names:
    :return:
    '''
    with open(path+"/maps/maps.json", 'w') as maps:
        maps_json = []
        for map in maps_names:
            maps_json.append(_maps_json(map))

        maps.write(json.dumps(maps_json, indent=4))
# #


if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    #
    # print("Select a file to open")
    # path_to_item_json = filedialog.askopenfilename()
    # print("Filename: ", path_to_item_json)
    print("Select the base-folder of the pack:")
    base_path = tk.filedialog.askdirectory()
    print("Path to base-folder of the pack: ", base_path)

    read_input = []
    location_list = []
    temp = []
    lvls = set()
    locations_dict = dict()
    # maps_names = []
    with open(base_path + '/scripts/autotracking/location_mapping.lua') as mapping:
        while inputs := mapping.readline():
            if "]" in inputs:
                if not inputs.strip()[0:2] == "--":
                    read_input.append(inputs.split("="))
            else:
                pass
    for k, _ in enumerate(read_input):
        read_input[k][1] = read_input[k][1][read_input[k][1].index('{') + 1: read_input[k][1].index('}')]
        location_list.append(read_input[k][1].replace('@', '').replace('"', '').split("/"))
    for i, _ in enumerate(location_list):
        if len(location_list[i][0]) > 1:
            temp.append(location_list[i][0])
    lvls = sorted(set(temp))

    create_maps(base_path, lvls)
    create_locations(base_path)
    # print("finished")

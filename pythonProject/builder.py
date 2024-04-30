import os
import json
import math
import random
import tkinter as tk
from tkinter import filedialog
import requests
import itertools


lvls = set()
locations_dict = dict()
maps_names = []
logic = dict()
open_chest = "open.png"
close_chest = "close.png"
def create_mappings(game_data: dict[str, int]):
    '''
    writes the 2 mapping files needed for location and item tracking via AP
    :param game_data:
    :return:
    '''
    items_data = game_data['item_name_to_id']
    locations_data = game_data['location_name_to_id']
    write_mapping(path=read_file_path, file_name='item_mapping', data = items_data, type='items')
    write_mapping(path=read_file_path, file_name='location_mapping', data = locations_data, type='locations')
    pass


# def create_location_mapping(game: str, location_data: dict[str, int]):
#     # game_data = games_dict[game]
#     locations = location_data['location_name_to_id']
#     print(locations.keys())
#     write_mapping(path=read_file_path, file_name='location_mapping')
#     pass


def write_mapping(path: str, file_name: str, data: dict[str, int], type: str):
    '''
    writes the corresponding mapping file if AP-ID's to names.
    searches for the most common delimiters used in locationnames to possibly preselect/-create some regions.
    Item-types need to be adjusted after that step.
    Defaults to "toggle"
    :param path:
    :param file_name:
    :param data:
    :param type:
    :return:
    '''
    with open(path + '/scripts/autotracking/' + file_name + '.lua', "w") as mapping:
        mapping.write(f'{file_name.upper()} = \u007b\n')
        match type:
            case 'items':
                for name, ids in data.items():
                    mapping.write(f'\t[{ids}] = \u007b"{name.replace(" ", "")}", "toggle"\u007d,\n'),
            case 'locations':
                delimiter = [' - ', ': ', ') ']
                for name, ids in data.items():
                    br = 'false'
                    for spacer in delimiter:
                        if spacer in name:
                            mapping.write(f'\t[{ids}] = \u007b"@{name.replace(f"{spacer}","/")}"\u007d,\n'),
                            br = 'true'
                            break

                        if br == "true":
                            continue

                        mapping.write(f'\t[{ids}] = \u007b"@{name}"\u007d,\n'),
                        break
        mapping.write("\u007d")


def create_items(path: str):
    '''
    gathers the items vom the item_mapping file and converts them according to their specified item_type into a
    pop-readable/-loadable json format.
    Pre-places the itemnames as names for the loaded images. needs to be adjusted if that is not fitting.
    :param path:
    :return:
    '''
    read_input = []
    item_list = []
    with open(path+'/scripts/autotracking/item_mapping.lua') as mapping:
        while inputs := mapping.readline():
            if "]" in inputs:
                read_input.append(inputs.split("="))
            else:
                pass

    for k, _ in enumerate(read_input):
        read_input[k][1] = read_input[k][1][read_input[k][1].index('{')+1: read_input[k][1].index('}')]
        item_list.append(read_input[k][1].replace('"', '').rsplit(', ',1))


    with open(path + "/items/items.json", "w") as items_file:
        items_file.write("[")
        # print(item_list)
        for item_name, item_types in item_list:
            # print(item, types)
            match item_types:
                case "toggle":
                    items_file.write(f'''
                    \u007b
                        "name": "{item_name}",
                        "type": "toggle",
                        "img": "/images/Items/{item_name}.png",
                        "codes": "{item_name.replace(' ', '')}"
                    \u007d,
                    ''')
                case "progressive":
                    items_file.write(f'''
                    \u007b
                        "name": "{item_name}",
                        "type": "progressive",
                        "loop": false,
                        "stages": [
                            \u007b
                                "img": "/images/Items/{item_name}.png",
                                "codes": "{item_name.replace(' ', '')}"
                            \u007d,
                            \u007b
                                "name": "{item_name} returned",
                                "img": "/images/Items/{item_name}.png",
                                "img_mods": "overlay|/images/Menu/Check.png",
                                "codes": "{item_name.replace(' ', '')}_prog"
                            \u007d
                        ],
                        "codes": "{item_name.replace(' ', '')}"
                    \u007d,
                    ''')
                case "progressive_toggle":
                    items_file.write(f'''
                    \u007b
                    "name": "{item_name}",
                    "type": "progressive_toggle",
                    "loop": false,
                    "stages": [
                        \u007b
                            "img": "/images/Items/{item_name}.png",
                            "codes": "{item_name.replace(' ', '')}"
                        \u007d,
                        \u007b
                            "name": "{item_name} returned",
                            "img": "/images/Items/{item_name}.png",
                            "img_mods": "overlay|/images/Menu/Check.png",
                            "codes": "{item_name.replace(' ', '')}_prog_tog"
                        \u007d
                    ],
                    "codes": "{item_name.replace(' ', '')}"
                    \u007d,
                    ''')
                case "consumable":
                    items_file.write(f'''
                    \u007b
                        "name": "{item_name}",
                        "type": "consumable",
                        "allow_disabled": false,
                        "min_quantity": 0,
                        "max_quantity": 10,
                        "increment": 1,
                        "initial_quantity": 0,
                        "img": "/images/Items/{item_name}.png",
                        "overlay_background": "#000000",
                        "codes": "{item_name.replace(' ', '')}"
                    \u007d,''')
                case "composite_toggle":
                    pass
                case "toggle_badged":
                    pass

        items_file.write('''
            {
            }
        ]''')
# #


def write_locations(loc_dict, region, file, logic_dict, overworld):
    '''
    if the logic form the rules-file could get split the location name into 3 sets (region, location, item) this
    function gets called.
    the set images for still closed and already opened items are set here, defaults to the poptracker provided
    open/closed images.
    Also try's to find matching region/location/items rules in the logicfile and writes them in the corresponding
    section. if nothing gets found access_rules get skipped and need to be added later. A file of the extracked rules is saved in the packs directory
    :param loc_dict:
    :param region:
    :param file:
    :param logic_dict:
    :return:
    '''
    # regions = region
    well = False
    sub_region = loc_dict[region]

    # print(sorted(sub_region), sub_region)
    temp_lists = []
    temp_dicts = []
    for i in sub_region.keys():
        if type(sub_region[i]) is list:
            temp_lists.append(i)
        else:
            temp_dicts.append(i)
    # print(temp_lists, temp_dicts)
    # sorted(temp_lists)
    # print(temp_lists)
    # sorted(sub_region)
    file.write(f'''
                    \u007b
                        "name": "{region}",
                        "chest_unopened_img": "/images/Items/{close_chest}",
                        "chest_opened_img": "/images/Items/{open_chest}",
                        "overlay_background": "#000000",
                        "access_rules": [" "],
                        ''')
    if len(temp_dicts) > 0:
        file.write(f'''
                        "children": [
                    ''')
        for location in temp_dicts:
            print(location, sub_region)
            # file.write(f'''
            #                             \u007b
            #                                 "name": "{location}",
            #                                 "chest_unopened_img": "/images/Items/{close_chest}",
            #                                 "chest_opened_img": "/images/Items/{open_chest}",
            #                                 "overlay_background": "#000000",
            #                                 "access_rules": [" "],
            #                                 "children": [
            #                             ''')
            # print(sub_region, region)
            # for k, regions in enumerate(sub_region.keys()):
                # print(len(sub_region[regions]), regions)
                # print(type(sub_region[regions]), type(sub_region[regions]) is dict)
            # print(len(test_1[list(test_1.keys())[0]]))
            # if len(test_1[list(test_1.keys())[0]]) > 0:
        # if type(sub_region) == dict:
        #         file.write('[')
        #         file.write(f'''
        #                     \u007b
        #                         "name": "{region}",
        #                         "chest_unopened_img": "/images/Items/{close_chest}",
        #                         "chest_opened_img": "/images/Items/{open_chest}",
        #                         "overlay_background": "#000000",
        #                         "access_rules": [" "],
        #                         "children": [
        #                     ''')
            write_locations(sub_region, location, file, logic_dict, overworld)
            # if well:
        # file.write('''
        #                 ]
        #             \u007d,''')
        file.write('''
                                ],''')
        # file.write('''
        #
        #                         ]
        #                     }
        #                 ]''')
    if len(temp_lists) > 0:
        # file.write(f'''
        #                     \u007b
        #                         "name": "{region}",
        #                         "chest_unopened_img": "/images/Items/{close_chest}",
        #                         "chest_opened_img": "/images/Items/{open_chest}",
        #                         "overlay_background": "#000000",
        #                         "section": [
        #                     ''')
        file.write(f'''

                                        "sections": [
                                    ''')
        for i, location in enumerate(temp_lists):
            # print("list", sub_region, region)
            # file.write(f'''
            #             \u007b
            #                 "name": "{location}",
            #                 "chest_unopened_img": "/images/Items/{close_chest}",
            #                 "chest_opened_img": "/images/Items/{open_chest}",
            #                 "overlay_background": "#000000",
            #                 "sections": [
            #             ''')
            # for k, check in enumerate(sub_region):
            # print(check) #, check_location)
            file.write(f'''
                            \u007b
                                "name": "{location}",''')
            # try:
            #     if logic_dict[region][location][check]:
            #         file.write(f'''
            #                     "access_rules": [ "{logic_dict[region][location][check][0]}" ],''')
            # except:
            #     pass
            file.write(f'''
                                "item_count": 1
                            ''')

                # print(k, len(lvl_locations[city][index])-1)
                # if k == len(loc_dict) - 1:
                #     file.write('''\u007d
                #                 ''')
                # else:
            if i+1 == len(temp_lists):
                file.write('''\u007d
                        ''')
            else:
                file.write('''\u007d,
                        ''')
            overworld.write(f'''
                                        \u007b
                                            "name": "{region} - {location}",
                                            "ref": "{region}/{location}"
                                        \u007d,
                                    ''')
        file.write(f'''
                            ],
                            "map_locations": [
                                \u007b
                                    "map": "Overworld",
                                    "x": {random.randint(10, 2500)},
                                    "y": {random.randint(10, 1500)},
                                    "size": 6
                                \u007d
                            ]
                            ''')

        # if 0 == len(loc_dict) - 1:
        #     # print(test, len(lvl_locations[city]))
        #     file.write('\u007d')
        # else:
        file.write('\u007d,')
            # overworld.write('\u007d,')
    else:
        file.write('''\u007d,
                                ''')
    # file.write('''
    #
    #                         ]
    #                     }
    #                 ]''')
            # return True
    # file.write('''
    #                                     ],''')
    # file.write('''
    #
    #             ]
    #         }''')


# def write_section(region, file, logic_dict):
#
#     test_1 = locations_dict[region]
#     print(len(test_1[list(test_1.keys())[0]]))
#     # if len(test_1[list(test_1.keys())[0]]) > 0:
#     for j, location in enumerate(locations_dict[region]):
#         file.write(f'''
#                     \u007b
#                         "name": "{location}",
#                         "chest_unopened_img": "/images/Items/{close_chest}",
#                         "chest_opened_img": "/images/Items/{open_chest}",
#                         "overlay_background": "#000000",
#                         "sections": [
#                     ''')
#         for k, check in enumerate(locations_dict[region][location]):
#             # print(check, check_location)
#             file.write(f'''
#                             \u007b
#                                 "name": "{check}",''')
#             try:
#                 if logic_dict[region][location][check]:
#                     file.write(f'''
#                                 "access_rules": [ "{logic_dict[region][location][check][0]}" ],''')
#             except:
#                 pass
#             file.write(f'''
#                                 "item_count": 1
#                             ''')
#
#             # print(k, len(lvl_locations[city][index])-1)
#             if k == len(locations_dict[region][location]) - 1:
#                 file.write('''\u007d
#                             ''')
#             else:
#                 file.write('''\u007d,
#                             ''')
#         file.write(f'''
#                             ],
#                             "map_locations": [
#                                 \u007b
#                                     "map": "Worldmap",
#                                     "x": {random.randint(10, 2500)},
#                                     "y": {random.randint(10, 1500)},
#                                     "size": 6
#                                 \u007d
#                             ]
#                             ''')
#         if j == len(locations_dict[region]) - 1:
#             # print(test, len(lvl_locations[city]))
#             file.write('\u007d')
#         else:
#             file.write('\u007d,')


# def write_2_layer_locations(region, file, logic_dict):
#     '''
#         if the logic form the rules-file could only split the location name into 2 sets (location,
#         item) this function gets called.
#         the set images for still closed and already opened items are set here, defaults to the poptracker provided
#         open/closed images.
#         Also try's to find matching location/items rules in the logicfile and writes them in the corresponding
#         section. if nothing gets found access_rules get skipped and need to be added later. A file of the extracked
#         rules is saved in the packs directory
#         :param region:
#         :param file:
#         :param logic_dict:
#         :return:
#         '''
#     with open(read_file_path + fr"\locations\{region}.json", "w") as locations_file:
#         locations_file.write('[')
#         for j, location in enumerate(locations_dict[region]):
#             file.write(f'''
#                             \u007b
#                                 "name": "{location}",
#                                 "chest_unopened_img": "/images/Items/{close_chest}",
#                                 "chest_opened_img": "/images/Items/{open_chest}",
#                                 "overlay_background": "#000000",
#                                 "sections": [
#                                     \u007b
#                                         "name": "{location}",''')
#             try:
#                 if logic_dict[region][location]:
#                     file.write(f'''
#                                     "access_rules": [ "{logic_dict[region][location][0]}" ],''')
#             except:
#                 pass
#                 file.write(f'''
#                                         "item_count": 1
#                                     \u007d
#                                     ],
#                                     "map_locations": [
#                                         \u007b
#                                             "map": "Worldmap",
#                                             "x": {random.randint(10, 500)},
#                                             "y": {random.randint(10, 500)},
#                                             "size": 6
#                                         \u007d
#                                     ]
#                                     ''')
#             if j == len(locations_dict[region]) - 1:
#                 # print(test, len(lvl_locations[city]))
#                 file.write('\u007d')
#             else:
#                 file.write('\u007d,')
#         file.write('''
#                     ]''')

# def write_1_layer_locations():


def location_dict_builder(location_dict: dict, path: list, location_list: list, logic_dict: dict, building: bool):
    # print(location_list)
    if building:
        if not len(location_list) == 1:
            for part in path:
                location_dict = location_dict[part]
            # print(location_list[1:], location_list[1:][0])
            # print(path)
            location_dict.setdefault(location_list[0], dict())
            # location_dict[location_list[0]].update({location_list[1:][0]: dict()})
            path.append(location_list[0])
            location_dict_builder(locations_dict, path, location_list[1:], logic_dict, True)
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
    return location_dict


def create_locations(path: str, logic: dict[str, str]):
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
    global lvls, locations_dict, maps_names
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
    lvls = set(temp)
    #

    with open(path+"/scripts/locations_import.lua", 'w') as locations_file:
        for i in lvls:
            locations_file.write(f'Tracker:AddLocations("locations/{i}.json")\n')
            open(path + f"/scripts/logic/{i}.lua", "x").close()
        locations_file.write(f'Tracker:AddLocations("locations/Overworld.json")\n')
        open(path + "/scripts/logic/location_definition.lua", "x").close()
    locations_dict = {e: {} for e in lvls}

    logic_dict = extract_logic()
    """
    Braucht nen rework.
    idealerweise rekursiv damit man nicht auf 2-3 ebene beschränkt ist.
    das gleiche für das eigentliche location building später
    """
    for location in location_list:
        locations_dict = location_dict_builder(locations_dict, [], location, logic_dict, True)
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

    if other_options[0] in [" ", "\n"]:
        print(other_options)
        open_chest = tk.filedialog.askopenfilename().split('/')[-1]
        close_chest = tk.filedialog.askopenfilename().split('/')[-1]
        with open(path + '/datapacke_url.txt', 'a') as file:
            file.write(f"{open_chest}, {close_chest}")
    else:
        open_chest = "open.png"
        close_chest = "close.png"
        # open_chest = other_options[0]
        # close_chest = other_options[1]
    with open(path+fr"\locations\Overworld.json", "w") as overworld:
        overworld.write('[')
        overworld.write(f'''
            \u007b
                "name": "Overworld",
                "chest_unopened_img": "/images/Items/{close_chest}",
                "chest_opened_img": "/images/Items/{open_chest}",
                "overlay_background": "#000000",
                "access_rules": [" "],
                "children": [
                ''')
        for i, locations_region in enumerate(locations_dict.keys()):
            # print(city, lvl_locations[city])
            overworld.write(f'''
                                \u007b
                                    "name": "{locations_region}",
                                    "chest_unopened_img": "/images/Items/{close_chest}",
                                    "chest_opened_img": "/images/Items/{open_chest}",
                                    "overlay_background": "#000000",
                                    "access_rules": [" "],
                                    "sections": [
                                    ''')
            with open(path+fr"\locations\{locations_region}.json", "w") as locations_file:
                locations_file.write('[')
                write_locations(locations_dict, locations_region, locations_file, logic_dict, overworld)
                # locations_file.write('''
                #
                #         ]
                #     }
                # ]''')
                locations_file.write('''
                            ]''')
                overworld.write(f'''
                                    ],
                                    "map_locations": [
                                        \u007b
                                            "map": "Overworld",
                                            "x": {random.randint(10, 2500)},
                                            "y": {random.randint(10, 1500)},
                                            "size": 6
                                        \u007d
                                    ]
                                    \u007d,
                                    ''')
        overworld.write('''
                                ]''')

        maps_names = ["Overworld"]
        for lvl in lvls:
            if len(locations_dict[lvl]) > 9:
                maps_names.append(lvl)
        overworld.write('''
                }
        ]''')
#


def create_maps(path: str):
    '''
    creates the maps used in the tabbed section in poptracker.
    uses only regions with more than 9 sections in it according to the sectioning in the locations_mapping
    :param path:
    :return:
    '''
    # with open("H:\mario-is-missing-AP-tracker\maps\maps.json", 'w') as maps:
    with open(path+"/maps/maps.json", 'w') as maps:
        maps.write('[')
        for i, map in enumerate(maps_names):
            # print(i, map)
            maps.write(f'''
            \u007b
                "name": "{map}",
                "location_size": 6,
                "location_border_thickness": 1,
                "img": "images/maps/{map}.png"
            ''')
            if i == len(maps_names) - 1:
                maps.write('\u007d')
            else:
                maps.write('\u007d,')
        maps.write('\n]')
# #


def create_tracker_tabs(path: str):
    '''
    creates a json scheme that adds the created maps from create_maps() into the loaded tracker file
    :param path:
    :return:
    '''
    # with open("H:\mario-is-missing-AP-tracker\layouts\\tabs.json", 'w') as tabs:
    with open(path+"/layouts/tabs.json", 'w') as tabs:
        tabbed_maps = ["tabbed_maps_horizontal", "tabbed_maps_vertical"]
        tabs.write('\u007b')
        for index, tabbed in enumerate(tabbed_maps):
            tabs.write(f'''
            "{tabbed}": \u007b
            "type": "tabbed",
            "tabs": [
            ''')
            for i, map in enumerate(maps_names):
                # print(i, map)
                tabs.write(f'''
                \u007b
                    "title": "{map}",
                    "content": \u007b
                        "type": "map",
                        "maps": [
                            "{map}"
                        ]
                    \u007d
                ''')
                if i == len(maps_names) - 1:
                    tabs.write('''
                \u007d''')
                else:
                    tabs.write('''
                \u007d,''')
            tabs.write('''
            ]''')
            if index == len(tabbed_maps) - 1:
                tabs.write('''
        \u007d''')
            else:
                tabs.write('''
        \u007d,''')
        tabs.write('''
    \u007d''')
# #


def create_broadcast_layout(path: str):
    '''
    creates a basic broadcast layout containing the items section of the normal tracker
    :param path:
    :return:
    '''
    # with open("H:\mario-is-missing-AP-tracker\layouts\\broadcast.json", 'w') as broadcast:
    with open(path+"/layouts/broadcast.json", 'w') as broadcast:
        broadcast.write('''
        {
        "tracker_broadcast": {
            "type": "array",
            "orientation": "vertical",
            "margin": "0,0",
            "content": [
                {
                    "type": "array",
                    "orientation": "vertical",
                    "margin": "0,0",
                    "content": [
                        {
                            "type": "layout",
                            "key": "shared_item_grid_vertical"
                         }
                    ]
                }
            ]
        }
    }''')
# #


def create_tracker_basic_layout(path: str):
    '''
    creates the full json for a basic tracker pack for poptracker.
    contains a map/item/settings/pins-section for a horizontal and vertical layout
    :param path:
    :return:
    '''
    with open(path+"/layouts/tracker.json", 'w') as tracker:
        tracker.write('''
        {
            "settings_popup": {
                "type": "array",
                "margin": "5",
                "content": [
                    {
                        "type": "group",
                        "header": "Autofill Settings",
                        "description": "Enable/Disable the automatic fill of the settings pannel from for connected Slot_Data",
                        "header_background": "#3e4b57",
                        "content": [
                            {
                                "type": "item",
                                "margin": "5,1,5,5",
                                "item": "autofill_settings"
                            }
                        ]
                    },
                    {
                        "type": "group",
                        "header": "Retro Caves",
                        "description": "Enable/Disable the automatic fill of the settings pannel from for connected Slot_Data",
                        "header_background": "#3e4b57",
                        "content": [
                            {
                                "type": "item",
                                "margin": "5,1,5,5",
                                "item": "retro_caves"
                            }
                        ]
                    }
                ]
            },
            "tracker_default": {
                "type": "container",
                "background": "#00000000",
                "content": {
                    "type": "dock",
                    "dropshadow": true,
                    "content": [
                        {
                            "type": "dock",
                            "dock": "left",
                            "v_alignment": "stretch",
                            "content": [
                                {
                                    "type": "group",
                                    "header": "Items",
                                    "dock": "top",
                                    "content": {
                                        "type": "layout",
                                        "key": "shared_item_grid_vertical"
                                    }
                                },
                                {
                                    "type": "group",
                                    "header": "Settings",
                                    "dock": "top",
                                    "content": {
                                        "type": "layout",
                                        "key": "setting_grid"
                                    }
                                },
                                {
                                    "type": "group",
                                    "header": "Pinned Locations",
                                    "content": {
                                        "style": "wrap",
                                        "type": "recentpins",
                                        "orientation": "vertical",
                                        "compact": true
                                    }
                                }
                            ]
                        },
                        {
                            "type": "dock",
                            "content": {
                                "type": "layout",
                                "key": "tabbed_maps_vertical"
                            }
                        }
                    ]
                }
            },
            "tracker_horizontal": {
                "type": "container",
                "background": "#00000000",
                "content": {
                    "type": "dock",
                    "dropshadow": true,
                    "content": [
                        {
                            "type": "dock",
                            "dock": "bottom",
                            "content": [
                                {
                                    "type": "group",
                                    "header": "Items",
                                    "dock": "left",
                                    "margin": "0,0,3,0",
                                    "content": {
                                        "type": "layout",
                                        "h_alignment": "center",
                                        "v_alignment": "center",
                                        "key": "shared_item_grid_horizontal"
                                    }
                                },
                                {
                                    "type": "group",
                                    "header": "Settings",
                                    "dock": "left",
                                    "margin": "0,0,3,0",
                                    "content": {
                                        "type": "layout",
                                        "h_alignment": "center",
                                        "v_alignment": "center",
                                        "key": "setting_grid"
                                    }
                                },
                                {
                                    "type": "group",
                                    "header": "Pinned Locations",
                                    "content": {
                                        "style": "wrap",
                                        "type": "recentpins",
                                        "orientation": "horizontal",
                                        "compact": true
                                    }
                                }
                            ]
                        },
                        {
                            "type": "dock",
                            "content": {
                                "type": "layout",
                                "key": "tabbed_maps_horizontal"
                            }
                        }
                    ]
                }
            }
        }''')
# #


def create_item_layout(path: str):
    '''
    creates basic item layout containing all items found in item_mapping. splits the items as evenly as possible.
    creates a horizontal and vertical layout
    :param path:
    :return:
    '''
    item_codes = []
    with open(path+'/items/items.json') as items:
        json_data = json.load(items)
        for data in json_data:
            if not data == {}:
                item_codes.append(data['codes'])
    with open(path + "/layouts/items.json", 'w') as item_layout:
        grid_oriententation = ['horizontal', 'vertical']
        item_layout.write('''
        {
    "shared_item_grid_horizontal": {
        "type": "array",
        "orientation": "vertical",
        "margin": "0,0",
        "content": [
            {
                "type": "array",
                "orientation": "horizontal",
                "margin": "0,0",
                "content": [
                    {
                        "type": "itemgrid",
                        "item_margin": "2, 2",
                        "h_alignment": "left",
                        "item_h_alignment": "center",
                        "item_v_alignment": "center",
                        "item_height": 36,
                        "item_width": 36,
                        "rows": [''')
        divider = math.sqrt(len(item_codes)).__ceil__()
        item_layout.write('\n[\n')
        for i, item in enumerate(item_codes):
            # item_layout.write('\n[\n')
            if (i+1) % divider == 0:
                item_layout.write(f'"{item}"\n')
            elif (i+1) % divider == 1 and i > 0 :
                item_layout.write(f']\n,[\n"{item}",\n')
            else:
                item_layout.write(f'"{item}",\n')
        item_layout.write(']\n]\n}\n]\n}\n]\n},')
        item_layout.write('''
            "shared_item_grid_vertical": {
                "type": "array",
                "orientation": "vertical",
                "margin": "0,0",
                "content": [
                    {
                        "type": "array",
                        "orientation": "vertical",
                        "margin": "0,0",
                        "content": [
                            {
                                "type": "itemgrid",
                                "item_margin": "2, 2",
                                "h_alignment": "left",
                                "item_h_alignment": "center",
                                "item_v_alignment": "center",
                                "item_height": 36,
                                "item_width": 36,
                                "rows": [''')
        divider = math.sqrt(len(item_codes)).__ceil__()
        item_layout.write('\n[\n')
        for i, item in enumerate(item_codes):
            # item_layout.write('\n[\n')
            if (i + 1) % divider == 0:
                item_layout.write(f'"{item}"\n')
            elif (i + 1) % divider == 1 and i > 0:
                item_layout.write(f']\n,[\n"{item}",\n')
            else:
                item_layout.write(f'"{item}",\n')
        item_layout.write(']\n]\n}\n]\n}\n]\n}\n}')


def generalized_rule_extractor(base_list: [str], delimiter1: str, delimiter2: str):
    '''
    try's to open a possibly provided file containing the used logic for the AP-rando.
    for now, it reads the file and only looks for lambda rules. may change later to get expanded to lists/dicts but
    that's for another day.
    try's to split the rules into their intended and correct order. () > and > or
    after splitting it recombines them via vector/matrix multiplication to create ever possible permutation of rules.
    writes the extracted rules into a file as backup.
    '''
    try:
        x = " | ".join(" + ".join(base_list.split(delimiter1)).split(delimiter2)).split(" | ")
    # logic_temp[i][1].replace(' or ', ' | ').replace(' and ', ' + ')

        for iter, sub_list in enumerate(x):
            if ' + ' in sub_list:
                x[iter] = sub_list.split("+")
            else:
                x[iter] = [sub_list]

            for sub_iter, code in enumerate(x[iter]):
                if '"' in code:
                    search = '"'
                elif "'" in code:
                    search = "'"
                else:
                    continue
                x[iter][sub_iter] = code[code.index(search) + 1:code.rindex(search)]
    except:
        x = base_list
    return list(itertools.product(*x))  # list cross multiplication to generate every


def slice_at_brackets(list_to_slice: []):
    lbracket = [j + 1 for j in range(len(list_to_slice)) if list_to_slice.startswith('(', j)]
    rbracket = [j + 1 for j in range(len(list_to_slice)) if list_to_slice.startswith(')', j)]
    if len(lbracket) == len(rbracket) - 1:
        rbracket.pop()
    lcount = 1
    rcount = 0
    stack = [lbracket[lcount - 1]]
    lastslice = 0
    temp = []
    while lcount < len(lbracket) and rcount < len(lbracket):
        # print("while", lcount, rcount)
        if len(stack) == 0 and lcount > 0 and rcount > 0:
            slice = rbracket[rcount]
            if lcount == len(lbracket):
                # print(temp)
                temp.append(list_to_slice[lastslice:])
            else:
                # print(temp)
                # print(rbracket[rcount], lbracket[lcount])
                if ' or ' in list_to_slice[lbracket[lcount]:rbracket[rcount]]:
                    temp.append(list_to_slice[lastslice:slice - 2])
                    lastslice = slice
                # else:
                #     # print(f'logic_temp[{i}][1]', lastslice, logic_temp[i][1][lastslice:])
                #     temp.append(logic_temp[i][1][lastslice:])

            stack.append(lbracket[lcount])
            lcount += 1
        else:
            if lbracket[lcount] < rbracket[rcount]:
                stack.append(lbracket[lcount])
                lcount += 1
            else:
                stack.pop()
                rcount += 1
    # lbracket = [j + 1 for j in range(len(list_to_slice)) if list_to_slice.startswith('(', j)]
    # rbracket = [j + 1 for j in range(len(list_to_slice)) if list_to_slice.startswith(')', j)]
    # if len(rbracket) == len(lbracket) - 1:
    #     lbracket.pop()
    # lcount = 1
    # rcount = 0
    # stack = [lbracket[lcount - 1]]
    # lastslice = 0
    # temp = []
    # while lcount < len(lbracket) - 1 and rcount < len(lbracket) - 1:
    #     if len(stack) == 0 and lcount > 0 and rcount > 0:
    #         slice = (lbracket[lcount] + rbracket[rcount]) // 2
    #         if not lcount == len(lbracket)-1:
    #             temp.append(list_to_slice[lastslice:slice])
    #         else:
    #             temp.append(list_to_slice[lastslice:])
    #         lastslice = slice
    #         stack.append(lbracket[lcount])
    #         lcount += 1
    #     else:
    #         if lbracket[lcount] < rbracket[rcount]:
    #             stack.append(lbracket[lcount])
    #             lcount += 1
    #         else:
    #             stack.pop()
    #             rcount += 1
    return temp


def extract_logic():
    """                           1 location             2+ rules, (if multiple lambdas then more lists else sublists in position 2
    ###     logic_temp[i] layout: [ [] ,                   [ [ ] , [ ] ], [ ], [ [ ] , [ ] ] ]
                            location_str    lambda            and    or   or       and
    """
    global logic
    logic_temp =[]
    logic_dict = {}
    file_path = filedialog.askopenfilename()
    if not file_path == '':
        with open(file_path) as logic_extract:
            temp = logic_extract.read().split('\n')
            for i in temp:
                if " lambda " in i.lower():
                    logic_temp.append(i.split("lambda"))  # """results in a list containing tuples of [location_string,

            for i, test in enumerate(logic_temp):
                # i = 81
                if not '(' in logic_temp[i][1] and not ')' in logic_temp[i][1]:
                    logic_temp[i][1] = []
                else:
                    temp = slice_at_brackets(logic_temp[i][1])
                    if not len(temp) == 0:
                        # print(temp)
                        logic_temp[i][1] = temp

                    if type(logic_temp[i][1]) == list:
                        for counter, _ in enumerate(logic_temp[i][1]):

                            logic_temp[i][1][counter] = generalized_rule_extractor(base_list=logic_temp[i][1][
                                counter], delimiter1=' or', delimiter2=' and ')

                    else:
                        logic_temp[i][1] = generalized_rule_extractor(base_list=logic_temp[i][1], delimiter1=' or',
                                                                      delimiter2=' and ')

                    if '"' in test[0]:
                        search = '"'
                    elif "'" in test[0]:
                        search = "'"
                    else:
                        continue
                    logic_temp[i][0] = test[0][test[0].index(search)+1:test[0].rindex(search)]

            for i, _ in enumerate(logic_temp):
                # print("test")
                for j, _ in enumerate(logic_temp[i][:-2]):
                    logic_temp[i][j] = logic_temp[i][j].strip('"').strip("'")

    with open(read_file_path+'/logic_backup.txt', 'w') as logic_backup:
        for line in logic_temp:
            logic_backup.write(f"{line}\n")
    delimiter = [
        '", "',
        "', '",
        '",',
        "',",
        ' - ',
        ': ',
        ') ']

    for index, _ in enumerate(logic_temp):
        for spacer in delimiter:
            if spacer in logic_temp[index][0]:
                logic_temp[index][0] = logic_temp[index][0].replace(f"{spacer}", "/")

            else:
                logic_temp[index][0] = logic_temp[index][0]
        logic_temp[index][0] = list(dict.fromkeys(logic_temp[index][0].split("/")))

    region_temp = []
    for i, _ in enumerate(logic_temp):
        region_temp.append(logic_temp[i][0][0])
    region_temp_set = set(region_temp)
    logic_dict = {e: {} for e in region_temp_set}
    for index, _ in enumerate(logic_temp):
        sub_list = logic_temp[index][0]
        if len(logic_temp[index][1]) == 1:
            print(logic_temp[index][1], logic_temp[index][1][0])
            logic_temp[index][1] = logic_temp[index][1][0]
        if len(sub_list) == 3:
            try:
                logic_dict[sub_list[0]][sub_list[1]].update({sub_list[2]: logic_temp[index][1]})
            except:
                logic_dict[sub_list[0]].update({sub_list[1]: {}})
                logic_dict[sub_list[0]][sub_list[1]].update({sub_list[2]: logic_temp[index][1]})
        elif len(sub_list) == 2:
            try:
                logic_dict[sub_list[0]].update({sub_list[1]: logic_temp[index][1]})
            except:
                pass
        elif len(sub_list) == 1:
            try:
                logic_dict.update({sub_list[0]: logic_temp[index][1]})
            except:
                pass
    return logic_dict


def create_base_structure(path: str):
    '''
    creates every needed directory and file needed to get a basic poptracker pack working and loading if the needed
    file is not already present
    :param path:
    :return:
    '''
    if not os.path.exists(path + "/scripts"):
        os.mkdir(path + "/scripts")
        os.mkdir(path + "/scripts/autotracking")
        os.mkdir(path + "/scripts/logic")
    if not os.path.exists(path + "/scripts/autotracking/archipelago.lua"):
        with open(path + "/scripts/autotracking/archipelago.lua", "w") as ap_lua:
            ap_lua.write('''
        ScriptHost:LoadScript("scripts/autotracking/item_mapping.lua")
ScriptHost:LoadScript("scripts/autotracking/location_mapping.lua")

CUR_INDEX = -1
--SLOT_DATA = nil

SLOT_DATA = {}

function has_value (t, val)
    for i, v in ipairs(t) do
        if v == val then return 1 end
    end
    return 0
end

function dump_table(o, depth)
    if depth == nil then
        depth = 0
    end
    if type(o) == 'table' then
        local tabs = ('\t'):rep(depth)
        local tabs2 = ('\t'):rep(depth + 1)
        local s = '{'
        for k, v in pairs(o) do
            if type(k) ~= 'number' then
                k = '"' .. k .. '"'
            end
            s = s .. tabs2 .. '[' .. k .. '] = ' .. dump_table(v, depth + 1) .. ','
        end
        return s .. tabs .. '}'
    else
        return tostring(o)
    end
end


function onClear(slot_data)
    --SLOT_DATA = slot_data
    CUR_INDEX = -1
    -- reset locations
    for _, location_array in pairs(LOCATION_MAPPING) do
        for _, location in pairs(location_array) do
            if location then
                local location_obj = Tracker:FindObjectForCode(location)
                if location_obj then
                    if location:sub(1, 1) == "@" then
                        location_obj.AvailableChestCount = location_obj.ChestCount
                    else
                        location_obj.Active = false
                    end
                end
            end
        end
    end
    -- reset items
    for _, item in pairs(ITEM_MAPPING) do
        for _, item_code in pairs(item[1]) do
            item_code, item_type = item
--            if item_code and item[2] then
            local item_obj = Tracker:FindObjectForCode(item_code)
--            if item_obj then
--                if item_type == "toggle" then
--                    item_obj.Active = false
--                elseif item_type == "progressive" then
--                    item_obj.CurrentStage = 0
--                    item_obj.Active = false
--                elseif item_type == "consumable" then
--                    if item_obj.MinCount then
--                        item_obj.AcquiredCount = item_obj.MinCount
--                    else
--                        item_obj.AcquiredCount = 0
--                    end
--                elseif item_type == "progressive_toggle" then
--                    item_obj.CurrentStage = 0
--                    item_obj.Active = false
--                end
--            end
            if item_obj then
                if item_obj.Type == "toggle" then
                    item_obj.Active = false
                elseif item_obj.Type == "progressive" then
                    item_obj.CurrentStage = 0
                    item_obj.Active = false
                elseif item_obj.Type == "consumable" then
                    if item_obj.MinCount then
                        item_obj.AcquiredCount = item_obj.MinCount
                    else
                        item_obj.AcquiredCount = 0
                    end
                elseif item_obj.Type == "progressive_toggle" then
                    item_obj.CurrentStage = 0
                    item_obj.Active = false
                end
            end
        end
--        end
    end
    PLAYER_ID = Archipelago.PlayerNumber or -1
    TEAM_NUMBER = Archipelago.TeamNumber or 0
    SLOT_DATA = slot_data
    -- if Tracker:FindObjectForCode("autofill_settings").Active == true then
    --     autoFill(slot_data)
    -- end
end

function onItem(index, item_id, item_name, player_number)
    if index <= CUR_INDEX then
        return
    end
    local is_local = player_number == Archipelago.PlayerNumber
    CUR_INDEX = index;
    local item = ITEM_MAPPING[item_id]
    if not item or not item[1] then
        --print(string.format("onItem: could not find item mapping for id %s", item_id))
        return
    end
--    for _, item_code in pairs(item[1]) do
        -- print(item[1], item[2])
    item_code = item[1]
    item_type = item[2]
    local item_obj = Tracker:FindObjectForCode(item_code)
--    if item_obj then
--        if item_type == "toggle" then
--            -- print("toggle")
--            item_obj.Active = true
--        elseif item_type == "progressive" then
--            -- print("progressive")
--            item_obj.Active = true
--        elseif item_type == "consumable" then
--            -- print("consumable")
--            item_obj.AcquiredCount = item_obj.AcquiredCount + item_obj.Increment
--        elseif item_type == "progressive_toggle" then
--            -- print("progressive_toggle")
--            if item_obj.Active then
--                item_obj.CurrentStage = item_obj.CurrentStage + 1
--            else
--                item_obj.Active = true
--            end
--        end
--    else
--        print(string.format("onItem: could not find object for code %s", item_code[1]))
--    end
    if item_obj then
        if item_obj.Type == "toggle" then
            -- print("toggle")
            item_obj.Active = true
        elseif item_obj.Type == "progressive" then
            -- print("progressive")
            item_obj.Active = true
        elseif item_obj.Type == "consumable" then
            -- print("consumable")
            item_obj.AcquiredCount = item_obj.AcquiredCount + item_obj.Increment
        elseif item_obj.Type == "progressive_toggle" then
            -- print("progressive_toggle")
            if item_obj.Active then
                item_obj.CurrentStage = item_obj.CurrentStage + 1
            else
                item_obj.Active = true
            end
        end
    else
        print(string.format("onItem: could not find object for code %s", item_code[1]))
    end
--    end
end

--called when a location gets cleared
function onLocation(location_id, location_name)
    local location_array = LOCATION_MAPPING[location_id]
    if not location_array or not location_array[1] then
        print(string.format("onLocation: could not find location mapping for id %s", location_id))
        return
    end

    for _, location in pairs(location_array) do
        local location_obj = Tracker:FindObjectForCode(location)
        -- print(location, location_obj)
        if location_obj then
            if location:sub(1, 1) == "@" then
                location_obj.AvailableChestCount = location_obj.AvailableChestCount - 1
            else
                location_obj.Active = true
            end
        else
            print(string.format("onLocation: could not find location_object for code %s", location))
        end
    end
    canFinish()
end

function onEvent(key, value, old_value)
    updateEvents(value)
end

function onEventsLaunch(key, value)
    updateEvents(value)
end

-- function autoFill()
--     if SLOT_DATA == nil  then
--         print("its fucked")
--         return
--     end
--     -- print(dump_table(SLOT_DATA))

--     mapToggle={[0]=0,[1]=1,[2]=1,[3]=1,[4]=1}
--     mapToggleReverse={[0]=1,[1]=0,[2]=0,[3]=0,[4]=0}
--     mapTripleReverse={[0]=2,[1]=1,[2]=0}

--     slotCodes = {
--         map_name = {code="", mapping=mapToggle...}
--     }
--     -- print(dump_table(SLOT_DATA))
--     -- print(Tracker:FindObjectForCode("autofill_settings").Active)
--     if Tracker:FindObjectForCode("autofill_settings").Active == true then
--         for settings_name , settings_value in pairs(SLOT_DATA) do
--             -- print(k, v)
--             if slotCodes[settings_name] then
--                 item = Tracker:FindObjectForCode(slotCodes[settings_name].code)
--                 if item.Type == "toggle" then
--                     item.Active = slotCodes[settings_name].mapping[settings_value]
--                 else 
--                     -- print(k,v,Tracker:FindObjectForCode(slotCodes[k].code).CurrentStage, slotCodes[k].mapping[v])
--                     item.CurrentStage = slotCodes[settings_name].mapping[settings_value]
--                 end
--             end
--         end
--     end
-- end


-- ScriptHost:AddWatchForCode("settings autofill handler", "autofill_settings", autoFill)
Archipelago:AddClearHandler("clear handler", onClear)
Archipelago:AddItemHandler("item handler", onItem)
Archipelago:AddLocationHandler("location handler", onLocation)
''')
    if not os.path.exists(path + "/scripts/init.lua"):
        with open(path + "/scripts/init.lua", "w") as init_lua:
            init_lua.write('''
            local variant = Tracker.ActiveVariantUID

Tracker:AddItems("items/items.json")
Tracker:AddItems("items/labels.json")

-- Items
ScriptHost:LoadScript("scripts/items_import.lua")

-- Logic
ScriptHost:LoadScript("scripts/logic/logic_helpers.lua")
ScriptHost:LoadScript("scripts/logic/logic_main.lua")
ScriptHost:LoadScript("scripts/logic_import.lua")

-- Maps
if Tracker.ActiveVariantUID == "maps-u" then
    Tracker:AddMaps("maps/maps-u.json")  
else
    Tracker:AddMaps("maps/maps.json")  
end  

if PopVersion and PopVersion >= "0.23.0" then
    Tracker:AddLocations("locations/dungeons.json")
end

-- Layout
ScriptHost:LoadScript("scripts/layouts_import.lua")

-- Locations
ScriptHost:LoadScript("scripts/locations_import.lua")

-- AutoTracking for Poptracker
if PopVersion and PopVersion >= "0.18.0" then
    ScriptHost:LoadScript("scripts/autotracking.lua")
end''')
    if not os.path.exists(path + "/scripts/layouts_import.lua"):
        with open(path + "/scripts/layouts_import.lua", "w") as layouts_lua:
            layouts_lua.write('''
        Tracker:AddLayouts("layouts/events.json")
Tracker:AddLayouts("layouts/settings.json")
Tracker:AddLayouts("layouts/items.json")
Tracker:AddLayouts("layouts/tabs.json")
Tracker:AddLayouts("layouts/tracker.json")
Tracker:AddLayouts("layouts/broadcast.json")
Tracker:AddLayouts("layouts/dungeon_items.json")
-- Tracker:AddLayouts("layouts/dungeon_items_keydrop.json")''')
    if not os.path.exists(path + "/scripts/settings.lua"):
        with open(path + "/scripts/settings.lua", "w") as settings_lua:
            settings_lua.write('''
        ------------------------------------------------------------------
-- Configuration options for scripted systems in this pack
------------------------------------------------------------------
AUTOTRACKER_ENABLE_ITEM_TRACKING = true
AUTOTRACKER_ENABLE_LOCATION_TRACKING = true''')
    if not os.path.exists(path + "/scripts/autotracking.lua"):
        with open(path + "/scripts/autotracking.lua", "w") as auto_lua:
            auto_lua.write('''
        -- Configuration --------------------------------------
AUTOTRACKER_ENABLE_DEBUG_LOGGING = true and ENABLE_DEBUG_LOG
AUTOTRACKER_ENABLE_DEBUG_LOGGING_AP = true and AUTOTRACKER_ENABLE_DEBUG_LOGGING
AUTOTRACKER_ENABLE_DEBUG_LOGGING_SNES = true and AUTOTRACKER_ENABLE_DEBUG_LOGGING
-------------------------------------------------------
print("")
print("Active Auto-Tracker Configuration")
print("---------------------------------------------------------------------")
print("Enable Item Tracking:        ", AUTOTRACKER_ENABLE_ITEM_TRACKING)
print("Enable Location Tracking:    ", AUTOTRACKER_ENABLE_LOCATION_TRACKING)
if AUTOTRACKER_ENABLE_DEBUG_LOGGING then
    print("Enable Debug Logging:        ", AUTOTRACKER_ENABLE_DEBUG_LOGGING)
    print("Enable AP Debug Logging:        ", AUTOTRACKER_ENABLE_DEBUG_LOGGING_AP)
    print("Enable SNES Debug Logging:        ", AUTOTRACKER_ENABLE_DEBUG_LOGGING_SNES)
end
print("---------------------------------------------------------------------")
print("")

ScriptHost:LoadScript("scripts/autotracking/settings.lua")
-- loads the AP autotracking code
ScriptHost:LoadScript("scripts/autotracking/archipelago.lua")
    

        ''')
    if not os.path.exists(path + "manifest.json"):
        with open(path + "/manifest.json", 'w') as manifest:
            manifest.write(f'''
\u007b
    "name": "{game_name} Archipelago",
    "game_name": "{game_name}",
    "package_version": "0.0.1",
    // "platform": "snes",
    "package_uid": "{game_name.lower()}_ap",
    "author": "builder_script",
    "variants": \u007b
        "Map Tracker": \u007b
            "display_name": "Map Tracker",
            "flags": ["ap"]
        \u007d,
        "Items Only": \u007b
            "display_name": "Items Only",
            "flags": ["ap"]
        \u007d
    \u007d
    // "versions_url": "https://raw.githubusercontent.com/StripesOO7/alttp-ap-poptracker-pack/versions/versions.json"
\u007d
''')
    if not os.path.exists(path + "/scripts/logic/logic_main.lua"):
        with open(path + "/scripts/logic/logic_main.lua", "w") as logic_lua:
            logic_lua.write('''
            ScriptHost:AddWatchForCode("keydropshuffle handler", "key_drop_shuffle", keyDropLayoutChange)
ScriptHost:AddWatchForCode("boss handler", "boss_shuffle", bossShuffle)
-- ScriptHost:AddWatchForCode("ow_dungeon details handler", "ow_dungeon_details", owDungeonDetails)


alttp_location = {}
alttp_location.__index = alttp_location

accessLVL= {
    [0] = "none",
    [1] = "partial",
    [3] = "inspect",
    [5] = "sequence break",
    [6] = "normal",
    [7] = "cleared"
}

-- Table to store named locations
named_locations = {}
staleness = 0

-- 
function can_reach(name)
    local location
    -- if type(region_name) == "function" then
    --     location = self
    -- else
    if type(name) == "table" then
        -- print(name.name)
        location = named_locations[name.name]
    else 
        location = named_locations[name]
    end
    -- print(location, name)
    -- end
    if location == nil then
        -- print(location, name)
        if type(name) == "table" then
        else
            print("Unknown location : " .. tostring(name))
        end
        return AccessibilityLevel.None
    end
    return location:accessibility()
end

-- creates a lua object for the given name. it acts as a representation of a overworld reagion or indoor locatoin and
-- tracks its connected objects wvia the exit-table
function alttp_location.new(name)
    local self = setmetatable({}, alttp_location)
    if name then
        named_locations[name] = self
        self.name = name
    else
        self.name = self
    end
    
    self.exits = {}
    self.staleness = -1
    self.keys = math.huge
    self.accessibility_level = AccessibilityLevel.None
    return self
end

local function always()
    return AccessibilityLevel.Normal
end

-- markes a 1-way connections between 2 "locations/regions" in the source "locations" exit-table with rules if provided
function alttp_location:connect_one_way(exit, rule)
    if type(exit) == "string" then
        exit = alttp_location.new(exit)
    end
    if rule == nil then
        rule = always
    end
    self.exits[#self.exits + 1] = { exit, rule }
end

-- markes a 2-way connection between 2 locations. acts as a shortcut for 2 connect_one_way-calls 
function alttp_location:connect_two_ways(exit, rule)
    self:connect_one_way(exit, rule)
    exit:connect_one_way(self, rule)
end

-- creates a 1-way connection from a region/location to another one via a 1-way connector like a ledge, hole,
-- self-closing door, 1-way teleport, ...
function alttp_location:connect_one_way_entrance(name, exit, rule)
    if rule == nil then
        rule = always
    end
    self.exits[#self.exits + 1] = { exit, rule }
end

-- creates a connection between 2 locations that is traversable in both ways using the same rules both ways
-- acts as a shortcut for 2 connect_one_way_entrance-calls
function alttp_location:connect_two_ways_entrance(name, exit, rule)
    if exit == nil then -- for ER
        return
    end
    self:connect_one_way_entrance(name, exit, rule)
    exit:connect_one_way_entrance(name, self, rule)
end

-- creates a connection between 2 locations that is traversable in both ways but each connection follow different rules.
-- acts as a shortcut for 2 connect_one_way_entrance-calls
function alttp_location:connect_two_ways_entrance_door_stuck(name, exit, rule1, rule2)
    self:connect_one_way_entrance(name, exit, rule1)
    exit:connect_one_way_entrance(name, self, rule2)
end

-- checks for the accessibility of a regino/location given its own exit requirements
function alttp_location:accessibility()
    if self.staleness < staleness then
        return AccessibilityLevel.None
    else
        return self.accessibility_level
    end
end

-- 
function alttp_location:discover(accessibility, keys)
    
    local change = false
    if accessibility > self:accessibility() then
        change = true
        self.staleness = staleness
        self.accessibility_level = accessibility
        self.keys = math.huge
    end
    if keys < self.keys then
        self.keys = keys
        change = true
    end

    if change then
        for _, exit in pairs(self.exits) do
            local location = exit[1]
            local rule = exit[2]

            local access, key = rule(keys)
            -- print(access)
            if access == 5 then
                access = AccessibilityLevel.SequenceBreak
            elseif access == true then
                access = AccessibilityLevel.Normal
            elseif access == false then
                access = AccessibilityLevel.None
            end
            if key == nil then
                key = keys
            end
            -- print(self.name) 
            -- print(accessLVL[self.accessibility_level], "from", self.name, "to", location.name, ":", accessLVL[access])
            location:discover(access, key)
        end
    end
end

entry_point = alttp_location.new("entry_point")
-- lightworld_spawns = alttp_location.new("lightworld_spawns")
-- darkworld_spawns = alttp_location.new("darkworld_spawns")

-- entry_point:connect_one_way(lightworld_spawns, function() return openOrStandard() end)
-- entry_point:connect_one_way(darkworld_spawns, function() return inverted() end)

-- 
function stateChanged()
    staleness = staleness + 1
    entry_point:discover(AccessibilityLevel.Normal, 0)
end

ScriptHost:AddWatchForCode("stateChanged", "*", stateChanged)
        ''')
    if not os.path.exists(path + "/scripts/logic/logic_helper.lua"):
        with open(path + "/scripts/logic/logic_helper.lua", "w") as logic_helper_lua:
            logic_helper_lua.write('''
            function A(result)
    if result then
        return AccessibilityLevel.Normal
    else
        return AccessibilityLevel.None
    end
end

function all(...)
    local args = { ... }
    local min = AccessibilityLevel.Normal
    for i, v in ipairs(args) do
        if type(v) == "boolean" then
            v = A(v)
        end
        if v < min then
            if v == AccessibilityLevel.None then
                return AccessibilityLevel.None
            else
                min = v
            end
        end
    end
    return min
end

function any(...)
    local args = { ... }
    local max = AccessibilityLevel.None
    for i, v in ipairs(args) do
        if type(v) == "boolean" then
            v = A(v)
        end
        if tonumber(v) > tonumber(max) then
            if tonumber(v) == AccessibilityLevel.Normal then
                return AccessibilityLevel.Normal
            else
                max = tonumber(v)
            end
        end
    end
    return max
end

function has(item, noKDS_amount, noKDS_amountInLogic, KDS_amount, KDS_amountInLogic)
    local count
    local amount
    local amountInLogic
    if (Tracker:FindObjectForCode("small_keys").CurrentStage == 2) and item:sub(-8,-1) == "smallkey" then -- universal keys
        return true
    end
    if Tracker:FindObjectForCode("key_drop_shuffle").Active then
        -- print(KDS_amount, KDS_amountInLogic)
        amount = KDS_amount
        amountInLogic = KDS_amountInLogic
        if item:sub(-8,-1) == "smallkey" then
            count = Tracker:ProviderCountForCode(item.."_drop")
        else
            count = Tracker:ProviderCountForCode(item)
        end
    else
        count = Tracker:ProviderCountForCode(item)
        amount = noKDS_amount
        amountInLogic = noKDS_amountInLogic
    end

    -- print(item, count, amount, amountInLogic)
    if amountInLogic then
        if count >= amountInLogic then
            return AccessibilityLevel.Normal
        elseif count >= amount then
            return AccessibilityLevel.SequenceBreak
        else
            return AccessibilityLevel.None
        end
    end
    if not amount then
        return count > 0
    else
        amount = tonumber(amount)
        return count >= amount
    end
end
            ''')
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
    if not (os.path.exists(path + "/scripts/autotracking/item_mapping.lua") and os.path.exists(path +
                                                                                                "/scripts/autotracking/location_mapping.lua")):
        create_mappings(game_data=games_dict[game_name])
        return exit()


root = tk.Tk()
root.withdraw()

read_file_path = tk.filedialog.askdirectory()
if not os.path.exists(read_file_path + '/datapacke_url.txt'):
    with open(read_file_path + '/datapacke_url.txt', "w") as base_file:
        url = input("datapackage source (url): ") or "https://archipelago.gg/datapackage"
        game = input("Game name from Datapackage: ")
        base_file.write(f"{url}, {game}, ")
datapackage_path, game_name, *other_options = open(read_file_path + '/datapacke_url.txt').readline().split(', ')

games_dict = requests.get(datapackage_path).json()['games']

create_base_structure(path=read_file_path)

# create_mappings(game_data=games_dict[game_name], game=game_name)
# create_item_mapping(location_data=games_dict[game_name], game=game_name)
# create_location_mapping(location_data=games_dict[game_name], game=game_name)

create_items(path=read_file_path)
create_locations(path=read_file_path, logic=logic)


create_maps(path=read_file_path)
create_broadcast_layout(path=read_file_path)
create_tracker_basic_layout(path=read_file_path)
create_tracker_tabs(path=read_file_path)
create_item_layout(path=read_file_path)
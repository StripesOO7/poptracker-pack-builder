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


def create_mappings(game_data: dict[str, int]):
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
    with open(path + '/scripts/autotracking/' + file_name + '.lua', "w") as mapping:
        mapping.write(f'{file_name.upper()} = \u007b\n')
        match type:
            case 'items':
                for name, ids in data.items():
                    mapping.write(f'\t[{ids}] = \u007b"{name}", "toggle"\u007d,\n'),
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
                        else:
                            mapping.write(f'\t[{ids}] = \u007b"@{name}"\u007d,\n'),
        mapping.write("\u007d")


def create_items(path: str):
    read_input = []
    item_list = []
    with open(path+'/scripts/autotracking/item_mapping.lua') as mapping:
        while input := mapping.readline():
            if "]" in input:
                read_input.append(input.split("="))
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
                                "codes": "{item_name.replace(' ', '')}_returned"
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
                            "codes": "{item_name.replace(' ', '')}_returned"
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


def create_locations(path: str, logic: dict[str, str]):
    read_input = []
    location_list = []
    temp = []
    global lvls, locations_dict, maps_names
    with open(path+'/scripts/autotracking/location_mapping.lua') as mapping:
        while input := mapping.readline():
            if "]" in input:
                read_input.append(input.split("="))
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

    with open(path+"/scripts/locations.lua", 'w') as locations_file:
        for i in lvls:
            locations_file.write(f'Tracker:AddLocations("locations/{i}.json")\n')
    locations_dict = {e: {} for e in lvls}

    logic_dict = extract_logic()

    for location in location_list:
        if not len(location) == 1:
            locations_dict[location[0]].update({location[1:][0]: list()})
        else:
            locations_dict[location[0]].update({location[0]: list()})
    for location in location_list:
        if len(location[1:]) > 1:
            locations_dict[location[0]][location[1:][0]].append(location[1:][1])
        elif len(location[1:]) == 1:
            locations_dict[location[0]][location[1:][0]].append(location[1:][0])
        else:
            try:
                locations_dict[location[0]][location[0]].append(logic_dict[location[0]])
            except:
                pass

    for i, location_region in enumerate(locations_dict.keys()):
        # print(city, lvl_locations[city])
        with open(path+fr"\locations\{location_region}.json", "w") as locations_file:
            locations_file.write('[')

            locations_file.write(f'''
            \u007b
                "name": "{location_region}",
                "chest_unopened_img": "/images/Items/{location_region}.png",
                "chest_opened_img": "/images/Items/open_Chest.png",
                "overlay_background": "#000000",
                "access_rules": [" "],
                "children": [
            ''')
            for j, location in enumerate(locations_dict[location_region]):
                locations_file.write(f'''
                \u007b
                    "name": "{location}",
                    "chest_unopened_img": "/images/Items/{location}.png",
                    "chest_opened_img": "/images/Items/{location}.png",
                    "overlay_background": "#000000",
                    "sections": [
                ''')
                for k, check in enumerate(locations_dict[location_region][location]):
                    # print(check, check_location)
                    locations_file.write(f'''
                        \u007b
                            "name": "{check}",''')
                    try:
                        if logic_dict[location_region][location][check]:
                            locations_file.write(f'''
                            "access_rules": [ "{logic_dict[location_region][location][check][0]}" ],''')
                    except:
                        pass
                    locations_file.write(f'''
                            "item_count": 1
                        ''')

                    # print(k, len(lvl_locations[city][index])-1)
                    if k == len(locations_dict[location_region][location])-1:
                        locations_file.write('''\u007d
                        ''')
                    else:
                        locations_file.write('''\u007d,
                        ''')
                locations_file.write(f'''
                        ],
                        "map_locations": [
                            \u007b
                                "map": "Worldmap",
                                "x": {random.randint(10,500)},
                                "y": {random.randint(10,500)},
                                "size": 6
                            \u007d
                        ]
                        ''')
                if j == len(locations_dict[location_region])-1:
                    # print(test, len(lvl_locations[city]))
                    locations_file.write('\u007d')
                else:
                    locations_file.write('\u007d,')
            locations_file.write('''
    
                ]
            }
        ]''')
    maps_names = ["Worldmap"]
    for lvl in lvls:
        if len(locations_dict[lvl]) > 9:
            maps_names.append(lvl)
#


def create_maps(path: str):
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
                "img": "images/Maps/{map}.png"
            ''')
            if i == len(maps_names) - 1:
                maps.write('\u007d')
            else:
                maps.write('\u007d,')
        maps.write('\n]')
# #


def create_tracker_tabs(path: str):
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
    return list(itertools.product(*x))  ### list cross multiplication to generate every


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
        with open(file_path) as extract_logic:
            temp = extract_logic.read().split('\n')
            for i in temp:
                if " lambda " in i.lower():
                    logic_temp.append(i.split("lambda"))  #"""results in a list containing tuples of [location_string,


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
        local s = '{\n'
        for k, v in pairs(o) do
            if type(k) ~= 'number' then
                k = '"' .. k .. '"'
            end
            s = s .. tabs2 .. '[' .. k .. '] = ' .. dump_table(v, depth + 1) .. ',\n'
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
            if item_code and item[2] then
                local item_obj = Tracker:FindObjectForCode(item_code)
                if item_obj then
                    if item[2] == "toggle" then
                        item_obj.Active = false
                    elseif item[2] == "progressive" then
                        item_obj.CurrentStage = 0
                        item_obj.Active = false
                    elseif item[2] == "consumable" then
                        if item_obj.MinCount then
                            item_obj.AcquiredCount = item_obj.MinCount
                        else
                            item_obj.AcquiredCount = 0
                        end
                    elseif item[2] == "progressive_toggle" then
                        item_obj.CurrentStage = 0
                        item_obj.Active = false
                    end
                end
            end
        end
    end
    PLAYER_ID = Archipelago.PlayerNumber or -1
    TEAM_NUMBER = Archipelago.TeamNumber or 0
    SLOT_DATA = slot_data
    -- if Tracker:FindObjectForCode("autofill_settings").Active == true then
    --     autoFill(slot_data)
    -- end
    -- bossShuffle()
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
    for _, item_code in pairs(item[1]) do
        -- print(item[1], item[2])
        local item_obj = Tracker:FindObjectForCode(item_code)
        if item_obj then
            if item_obj.Type == "toggle" then
                -- print("toggle")
                item_obj.Active = true
            elseif item[2] == "progressive" then
                -- print("progressive")
                item_obj.Active = true
            elseif item[2] == "consumable" then
                -- print("consumable")
                item_obj.AcquiredCount = item_obj.AcquiredCount + item_obj.Increment
            elseif item[2] == "progressive_toggle" then
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
    end
    canFinish()
    calcHeartpieces()
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
--     mapDungeonItem={[0]=false,[1]=true,[2]=true,[3]=true,[4]=true,[6]=true}

--     -- mapGlitches={[0]=0,[1]=2,[2]=3,[3]=0,[4]=0}
--     -- progressive={[]=,}
--     mapMode={["open"]=0,["inverted"]=1,["standard"]=2}
--     mapGoals={["crystals"]=0,["ganon"]=1,["bosses"]=2,["pedestal"]=3,["ganonpedestal"]=4,["triforcehunt"]=5,["ganontriforcehunt"]=6,["icerodhunt"]=7,["localtriforcehunt"]=5,["localganontriforcehunt"]=6}
--     mapDark={["none"]=0,["lamp"]=1,["scornes"]=2} -- none=dark room, lamp=vanilla, scornes = firerod
--     mapMedalion={["Bombos"]="bombos",["Ether"]="ether",["Quake"]="quake"}
--     -- retro_caves={[]=}
--     mapBosses={[0]=0,[1]=1,[2]=1,[3]=1,[4]=2}
--     mapEnemizer={[0]=false,[1]=true,[2]=true}
--     -- shop_shuffle={[]=,}


--     slotCodes = {
--         -- glitches_required={code="glitches", mapping=mapToggleReverse},
--         key_drop_shuffle={code="key_drop_shuffle", mapping=mapDungeonItem},
--         pot_shuffle={code="key_drop_shuffle", mapping=mapDungeonItem},
--         dark_room_logic={code="dark_mode", mapping=mapDark},
--         bigkey_shuffle={code="big_keys", mapping=mapDungeonItem},
--         smallkey_shuffle={code="small_keys", mapping=mapToggle},
--         map_shuffle={code="map", mapping=mapDungeonItem},
--         compass_shuffle={code="compass", mapping=mapDungeonItem},
--         -- progressive={code="progressive_items", mapping=mapToggle},
--         goal={code="goal", mapping=mapGoals},
--         crystals_needed_for_gt={code="gt_access", mapping=nil},
--         crystals_needed_for_ganon={code="ganon_killable", mapping=nil},
--         mode={code="start_option", mapping=mapMode},
--         -- retro_bow={code="", mapping=mapToggleReverse},
--         retro_caves={code="retro_caves", mapping=mapDungeonItem},
--         swordless={code="swordless", mapping=mapDungeonItem},
--         -- item_pool={code="", mapping=mapToggle},
--         me_medallion={code="", mapping=mapMedalion},
--         tr_medallion={code="", mapping=mapMedalion},
--         boss_shuffle={code="boss_shuffle", mapping=mapBosses},
--         enemy_shuffle={code="enemizer", mapping=mapEnemizer},
--         shop_shuffle={code="shop_sanity", mapping=nil},
--         triforce_pieces_required={code="triforce_pieces_needed", mapping=nil}
--         -- glitch_boots={code="glitches", mapping=nil}
--     }
--     -- print(dump_table(SLOT_DATA))
--     -- print(Tracker:FindObjectForCode("autofill_settings").Active)
--     if Tracker:FindObjectForCode("autofill_settings").Active == true then
--         for settings_name , settings_value in pairs(SLOT_DATA) do
--             -- print(k, v)
--             if settings_name == "crystals_needed_for_gt" 
--             or settings_name == "crystals_needed_for_ganon" 
--             or settings_name == "triforce_pieces_required" then
--                 Tracker:FindObjectForCode(slotCodes[settings_name].code).AcquiredCount = settings_value
--             elseif settings_name == "shop_shuffle" then
--                 item = Tracker:FindObjectForCode(slotCodes[settings_name].code)
--                 if settings_value ~= "none" then
--                     item.Active = true
--                 elseif settings_value == "none" then
--                     item.Active = false
--                 end
--             elseif settings_name == "shop_item_slots" then
--                 Tracker:FindObjectForCode("shop_sanity").AcquiredCount = settings_value 
--                 Tracker:FindObjectForCode("shop_sanity").Active = true
--             elseif slotCodes[settings_name] then
--                 item = Tracker:FindObjectForCode(slotCodes[settings_name].code)
--                 if item.Type == "toggle" then
--                     item.Active = slotCodes[settings_name].mapping[settings_value]
--                 else 
--                     -- print(k,v,Tracker:FindObjectForCode(slotCodes[k].code).CurrentStage, slotCodes[k].mapping[v])
--                     item.CurrentStage = slotCodes[settings_name].mapping[settings_value]
--                 end
--             end
--         end
--         if SLOT_DATA["mm_medalion"] == SLOT_DATA["tr_medalion"] then
--             Tracker:FindObjectForCode(string.lower(SLOT_DATA["mm_medalion"])).CurrentStage = 3
--         else
--             Tracker:FindObjectForCode(string.lower(SLOT_DATA["mm_medalion"])).CurrentStage = 2
--             Tracker:FindObjectForCode(string.lower(SLOT_DATA["tr_medalion"])).CurrentStage = 1
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

-- Logic
ScriptHost:LoadScript("scripts/logic/logic.lua")

-- Maps
if Tracker.ActiveVariantUID == "Items Only" then
    Tracker:AddMaps("maps/maps.json")  
end

Tracker:AddMaps("maps/maps.json")
-- Layout
ScriptHost:LoadScript("scripts/layouts.lua")

-- Locations
ScriptHost:LoadScript("scripts/locations.lua")
-- Tracker:AddLocations("locations/locations.json")


-- AutoTracking for Poptracker
if PopVersion and PopVersion >= "0.18.0" then
    ScriptHost:LoadScript("scripts/autotracking.lua")
end''')
    if not os.path.exists(path + "/scripts/layouts.lua"):
        with open(path + "/scripts/layouts.lua", "w") as layouts_lua:
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
    if not os.path.exists(path + "/scripts/logic/logic.lua"):
        with open(path + "/scripts/logic/logic.lua", "w") as logic_lua:
            logic_lua.write('''
        ''')
    if not os.path.exists(path + "/images"):
        os.mkdir(path + "/images")
        os.mkdir(path + "/images/items")
        os.mkdir(path + "/images/maps")
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
        base_file.write(f"{url}, {game}")
datapackage_path, game_name = open(read_file_path + '/datapacke_url.txt').readline().split(', ')

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
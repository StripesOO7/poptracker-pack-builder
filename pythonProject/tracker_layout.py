import json
import math
import tkinter as tk
from tkinter import filedialog


def _maps_layouts(map_name):
    layout_json = {
        "title": f"{map_name}",
        "content": {"type": "map", "maps": [f"{map_name}"]},
    }
    return layout_json


def create_tracker_tabs(path: str, maps_names: list):
    """
    creates a json scheme that adds the created maps from create_maps() into the loaded tracker file
    :param path:
    :param maps_names:
    :return:
    """

    with open(path + "/layouts/tabs.json", "w") as tabs:
        tabbed_maps_horizontal = {"type": "tabbed", "tabs": []}
        tabbed_maps_vertical = {"type": "tabbed", "tabs": []}

        for map in maps_names:
            tabbed_maps_vertical["tabs"].append(_maps_layouts(map))
            tabbed_maps_horizontal["tabs"].append(_maps_layouts(map))
        tab_json_obj = {
            "tabbed_maps_horizontal": tabbed_maps_horizontal,
            "tabbed_maps_vertical": tabbed_maps_vertical,
        }

        tabs.write(f"{json.dumps(tab_json_obj, indent=4)}")


# #


def create_broadcast_layout(path: str):
    """
    creates a basic broadcast layout containing the items section of the normal tracker
    :param path:
    :return:
    """
    with open(path + "/layouts/broadcast.json", "w") as broadcast:
        broadcast_json = {
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
                            {"type": "layout", "key": "shared_item_grid_vertical"}
                        ],
                    }
                ],
            }
        }
        broadcast.write(json.dumps(broadcast_json, indent=4))


# #


def create_tracker_basic_layout(path: str):
    """
    creates the full json for a basic tracker pack for poptracker.
    contains a map/item/settings/pins-section for a horizontal and vertical layout
    :param path:
    :return:
    """
    with open(path + "/layouts/tracker.json", "w") as tracker:
        track_data = {
            "tracker_default": {
                "type": "container",
                "background": "#00000000",
                "content": {
                    "type": "dock",
                    "dropshadow": True,
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
                                        "key": "shared_item_grid_vertical",
                                    },
                                },
                                {
                                    "type": "group",
                                    "header": "Settings",
                                    "dock": "top",
                                    "content": {
                                        "type": "layout",
                                        "key": "setting_grid",
                                    },
                                },
                                {
                                    "type": "group",
                                    "header": "Pinned Locations",
                                    "content": {
                                        "style": "wrap",
                                        "type": "recentpins",
                                        "orientation": "vertical",
                                        "compact": True,
                                    },
                                },
                            ],
                        },
                        {
                            "type": "dock",
                            "content": {
                                "type": "layout",
                                "key": "tabbed_maps_vertical",
                            },
                        },
                    ],
                },
            },
            "tracker_horizontal": {
                "type": "container",
                "background": "#00000000",
                "content": {
                    "type": "dock",
                    "dropshadow": True,
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
                                        "key": "shared_item_grid_horizontal",
                                    },
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
                                        "key": "setting_grid",
                                    },
                                },
                                {
                                    "type": "group",
                                    "header": "Pinned Locations",
                                    "content": {
                                        "style": "wrap",
                                        "type": "recentpins",
                                        "orientation": "horizontal",
                                        "compact": True,
                                    },
                                },
                            ],
                        },
                        {
                            "type": "dock",
                            "content": {
                                "type": "layout",
                                "key": "tabbed_maps_horizontal",
                            },
                        },
                    ],
                },
            },
        }

        tracker.write(json.dumps(track_data, indent=4))
    # #
    with open(path + "/layouts/settings_popup.json", "w") as settings_popup:
        settings_popup_json = {
            "settings_popup": {
                "type": "array",
                "margin": "5",
                "content": [
                    {
                        "type": "group",
                        "header": "Autofill Settings",
                        "description": "Enable/Disable the automatic fill of the settings panel from for connected Slot_Data",
                        "header_background": "#3e4b57",
                        "content": [
                            {
                                "type": "item",
                                "margin": "5,1,5,5",
                                "item": "autofill_settings",
                            }
                        ],
                    }
                ],
            }
        }
        settings_popup.write(json.dumps(settings_popup_json, indent=4))


def create_item_layout(path: str):
    """
    creates basic item layout containing all items found in item_mapping. splits the items as evenly as possible.
    creates a horizontal and vertical layout
    :param path:
    :return:
    """
    item_codes = []
    with open(path + "/items/items.json") as items:
        json_data = json.load(items)
        for data in json_data:
            if not data == {}:
                item_codes.append(data["codes"])
    with open(path + "/layouts/items.json", "w") as item_layout:
        item_layout_json = dict()
        item_layout_json["shared_item_grid_horizontal"] = {
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
                            "rows": [],
                        }
                    ],
                }
            ],
        }
        item_layout_json["shared_item_grid_vertical"] = {
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
                            "rows": [],
                        }
                    ],
                }
            ],
        }
        divider = math.sqrt(len(item_codes)).__ceil__()
        for i, item in enumerate(item_codes):
            if (i + 1) % divider == 1:
                item_layout_json["shared_item_grid_horizontal"]["content"][0][
                    "content"
                ][0]["rows"].append([])
                item_layout_json["shared_item_grid_vertical"]["content"][0]["content"][
                    0
                ]["rows"].append([])
            item_layout_json["shared_item_grid_horizontal"]["content"][0]["content"][0][
                "rows"
            ][i // divider].append(item)
            item_layout_json["shared_item_grid_vertical"]["content"][0]["content"][0][
                "rows"
            ][i // divider].append(item)

        item_layout.write(json.dumps(item_layout_json, indent=4))


if __name__ == "__main__":
    import json
    import math
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()

    print("Select the base-folder of the pack:")
    save_file_path = tk.filedialog.askdirectory()
    print("Path to base-folder of the pack: ", save_file_path)

    read_input = []
    location_list = []
    temp = []
    lvls = set()
    locations_dict = dict()
    maps_names = []
    with open(save_file_path + "/scripts/autotracking/location_mapping.lua") as mapping:
        while inputs := mapping.readline():
            if "]" in inputs:
                if not inputs.strip()[0:2] == "--":
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

    create_tracker_tabs(save_file_path, lvls)
    create_broadcast_layout(save_file_path)
    create_tracker_basic_layout(save_file_path)
    create_item_layout(save_file_path)

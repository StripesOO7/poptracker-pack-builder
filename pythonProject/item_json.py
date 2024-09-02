import json
import tkinter as tk
from tkinter import filedialog

def _stages(name:str):
    stage1 = {
        "name": f"{name} stage1",
        "inherit_codes": True,
        "img": f"/images/items/{name}.png",
        "img_mod": "",
        "codes": f"{name.replace(' ', '')}_stage1"
    }

    stage2 = {
        "name": f"{name} stage2",
        "inherit_codes": True,
        "img": f"/images/items/{name}.png",
        "img_mod": "",
        "codes": f"{name.replace(' ', '')}_stage2"
    }

    stage3 = {
        "name": f"{name} stage3",
        "inherit_codes": True,
        "img": f"/images/items/{name}.png",
        "img_mod": "",
        "codes": f"{name.replace(' ', '')}_stage3"
    }
    return [stage1, stage2, stage3]

def _item_toggle_preset(item_name:str):
    toggle_json_preset = {
        "name": item_name,
        "type": "toggle",
        "img": f"images/items/{item_name}.png",
        "img_mods": "",
        "codes": f"{item_name.replace(' ', '')}"
    }

    return toggle_json_preset

def _item_progressive_toggle_preset(item_name:str):
    progressive_toggle_json_preset = {
        "name": f"{item_name}",
        "type": "progressive_toggle",
        "loop": False,
        "initial_stage_idx": 0,
        "initial_active_state": False,
        "stages": _stages(item_name),
        "codes": f"{item_name.replace(' ', '')}"
    }
    return progressive_toggle_json_preset

def _item_progressive_preset(item_name:str):
    progressive_json_preset = {
        "name": f"{item_name}",
        "type": "progressive",
        "loop": False,
        "allow_disabled": True,
        "initial_stage_idx": 0,
        "stages": _stages(item_name),
        "codes": f"{item_name.replace(' ', '')}"
    }
    return progressive_json_preset

def _item_consumable_preset(item_name:str):
    consumable_json_preset = {
        "name": item_name,
        "type": "consumable",
        "img": f"images/items/{item_name}.png",
        "img_mods": "",
        "min_quantity": 0,
        "max_quantity": 10,
        "increment": 1,
        "decrement": 1,
        "initial_quantity": 2,
        "overlay_background": "#000000",
        "codes": f"{item_name.replace(' ', '')}"
    }

    return consumable_json_preset

def _item_static_preset(item_name:str):
    static_json_preset = {
        "name": item_name,
        "type": "static",
        "img": f"images/items/{item_name}.png",
        "img_mods": "",
        "codes": f"{item_name.replace(' ', '')}"
    }

    return static_json_preset



def create_items(path: str):
    '''
    gathers the items from the item_mapping.lua file and converts them according to their specified item_type into a
    poptracker-readable/-loadable json format.
    ignores with "--" commented out lines.
    Pre-places the itemnames as names for the loaded images. needs to be adjusted if that is not fitting.
    :param path: Path to the root folder of the Trackerpack
    :return: none
    '''
    read_input = []
    item_list = []
    for file in ['hints_mapping', 'item_mapping']:
        print(file)
        with open(path+fr'/scripts/autotracking/{file}.lua') as mapping:
            while inputs := mapping.readline():
                if "]" in inputs:
                    if not (inputs.strip()[0:2] == "--" or inputs.strip()[0:2] == "//"):
                        read_input.append(inputs.split("="))
                else:
                    pass

        for k, _ in enumerate(read_input):
            first_open = read_input[k][1].index('{')
            last_close = read_input[k][1].index('},\n') if read_input[k][1].find('},\n') > 0  else read_input[k][
                1].index('}\n')
            # second_close = read_input[k][1][first_close:].index('}')
            read_input[k][1] = read_input[k][1][first_open+1: last_close].strip()
            item_list.append(read_input[k][1].replace('"', '').rsplit(', ',1))

        if file == 'item_mapping':
            name = 'items'
        elif file == 'hints_mapping':
            name = 'hint_items'
        else:
            name = 'items_default'
        item_list = list(set(tuple(sub) for sub in item_list))

        with open(path + rf"/items/{name}.json", "w") as items_file:
            # items_file.write("[")
            # print(item_list)
            item_json_obj = []

            for item_name, item_types in item_list:
                # print(item_name, item_types)
                item_name = item_name[item_name.index('{')+1:item_name.index('}')]
                match item_types:
                    case "toggle":
                        item_json_obj.append(_item_toggle_preset(item_name))
                    case "progressive":
                        item_json_obj.append(_item_progressive_preset(item_name))
                    case "progressive_toggle":
                        item_json_obj.append(_item_progressive_toggle_preset(item_name))
                    case "consumable":
                        item_json_obj.append(_item_consumable_preset(item_name))
                    case "static":
                        item_json_obj.append(_item_static_preset(item_name))
                    case "composite_toggle":
                        pass
                    case "toggle_badged":
                        pass
                    case _:
                        item_json_obj.append(_item_toggle_preset(item_name))

            items_file.write(f'{json.dumps(item_json_obj, indent=4)}')
# #


if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    #
    # print("Select a file to open")
    # path_to_item_json = filedialog.askopenfilename()
    # print("Filename: ", path_to_item_json)
    print("Select the base-folder of the pack:")
    save_file_path = tk.filedialog.askdirectory()
    print("Path to base-folder of the pack: ", save_file_path)
    create_items(save_file_path)

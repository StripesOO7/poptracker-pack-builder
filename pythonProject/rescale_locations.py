def key_lookup(json_dict):
    if "map_locations" in json_dict.keys():
        for map_index, _ in enumerate(json_dict["map_locations"]):
            json_dict["map_locations"][map_index]["x"] = math.floor(int(json_dict["map_locations"][map_index]["x"])*
                                                                ratio_width)
            json_dict["map_locations"][map_index]["y"] = math.floor(int(json_dict["map_locations"][map_index]["y"]) *
                                                               ratio_height)
    if "children" in json_dict.keys():
        for index, child in enumerate(json_dict["children"]):
            json_dict["children"][index] = key_lookup(json_dict["children"][index])
    return json_dict

if __name__ == '__main__':
    import json
    import math
    import tkinter as tk
    from tkinter import filedialog
    from PIL import Image

    root = tk.Tk()
    root.withdraw()

    print("Select the json to be recalculated. first choose directory second the file itself: ")
    save_file_name = tk.filedialog.askopenfilename()
    print("Path to location json-file: ", save_file_name)
    print("Select old image:")
    old_img = tk.filedialog.askopenfilename()
    print("Select new image:")
    new_img = tk.filedialog.askopenfilename()

    old_width, old_height = Image.open(old_img).size
    new_width, new_height = Image.open(new_img).size
    ratio_width = new_width/old_width
    ratio_height = new_height/old_height


    with open(f"{save_file_name}", encoding="utf-8") as recalc_json_file:
        file_list = recalc_json_file.readlines()
        file_str = "".join(file_list)
        file_json_list = json.loads(file_str)
        for json_obj in file_json_list:
            json_obj = key_lookup(json_obj)
    with open(f"{save_file_name.replace('.json', '_recalc.json')}", "w") as new_file:
        new_file.write(json.dumps(file_json_list, indent=4))

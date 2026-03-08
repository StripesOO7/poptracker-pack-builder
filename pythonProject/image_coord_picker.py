import os
from typing import Any, Dict, List

from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, Variable, ttk
import json


coords = (0,0)
locations_json_selected = ""
map_json_selected = ""
og_img_size = (0,0)
scaling_factor = 1
og_img_width = og_img_size[0]
og_img_height = og_img_size[1]
new_data = {}
rectangle_id = []


def traverse_json_back(index, json_dict, path):
    if type(json_dict) == list:
        for idx, entry in enumerate(json_dict):
            if index == entry["name"]:
                path.append(idx)
                return entry
        return json_dict
    else:
        return {}

def build_map_dict(x, y, map_name, size, shape):
    return {
        "map": map_name,
        "x": x,
        "y": y,
        "size": size,
        "shape": shape,
    }

def write_json_partially(path, location_section_json, changed_part):
    if len(path) > 1:
        location_section_json[path[0]] = write_json_partially(path[1:], location_section_json[path[0]], changed_part)
        return location_section_json
    else:
        if path[0] == len(location_section_json):
            location_section_json.append(changed_part)
        else:
            location_section_json[path[0]] = changed_part
        return location_section_json
    pass

def save_to_new_file():
    with open(f'{base_path}/locations/{locations_json_selected.replace(".json", "_new.json")}', "w") as new_json:
        save()
        new_json.write(json.dumps(location_section_json, indent=4))

def save_to_old_file():
    with open(f'{base_path}/locations/{locations_json_selected}', "w") as old_json:
        save()
        old_json.write(json.dumps(location_section_json, indent=4))

def save():
    # location_section_json
    # filled with the split names in the location list intersected with integers for list traversal
    found_map = False
    for location in location_list:
        path = []
        tmp = location_section_json
        if location in new_data.keys():
            for index, step in enumerate((location.split("/"))):
                tmp = traverse_json_back(step, tmp, path)
                if index+1 == len(location.split("/")): # reached last stage of dict
                    path.append("map_locations")
                    tmp = tmp["map_locations"]
                else: #not last stage reached
                    path.append("children")
                    tmp = tmp["children"]
                    continue
                print(index ,step, tmp)
                # we are at the last stage of of the dict aka inside map_locations
                for index, map in enumerate(tmp): # iterate over the existing map_locations
                    if map["map"] == map_json_selected:
                        found_map = True
                        path.append(index)
                        break # exit loop after finding correct map and replace data
                if not found_map: # # never found the map key to replace so we create a new entry
                    path.append(index+1)
                break
            location_section_json[path[0]] = write_json_partially(path[1:], location_section_json[path[0]],
                                                                  new_data[location][0])
        else:
            pass


def resize_image(event):
    print("start run resize image")
    global image, scaling_factor, canvas_id, new_data
    # new_data = {}
    if event.width / og_img_width < event.height / og_img_height:
        scaling_factor = event.width / og_img_width
    else:
        scaling_factor = event.height / og_img_height
    new_width = round(og_img_width * scaling_factor)
    new_height = round(og_img_height * scaling_factor)
    image = copy_of_image.resize((new_width, new_height))
    photo = ImageTk.PhotoImage(image)
    canvas.delete(canvas_id)
    # for id in rectangle_id:
    #     canvas.delete(id)
    # rectangle_id.clear()
    canvas.create_image(0, 0, image=photo, anchor="nw")
    for location in new_data.keys():
        canvas.delete(new_data[location][1])
        canvas.delete(new_data[location][2])
        new_data[location][1] = canvas.create_rectangle(
            (new_data[location][0]["x"]*scaling_factor) - 5,
            (new_data[location][0]["y"]*scaling_factor) - 5,
            (new_data[location][0]["x"]*scaling_factor) + 5,
            (new_data[location][0]["y"]*scaling_factor) + 5,
            fill="red"
        )
        new_data[location][2] = canvas.create_text(
            new_data[location][0]["x"]*scaling_factor,
            new_data[location][0]["y"]*scaling_factor,
            text=(
                f"x:{new_data[location][0]['x']}, y: {new_data[location][0]['y']}\n"
                f"{new_data[location][0]['map']},\n"
                f"shape:{new_data[location][0]['shape']}\n"
                f"size:{new_data[location][0]['size']}"
            )
        )
    canvas.image = photo  # avoid garbage collection
    print("end run resize image")

def place_location(event):
    print("clicked at", event.x, event.y)
    print("scaling factor", scaling_factor)
    print("actual image coords", event.x//scaling_factor, event.y//scaling_factor)
    if frame_location_selection.focus_get().selection_get() in new_data.keys():
        canvas.delete(new_data[frame_location_selection.focus_get().selection_get()][1])
        canvas.delete(new_data[frame_location_selection.focus_get().selection_get()][2])
    canvas.pack()
    shape_id = canvas.create_rectangle(event.x - 5, event.y - 5, event.x + 5, event.y + 5, fill="red")
    text_id = canvas.create_text(event.x, event.y, text=(
        f"x:{event.x // scaling_factor}, y: {event.y // scaling_factor}\n"
        f"location name: {frame_location_selection.focus_get().selection_get()},\n"
        f"shape:{shape_button['values'][shape_button.current()]}\n"
        f"size:{size_button['values'][size_button.current()]}")
                                 )
    new_data[frame_location_selection.focus_get().selection_get()] = [
        build_map_dict(
            x = int(event.x//scaling_factor),
            y = int(event.y//scaling_factor),
            map_name = map_json_selected,
            size = size_button['values'][size_button.current()],
            shape = shape_button['values'][shape_button.current()],
        ),
        shape_id,
        text_id
    ]
    # print(new_data)


def update_coords(x, y):
    global coords
    coords = (x, y)


def dialog():

    if window.focus_get().__str__().split(".")[-1] == "json":
        global locations_json_selected
        locations_json_selected = window.focus_get().selection_get()
    if window.focus_get().__str__().split(".")[-1] == "maps":
        global map_json_selected
        map_json_selected = window.focus_get().selection_get()
    if not locations_json_selected == "" and not map_json_selected == "":
        window.quit()
    # return messagebox.showinfo('Selection', 'Your Choice: ' + \
    # window.focus_get().selection_get())

def select_location():
    return window.focus_get().selection_get()

def traverse_json(region, path, location_list):
    new_path = f"{path}/{region['name']}"
    if "sections" in region.keys():
        location_list.append(new_path[1:])
        # return
    if "children" in region.keys():
        for child in region["children"]:
            traverse_json(child, new_path, location_list)
    if "map_locations" in region.keys():
        for map in region["map_locations"]:
            if map["map"] == map_json_selected:
                new_data[new_path[1:]] = [
                    build_map_dict(
                        x=int(map['x']),
                        y=int(map['y']),
                        map_name=map['map'],
                        size=map['size'] if 'size' in map.keys() else 10,
                        shape=map['shape'] if 'shape' in map.keys() else 'rect',
                    ),
                    canvas.create_rectangle(
                        (map["x"]*scaling_factor) - 5,
                        (map["y"]*scaling_factor) - 5,
                        (map["x"]*scaling_factor) + 5,
                        (map["y"]*scaling_factor) + 5,
                        fill="red"
                    ),
                    canvas.create_text(
                        map["x"]*scaling_factor,
                        map["y"]*scaling_factor,
                        text=(
                            f"x:{map['x']}, y: {map['y']}\n"
                            f"location name: {new_path[1:]},\n"
                            f"shape:{map['size'] if 'size' in map.keys() else 10}\n"
                            f"size:{map['shape'] if 'shape' in map.keys() else 'rect'}"
                        )
                    )
                ]
                print("placed as square")



if __name__ == "__main__":
    locations_json_selected=""
    map_json_selected=""
    window = tk.Tk()
    window.withdraw()

    window.columnconfigure([0,1,2],  weight=1)
    window.rowconfigure(0, weight=1)

    frame_map_selection = tk.Frame(window)
    frame_map_selection.grid(row=0, column=1, sticky="nsew")
    frame_map_selection.columnconfigure(0, weight=1)
    frame_map_selection.rowconfigure(1, weight=2)
    frame_map_selection.rowconfigure([0,2], weight=0)

    frame_location_selection = tk.Frame(window)
    frame_location_selection.grid(row=0, column=0, sticky="nsew")
    frame_location_selection.columnconfigure(0, weight=1)
    frame_location_selection.rowconfigure(1, weight=2)
    frame_location_selection.rowconfigure([0,2], weight=0)


    # Maps side
    scrollbar_maps = tk.Scrollbar(frame_map_selection, orient="vertical")
    window_list_of_maps = tk.Listbox(frame_map_selection, name="maps", yscrollcommand=scrollbar_maps.set)
                                     # , exportselection=False)
    scrollbar_maps.config(command=window_list_of_maps.yview)
    header_maps = tk.Label(frame_map_selection, text="Select a map")

    header_maps.grid_configure(row=0, column=0,  sticky="ew")
    btn_map = tk.Button(frame_map_selection, text='Select Map', command=dialog)
    btn_map.grid_configure(row=2, column=0, padx=5, pady=5, sticky="ew")
    scrollbar_maps.grid_configure(row=1, column=1, sticky="ns")
    window_list_of_maps.grid_configure(row=1, column=0, sticky="nsew")

    # location side
    scrollbar_locations = tk.Scrollbar(frame_location_selection, orient="vertical")
    window_list_of_locations = tk.Listbox(frame_location_selection, name="json", yscrollcommand=scrollbar_locations.set)
                                          # , exportselection=False)
    scrollbar_locations.config(command=window_list_of_locations.yview)
    btn_locations = tk.Button(frame_location_selection, text='select JSON', command=dialog)
    header_locations = tk.Label(frame_location_selection, text="Select location source")

    header_locations.grid_configure(row=0, column=0,  sticky="ew")
    btn_locations.grid_configure(row=2, column=0, padx=5, pady=5, sticky="ew")
    scrollbar_locations.grid_configure(row=1, column=1, sticky="ns")
    window_list_of_locations.grid_configure(row=1, column=0, sticky="nsew")


    base_path = tk.filedialog.askdirectory()


    #select image to open
    map_list = {}
    json_maps = json.load(open(f"{base_path}/maps/maps.json"))
    for map_json in json_maps:
        map_list[map_json["name"]] = f'{base_path}/{map_json["img"]}'
        window_list_of_maps.insert(tk.END, map_json["name"])

    #select locations json to tp apply the images coords to
    locations_files = os.listdir(f'{base_path}/locations')
    # print(locations_files)
    for location in locations_files:
        # print(location)
        window_list_of_locations.insert(tk.END, location)





    window.deiconify()
    window.mainloop()

    frame_map_selection.grid_forget()
    frame_location_selection.grid_forget()


    print(map_json_selected, locations_json_selected)
    if not map_json_selected == "":
        map_name = map_json_selected
        map_image_path = map_list[map_json_selected]
        # locations_json = json.load(open(f"{base_path}/locations/{map_json_selected}"))
        # for map_name, map_image_path in map_list:
        print(map_name, map_image_path)

        window.columnconfigure(0, weight=2)
        window.columnconfigure(1, weight=5)
        window.columnconfigure(2, weight=0)


        frame_location_selection = tk.Frame(window)
        frame_location_selection.grid(row=0, column=0, sticky="nsew")


        frame_map_image = tk.Frame(window)
        frame_map_image.grid(row=0, column=1, sticky="nsew")

        frame_settings = tk.Frame(window)
        frame_settings.grid(row=0, column=2, sticky="nsew")

        #settings
        shape_button = ttk.Combobox(frame_settings, state="readonly", values=("rect", "diamond", "trapezoid"))
        shape_button.set(shape_button["values"][0])
        shape_button.pack()

        size_button = ttk.Combobox(frame_settings, state="readonly", values=[str(i) for i in range(10, 41 ,2)])
        size_button.set(size_button["values"][0])
        size_button.pack()

        save_new_button = tk.Button(frame_settings, text="Save to new file", command=save_to_new_file)
        save_new_button.pack()

        # save_old_button = tk.Button(frame_settings, text="Overwrite existing file", command=save_to_old_file)
        # save_old_button.pack()

        ttk.Sizegrip(frame_settings)
        # menu_shape.pack()
        # img = cv2.imread(map_image_path)

        #image to display
        image = Image.open(fr"{map_image_path}")
        og_img_size = image.size
        og_img_width = og_img_size[0]
        og_img_height = og_img_size[1]
        copy_of_image = image.copy()
        img = ImageTk.PhotoImage(image=image, name="map image")


        canvas = tk.Canvas(frame_map_image, name="map image test", width=img.width(), height=img.height())


        location_section_json = json.load(open(f'{base_path}/locations/{locations_json_selected}'))
        location_list = []
        for region in location_section_json:
            path = ""
            print(region["name"])
            traverse_json(region, path, location_list)

        # window.resizable(True, True)
        canvas = tk.Canvas(frame_map_image, name="map image test", width=img.width(), height=img.height())
        canvas_id = canvas.create_image(0, 0, image=img, anchor="nw")
        canvas.pack(expand=True, fill="both")
        # canvas.pack(expand=True, fill="both")
        canvas.bind("<Configure>", resize_image)
        # canvas.bind("<Button-1>", callback)
        # canvas.bind("<MouseWheel>", resize_image)
        # canvas.bind("<B1-Motion>", callback)
        canvas.bind("<ButtonRelease-1>", place_location)



        # btn_map = tk.Button(frame, text='Select Location', command=select_location)
        scrollbar_location_section_y = tk.Scrollbar(frame_location_selection, orient="vertical")
        location_section_list = tk.Listbox(frame_location_selection, name="locations",
                                           yscrollcommand=scrollbar_location_section_y.set)#, exportselection=False)
        # location_section_list.bind("<<ListboxSelect>>", callback)
        scrollbar_location_section_y.config(command=window_list_of_locations.yview)

        scrollbar_canvas_y = tk.Scrollbar(frame_map_image, orient="vertical")
        scrollbar_canvas_x = tk.Scrollbar(frame_map_image, orient="horizontal")
        canvas.config(yscrollcommand=scrollbar_canvas_y.set, xscrollcommand=scrollbar_canvas_x.set)
        scrollbar_canvas_y.config(command=window_list_of_locations.yview)
        scrollbar_canvas_x.config(command=window_list_of_locations.xview)

        for location in location_list:
            location_section_list.insert(tk.END, location)
        location_section_list.pack(expand=True, fill="both")


        window.mainloop()
    # window.mainloop()
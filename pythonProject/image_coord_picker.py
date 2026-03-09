import os
from operator import index
from typing import Any, Dict, List, Literal, Optional, Tuple

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
canvas_img_id = 0
def create_frame(window_ref:Any,
                 name:str,
                 row_config:Optional[List[Tuple[int, int]]] | None = None,
                 column_config:Optional[List[Tuple[int,int]]] | None = None,
                 position:Optional[Tuple[int, int] | None] = None,
                 sticky_direction:str="nswe"):
    '''
    :param window_ref: reference to the created tk.TK() window
    :param position: position of the frame. (row, column)
    :param sticky_direction: direction of what way the frame should stick to when outer widget is bigger than frame.
    :param row_config: row config for expansion-weight for each row. List[(<index of row>,<weight>), ...]
    :param column_config: column config for expansion-weight for each column. List[(<index of column>,<weight>), ...]
    '''
    
    frame = tk.Frame(window_ref, )
    if name:
        frame.name = name
    if position:
        frame.grid(row=position[0], column=position[1], sticky=sticky_direction)
    if row_config:
        for config in row_config:
            frame.rowconfigure(config[0], weight=config[1])
    if column_config:
        for config in column_config:
            frame.columnconfigure(config[0], weight=config[1])
    return frame

def create_scrollbar(widget_ref:Any, position:Optional[Tuple[int, int] | None] = None,
                     orientation:Literal["vertical", "horizontal"]="vertical", 
                     sticky_direction:str="nswe"):
    scrollbar = tk.Scrollbar(widget_ref, orient=orientation)
    if position:
        scrollbar.grid_configure(row=position[0], column=position[1], sticky=sticky_direction)
    return scrollbar

def create_button(widget_ref:Any , text:str, command_ref:Any , position:Optional[Tuple[int, int] | None] = None,
                  sticky_direction:str="nswe"):
    '''
    :param widget_ref reference to the created tk.TK() window
    :param text
    :param position: position of the frame. (row, column)
    :param command_ref: function the button should call when clicked
    :param sticky_direction: direction of what way the frame should stick to when outer widget is bigger than frame.
    '''
    btn = tk.Button(widget_ref, text=text, command=command_ref)
    if position:
        btn.grid_configure(row=position[0], column=position[1], padx=5, pady=5, sticky=sticky_direction)
    return btn

def create_listbox(widget_ref:Any , name, position:Optional[Tuple[int, int] | None] = None, sticky_direction:str="nswe"):
    '''
    :param widget_ref reference to the created tk.TK() window
    :param name
    :param position: position of the frame. (row, column)
    :param sticky_direction: direction of what way the frame should stick to when outer widget is bigger than frame.
    '''
    
    listbox = tk.Listbox(widget_ref , name=name)
    if position:
        listbox.grid_configure(row=position[0], column=position[1], sticky=sticky_direction)
    return listbox

def create_canvas(widget_ref, name:str, img_ref, anchor:str):
    canvas = tk.Canvas(widget_ref, name=name, width=img_ref.width(), height=img_ref.height())
    canvas_img_id = canvas.create_image(500, 550, image=img_ref, anchor=anchor)
    canvas.image = img_ref
    return canvas, canvas_img_id

def create_label(widget_ref:Any, text:str, position:Optional[Tuple[int, int] | None] = None, sticky_direction:str="nswe"):
    label = tk.Label(widget_ref, text=text)
    if position:
        label.grid_configure(row=position[0], column=position[1], sticky=sticky_direction)
    return label

def create_combobox(widget_ref, state:str, value_list:List[str], default:str, name:str):
    combobox = ttk.Combobox(
        widget_ref,
        state=state,
        values=value_list
    )
    if name:
        combobox.name = name
    default_index = 0
    try:
        default_index = combobox["values"].index(default)
    except ValueError:
        pass
    combobox.set(combobox["values"][default_index])
    combobox.pack(pady=10, padx=10)
    return combobox

def combine_scrollbar_with_widget(scrollbar_ref:Any , widget_ref:Any , scrollbar_command_ref:Any, 
                                  widget_command_ref:Any, widget_command_direction:str):
    scrollbar_ref.config(command=scrollbar_command_ref)
    widget_ref.config(**{widget_command_direction: widget_command_ref})
    
    
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


# def load_already_present_data(new_data, canvas):
#     for location in new_data.keys():
#         canvas.delete(new_data[location][1])
#         canvas.delete(new_data[location][2])
#         new_data[location][1] = canvas.create_rectangle(
#             (new_data[location][0]["x"]*scaling_factor) - 5,
#             (new_data[location][0]["y"]*scaling_factor) - 5,
#             (new_data[location][0]["x"]*scaling_factor) + 5,
#             (new_data[location][0]["y"]*scaling_factor) + 5,
#             fill="red"
#         )
#         new_data[location][2] = canvas.create_text(
#             new_data[location][0]["x"]*scaling_factor,
#             new_data[location][0]["y"]*scaling_factor,
#             text=(
#                 f"x:{new_data[location][0]['x']}, y: {new_data[location][0]['y']}\n"
#                 f"{new_data[location][0]['map']},\n"
#                 f"shape:{new_data[location][0]['shape']}\n"
#                 f"size:{new_data[location][0]['size']}"
#             )
#         )
#     return new_data

# def zoom_in(event):
#     # Increase the image size by a factor (e.g., 1.2)
#     image = image.resize((int(image.width * 1.2), int(image.height * 1.2)), Image.ANTIALIAS)
#     tk_image = ImageTk.PhotoImage(image)
#     canvas.delete("all")
#     canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
#
#
# def zoom_out(event):
#     # Decrease the image size by a factor (e.g., 0.8)
#     image = image.resize((int(image.width * 0.8), int(image.height * 0.8)), Image.ANTIALIAS)
#     tk_image = ImageTk.PhotoImage(image)
#     canvas.delete("all")
#     canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)

def load_new_base_image(img_path:str=""):
    global og_img_size, og_img_width, og_img_height, image, copy_of_image
    # canvas.delete(canvas_img_id)
    new_img_path = img_path
    if img_path == "":
        new_img_path = filedialog.askopenfilename()
    image = Image.open(fr"{new_img_path}")
    og_img_size = image.size
    og_img_width = og_img_size[0] if og_img_size[0] < 1000 else 1000
    og_img_height = og_img_size[1] if og_img_size[1] < 700 else 700
    copy_of_image = image.copy()
    if img_path == "":
        window.geometry(f"{og_img_width}x{og_img_height}")
        # window.event_generate(sequence="<Configure>", height=og_img_height, width=og_img_width)
    #     event.widget.event_generate(sequence="<Configure>", width=500, height=500)
        # return resize_image(canvas.event_generate(sequence="<Configure>>", width=500, height=500))
    return ImageTk.PhotoImage(image=image, name="map image")


def save_new_base_image():
    pass


def resize_image(event):
    if event.width < 10 or event.height < 10:
        return
    print("start run resize image")
    # canvas = event.widget()
    global image, scaling_factor, canvas_img_id, new_data
    # new_data = {}
    if event.width / og_img_width < event.height / og_img_height:
        scaling_factor = event.width / og_img_width
    else:
        scaling_factor = event.height / og_img_height

    new_width = round(og_img_width * scaling_factor)
    new_height = round(og_img_height * scaling_factor)


    image = copy_of_image.resize((new_width, new_height))
    photo = ImageTk.PhotoImage(image)

    canvas = get_entity(tk.Canvas, "map image canvas")

    if isinstance(canvas, tk.Canvas):
        canvas.delete(canvas_img_id)
        # for id in rectangle_id:
        #     canvas.delete(id)
        # rectangle_id.clear()
        canvas_img_id = canvas.create_image(0, 0, image=photo, anchor="nw")

        canvas.image = photo  # avoid garbage collection
        # load_already_present_data(new_data, canvas)
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

    print("end run resize image")

def get_entity(entity_type:Any, name:str):
    canvas_found = False
    for children in window.winfo_children():
        if canvas_found:
            break
        for child in children.winfo_children():
            if isinstance(child, entity_type):
                entity = child
                canvas_found = True
                break
    return entity or None


def place_location(event):
    print("clicked at", event.x, event.y)
    print("scaling factor", scaling_factor)
    print("actual image coords", event.x//scaling_factor, event.y//scaling_factor)
    canvas = get_entity(tk.Canvas, "map image canvas")
    shape_selection = get_entity(ttk.Combobox, "shape_selection")
    size_selection = get_entity(ttk.Combobox, "size_selection")
    if isinstance(canvas, tk.Canvas) and isinstance(shape_selection, ttk.Combobox) and isinstance(size_selection, ttk.Combobox):
        if frame_location_selection.focus_get().selection_get() in new_data.keys():
            canvas.delete(new_data[frame_location_selection.focus_get().selection_get()][1])
            canvas.delete(new_data[frame_location_selection.focus_get().selection_get()][2])
        canvas.pack()
        shape_id = canvas.create_rectangle(event.x - 5, event.y - 5, event.x + 5, event.y + 5, fill="red")
        text_id = canvas.create_text(event.x, event.y, text=(
            f"x:{event.x // scaling_factor}, y: {event.y // scaling_factor}\n"
            f"location name: {frame_location_selection.focus_get().selection_get()},\n"
            f"shape:{shape_selection['values'][shape_selection.current()]}\n"
            f"size:{size_selection['values'][size_selection.current()]}")
                                     )
        new_data[frame_location_selection.focus_get().selection_get()] = [
            build_map_dict(
                x = int(event.x//scaling_factor),
                y = int(event.y//scaling_factor),
                map_name = map_json_selected,
                size = size_selection['values'][size_selection.current()],
                shape = shape_selection['values'][shape_selection.current()],
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

def traverse_json(region, path, location_list, canvas_ref):
    new_path = f"{path}/{region['name']}"
    if "sections" in region.keys():
        location_list.append(new_path[1:])
        # return
    if "children" in region.keys():
        for child in region["children"]:
            traverse_json(child, new_path, location_list, canvas_ref)
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
                    canvas_ref.create_rectangle(
                        (map["x"]*scaling_factor) - 5,
                        (map["y"]*scaling_factor) - 5,
                        (map["x"]*scaling_factor) + 5,
                        (map["y"]*scaling_factor) + 5,
                        fill="red"
                    ),
                    canvas_ref.create_text(
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

def load_list_of_maps(window_list_of_maps, maps_path):
    for map_json in json.load(open(maps_path)):
        map_list[map_json["name"]] = f'{base_path}/{map_json["img"]}'
        window_list_of_maps.insert(tk.END, map_json["name"])

    # select locations json to tp apply the images coords to
    locations_files = os.listdir(f'{base_path}/locations')

def load_list_of_locations(window_list_of_locations, locations_dir):
    # print(locations_files)
    for location in os.listdir(locations_dir):
        # print(location)
        window_list_of_locations.insert(tk.END, location)


def start_selection_screen(window_red:Any, base_path:str, map_list):
    window.columnconfigure([0, 1, 2], weight=1)
    window.rowconfigure(0, weight=1)

    frame_map_selection = create_frame(window_ref=window, name="map_selection", position=(0, 1),
                                       row_config=[(0, 0), (1, 2), (2, 0)], column_config=[(0, 1)],
                                       sticky_direction="nsew")
    frame_location_selection = create_frame(window_ref=window, name="location_selection", position=(0, 0),
                                            row_config=[(0, 0), (1, 2), (2, 0)], column_config=[(0, 1)],
                                            sticky_direction="nsew")

    # Maps side
    scrollbar_maps = create_scrollbar(frame_map_selection, orientation="vertical", position=(1, 1),
                                      sticky_direction="ns")
    window_list_of_maps = create_listbox(frame_map_selection, name="maps", position=(1, 0),
                                         sticky_direction="nsew")
    # location side
    scrollbar_locations = create_scrollbar(frame_location_selection, orientation="vertical", position=(1, 1),
                                           sticky_direction="ns")
    window_list_of_locations = create_listbox(frame_location_selection, name="json", position=(1, 0),
                                              sticky_direction="nsew")


    combine_scrollbar_with_widget(scrollbar_maps, window_list_of_maps,
                                  scrollbar_command_ref=window_list_of_maps.yview,
                                  widget_command_ref=scrollbar_maps.set,
                                  widget_command_direction="yscrollcommand")

    combine_scrollbar_with_widget(scrollbar_ref=scrollbar_locations,
                                  widget_ref=window_list_of_locations,
                                  scrollbar_command_ref=window_list_of_locations.yview,
                                  widget_command_ref=scrollbar_locations.set,
                                  widget_command_direction="yscrollcommand"
                                  )

    header_maps = create_label(frame_map_selection, text="Select a map", position=(0, 0), sticky_direction="ew")
    btn_map = create_button(frame_map_selection, text='Select Map', command_ref=dialog, position=(2, 0),
                            sticky_direction="ew")

    header_locations = create_label(frame_location_selection, text="Select location source", position=(0, 0),
                                    sticky_direction="ew")
    btn_locations = create_button(frame_location_selection, text='select JSON', command_ref=dialog, position=(2, 0),
                                  sticky_direction="ew")
    # select image to open
    # map_list = {}
    # json_maps = json.load(open(f"{base_path}/maps/maps.json"))
    load_list_of_maps(window_list_of_maps, f"{base_path}/maps/maps.json")
    # for map_json in json_maps:
    #     map_list[map_json["name"]] = f'{base_path}/{map_json["img"]}'
    #     window_list_of_maps.insert(tk.END, map_json["name"])

    # select locations json to tp apply the images coords to
    # locations_files = os.listdir(f'{base_path}/locations')
    load_list_of_locations(window_list_of_locations, f'{base_path}/locations')
    # # print(locations_files)
    # for location in locations_files:
    #     # print(location)
    #     window_list_of_locations.insert(tk.END, location)

    # window.deiconify()
    # window.mainloop()
    return frame_map_selection, frame_location_selection, window_list_of_locations


def start_edit_screen(window_ref:Any, base_path:str, map_list, selected_map, selected_location,
                      location_section_json, location_list):
    map_name = selected_map
    img = load_new_base_image(img_path=map_list[map_json_selected])
    # map_image_path = map_list[map_json_selected]
    # locations_json = json.load(open(f"{base_path}/locations/{map_json_selected}"))
    # for map_name, map_image_path in map_list:
    # print(map_name, map_image_path)

    window.columnconfigure(0, weight=1, minsize=200)
    window.columnconfigure(1, weight=5)
    window.columnconfigure(2, weight=0)

    frame_location_selection = create_frame(window, name="location_selection", position=(0, 0), sticky_direction="nsew")

    frame_map_image = create_frame(window, name="map_image", position=(0, 1), sticky_direction="nsew")

    frame_settings = create_frame(window, name="settings", position=(0, 2), sticky_direction="nsew")

    # settings
    shape_selection = create_combobox(frame_settings, state="readonly",
                                      value_list=["rect", "diamond", "trapezoid"], default="rect", name="shape_selection")

    size_selection = create_combobox(frame_settings, state="readonly",
                                     value_list=[str(i) for i in range(10, 41, 2)], default="10", name="size_selection")

    save_new_button = create_button(frame_settings, text="Save to new file", command_ref=save_to_new_file)
    # save_old_button = create_button(frame_settings,text="Overwrite existing file",command_ref=save_to_old_file)
    load_new_image_button = create_button(frame_settings, text="Load new BaseImage", command_ref=save_to_new_file)
    save_new_button.pack()
    # save_old_button.pack()
    load_new_image_button.pack()
    # save_old_button = tk.Button(frame_settings, text="Overwrite existing file", command=save_to_old_file)
    # save_old_button.pack()

    # load_new_image_button = tk.Button(
    #     frame_settings,
    #     text="Load new BaseImage",
    #     command=load_new_base_image
    # )
    # load_new_image_button.bind("<Button-1>", load_new_base_image)
    # load_new_image_button.pack(pady=10, padx=10)

    # save_new_image_button = tk.Button(
    #     frame_settings,
    #     text="Save new BaseImage",
    #     command=save_new_base_image
    # )
    # save_new_image_button.bind("<Button-1>", save_new_base_image)
    # save_new_image_button.pack(pady=10, padx=10)

    # ttk.Sizegrip(frame_settings)
    # menu_shape.pack()
    # img = cv2.imread(map_image_path)

    # image to display
    # image = Image.open(fr"{map_image_path}")
    # og_img_size = image.size
    # og_img_width = og_img_size[0]
    # og_img_height = og_img_size[1]
    # copy_of_image = image.copy()
    # img = ImageTk.PhotoImage(image=image, name="map image")

    canvas, canvas_img_id = create_canvas(frame_map_image, name="map image canvas", img_ref=img, anchor="nw")
    # canvas = tk.Canvas(frame_map_image, name="map image test", width=img.width(), height=img.height())
    # canvas_img_id = canvas.create_image(500, 550, image=img, anchor="nw")
    # canvas.image = img

    location_section_json = json.load(open(f'{base_path}/locations/{locations_json_selected}'))
    for region in location_section_json:
        path = ""
        print(region["name"])
        traverse_json(region, path, location_list, canvas)

    # window.resizable(True, True)
    # canvas = tk.Canvas(frame_map_image, name="map image test", width=img.width(), height=img.height())

    canvas.pack(expand=True, fill="both")
    # canvas.pack(expand=True, fill="both")
    canvas.bind("<Configure>", resize_image)
    # canvas.bind("<Button-1>", callback)
    # canvas.bind("<Button-4>", zoom_in)
    # canvas.bind("<Button-5>", zoom_out)
    # canvas.bind("<MouseWheel>", resize_image)
    # canvas.bind("<B1-Motion>", callback)
    canvas.bind("<ButtonRelease-1>", place_location)

    # btn_map = tk.Button(frame, text='Select Location', command=select_location)
    scrollbar_location_section_y = tk.Scrollbar(frame_location_selection, orient="vertical")
    location_section_list = tk.Listbox(frame_location_selection, name="locations",
                                       yscrollcommand=scrollbar_location_section_y.set)  # , exportselection=False)
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


if __name__ == "__main__":
    locations_json_selected=""
    map_json_selected=""
    map_list = {}



    window = tk.Tk()
    window.withdraw()

    window.columnconfigure([0,1,2],  weight=1)
    window.rowconfigure(0, weight=1)

    base_path = tk.filedialog.askdirectory()

    frame_map_selection, frame_location_selection, window_list_of_locations = start_selection_screen(window, base_path, map_list)
    window.deiconify()
    window.mainloop()


    # print(window)
    # frame_map_selection = window.children.get("map_selection")
    # frame_location_selection = window.children.get("location_selection")

    frame_map_selection.destroy()
    frame_location_selection.destroy()
    # frame_map_selection.grid_forget()
    # frame_location_selection.grid_forget()


    print(map_json_selected, locations_json_selected)
    if not map_json_selected == "" and not locations_json_selected == "":
        location_section_json = {}
        location_list = []
        start_edit_screen(window, base_path, map_list, map_json_selected, locations_json_selected,
                          location_section_json, location_list)



        window.mainloop()
    print("etest")
    # window.mainloop()
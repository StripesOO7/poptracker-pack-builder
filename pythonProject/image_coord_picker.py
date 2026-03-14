import os
import shutil
from typing import Any, List, Literal, Optional, Tuple

from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, ttk
import json


coords = (0, 0)
locations_json_selected = ""
map_json_selected = ""
og_img_size = (0, 0)
scaling_factor = 1
og_img_width = og_img_size[0]
og_img_height = og_img_size[1]
new_data = {}
rectangle_id = []
canvas_img_id = 0
loop = True
selected_file_path = ""
new_map_window = None


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
        frame.grid_configure(row=position[0], column=position[1])
    if sticky_direction:
        frame.grid_configure(sticky=sticky_direction)
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
        scrollbar.grid_configure(row=position[0], column=position[1])
    if sticky_direction:
        scrollbar.grid_configure(sticky=sticky_direction)
    # else:
    #     scrollbar.pack()
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
        btn.grid_configure(row=position[0], column=position[1], padx=5, pady=5)
    if sticky_direction:
        btn.grid_configure(sticky=sticky_direction)
    # else:
    #     btn.pack()
    # btn.pack(pady=10, padx=10)
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
    # else:
    #     listbox.pack()
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
    if sticky_direction:
        label.grid_configure(sticky=sticky_direction)
    # else:
    #     label.pack()
    return label

def create_combobox(widget_ref, state:str, value_list:List[str], default:str, name:str,
                    position:Optional[Tuple[int, int] | None] = None, sticky_direction:str="nswe"):
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
    if position:
        combobox.grid_configure(row=position[0], column=position[1], sticky=sticky_direction)
    if sticky_direction:
        combobox.grid_configure(sticky=sticky_direction)
    combobox.set(combobox["values"][default_index])
    # combobox.pack(pady=10, padx=10)
    return combobox

def create_input_field(widget_ref, name:str,
                       position:Optional[Tuple[int, int] | None] = None,
                       sticky_direction:str="nswe"):
    input_field = tk.Entry(widget_ref, name=name)
    if position:
        input_field.grid_configure(row=position[0], column=position[1])
    if sticky_direction:
        input_field.grid_configure(sticky=sticky_direction)
    if name:
        input_field.name = name
    return input_field


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


def go_back_to_selection():
    global locations_json_selected, map_json_selected, new_data
    map_json_selected = ""
    locations_json_selected = ""
    new_data = {}

    for child in window.winfo_children():
        child.destroy()
    window.quit()

def exit_loop():
    global loop
    loop=False
    window.quit()

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
    global new_data
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
def draw_rectangle(canvas_ref: Any, x: int, y: int, scaling_factor: float|int, fill_color: str, size:int):
    size_offset = round(size/2)
    adjusted_x = x * scaling_factor
    adjusted_y = y * scaling_factor
    adjusted_offset = size_offset * scaling_factor
    return canvas_ref.create_polygon(
        adjusted_x - adjusted_offset, adjusted_y - adjusted_offset,
        adjusted_x + adjusted_offset, adjusted_y - adjusted_offset,
        adjusted_x + adjusted_offset, adjusted_y + adjusted_offset,
        adjusted_x - adjusted_offset, adjusted_y + adjusted_offset,
        fill="red",
    )

def draw_diamond(canvas_ref:Any, x:int, y:int, scaling_factor:float|int, fill_color:str, size:int):
    size_offset = round(size / 2)
    adjusted_x = x * scaling_factor
    adjusted_y = y * scaling_factor
    adjusted_offset = size_offset * scaling_factor
    return canvas_ref.create_polygon(
        adjusted_x - adjusted_offset , adjusted_y,
        adjusted_x, adjusted_y - adjusted_offset ,
        adjusted_x + adjusted_offset , adjusted_y,
        adjusted_x, adjusted_y + adjusted_offset ,
        fill="red",
    )

def draw_trapezoid(canvas_ref:Any, x:int, y:int, scaling_factor:float|int, fill_color:str, size:int):
    size_offset = round(size / 2)
    adjusted_x = x * scaling_factor
    adjusted_y = y * scaling_factor
    adjusted_offset = size_offset * scaling_factor
    return canvas_ref.create_polygon(
        adjusted_x - round(adjusted_offset/2), adjusted_y - adjusted_offset,
        adjusted_x + round(adjusted_offset/2), adjusted_y - adjusted_offset,
        adjusted_x + adjusted_offset, adjusted_y + adjusted_offset,
        adjusted_x - adjusted_offset, adjusted_y + adjusted_offset,
        fill="red",
    )


def draw_shape_and_text(widget_ref:Any, location_dataset:dict[str, Any], shape: str, scaling_factor:float|int,
                       location_path:str, selected_size:int, textcolor:str="black") -> Tuple[int, int]:
    assert isinstance(widget_ref, tk.Canvas)
    match shape:
        case "rect":
            rect_id = draw_rectangle(canvas_ref=widget_ref, x=location_dataset["x"], y=location_dataset["y"],
                             scaling_factor=scaling_factor, size=selected_size, fill_color="red")
        case "diamond":
            rect_id = draw_diamond(canvas_ref=widget_ref, x=location_dataset["x"], y=location_dataset["y"],
                                     scaling_factor=scaling_factor, size=selected_size, fill_color="red")
        case "trapezoid":
            rect_id = draw_trapezoid(canvas_ref=widget_ref, x=location_dataset["x"], y=location_dataset["y"],
                                     scaling_factor=scaling_factor, size=selected_size, fill_color="red")
        case _:
            rect_id = draw_rectangle(canvas_ref=widget_ref, x=location_dataset["x"], y=location_dataset["y"],
                                     scaling_factor=scaling_factor, size=selected_size, fill_color="red")
    text_id = widget_ref.create_text(
        location_dataset["x"] * scaling_factor,
        location_dataset["y"] * scaling_factor,
        fill=textcolor,
        font=("Purisa", 10),
        width=200,
        text=(
            f"x:{location_dataset['x']}, y: {location_dataset['y']}\n"
            f"location name: {location_path[1 if location_path[0] == '/' else 0:]},\n"
            f"shape:{location_dataset['size'] if 'size' in location_dataset.keys() else 10}\n"
            f"size:{location_dataset['shape'] if 'shape' in location_dataset.keys() else 'rect'}"
        ),
        # anchor="nw",
    )
    return rect_id, text_id

def load_new_base_image(window_ref:Any, img_path:str=""):
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
        window_ref.geometry(f"{og_img_width}x{og_img_height}")
        # window_ref.event_generate(sequence="<Configure>", height=og_img_height, width=og_img_width)
    #     event.widget.event_generate(sequence="<Configure>", width=500, height=500)
        # return resize_image(canvas.event_generate(sequence="<Configure>>", width=500, height=500))
    return ImageTk.PhotoImage(image=image, name="map image")


def save_new_base_image():
    pass


def resize_image(event):
    if event.width < 10 or event.height < 10:
        return
    # print("start run resize image")
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

    canvas, _ = get_entity(window, tk.Canvas, "map image canvas")

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
            del new_data[location][2]
            del new_data[location][1]
            new_data[location].extend(draw_shape_and_text(
                    widget_ref=canvas,
                    location_dataset=new_data[location][0],
                    shape=new_data[location][0]["shape"],
                    selected_size=new_data[location][0]["size"],
                    scaling_factor=scaling_factor,
                    location_path=location,
                    textcolor="black"
                )
            )
            # new_data[location][1] = canvas.create_rectangle(
            #     (new_data[location][0]["x"]*scaling_factor) - 5,
            #     (new_data[location][0]["y"]*scaling_factor) - 5,
            #     (new_data[location][0]["x"]*scaling_factor) + 5,
            #     (new_data[location][0]["y"]*scaling_factor) + 5,
            #     fill="red"
            # )
            # new_data[location][2] = canvas.create_text(
            #     new_data[location][0]["x"]*scaling_factor,
            #     new_data[location][0]["y"]*scaling_factor,
            #     text=(
            #         f"x:{new_data[location][0]['x']}, y: {new_data[location][0]['y']}\n"
            #         f"{new_data[location][0]['map']},\n"
            #         f"shape:{new_data[location][0]['shape']}\n"
            #         f"size:{new_data[location][0]['size']}"
            #     )
            # )

    # print("end run resize image")

def get_entity(widget_ref:Any, entity_type:Any, name:str):
    entity_found = False
    entity = None
    for child in widget_ref.winfo_children():
        if entity_found:
            break
        if isinstance(child, entity_type):
            for key in ("name", "_name"):
                try:
                    value = getattr(child, key)
                    if value == name:
                        entity = child
                        entity_found = True
                        break
                    else:
                        continue
                # except NameError as e:
                #     # print(e)
                #     continue
                except AttributeError as e:
                    # print(e)
                    continue
        elif len(child.winfo_children()) > 0:
            entity, entity_found = get_entity(child, entity_type, name)
            if entity_found:
                break
        else:
            continue
    return entity, entity_found


def restore_default_markings():
    base_json = json.load(open(f'{base_path}/locations/{locations_json_selected}'))
    canvas, _ = get_entity(window, tk.Canvas, "map image canvas")

    placed_locations_list, _ = get_entity(window, tk.Listbox, "placed_locations")
    unplaced_locations_list, _ = get_entity(window, tk.Listbox, "unplaced_locations")
    assert isinstance(placed_locations_list, tk.Listbox), "placed_locations is not of type tk.Listbox"
    assert isinstance(unplaced_locations_list, tk.Listbox), "unplaced_locations is not of type tk.Listbox"

    for nodes in new_data.keys():
        canvas.delete(new_data[nodes][1])
        canvas.delete(new_data[nodes][2])

    new_data.clear()
    location_list.clear()
    for region in base_json:
        path = ""
        print(region["name"])
        traverse_json(region, path, location_list, canvas)
    placed_locations_list.delete(0, tk.END)
    unplaced_locations_list.delete(0, tk.END)
    print("pause")
    for location in location_list:
        if location["placed"]:
            placed_locations_list.insert(tk.END, location["location"])
        else:
            unplaced_locations_list.insert(tk.END, location["location"])
    pass


def place_location(event):
    print("clicked at", event.x, event.y)
    print("scaling factor", scaling_factor)
    print("actual image coords", event.x//scaling_factor, event.y//scaling_factor)

    canvas, _ = get_entity(window, tk.Canvas, "map image canvas")
    shape_selection, _ = get_entity(window, ttk.Combobox, "shape_selection")
    size_selection, _ = get_entity(window, ttk.Combobox, "size_selection")

    # if event.widget.master.name ==
    unplaced_locations, _ = get_entity(window, tk.Listbox, "unplaced_locations")
    placed_locations, _ = get_entity(window, tk.Listbox, "placed_locations")

    assert isinstance(canvas, tk.Canvas), "canvas is not of type tk.Canvas"
    assert isinstance(shape_selection, ttk.Combobox), "shape_selection is not of type ttk.Combobox"
    assert isinstance(size_selection, ttk.Combobox), "size_selection is not of type ttk.Combobox"
    assert isinstance(unplaced_locations, tk.Listbox), "unplaced_locations is not of type tk.Listbox"
    assert isinstance(placed_locations, tk.Listbox), "placed_locations is not of type tk.Listbox"
    if len(unplaced_locations.curselection()) > 0:
        selected_unplaced_location = unplaced_locations.get(unplaced_locations.curselection()[0])
    else:
        selected_unplaced_location = None
    if len(placed_locations.curselection()) > 0 :
        selected_placed_location = placed_locations.get(placed_locations.curselection()[0])
    else:
        selected_placed_location = None
    # selected_placed_location = placed_locations.get(placed_locations.curselection())

    selected_location = selected_unplaced_location or selected_placed_location or ""


    if selected_location in new_data.keys():
        canvas.delete(new_data[selected_location][1])
        canvas.delete(new_data[selected_location][2])
    else:
        if selected_location in unplaced_locations.get(0, tk.END):
            move_from_to(from_list=unplaced_locations,
                         to_list=placed_locations,
                         selected_item_list=unplaced_locations.curselection(),
                         selected_object=unplaced_locations, )
        unplaced_locations.selection_clear(0, tk.END)
        placed_locations.selection_clear(0, tk.END)
        placed_locations.selection_set(tk.END)
    # canvas.pack()
    # shape_id = canvas.create_rectangle(event.x - 5, event.y - 5, event.x + 5, event.y + 5, fill="red")
    # text_id = canvas.create_text(event.x, event.y, text=(
    #     f"x:{event.x // scaling_factor}, y: {event.y // scaling_factor}\n"
    #     f"location name: {selected_location},\n"
    #     f"shape:{shape_selection['values'][shape_selection.current()]}\n"
    #     f"size:{size_selection['values'][size_selection.current()]}")
    #                              )
    new_data[selected_location] = [
        build_map_dict(
            x=int(event.x//scaling_factor),
            y=int(event.y//scaling_factor),
            map_name=map_json_selected,
            size=size_selection['values'][size_selection.current()],
            shape=shape_selection['values'][shape_selection.current()],
        )
    ]
    new_data[selected_location].extend(draw_shape_and_text(
            widget_ref=canvas,
            location_path=selected_location,
            location_dataset=new_data[selected_location][0],
            shape=new_data[selected_location][0]["shape"],
            selected_size=new_data[selected_location][0]["size"],
            scaling_factor=scaling_factor,
            textcolor="black"
        )
    )
    # print(new_data)

# def unfocus(event):
#     placed_locations_selection, _ = get_entity(event.widget.master, tk.Listbox, "placed_locations")
#     unplaced_locations_selection, _ = get_entity(event.widget.master, tk.Listbox, "unplaced_locations")
#     assert isinstance(placed_locations_selection, tk.Listbox)
#     assert isinstance(unplaced_locations_selection, tk.Listbox)
#     try:
#         print(event.widget.master.__getattribute__("name"))
#         print(window.focus_get().__getattribute__("name"))
#     except:
#         print(event.widget.master.__getattribute__("_name"))
#         print(window.focus_get().__getattribute__("_name"))
#     if placed_locations_selection == window.focus_get():
#         for selection in unplaced_locations_selection.curselection():
#             unplaced_locations_selection.selection_clear(selection)
#     elif unplaced_locations_selection == window.focus_get():
#         for selection in placed_locations_selection.curselection():
#             placed_locations_selection.selection_clear(selection)
#     else:
#         pass


def move_from_to(from_list, to_list, selected_item_list=None, selected_object=None):
    if selected_object is None:
        return
    if selected_item_list is None:
        selected_item_list = selected_object.curselection()[0]
    for item_index in selected_item_list:
        to_list.insert(tk.END, from_list.get(item_index))
        from_list.delete(item_index)

        # to_list.insert(tk.END, selected_object.get(item_index))

def remove_placed_location(event):
    target_frame_location_selection = event.widget.master
    # target_frame_location_selection, _ = get_entity(window, tk.Frame, "location_selection")
    assert isinstance(target_frame_location_selection, tk.Frame), \
        "target_frame_location_selection is not of type tk.Frame"

    placed_locations_list, _ = get_entity(target_frame_location_selection, tk.Listbox, "placed_locations")
    unplaced_locations_list, _ = get_entity(target_frame_location_selection, tk.Listbox, "unplaced_locations")
    assert isinstance(placed_locations_list,  tk.Listbox), "placed_locations is not of type tk.Listbox"
    assert isinstance(unplaced_locations_list,  tk.Listbox), "unplaced_locations is not of type tk.Listbox"
    assert len(placed_locations_list.curselection()) > 0, "nothing selected"

    canvas, _ = get_entity(window, tk.Canvas, "map image canvas")
    assert isinstance(canvas, tk.Canvas), "canvas is not of type tk.Canvas"

    for item in placed_locations_list.curselection():
        selected_location = placed_locations_list.get(item)
        if selected_location in new_data.keys():
            canvas.delete(new_data[selected_location][1])
            canvas.delete(new_data[selected_location][2])
            del new_data[selected_location]

    move_from_to(from_list=placed_locations_list,
                 to_list=unplaced_locations_list,
                 selected_item_list=placed_locations_list.curselection(),
                 selected_object=placed_locations_list)
    pass

def choose_file_path():
    global selected_file_path
    selected_file_path = filedialog.askopenfilename()

def write_new_map_json_entry():
    global selected_file_path
    name = ""
    filename = ""
    if new_map_window is None:
        map_selected, _ = get_entity(widget_ref=window, entity_type=tk.Listbox, name="list_of_maps")
        assert isinstance(map_selected, tk.Listbox), "name_selected is not of type tk.Listbox"
        name_selection = map_selected.curselection()
        assert len(name_selection) > 0, "nothing selected"
        name = map_selected.get(name_selection[0])

    else:
        name_input, _ = get_entity(widget_ref=new_map_window, entity_type=tk.Entry, name="name input")
        assert isinstance(name_input, tk.Entry), "name_selected is not of type tk.Entry"
        name = name_input.get()
        if not selected_file_path == "":
            if not (base_path in selected_file_path):
                filename = os.path.basename(selected_file_path)
                shutil.copy(selected_file_path, fr"{base_path}/images/{filename}")
            filename = os.path.basename(selected_file_path)
        assert not filename == ""

    assert not name == ""

    with open(fr"{base_path}/maps/maps.json", "r+") as maps_json_file:
        tmp_dict = json.load(maps_json_file)
        maps_json_file.seek(0)
        maps_json_file.truncate()
        if new_map_window is None:
            for index, map_details in enumerate(tmp_dict):
                if map_details["name"] == name:
                    break
            del tmp_dict[index]
        else:
            tmp_dict.append(
                {
                    "name": name,
                    "img": f"images/{filename}",
                    "location_border_thickness": 1,
                    "location_size": 6,
                }
            )
        maps_json_file.write(json.dumps(tmp_dict))
    selected_file_path = ""
    if new_map_window is None:
        pass
    else:
        new_map_window.quit()

def reload_map_list():
    map_listbox, _ = get_entity(window, tk.Listbox, "list_of_maps")
    assert isinstance(map_listbox, tk.Listbox)

    map_listbox.delete(0, tk.END)
    load_list_of_maps(map_listbox, fr"{base_path}/maps/maps.json")

def remove_map():
    write_new_map_json_entry()
    reload_map_list()

def add_new_map():
    global new_map_window
    new_map_window = tk.Tk(baseName="map selection window")
    new_map_window.config(bg="yellow")
    new_map_window.geometry(f"{300}x{300}")
    text_input_frame = create_frame(window_ref=new_map_window, name="text input frame",
                                    position=(0, 0), sticky_direction="nsew")
    name_label = create_label(widget_ref=text_input_frame, text="Map Name", position=(0, 0), sticky_direction="ew")
    img_label = create_label(widget_ref=text_input_frame, text="Map Image", position=(1, 0), sticky_direction="ew")
    name_input = create_input_field(widget_ref=text_input_frame, name="name input", position=(0, 1), sticky_direction="nsew")
    select_image_btn = create_button(widget_ref=text_input_frame, text="Select image",
                                     command_ref=choose_file_path, position=(1, 1), sticky_direction="nsew")
    name_input.grid_configure(padx=5, pady=5)
    select_image_btn.grid_configure(padx=5, pady=5)
    # new_map_image_path = filedialog.askopenfilename()

    exit_text_input = create_button(widget_ref=new_map_window, text="exit new map selection",
                                    position=(2, 0), sticky_direction="nsew", command_ref=new_map_window.quit)

    save_map_addition = create_button(widget_ref=new_map_window, text="save new map",
                                      position=(3, 0), sticky_direction="nsew", command_ref=write_new_map_json_entry)

    new_map_window.mainloop()
    # tk.forget(new_map_window)
    try:
        new_map_window.destroy()
        new_map_window = None
        reload_map_list()

    except:
        pass

def update_coords(x, y):
    global coords
    coords = (x, y)


def dialog():
    global locations_json_selected, map_json_selected
    list_of_locations, _ = get_entity(window, tk.Listbox, "list_of_locations")
    list_of_maps, _ = get_entity(window, tk.Listbox, "list_of_maps")


    if isinstance(list_of_locations, tk.Listbox):
        locations_json_selected = list_of_locations.get((list_of_locations.curselection()))
    if isinstance(list_of_maps, tk.Listbox):
        map_json_selected = list_of_maps.get((list_of_maps.curselection()))

    if not locations_json_selected == "" and not map_json_selected == "":
        window.quit()
    # return messagebox.showinfo('Selection', 'Your Choice: ' + \
    # window.focus_get().selection_get())

def select_location():
    return window.focus_get().selection_get()

def traverse_json(region, path, location_list, canvas_ref):
    new_path = f"{path}/{region['name']}"
    selected_textcolor= "black"
    name_key = new_path[1:]
    if "sections" in region.keys():
        location_list.append(
            {
                "location": name_key,
                "placed": False,
            }
        )
        # return
    if "children" in region.keys():
        for child in region["children"]:
            traverse_json(child, new_path, location_list, canvas_ref)
    if "map_locations" in region.keys():
        for map in region["map_locations"]:
            if map["map"] == map_json_selected:
                new_data[name_key] = [
                    build_map_dict(
                        x=int(map['x']),
                        y=int(map['y']),
                        map_name=map['map'],
                        size=map['size'] if 'size' in map.keys() else 10,
                        shape=map['shape'] if 'shape' in map.keys() else 'rect',
                    )
                ]
                new_data[name_key].extend(draw_shape_and_text(
                        widget_ref=canvas_ref,
                        location_dataset=new_data[name_key][0],
                        shape=new_data[name_key][0]["shape"],
                        selected_size=new_data[name_key][0]["size"],
                        scaling_factor=scaling_factor,
                        location_path=new_path,
                        textcolor=selected_textcolor
                    )
                )
                location_list[-1]["placed"] = True
                print("placed as square")

def load_list_of_maps(window_list_of_maps, maps_path):
    tmp_map_list = {}
    with open(maps_path) as maps_file:
        for map_json in json.load(maps_file):
            tmp_map_list[map_json["name"]] = f'{base_path}/{map_json["img"]}'
    # map_list = (sorted(tmp_map_list.keys()))
    for key in sorted(tmp_map_list.keys()):
        map_list[key] = tmp_map_list[key]
    for map_name in map_list.keys():
        window_list_of_maps.insert(tk.END, map_name)

    # select locations json to tp apply the images coords to
    # locations_files = os.listdir(f'{base_path}/locations')

def load_list_of_locations(window_list_of_locations, locations_dir):
    # print(locations_files)
    tmp_list = sorted(os.listdir(locations_dir))
    # tmp_list = tmp_list.sort()
    for location in tmp_list:
        window_list_of_locations.insert(tk.END, location)


def start_selection_screen(window_ref:Any, base_path:str):
    window_ref.columnconfigure([0, 1], weight=1)
    window_ref.rowconfigure(0, weight=1)

    frame_map_selection = create_frame(window_ref=window_ref, name="map_selection", position=(0, 1),
                                       row_config=[(0, 0), (1, 2), (2, 0)], column_config=[(0, 1), (1, 0)],
                                       sticky_direction="nsew")
    frame_location_selection = create_frame(window_ref=window_ref, name="location_selection", position=(0, 0),
                                            row_config=[(0, 0), (1, 2), (2, 0)], column_config=[(0, 1), (1, 0)],
                                            sticky_direction="nsew")
    # Maps side
    scrollbar_maps = create_scrollbar(frame_map_selection, orientation="vertical", position=(1, 1),
                                      sticky_direction="ns")
    window_list_of_maps = create_listbox(frame_map_selection, name="list_of_maps", position=(1, 0),
                                         sticky_direction="nsew")
    # location side
    scrollbar_locations = create_scrollbar(frame_location_selection, orientation="vertical", position=(1, 1),
                                           sticky_direction="ns")
    window_list_of_locations = create_listbox(frame_location_selection, name="list_of_locations", position=(1, 0),
                                              sticky_direction="nsew")

    window_list_of_maps.configure(exportselection=False)
    window_list_of_locations.configure(exportselection=False)


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
    # btn_map = create_button(frame_map_selection, text='Go with selection', command_ref=dialog, position=(2, 0),
    #                         sticky_direction="ew")

    header_locations = create_label(frame_location_selection, text="Select location source", position=(0, 0),
                                    sticky_direction="ew")
    btn_locations = create_button(frame_location_selection, text='Go with selection', command_ref=dialog, position=(2, 0),
                                  sticky_direction="ew")


    map_subframe = create_frame(frame_map_selection, name="map_subframe", position=(2, 0), sticky_direction="w")
    create_new_map = create_button(map_subframe, text="Add new Map", command_ref=add_new_map,
                                   position=(0, 0), sticky_direction="ew")
    create_new_map = create_button(map_subframe, text="Remove selected Map", command_ref=remove_map,
                                   position=(0, 1), sticky_direction="ew")
    # create_new_map = create_button(frame_location_selection, text="Add new Map", command_ref=add_new_location,
    #                                position=(3, 0), sticky_direction="ew")
    button_frame = create_frame(window_ref=window_ref, name="button_space", position=(3, 0),
                                       sticky_direction="ew")
    exit_loop_button = create_button(button_frame, text="Exit", command_ref=exit_loop, sticky_direction="ew")
    exit_loop_button.grid(row=4, columnspan=2, sticky="ew", padx=5, pady=5)
    # select image to open
    # map_list = {}
    # json_maps = json.load(open(f"{base_path}/maps/maps.json"))
    load_list_of_maps(window_list_of_maps, fr"{base_path}/maps/maps.json")
    # for map_json in json_maps:
    #     map_list[map_json["name"]] = f'{base_path}/{map_json["img"]}'
    #     window_list_of_maps.insert(tk.END, map_json["name"])

    # select locations json to tp apply the images coords to
    # locations_files = os.listdir(f'{base_path}/locations')
    load_list_of_locations(window_list_of_locations, fr'{base_path}/locations')
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

    img = load_new_base_image(window_ref=window_ref, img_path=map_list[map_json_selected])
    # map_image_path = map_list[map_json_selected]
    # locations_json = json.load(open(f"{base_path}/locations/{map_json_selected}"))
    # for map_name, map_image_path in map_list:
    # print(map_name, map_image_path)

    window_ref.columnconfigure(0, weight=1)
    window_ref.columnconfigure(1, weight=5)
    window_ref.columnconfigure(2, weight=0)

    frame_location_selection = create_frame(window_ref, name="location_selection", position=(0, 0), sticky_direction="nsew",
                                            # row_config=[(0, 1), (1, 1)],
                                            column_config=[(0, 1), (1, 0)]
                                            )
    frame_map_image = create_frame(window_ref, name="map_image", position=(0, 1), sticky_direction="nsew")

    frame_settings = create_frame(window_ref, name="settings", position=(0, 2), sticky_direction="nsew")

    # settings
    shape_selection = create_combobox(frame_settings, state="readonly",
                                      value_list=["rect", "diamond", "trapezoid"], default="rect", name="shape_selection")

    size_selection = create_combobox(frame_settings, state="readonly",
                                     value_list=[str(i) for i in range(10, 41, 2)], default="10", name="size_selection")

    save_new_button = create_button(frame_settings, text="Save to new file",
                                    command_ref=save_to_new_file)
    # save_old_button = create_button(frame_settin text="Overwrite existing file",
    # command_ref=save_to_old_file)
    load_new_image_button = create_button(frame_settings, text="Load new BaseImage",
                                          command_ref=load_new_base_image)

    go_back_to_selection_button = create_button(frame_settings, text="Go back to selection",
                                           command_ref=go_back_to_selection)
    exit_loop_button = create_button(frame_settings, text="Exit", command_ref=exit_loop)
    restore_defaults_button = create_button(frame_settings, text="Restore Defaults",
                                           command_ref=restore_default_markings)
    for i, child in enumerate(frame_settings.winfo_children()):
        child.grid(row=i, column=0, pady=5)
        child.columnconfigure(0, weight=0)


    # save_new_button.pack()
    # save_old_button.pack()
    # load_new_image_button.pack()
    # go_back_to_selection_button.pack()
    # exit_loop_button.pack()


    frame_map_image.columnconfigure(0, weight=5, minsize=500)
    frame_map_image.rowconfigure(0, weight=5)
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
    canvas.grid(row=0, column=0, sticky="nsew")
    # canvas.pack(expand=True, fill="both")
    canvas.bind("<Configure>", resize_image)
    # canvas.bind("<MouseWheel>", restore_default_markings)
    # canvas.bind("<Button-4>", resize_image)
    # canvas.bind("<Button4>", resize_image)
    # canvas.bind("<MouseWheel>", resize_image)
    # canvas.bind("<Button3-Motion>", restore_default_markings)
    canvas.bind("<ButtonRelease-1>", place_location)


    unplaced_location_label = create_label(frame_location_selection, text="unplaced locations", position=(0, 0),
                                           sticky_direction="ew")
    scrollbar_unplaced_location_section_y = create_scrollbar(frame_location_selection, position=(1, 1) ,
                                            orientation="vertical", sticky_direction="ns")
    unplaced_location_section_list = create_listbox(frame_location_selection, position=(1, 0),
                                            name="unplaced_locations", sticky_direction="nsew")# ,
    # exportselection=False)
    unplaced_location_section_list.configure(exportselection=False, )
    combine_scrollbar_with_widget(scrollbar_unplaced_location_section_y,
                                  unplaced_location_section_list,
                                  unplaced_location_section_list.yview,
                                  widget_command_ref=scrollbar_unplaced_location_section_y.set,
                                  widget_command_direction="yscrollcommand")


    placed_location_label = create_label(frame_location_selection, text="placed locations", position=(2, 0),
                                         sticky_direction="ew")
    scrollbar_placed_location_section_y = create_scrollbar(frame_location_selection, position=(3, 1),
                                            orientation="vertical", sticky_direction="ns")
    placed_location_section_list = create_listbox(frame_location_selection, position=(3, 0),
                                            name="placed_locations", sticky_direction="nsew")  # ,
    # exportselection=False)
    placed_location_section_list.configure(exportselection=False)
    combine_scrollbar_with_widget(scrollbar_placed_location_section_y,
                                  placed_location_section_list,
                                  placed_location_section_list.yview,
                                  widget_command_ref=scrollbar_placed_location_section_y.set,
                                  widget_command_direction="yscrollcommand")

    # placed_location_section_list.bind("<FocusIn>", unfocus)
    # unplaced_location_section_list.bind("<FocusIn>", unfocus)
    # scrollbar_canvas_y = create_scrollbar(frame_map_image, position=(0, 1), orientation="vertical",
    #                                       sticky_direction="ns")
    # scrollbar_canvas_x = create_scrollbar(frame_map_image, position=(1, 0), orientation="horizontal",
    #                                       sticky_direction="ew")
    # btn_map = tk.Button(frame, text='Select Location', command=select_location)

    # scrollbar_canvas_y.config(command=canvas.yview)
    # scrollbar_canvas_x.config(command=canvas.xview)

    for location in location_list:
        if location["placed"]:
            placed_location_section_list.insert(tk.END, location["location"])
        else:
            unplaced_location_section_list.insert(tk.END, location["location"])
    # unplaced_location_section_list.grid(row=1, column=0, sticky="nsew")
    # placed_location_section_list.grid(row=3, column=0, sticky="nsew")

    # unplaced_location_section_list.bind("<Button-3>", unplaced_location_section_list.selection_clear(0, tk.END))
    placed_location_section_list.bind("<Button-3>", remove_placed_location)
    # unplaced_location_section_list.pack(expand=True, fill="both")


if __name__ == "__main__":
    locations_json_selected=""
    map_json_selected=""
    map_list = {}
    loop = True



    window = tk.Tk()
    window.withdraw()

    window.columnconfigure([0, 1],  weight=1)
    window.rowconfigure(0, weight=1)

    base_path = tk.filedialog.askdirectory()
    if base_path == "":
        exit()
    while loop:
        start_selection_screen(window, base_path)
        window.deiconify()
        window.geometry(f"{int(window.winfo_screenwidth()/1.4)}x{int(window.winfo_screenheight()/2)}")
        window.mainloop()

        frame_map_selection, _ = get_entity(window, tk.Frame, "map_selection")
        frame_location_selection, _ = get_entity(window, tk.Frame, "location_selection")
        window_list_of_locations, _ = get_entity(window, tk.Listbox, "list_of_locations")
        button_frame_ref, _ = get_entity(window, tk.Frame, "button_space")
        # print(window)
        # frame_map_selection = window.children.get("map_selection")
        # frame_location_selection = window.children.get("location_selection")
        assert isinstance(frame_map_selection, tk.Frame), "frame_map_selection not of type tk.Frame"
        assert isinstance(frame_location_selection, tk.Frame), "frame_location_selection not of type tk.Frame"
        assert isinstance(window_list_of_locations, tk.Listbox), "window_list_of_locations not of type tk.Listbox"
        assert isinstance(button_frame_ref, tk.Frame), "button_frame_ref not of type tk.Frame"
        frame_map_selection.destroy()
        frame_location_selection.destroy()
        button_frame_ref.destroy()
        # frame_map_selection.grid_forget()
        # frame_location_selection.grid_forget()


        print(map_json_selected, locations_json_selected)
        if not map_json_selected == "" and not locations_json_selected == "":
            location_section_json = {}
            location_list = []
            start_edit_screen(window, base_path, map_list, map_json_selected, locations_json_selected,
                              location_section_json, location_list)



            window.mainloop()
        # print("test")
    # window.mainloop()
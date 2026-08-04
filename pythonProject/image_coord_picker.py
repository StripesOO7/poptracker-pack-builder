import os
import shutil
from typing import Any, List, Literal, Optional, Tuple, Self
from enum import StrEnum, IntEnum

from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, ttk, Canvas, Frame
import json5

class ValidationException(Exception):
    pass

class Shape(StrEnum):
    RECT = "rect"
    DIAMOND = "diamond"
    TRAPEZOID = "trapezoid"

class MapPosition:
    """Handles a position on the map"""
    x: int
    y: int
    shape: Shape
    size: int
    border_thickness: int
    
    # Identifier for the related map
    map: str

    # List of Tk inter object IDs
    shapes: list[int]

    def __init__(self, map: str, x: int, y: int, size: int=10, shape: Shape=Shape.RECT):
        self.place(map, x, y, size, shape)

        self.shapes = []

    def __str__(self):
        return (
            f"x:{self.x}, y: {self.y}\n"
            f"shape:{self.shape}\n"
            f"size:{self.size}"
        )

    def is_placed_on(self, map: str):
        return self.map == map

    def place(self, map: str, x: int, y: int, size: int=10, shape: Shape=Shape.RECT):
        self.map = map
        self.x = x
        self.y = y
        self.size = size
        self.shape = shape

    def draw(self, section_name: str, map: str, canvas: Canvas, scale: float=1.0, text_color: str="black"):
        if self.map != map:
            # Not the correct map, skip rendering
            return
        
        method = draw_rectangle
        if self.shape is Shape.DIAMOND:
            method = draw_diamond
        elif self.shape is Shape.TRAPEZOID:
            method = draw_trapezoid
        
        self.shapes.append(method(canvas_ref=canvas, x=self.x, y=self.y, scaling_factor=scale, fill_color="red", size=self.size))
        self.shapes.append(canvas.create_text(
            self.x * scale,
            self.y * scale,
            fill=text_color,
            font=("Purisa", 10),
            width=200,
            text=f"{section_name}\n{str(self)}"
        ))

    def clear(self, canvas: Canvas):
        """Remove any drawn primitive"""
        for shape_id in self.shapes:
            canvas.delete(shape_id)

        self.shapes = []

    def to_json(self):
        return {
            "map": self.map,
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "shape": str(self.shape),
        }

class Section:
    name: str

    def __init__(self, name: str):
        self.name = name

    def to_json(self):
        return {
            "name": self.name
        }

class Location:
    """Handle one location object with one or several map position associated to sections"""
    children: list[Self]
    map_locations: list[MapPosition]
    sections: list[Section]
    name: str

    def __init__(self, name: str):
        self.name = name

        self.children = []
        self.map_locations = []
        self.sections = []

    def is_placed_on(self, map: str):
        """Indicate if at least one position of this location is on the selected map"""
        for map_position in self.map_locations:
            if map_position.is_placed_on(map):
                return True
        return False

    def place(self, map: str, x: int, y: int, size: int, shape: Shape):
        placed = False
        for map_position in self.map_locations:
            if map_position.map != map:
                continue

            map_position.place(map, x, y, size, shape)
            placed = True

        if not placed:
            self.map_locations.append(MapPosition(map, x, y, size, shape))

    def remove(self, map: str, canvas: Canvas):
        """Remove the placement on the given map"""
        self.clear(canvas)
        self.map_locations = [map_position for map_position in self.map_locations if map_position.map != map]

    def draw(self, section_name: str, map: str, canvas: Canvas, scale: float=1.0, text_color: str="black"):
        for map_position in self.map_locations:
            map_position.draw(section_name=section_name, map=map, canvas=canvas, scale=scale, text_color=text_color)

    def clear(self, canvas: Canvas):
        for map_position in self.map_locations:
            map_position.clear(canvas)

    def to_json(self):
        json: dict[str, Any] = {
            "name": self.name,
        }

        if len(self.children) > 0:
            json["children"] = [ location.to_json() for location in self.children ]
        if len(self.map_locations) > 0:
            json["map_locations"] = [ map_position.to_json() for map_position in self.map_locations ]
        if len(self.sections) > 0:
            json["sections"] = [ section.to_json() for section in self.sections ]

        return json

class Locations:
    """Handle the list of all locations"""
    locations: list[Location] = []

    placed_locations: list[Location] = []
    unplaced_locations: list[Location] = []

    def place(self, location: Location, map: str, x: int, y: int, size: int, shape: Shape):
        """Place a location on the map"""
        location.place(map, x, y, size, shape)

        if location in self.unplaced_locations:
            self.unplaced_locations.remove(location)

        if location not in self.placed_locations:
            self.placed_locations.append(location)

    def remove(self, location: Location, map: str, canvas: Canvas):
        """Remove the placement off a location on the given map"""
        location.remove(map=map, canvas=canvas)

        if location in self.placed_locations:
            self.placed_locations.remove(location)

        if location not in self.unplaced_locations:
            self.unplaced_locations.append(location)

    def clear(self, canvas: Canvas):
        """Erase any drawn section"""
        for location in self.locations:
            location.clear(canvas)

    def draw(self, map: str, canvas: Canvas, scale: float=1.0):
        for location in self.placed_locations:
            location.clear(canvas=canvas)

            for section in location.sections:
                location.draw(section.name, map=map, canvas=canvas, scale=scale)

    def load(self, map: str, canvas: Canvas, base_path: str, filename: str):
        """Clear existing locations and load the selected location file"""
        self.clear(canvas=canvas)

        self.placed_locations = []
        self.unplaced_locations = []

        self.locations = []
        json_data = json5.load(open(f'{base_path}/locations/{filename}'))
        for location_data in json_data:
            self.locations.append(self._load_location(map, location_data))

    def _load_location(self, map: str, location_data: dict, locations: list[Location]=[], path: str="") -> Location:
        """Load one raw JSON location data entry"""
        name = location_data.get("name", None)
        if name is None:
            raise ValidationException(f"Location has no name: {location_data}")

        debug(f"Loading {name}")

        location = Location(name=name)

        for section_data in location_data.get("sections", []):
            name = section_data.get("name", None)
            if name is None:
                warn(f"Empty section: {section_data}")
                continue

            section = Section(name)
            location.sections.append(section)
            
        for child_data in location_data.get("children", []):
            location.children.append(
                self._load_location(map, child_data, locations, path)
            )

        placed = False
        for map_position_data in location_data.get("map_locations", []):
            map = map_position_data.get("map", None)
            if map is None:
                warn(f"Got an empty map position: {map}")
                continue

            try:
                location.map_locations.append(MapPosition(
                    map=map,
                    x=map_position_data.get("x", 0),
                    y=map_position_data.get("y", 0),
                    size=map_position_data.get("size", 10),
                    shape=Shape(map_position_data.get("shape", "rect"))
                ))

                if map == map_json_selected:
                    placed = True
            except Exception:
                error(f"Invalid map_locations entry: {map_position_data}")

        if placed:
            self.placed_locations.append(location)
        else:
            self.unplaced_locations.append(location)
                    
        return location

    def get_section_location(self, section_name: str, locations: list[Location] | None=None):
        """Get a location that contains a specific section"""
        if locations is None:
            locations = self.locations
        
        needle = None
        for location in locations:
            for section in location.sections:
                if section.name == section_name:
                    return location

            needle = self.get_section_location(section_name, location.children)
            if needle is not None:
                return needle

        return needle

    def generator(self, locations: list[Location] | None=None):
        """Allows to browse each location individualy"""
        if locations is None:
            locations = self.locations

        for location in locations:
            yield location

            yield from self.generator(location.children)

    def to_json(self):
        return [
            location.to_json() for location in self.locations
        ]

class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

LOGLEVEL = LogLevel.CRITICAL

def _print(level: LogLevel, message: str):
    if LOGLEVEL <= level:
        print(message)

def error(message: str):
    _print(LogLevel.ERROR, f"Error: {message}")

def warn(message: str):
    _print(LogLevel.WARNING, f"Warning: {message}")

def info(message: str):
    _print(LogLevel.INFO, f"{message}")

def debug(message: str):
    _print(LogLevel.DEBUG, f"Debug: {message}")

locations: Locations = Locations()

locations_json_selected = ""
map_json_selected = ""
og_img_size = (0, 0)
scaling_factor = 1
og_img_width = og_img_size[0]
og_img_height = og_img_size[1]
canvas_img_id = 0
loop = True
selected_file_path = ""
new_map_window = None
zoom_scale = 1.0

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
    
    frame = tk.Frame(window_ref, name=name)
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
    return listbox

def create_canvas(widget_ref, name:str, img_ref, anchor:str, position:Optional[Tuple[int, int] | None] = None):
    canvas = tk.Canvas(widget_ref, name=name, width=img_ref.width(), height=img_ref.height())
    canvas_img_id = canvas.create_image(0, 0, image=img_ref, anchor=anchor)
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
        values=value_list,
        name=name
    )
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
    return input_field

def combine_scrollbar_with_widget(scrollbar_ref:Any , widget_ref:Any , scrollbar_command_ref:Any, 
                                  widget_command_ref:Any, widget_command_direction:str):
    scrollbar_ref.config(command=scrollbar_command_ref)
    widget_ref.config(**{widget_command_direction: widget_command_ref})

def go_back_to_selection():
    global locations_json_selected, map_json_selected
    map_json_selected = ""
    locations_json_selected = ""

    for child in window.winfo_children():
        child.destroy()
    window.quit()

def exit_loop():
    global loop
    loop=False
    window.quit()

def save(filename: str):
    with open(f"{base_path}/locations/{filename}", "w") as file:
        file.write(json5.dumps(locations.to_json(), indent=4, quote_keys=True, trailing_commas=False))

def save_to_new_file():
    save(locations_json_selected.replace(".json", "_new.json"))

def save_to_old_file():
    save(locations_json_selected)

def zoom_in(canvas: Canvas) -> float:
    global zoom_scale
    zoom_scale *= 1.2
    redraw_canvas(canvas)
    return 1.2

def zoom_out(canvas: Canvas):
    global zoom_scale
    zoom_scale *= 0.8
    redraw_canvas(canvas)
    return 0.8

def zoom_canvas(event, canvas: Canvas):
    global zoom_scale

    canvas_x = canvas.canvasx(event.x)
    canvas_y = canvas.canvasy(event.y)

    factor = 1.0
    if event.delta > 0:
        factor = zoom_in(canvas)
    elif event.delta < 0:
        factor = zoom_out(canvas)
    
    new_width = round(og_img_width * scaling_factor)
    new_height = round(og_img_height * scaling_factor)

    new_xview = (canvas_x * factor - event.x) / new_width
    new_yview = (canvas_y * factor - event.y) / new_height

    canvas.xview_moveto(new_xview)
    canvas.yview_moveto(new_yview)

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
        fill=fill_color,
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
        fill=fill_color,
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
        fill=fill_color,
    )

def load_new_base_image(window_ref:Any, img_path:str=""):
    global og_img_size, og_img_width, og_img_height, image, copy_of_image
    new_img_path = img_path
    if img_path == "":
        new_img_path = filedialog.askopenfilename(title="Select the new image to be loaded")
    image = Image.open(fr"{new_img_path}")
    og_img_size = image.size
    og_img_width = og_img_size[0] # if og_img_size[0] < 1000 else 1000
    og_img_height = og_img_size[1] # if og_img_size[1] < 700 else 700
    copy_of_image = image.copy()
    if img_path == "":
        window_ref.geometry(f"{og_img_width}x{og_img_height}")
    return ImageTk.PhotoImage(image=image, name="map image")

def resize_image(event, canvas: Canvas):
    global base_scale

    if event.width < 10 or event.height < 10:
        return

    if event.width / og_img_width < event.height / og_img_height:
        base_scale = event.width / og_img_width
    else:
        base_scale = event.height / og_img_height

    redraw_canvas(canvas)

def redraw_canvas(canvas: Canvas):
    global locations, image, canvas_img_id, scaling_factor

    scaling_factor = base_scale * zoom_scale

    new_width = round(og_img_width * scaling_factor)
    new_height = round(og_img_height * scaling_factor)

    image = copy_of_image.resize((new_width, new_height))
    photo = ImageTk.PhotoImage(image)

    canvas.delete(canvas_img_id)
    canvas_img_id = canvas.create_image(0, 0, image=photo, anchor="nw")
    canvas.image = photo

    canvas.configure(scrollregion=(0, 0, new_width, new_height))

    locations.clear(canvas=canvas)
    locations.draw(map=map_json_selected, canvas=canvas, scale=scaling_factor)

def refresh_section_selectors(locations: Locations, placed_locations_list: tk.Listbox, unplaced_locations_list: tk.Listbox):
    """Reload the content of the placed/unplaced section lists"""
    placed_scroll = placed_locations_list.yview()
    unplaced_scroll = unplaced_locations_list.yview()

    placed_locations_list.delete(0, tk.END)
    unplaced_locations_list.delete(0, tk.END)

    for location in locations.placed_locations:
        for section in location.sections:
            placed_locations_list.insert(tk.END, section.name)
    
    for location in locations.unplaced_locations:
        for section in location.sections:
            unplaced_locations_list.insert(tk.END, section.name)

    placed_locations_list.yview_moveto(placed_scroll[0])
    unplaced_locations_list.yview_moveto(unplaced_scroll[0])

def restore_default_markings(canvas: Canvas, placed_locations_list: tk.Listbox, unplaced_locations_list: tk.Listbox):
    global locations

    locations.clear(canvas=canvas)
    locations.load(map=map_json_selected, canvas=canvas, base_path=base_path, filename=locations_json_selected)
    locations.draw(map=map_json_selected, canvas=canvas, scale=scaling_factor)
    refresh_section_selectors(locations, placed_locations_list, unplaced_locations_list)

def place_location(event, canvas: Canvas, shape_selection: ttk.Combobox, size_selection: ttk.Combobox, placed_locations: tk.Listbox, unplaced_locations: tk.Listbox):
    debug(f"clicked at {event.x} {event.y}")
    debug(f"scaling factor {scaling_factor}")
    debug(f"actual image coords {event.x //scaling_factor} {event.y // scaling_factor}")

    if len(unplaced_locations.curselection()) > 0:
        selected_location = unplaced_locations.get(unplaced_locations.curselection()[0])
    elif len(placed_locations.curselection()) > 0 :
        selected_location = placed_locations.get(placed_locations.curselection()[0])
    else:
        selected_location = None

    if selected_location is None:
        # Nothing selected, nothing to do
        return

    location = locations.get_section_location(selected_location)
    if location is None:
        error(f"Cannot find the section name {select_location}")
        return
        
    canvas_x = canvas.canvasx(event.x)
    canvas_y = canvas.canvasy(event.y)

    location.clear(canvas=canvas)
    locations.place(
        location=location,
        map=map_json_selected,
        x=int(canvas_x // scaling_factor),
        y=int(canvas_y // scaling_factor),
        size=int(size_selection['values'][size_selection.current()]),
        shape=Shape(shape_selection['values'][shape_selection.current()]),
    )

    locations.draw(map=map_json_selected, canvas=canvas, scale=scaling_factor)
    refresh_section_selectors(locations, placed_locations, unplaced_locations)
    
    placed_locations.selection_set(tk.END)
    placed_locations.see(tk.END)

def remove_placed_location(_, canvas: Canvas, placed_locations_list: tk.Listbox, unplaced_locations_list: tk.Listbox):
    for selection_index in placed_locations_list.curselection():
        section_name = placed_locations_list.get(selection_index)
        location = locations.get_section_location(section_name)
        if location is None:
            # Cant find that section
            warn(f"Unable to find selected section {section_name}")
            continue
        
        locations.remove(location=location, canvas=canvas, map=map_json_selected)

    refresh_section_selectors(locations, placed_locations_list, unplaced_locations_list)

def choose_file_path():
    global selected_file_path
    selected_file_path = filedialog.askopenfilename()

def write_new_map_json_entry(map_listbox: tk.Listbox | None, name_input: tk.Entry | None):
    global selected_file_path
    name = ""
    filename = ""
    if map_listbox is not None:
        name_selection = map_listbox.curselection()
        assert len(name_selection) > 0, "nothing selected"
        name = map_listbox.get(name_selection[0])
    elif name_input is not None:
        name = name_input.get()
        if not selected_file_path == "":
            if not (base_path in selected_file_path):
                filename = os.path.basename(selected_file_path)
                shutil.copy(selected_file_path, fr"{base_path}/images/{filename}")
            filename = os.path.basename(selected_file_path)
        assert not filename == ""
    else:
        # Nothing allows map selection
        error("Can't access map selection objects")
        return

    assert not name == ""

    maps_path = fr"{base_path}/maps/maps.json"
    if not os.path.exists(maps_path):
        maps_path = map_json_path
    with open(maps_path, "r+") as maps_json_file:
        tmp_dict = json5.load(maps_json_file)
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
        maps_json_file.write(json5.dumps(tmp_dict, indent=4, quote_keys=True, trailing_commas=False))
    selected_file_path = ""
    if new_map_window is None:
        pass
    else:
        new_map_window.quit()

def reload_map_list(map_listbox: tk.Listbox):
    map_listbox.delete(0, tk.END)
    load_list_of_maps(map_listbox, fr"{base_path}/maps/maps.json")

def remove_map(map_listbox: tk.Listbox, name_input: tk.Entry | None):
    write_new_map_json_entry(map_listbox, name_input)
    reload_map_list(map_listbox)

def add_new_map(map_listbox: tk.Listbox):
    global new_map_window
    new_map_window = tk.Tk(baseName="map selection window")
    new_map_window.config(bg="yellow")
    new_map_window.geometry(f"{300}x{300}")
    text_input_frame = create_frame(window_ref=new_map_window, name="text input frame", position=(0, 0), sticky_direction="nsew")
    create_label(widget_ref=text_input_frame, text="Map Name", position=(0, 0), sticky_direction="ew")
    create_label(widget_ref=text_input_frame, text="Map Image", position=(1, 0), sticky_direction="ew")
    name_input = create_input_field(widget_ref=text_input_frame, name="name input", position=(0, 1), sticky_direction="nsew")
    select_image_btn = create_button(widget_ref=text_input_frame, text="Select image", command_ref=choose_file_path, position=(1, 1), sticky_direction="nsew")
    name_input.grid_configure(padx=5, pady=5)
    select_image_btn.grid_configure(padx=5, pady=5)

    create_button(widget_ref=new_map_window, text="exit new map selection", position=(2, 0), sticky_direction="nsew", command_ref=new_map_window.quit)
    create_button(widget_ref=new_map_window, text="save new map", position=(3, 0), sticky_direction="nsew", command_ref=lambda: write_new_map_json_entry(None, name_input))

    new_map_window.mainloop()
    try:
        new_map_window.destroy()
        new_map_window = None
        reload_map_list(map_listbox)
    except:
        pass

def dialog(list_of_locations: tk.Listbox, list_of_maps: tk.Listbox):
    global locations_json_selected, map_json_selected

    locations_json_selected = list_of_locations.get((list_of_locations.curselection()))
    map_json_selected = list_of_maps.get((list_of_maps.curselection()))

    if locations_json_selected != "" and map_json_selected != "":
        window.quit()

def select_location():
    focus = window.focus_get()
    if focus is not None:
        focus.selection_get()

def load_list_of_maps(window_list_of_maps, maps_path):
    tmp_map_list = {}
    if not os.path.exists(maps_path):
        maps_path = map_json_path
    with open(maps_path) as maps_file:
        for map_json in json5.load(maps_file):
            tmp_map_list[map_json["name"]] = f'{base_path}/{map_json["img"]}'
    for key in sorted(tmp_map_list.keys()):
        map_list[key] = tmp_map_list[key]
    for map_name in map_list.keys():
        window_list_of_maps.insert(tk.END, map_name)

def load_list_of_locations(window_list_of_locations, locations_dir):
    filenames = sorted(os.listdir(locations_dir))
    for filename in filenames:
        window_list_of_locations.insert(tk.END, filename)

def start_pan(event, canvas: Canvas):
    canvas.scan_mark(event.x, event.y)

def pan_motion(event, canvas: Canvas):
    canvas.scan_dragto(event.x, event.y, gain=1)

def start_selection_screen(window_ref: tk.Tk, base_path:str) -> tuple[Frame, Frame, Frame]:
    window_ref.columnconfigure([0, 1], weight=1)
    window_ref.rowconfigure(0, weight=1)

    frame_map_selection = create_frame(window_ref=window_ref, name="map_selection", position=(0, 1),
                                       row_config=[(0, 0), (1, 2), (2, 0)], column_config=[(0, 1), (1, 0)],
                                       sticky_direction="nsew")
    frame_location_selection = create_frame(window_ref=window_ref, name="location_selection", position=(0, 0),
                                            row_config=[(0, 0), (1, 2), (2, 0)], column_config=[(0, 1), (1, 0)],
                                            sticky_direction="nsew")
    # Maps side
    scrollbar_maps = create_scrollbar(frame_map_selection, orientation="vertical", position=(1, 1), sticky_direction="ns")
    window_list_of_maps = create_listbox(frame_map_selection, name="list_of_maps", position=(1, 0), sticky_direction="nsew")
    # location side
    scrollbar_locations = create_scrollbar(frame_location_selection, orientation="vertical", position=(1, 1), sticky_direction="ns")
    window_list_of_locations = create_listbox(frame_location_selection, name="list_of_locations", position=(1, 0), sticky_direction="nsew")

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

    create_label(frame_map_selection, text="Select a map", position=(0, 0), sticky_direction="ew")
    create_label(frame_location_selection, text="Select location source", position=(0, 0), sticky_direction="ew")
    create_button(frame_location_selection, text='Go with selection', command_ref=lambda: dialog(window_list_of_locations, window_list_of_maps), position=(2, 0), sticky_direction="ew")

    map_subframe = create_frame(frame_map_selection, name="map_subframe", position=(2, 0), sticky_direction="w")
    create_button(map_subframe, text="Add new Map", command_ref=lambda: add_new_map(window_list_of_maps), position=(0, 0), sticky_direction="ew")
    create_button(map_subframe, text="Remove selected Map", command_ref=lambda: remove_map(window_list_of_maps, name_input=None), position=(0, 1), sticky_direction="ew")
    button_frame = create_frame(window_ref=window_ref, name="button_space", position=(3, 0), sticky_direction="ew")
    exit_loop_button = create_button(button_frame, text="Exit", command_ref=exit_loop, sticky_direction="ew")
    exit_loop_button.grid(row=4, columnspan=2, sticky="ew", padx=5, pady=5)
    
    load_list_of_maps(window_list_of_maps, fr"{base_path}/maps/maps.json")
    load_list_of_locations(window_list_of_locations, fr'{base_path}/locations')

    return frame_map_selection, frame_location_selection, button_frame

def start_edit_screen(window_ref:Any, base_path:str, map_list):
    global locations
    img = load_new_base_image(window_ref=window_ref, img_path=map_list[map_json_selected])

    window_ref.columnconfigure(0, weight=1, minsize=300)
    window_ref.columnconfigure(1, weight=3)
    window_ref.columnconfigure(2, weight=0)

    frame_location_selection = create_frame(window_ref, name="location_selection", position=(0, 0), sticky_direction="nsew", column_config=[(0, 1), (1, 0)])
    frame_map_image = create_frame(window_ref, name="map_image", position=(0, 1), sticky_direction="nsew")
    frame_settings = create_frame(window_ref, name="settings", position=(0, 2), sticky_direction="nsew")

    frame_location_selection.rowconfigure(1, weight=1)
    frame_location_selection.rowconfigure(3, weight=1)

    # settings
    shape_selection_combobox = create_combobox(frame_settings, state="readonly", value_list=["rect", "diamond", "trapezoid"], default="rect", name="shape_selection")
    size_selection_combobox = create_combobox(frame_settings, state="readonly", value_list=[str(i) for i in range(6, 41, 2)], default="10", name="size_selection")

    create_button(frame_settings, text="Save to new file", command_ref=save_to_new_file)
    create_button(frame_settings, text="Overwrite existing file", command_ref=save_to_old_file)
    create_button(frame_settings, text="Load new BaseImage", command_ref=lambda: load_new_base_image(window_ref=window_ref, img_path=map_list[map_json_selected]))
    create_button(frame_settings, text="Go back to selection", command_ref=go_back_to_selection)
    create_button(frame_settings, text="Exit", command_ref=exit_loop)
    create_button(frame_settings, text="Restore Defaults", command_ref=lambda: restore_default_markings(canvas, placed_location_section_list, unplaced_location_section_list))
    for i, child in enumerate(frame_settings.winfo_children()):
        if isinstance(child, tk.Widget):
            child.grid(row=i, column=0, pady=5)
            child.columnconfigure(0, weight=0)

    frame_map_image.columnconfigure(0, weight=1)
    frame_map_image.rowconfigure(0, weight=1)
    canvas, _ = create_canvas(frame_map_image, name="map image canvas", img_ref=img, anchor="nw", position=(0,0))
    create_button(widget_ref=frame_map_image, position=(2,0), sticky_direction="ew", command_ref=lambda: zoom_in(canvas), text="zoom in")
    create_button(widget_ref=frame_map_image, position=(2,1), sticky_direction="ew", command_ref=lambda: zoom_out(canvas), text="zoom out")

    canvas.grid(row=0, column=0, sticky="nsew")
    canvas.bind("<Configure>", lambda event: resize_image(event, canvas))
    canvas.bind("<ButtonRelease-1>", lambda event: place_location(event, canvas, shape_selection_combobox, size_selection_combobox, placed_location_section_list, unplaced_location_section_list))

    create_label(frame_location_selection, text="unplaced locations", position=(0, 0), sticky_direction="ew")
    scrollbar_unplaced_location_section_y = create_scrollbar(frame_location_selection, position=(1, 1), orientation="vertical", sticky_direction="ns")
    unplaced_location_section_list = create_listbox(frame_location_selection, position=(1, 0), name="unplaced_locations", sticky_direction="nsew")
    
    unplaced_location_section_list.configure(exportselection=False, )
    combine_scrollbar_with_widget(scrollbar_unplaced_location_section_y,
                                  unplaced_location_section_list,
                                  unplaced_location_section_list.yview,
                                  widget_command_ref=scrollbar_unplaced_location_section_y.set,
                                  widget_command_direction="yscrollcommand")

    create_label(frame_location_selection, text="placed locations", position=(2, 0), sticky_direction="ew")
    scrollbar_placed_location_section_y = create_scrollbar(frame_location_selection, position=(3, 1), orientation="vertical", sticky_direction="ns")
    placed_location_section_list = create_listbox(frame_location_selection, position=(3, 0), name="placed_locations", sticky_direction="nsew")
    placed_location_section_list.configure(exportselection=False)
    combine_scrollbar_with_widget(scrollbar_placed_location_section_y,
                                  placed_location_section_list,
                                  placed_location_section_list.yview,
                                  widget_command_ref=scrollbar_placed_location_section_y.set,
                                  widget_command_direction="yscrollcommand")

    scrollbar_canvas_y = create_scrollbar(frame_map_image, position=(0, 1), orientation="vertical", sticky_direction="ns")
    scrollbar_canvas_x = create_scrollbar(frame_map_image, position=(1, 0), orientation="horizontal", sticky_direction="ew")

    canvas.bind("<ButtonPress-3>", lambda event: start_pan(event, canvas))
    canvas.bind("<B3-Motion>", lambda event: pan_motion(event, canvas))
    canvas.bind("<MouseWheel>", lambda event: zoom_canvas(event, canvas))

    combine_scrollbar_with_widget(scrollbar_canvas_y,
                                  canvas,
                                  canvas.yview,
                                  widget_command_ref=scrollbar_canvas_y.set,
                                  widget_command_direction="yscrollcommand")
    combine_scrollbar_with_widget(scrollbar_canvas_x,
                                  canvas,
                                  canvas.xview,
                                  widget_command_ref=scrollbar_canvas_x.set,
                                  widget_command_direction="xscrollcommand")
    canvas.configure(scrollregion=(0, 0, img.width(), img.height()))

    placed_location_section_list.bind("<Button-3>", lambda event: remove_placed_location(event, canvas, placed_location_section_list, unplaced_location_section_list))

    load_new_base_image(window_ref=window_ref, img_path=map_list[map_json_selected])
    
    locations.load(map=map_json_selected, canvas=canvas, base_path=base_path, filename=locations_json_selected)
    locations.draw(map=map_json_selected, canvas=canvas, scale=scaling_factor)
    refresh_section_selectors(locations, placed_location_section_list, unplaced_location_section_list)

if __name__ == "__main__":
    locations_json_selected=""
    map_json_selected=""
    map_list = {}
    loop = True

    window = tk.Tk()
    window.withdraw()

    window.columnconfigure([0, 1],  weight=1)
    window.rowconfigure(0, weight=1)

    base_path = filedialog.askdirectory(title="select the base folder for the pack")
    map_json_path = filedialog.askopenfilename(title="select the map json file", initialdir=base_path+"/maps/")
    if base_path == "":
        exit()
    
    while loop:
        try:
            frame_map_selection, frame_location_selection, button_frame_ref = start_selection_screen(window, base_path)
            window.deiconify()
            window.geometry(f"{int(window.winfo_screenwidth()/1.4)}x{int(window.winfo_screenheight()/2)}")
            window.mainloop()

            frame_map_selection.destroy()
            frame_location_selection.destroy()
            button_frame_ref.destroy()

            if map_json_selected != "" and locations_json_selected != "":
                start_edit_screen(window, base_path, map_list)

                window.mainloop()
        except tk.TclError:
            info("Program has stopped")
            break

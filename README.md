# Poptracker Packbuilder-Script

This set of scripts is build to make it easier to start making a trackerpack for [Poptracker](https://github.com/black-sliver/PopTracker)
Its builds the base file- and folder-structure expected from Poptracker from scratch based on the [Archipelago](https://archipelago.gg/)-Datapackages


## Getting started

This script is still work in progress but already creates packs working with Poptracker version from 0.27.0 onwards (as
of Aug 2024)

To use this script you need to have [Python](https://www.python.org/downloads/) installed. tested with 3.11+ earlier
versions should also work but at least 3.11 is recommended for sake of not having an outdated version anyway
From here on i assume you know how to run scripts with Python.

### Very first run

On the very first run the Script will install some needed Python packages listed in the requirements.txt. Mainly the
requests package to load the needed Archipelago-Datapackage and PIL for creating images for textbased Settings if needed

## How to build a Pack

When you are starting to Build a fresh pack you will need to run `builder.py` which is the Main script for all of this. 

It will ask you so select a folder to create the packs base-structure into. 
*Idealy this folder is empty to have a clean working area* but preexisting folders and files wont be overwritten unless
they conflict with the naming scheme for Poptracker.
Next the Pack askes for a source, an URL, to fetch the needed Datapackage from. This can be
`https://archipelago.gg/datapackage` for supported Games or i.e `http://localhost/datapackage` if you are locally hosting a copy of the Archipelago Webhost with custom (unsupported/in-development) apworlds.
After that it will ask for the **exact** name of the game you want to create the Tracker for. It needs to match the one from the Datapackage.  
After both has been provided these information get stored inside of `datapackage_url.txt`

If you already have a files called `datapackage_url.txt` containing these information in the format
`<Datapackage_URL>, <game_name>` they will get loaded from there instead of being asked for.

Now the Datapackage gets loaded, the needed gamedata extracted and stored inside of the 2 main files the rest of the pack gets build from. 
These files are stored inside `/scripts/autotracking/` and are called `location_mapping.lua` and `item_mapping.lua`.

After creating these 2 files alongeside the folder-basestructure and some other base files the first run get terminated. 

### Manual editing of the 2 main files

For a better explanaition of the terminology used here reference the [Poptracker Packs Interface-Guide](https://github.com/black-sliver/PopTracker/blob/master/doc/PACKS.md)

These 2 main files follow a relativly strict form that need to be maintained if you want to use this script any further
or later on to reset/redo parts of the pack.

#### item_mapping.lua
each line in `item_mapping.lua` looks like this:
```[<AP_item_ID>] = {{"<itemcode/-name>"}, "<item_type>"},```
- AP_item_ID --> the ID send out by Archipelago for this specific item
- itemcode/-name --> the code used to reference the item inside of Poptracker
- item_type --> the type you want to classify the item as inside Poptracker. Possible types are:
`"progressive", "toggle, "progressive_toggle", "static", "consumable" , "composite_toggle", and "composite_toggle"`
although the last 2 (`"composite_toggle", and "composite_toggle"`) are ignored for the sake of simplicity in this script

##### To-Do's for Manual editing:
- change the itemname/-code to something readable but ommit annotations like an amount. i.e from `money(500)` to just
  `money`, or `arrows(10)` to `arrows`. 
- change the type to the one you want to use inside Poptracker to represent this item.

all brackets need to stay the way they are!

#### location_mapping.lua
each line in `location_mapping.lua` looks like this:
```[<AP_location_ID>] = {"<AP_location_name>"},```
- AP_location_ID --> the ID send out by Archipelago for this specific location
- AP_location_name --> the path inside of poptrackers location tree-like structure for this location

This __WILL__ need you as the packauthor to have put some thought into how you want to structure you trackerpack,
because all the needed files poptracker read to show this location on a map and put accessibility-logic to it more or
less depends on this and somewhat definies how easy you will have it building logic for this pack later on. 
as you will see the location is already prefixed with an `@`. this is needed for poptracker to identify it as a
location-path. so keep that `@` where it is.

__tip:__
Make it that checks/locations that are next to each other in the same region/room/sub-area have the same path-prefix.
This way they get pre-grouped for a detailed map view.
without grouping them all the locations would either be in 1 single sqaure if you just put themm all in
`@region/<location_name>` or the will be all in their own square on the map when you are too granular. The last one also
happens if you dont group them at all. 

##### To-Do's for Manual editing:

- change the `AP_location_name` to a path you think best describes the location of the path inside your games world.
  Poptracker calles them sections and if you will need to separate the differen layers of sections with `/`. 
Therese is no limit on how many separations you can make but at some points readablity __WILL__ suffer

__caution__ : have a location names the same as section in the same place will cause the script to cause an error. so
having `@dungeon/boomerang room` and `@dungeon/boomerang room/pot` will cause issue. better but them on the same plane
such as `@dungeon/boomerang room/boomerang` and `@dungeon/boomerang room/pot`
Also avoid using forbidden characters for filenames such as `:, <, >,...` side your path. especially on the top most layer



Examples:
- you have a chest inside of a dungeon. the resulting path could look like --> `@dungeon_name/room_name/chest`
- you have a NPC giving you an item in the overworld. the resulting path could look like --> `@region_name/NPC_name`
- - you have a NPC inside of a building in a town giving you an item. the resulting path could look like -->
    `@town_name/house_name/NPC_name`

real world examples:
```
Items:
OOT
[66128] = {{"ProgressiveHookshot"}, "progressive"},
Pokemon red/blue
[172000073] = {{"pokeflute"}, "toggle"},
Super Metroid
[83000] = {{"etank"}, "consumable"},

Locations:
OOT
[67966] = {"@ZR/Near Domain/Waterfall/Red Rupee 1"},
Pokemon red/blue
[172000006] = {"@Kanto/Pallet Town/Oak's Post-Route-22-Rival Gift"},
Super Metroid
[82029] = {"@Brinstar/Energy Tank, Brinstar Ceiling/"},
```

### After manual editing

After you are finished with editing both of these files you can run the script (`builder.py`) again.
It will ask again for the root folder of your pack. the same folder you selected previously and where all the folders
and files already got created.
This time the script will read the 2 mapping.lua files and create a bunch of json files containing all the needed
information for Poptracker to know how to handle the items and how to structure the locations fully according to your
manually edited structre. 
__Items__
When the script is finished you will have 1 files called items.json located in `items/items.json` containing all the
information for your items ready for Poptracker to use. here you can now edit item-specific information such as the
imagename (defaults to `itemname.png`), the starting amount for consumables, and more.
Images need to be provided separatety. the picture names dont need to match the autogenerated ones BUT they do need to
match in the end....So rename the pictures AND/OR alter the paths in `items.json` 
__Locations__
For locations you will find multiple files indside of `locations/`. These are all separated by the topmost regions you
choose for your locations in `location_mapping.lua` as well as a file called `Overworld.json` incaining so-called
refrences (links) to ALL locations also devided by their topmost region. This Overworld file combines all checks for
each topmost region for be shown as 1 square on a less detailed overworld map.
The other files are intended for more detailed sub-maps
__Maps__
Inside the Maps folder will be a single file called maps.json containing the predefined json structured for map-tabs for
poptracker. the script will create a tab for each topmost-region that has at least 10 items inside of it. This Value can
easily be adjusted in `location_json.py` at
```python
for lvl in lvls:
    if len(locations_dict[lvl]) > 9:
        maps_names.append(lvl)
```
__Layouts__
Layout define you things are visibly structured in Poptracker. It is strongly recommendet to read about how structures
work in the [Poptracker Packs Interface-Guide](https://github.com/black-sliver/PopTracker/blob/master/doc/PACKS.md).
The script creates multiple files to make things more readable but in the end they get loaded as nested imports from
Poptracker. Play around with it to see how things work together but keep an untouched version or run `location_json.py`
again to restore the default state from the script.

## Generate images for textbased settings



## Partial rerun/restore
- to restore the everything inside of `items/` rerun `item_json.py`
- to restore everything in `locations/`, `maps/`AND `layouts/` rerun `location_json.py`
- to reset the `item/location_mapping.lua` delete them and rerun `builder.py`

## Full reset
If you want to reset the pack to the state after you manually edited the mapping.lua files  you just rerun `builder.py`
entirely. Maybe need to delete some extra files if you created them afterwards


import os
import json
import tkinter as tk
from tkinter import filedialog
import requests


def create_base_structure(path: str, game_name: str, game_dict: dict):
    """
    creates every needed directory and file needed to get a basic poptracker pack working and loading if the needed
    file is not already present
    :param str path: Path to the root folder of the Trackerpack
    :param str game_name: Name of the Game the Tracker is Made for. needs to Match the name in the AP datapackage
    :param dict game_dict: the json formated part from the AP datapackage for the specified game
    :return:
    """
    if not os.path.exists(path + "/scripts"):
        os.mkdir(path + "/scripts")
        os.mkdir(path + "/scripts/autotracking")
        os.mkdir(path + "/scripts/logic")
    if not os.path.exists(path + "/scripts/autotracking/archipelago.lua"):
        with open(path + "/scripts/autotracking/archipelago.lua", "w") as ap_lua:
            ap_lua.write(
                """
require("scripts/autotracking/item_mapping")
require("scripts/autotracking/location_mapping")
require("scripts/autotracking/hints_mapping")

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
        local tabs = ('\\t'):rep(depth)
        local tabs2 = ('\\t'):rep(depth + 1)
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

function forceUpdate()
    local update = Tracker:FindObjectForCode("update")
    update.Active = not update.Active
end

function onClearHandler(slot_data)
    local clear_timer = os.clock()
    
    ScriptHost:RemoveWatchForCode("StateChange")
    -- Disable tracker updates.
    Tracker.BulkUpdate = true
    -- Use a protected call so that tracker updates always get enabled again, even if an error occurred.
    local ok, err = pcall(onClear, slot_data)
    -- Enable tracker updates again.
    if ok then
        -- Defer re-enabling tracker updates until the next frame, which doesn't happen until all received items/cleared
        -- locations from AP have been processed.
        local handlerName = "AP onClearHandler"
        local function frameCallback()
            ScriptHost:AddWatchForCode("StateChange", "*", StateChange)
            ScriptHost:RemoveOnFrameHandler(handlerName)
            Tracker.BulkUpdate = false
            forceUpdate()
            print(string.format("Time taken total: %.2f", os.clock() - clear_timer))
        end
        ScriptHost:AddOnFrameHandler(handlerName, frameCallback)
    else
        Tracker.BulkUpdate = false
        print("Error: onClear failed:")
        print(err)
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
    for _, item_pair in pairs(ITEM_MAPPING) do
        for item_type, item_code in pairs(item_pair) do
            local item_obj = Tracker:FindObjectForCode(item_code)
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
    end
    PLAYER_ID = Archipelago.PlayerNumber or -1
    TEAM_NUMBER = Archipelago.TeamNumber or 0
    SLOT_DATA = slot_data
    -- if Tracker:FindObjectForCode("autofill_settings").Active == true then
    --     autoFill(slot_data)
    -- end
    -- print(PLAYER_ID, TEAM_NUMBER)
    if Archipelago.PlayerNumber > -1 then

        HINTS_ID = "_read_hints_"..TEAM_NUMBER.."_"..PLAYER_ID
        Archipelago:SetNotify({HINTS_ID})
        Archipelago:Get({HINTS_ID})
    end
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
    for _, item_pair in pairs(item) do
        item_code = item_pair[1]
        item_type = item_pair[2]
        local item_obj = Tracker:FindObjectForCode(item_code)
        if item_obj then
            if item_obj.Type == "toggle" then
                -- print("toggle")
                item_obj.Active = true
            elseif item_obj.Type == "progressive" then
                -- print("progressive")
                item_obj.Active = true
            elseif item_obj.Type == "consumable" then
                -- print("consumable")
                item_obj.AcquiredCount = item_obj.AcquiredCount + item_obj.Increment * (tonumber(item_pair[3]) or 1)
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
    end
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
end

function onEvent(key, value, old_value)
    updateEvents(value)
end

function onEventsLaunch(key, value)
    updateEvents(value)
end

-- this Autofill function is meant as an example on how to do the reading from slotdata and mapping the values to 
-- your own settings
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

function onNotify(key, value, old_value)
    print("onNotify", key, value, old_value)
    if value ~= old_value and key == HINTS_ID then
        for _, hint in ipairs(value) do
            if hint.finding_player == Archipelago.PlayerNumber then
                if hint.found then
                    updateHints(hint.location, true)
                else
                    updateHints(hint.location, false)
                end
            end
        end
    end
end

function onNotifyLaunch(key, value)
    print("onNotifyLaunch", key, value)
    if key == HINTS_ID then
        for _, hint in ipairs(value) do
            -- print("hint", hint, hint.found)
            -- print(dump_table(hint))
            if hint.finding_player == Archipelago.PlayerNumber then
                if hint.found then
                    updateHints(hint.location, true)
                else
                    updateHints(hint.location, false)
                end
            end
        end
    end
end

function updateHints(locationID, clear)
    local item_codes = HINTS_MAPPING[locationID]

    for _, item_table in ipairs(item_codes, clear) do
        for _, item_code in ipairs(item_table) do
            local obj = Tracker:FindObjectForCode(item_code)
            if obj then
                if not clear then
                    obj.Active = true
                else
                    obj.Active = false
                end
            else
                print(string.format("No object found for code: %s", item_code))
            end
        end
    end
end


-- ScriptHost:AddWatchForCode("settings autofill handler", "autofill_settings", autoFill)
Archipelago:AddClearHandler("clear handler", onClearHandler)
Archipelago:AddItemHandler("item handler", onItem)
Archipelago:AddLocationHandler("location handler", onLocation)

Archipelago:AddSetReplyHandler("notify handler", onNotify)
Archipelago:AddRetrievedHandler("notify launch handler", onNotifyLaunch)



--doc
--hint layout
-- {
--     ["receiving_player"] = 1,
--     ["class"] = Hint,
--     ["finding_player"] = 1,
--     ["location"] = 67361,
--     ["found"] = false,
--     ["item_flags"] = 2,
--     ["entrance"] = ,
--     ["item"] = 66062,
-- } 
"""
            )
    if not os.path.exists(path + "/scripts/init.lua"):
        with open(path + "/scripts/init.lua", "w") as init_lua:
            init_lua.write(
                """
local variant = Tracker.ActiveVariantUID

-- Items
require("scripts/items_import")

-- Logic
require("scripts/logic/logic_helper")
require("scripts/logic/logic_main")

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
require("scripts/layouts_import")

-- Locations
require("scripts/locations_import")

-- AutoTracking for Poptracker
if PopVersion and PopVersion >= "0.26.0" then
    require("scripts/autotracking")
end"""
            )
    if not os.path.exists(path + "scripts/items_import.lua"):
        with open(path + "/scripts/items_import.lua", "w") as items_lua:
            items_lua.write(
                """
Tracker:AddItems("items/items.json")
Tracker:AddItems("items/hint_items.json")
Tracker:AddItems("items/location_items.json")
Tracker:AddItems("items/labels.json")
                """
            )
    if not os.path.exists(path + "/scripts/layouts_import.lua"):
        with open(path + "/scripts/layouts_import.lua", "w") as layouts_lua:
            layouts_lua.write(
                """
Tracker:AddLayouts("layouts/events.json")
Tracker:AddLayouts("layouts/settings_popup.json")
Tracker:AddLayouts("layouts/items.json")
Tracker:AddLayouts("layouts/tabs.json")
Tracker:AddLayouts("layouts/tracker.json")
Tracker:AddLayouts("layouts/broadcast.json")
Tracker:AddLayouts("layouts/dungeon_items.json")
-- Tracker:AddLayouts("layouts/dungeon_items_keydrop.json")"""
            )
    if not os.path.exists(path + "/scripts/settings.lua"):
        with open(path + "/scripts/settings.lua", "w") as settings_lua:
            settings_lua.write(
                """
------------------------------------------------------------------
-- Configuration options for scripted systems in this pack
------------------------------------------------------------------
AUTOTRACKER_ENABLE_ITEM_TRACKING = true
AUTOTRACKER_ENABLE_LOCATION_TRACKING = true"""
            )
    if not os.path.exists(path + "/scripts/autotracking.lua"):
        with open(path + "/scripts/autotracking.lua", "w") as auto_lua:
            auto_lua.write(
                """
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

require("scripts/settings")
-- loads the AP autotracking code
require("scripts/autotracking/archipelago")


        """
            )
    if not os.path.exists(path + "manifest.json"):
        game_name_lua = game_name.lower().replace(' ', '_')
        with open(path + "/manifest.json", "w") as manifest:
            manifest_json = {
                "name": f"{game_name} Archipelago",
                "game_name": f"{game_name}",
                "package_version": "0.0.1",
                "package_uid": f"{game_name.lower()}_ap",
                "author": "builder_script",
                "variants": {
                    "Map Tracker": {"display_name": "Map Tracker", "flags": ["ap"]},
                    "Items Only": {"display_name": "Items Only", "flags": ["ap"]},
                },
                "min_poptracker_version": "0.27.0",
            }
            # manifest["platform"] = "snes"
            # manifest["versions_url"] = "https://raw.githubusercontent.com/<username>/<repo_name>/versions/versions.json"
            manifest.write(json.dumps(manifest_json, indent=4))
    if not os.path.exists(path + "/scripts/logic/logic_main.lua"):
        with open(path + "/scripts/logic/logic_main.lua", "w") as logic_lua:
            logic_lua.write(
                f"""
-- ScriptHost:AddWatchForCode("ow_dungeon details handler", "ow_dungeon_details", owDungeonDetails)


{game_name_lua}_location = \u007b\u007d
{game_name_lua}_location.__index = {game_name_lua}_location

accessLVL= \u007b
    [0] = "none",
    [1] = "partial",
    [3] = "inspect",
    [5] = "sequence break",
    [6] = "normal",
    [7] = "cleared"
\u007d

-- Table to store named locations
named_locations = \u007b\u007d
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

-- creates a lua object for the given name. it acts as a representation of a overworld region or indoor location and
-- tracks its connected objects via the exit-table
function {game_name_lua}_location.new(name)
    local self = setmetatable(\u007b\u007d, {game_name_lua}_location)
    if name then
        named_locations[name] = self
        self.name = name
    else
        self.name = self
    end

    self.exits = \u007b\u007d
    self.staleness = -1
    self.keys = math.huge
    self.accessibility_level = AccessibilityLevel.None
    return self
end

local function always()
    return AccessibilityLevel.Normal
end

-- marks a 1-way connections between 2 "locations/regions" in the source "locations" exit-table with rules if provided
function {game_name_lua}_location:connect_one_way(exit, rule)
    if type(exit) == "string" then
        exit = {game_name_lua}_location.new(exit)
    end
    if rule == nil then
        rule = always
    end
    self.exits[#self.exits + 1] = \u007b exit, rule \u007d
end

-- marks a 2-way connection between 2 locations. acts as a shortcut for 2 connect_one_way-calls 
function {game_name_lua}_location:connect_two_ways(exit, rule)
    self:connect_one_way(exit, rule)
    exit:connect_one_way(self, rule)
end

-- creates a 1-way connection from a region/location to another one via a 1-way connector like a ledge, hole,
-- self-closing door, 1-way teleport, ...
function {game_name_lua}_location:connect_one_way_entrance(name, exit, rule)
    if rule == nil then
        rule = always
    end
    self.exits[#self.exits + 1] = \u007b exit, rule \u007d
end

-- creates a connection between 2 locations that is traversable in both ways using the same rules both ways
-- acts as a shortcut for 2 connect_one_way_entrance-calls
function {game_name_lua}_location:connect_two_ways_entrance(name, exit, rule)
    if exit == nil then -- for ER
        return
    end
    self:connect_one_way_entrance(name, exit, rule)
    exit:connect_one_way_entrance(name, self, rule)
end

-- creates a connection between 2 locations that is traversable in both ways but each connection follow different rules.
-- acts as a shortcut for 2 connect_one_way_entrance-calls
function {game_name_lua}_location:connect_two_ways_entrance_door_stuck(name, exit, rule1, rule2)
    self:connect_one_way_entrance(name, exit, rule1)
    exit:connect_one_way_entrance(name, self, rule2)
end

-- checks for the accessibility of a regino/location given its own exit requirements
function {game_name_lua}_location:accessibility()
    if self.staleness < staleness then
        return AccessibilityLevel.None
    else
        return self.accessibility_level
    end
end

-- 
function {game_name_lua}_location:discover(accessibility, keys)

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

entry_point = {game_name_lua}_location.new("entry_point")

-- 
function stateChanged()
    staleness = staleness + 1
    entry_point:discover(AccessibilityLevel.Normal, 0)
end

ScriptHost:AddWatchForCode("stateChanged", "*", stateChanged)
        """
            )
    if not os.path.exists(path + "/scripts/logic/logic_helper.lua"):
        with open(path + "/scripts/logic/logic_helper.lua", "w") as logic_helper_lua:
            logic_helper_lua.write(
                """
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

function has(item, amount, amountInLogic)
-- function has(item, noKDS_amount, noKDS_amountInLogic, KDS_amount, KDS_amountInLogic)
    local count
    local amount
    local amountInLogic

    -- print(item, count, amount, amountInLogic)
    count = Tracker:ProviderCountForCode(item)
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
            """
            )
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
    if not os.path.exists(path + "/scripts/autotracking/hints_mapping.lua"):
        open(path + rf"/scripts/autotracking/hints_mapping.lua", "w").close()
    if not (
        os.path.exists(path + "/scripts/autotracking/item_mapping.lua")
        and os.path.exists(path + "/scripts/autotracking/location_mapping.lua")
    ):
        _create_mappings(path=path, game_data=game_dict[game_name])
        return exit()


def _create_mappings(path: str, game_data: dict[str, int]):
    """
    writes the 2 mapping files needed for location and item tracking via AP
    :param game_data:
    :return:
    """
    items_data = game_data["item_name_to_id"]
    locations_data = game_data["location_name_to_id"]
    _write_mapping(path=path, file_name="item_mapping", data=items_data, type="items")
    _write_mapping(
        path=path, file_name="location_mapping", data=locations_data, type="locations"
    )
    pass


def _write_mapping(path: str, file_name: str, data: dict[str, int], type: str):
    """
    writes the corresponding mapping file if AP-ID's to names.
    searches for the most common delimiters used in locationnames to possibly preselect/-create some regions.
    Item-types need to be adjusted after that step.
    Defaults to "toggle"
    :param path:
    :param file_name:
    :param data:
    :param type:
    :return:
    """
    delimiter = [" - ", ": ", ") "]
    replacement = ["/", "/", ")/"]
    with open(path + "/scripts/autotracking/" + file_name + ".lua", "w") as mapping:
        mapping.write(f"{file_name.upper()} = \u007b\n")
        match type:
            case "items":
                for name, ids in data.items():
                    mapping.write(
                        f'\t[{ids}] = \u007b\u007b"{name.replace(" ", "").lower()}", "toggle"\u007d\u007d,'
                        f"\n"
                    )
            case "locations":
                for name, ids in data.items():
                    br = "false"

                    for i, spacer in enumerate(delimiter):
                        if spacer in name:
                            opened = name.find("(")
                            closed = name.find(")")
                            check_inbetween = name.find(spacer)
                            if opened < check_inbetween and check_inbetween < closed:
                                name = name[:closed] + name[closed:].replace(
                                    f"{spacer}", replacement[i]
                                )
                                name = name.replace(f"{spacer}", " - ")
                            else:
                                name = name.replace(f"{spacer}", replacement[i])
                    mapping.write(f'\t[{ids}] = \u007b"@{name}"\u007d,\n')
        mapping.write("\u007d")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    print(
        """
    Please select the Directory the pack should be created in
    If there is no file called 'datapackage_url.txt' already present please provide the requested information.
    """
    )
    read_file_path = tk.filedialog.askdirectory()
    if not os.path.exists(read_file_path + "/datapackage_url.txt"):
        with open(read_file_path + "/datapackage_url.txt", "w") as base_file:
            url = (
                input("datapackage source (url): ")
                or "https://archipelago.gg/datapackage"
            )
            game = input("Game name from Datapackage: ")
            base_file.write(f"{url}, {game}, ")
    datapackage_path, game_name, *other_options = (
        open(read_file_path + "/datapackage_url.txt").readline().split(", ")
    )

    games_dict = requests.get(datapackage_path).json()["games"]

    create_base_structure(
        path=read_file_path, game_name=game_name, game_dict=games_dict
    )

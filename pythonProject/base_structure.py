import os
import json
import random
import tkinter as tk
from tkinter import filedialog
import requests


def create_base_structure(path: str, game_name: str, game_dict: dict, test_state: bool = False):
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
        with open(path + "/scripts/autotracking/archipelago.lua", "w", encoding="utf-8") as ap_lua:
            ap_lua.write(
                """
require("scripts/autotracking/item_mapping")
require("scripts/autotracking/location_mapping")

CUR_INDEX = -1
--SLOT_DATA = nil

ALL_LOCATIONS = {}
SLOT_DATA = {}

MANUAL_CHECKED = true
ROOM_SEED = "default"

if Highlight then
    HIGHTLIGHT_LEVEL= {
        [0] = Highlight.Unspecified,
        [10] = Highlight.NoPriority,
        [20] = Highlight.Avoid,
        [30] = Highlight.Priority,
        [40] = Highlight.None,
    }
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

function LocationHandler(location)
    if MANUAL_CHECKED then
        local storage_item = Tracker:FindObjectForCode("manual_location_storage")
        if Archipelago.PlayerNumber == -1 then -- not connected
            if ROOM_SEED ~= "default" then -- seed is from previous connection
                ROOM_SEED = "default"
                storage_item.ItemState.MANUAL_LOCATIONS["default"] = {}
            else -- seed is default
            end
        end
        local full_path = location.FullID
        if storage_item.ItemState.MANUAL_LOCATIONS[ROOM_SEED][full_path] then --not in list for curretn seed
            if location.AvailableChestCount < location.ChestCount then --add to list
                storage_item.ItemState.MANUAL_LOCATIONS[ROOM_SEED][full_path] = location.AvailableChestCount
            else --remove from list of set back to max chestcount
                storage_item.ItemState.MANUAL_LOCATIONS[ROOM_SEED][full_path] = nil
            end
        elseif location.AvailableChestCount < location.ChestCount then -- not in list and not set back to its max chest count
            storage_item.ItemState.MANUAL_LOCATIONS[ROOM_SEED][full_path] = location.AvailableChestCount
        else
        end
    end
    local storage_item = Tracker:FindObjectForCode("manual_location_storage")
    -- print(dump_table(storage_item.ItemState.MANUAL_LOCATIONS))
    ForceUpdate() -- 
end

function ForceUpdate()
    local update = Tracker:FindObjectForCode("update")
    if update == nil then
        return
    end
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
            ScriptHost:AddWatchForCode("StateChange", "*", StateChanged)
            ScriptHost:RemoveOnFrameHandler(handlerName)
            Tracker.BulkUpdate = false
            ForceUpdate()
            print(string.format("Time taken total: %.2f", os.clock() - clear_timer))
        end
        ScriptHost:AddOnFrameHandler(handlerName, frameCallback)
    else
        Tracker.BulkUpdate = false
        print("Error: onClear failed:")
        print(err)
    end
end

function preOnClear()
    PLAYER_ID = Archipelago.PlayerNumber or -1
    TEAM_NUMBER = Archipelago.TeamNumber or 0
    if Archipelago.PlayerNumber > -1 then
        if #ALL_LOCATIONS > 0 then
            ALL_LOCATIONS = {}
        end
        for _, value in pairs(Archipelago.MissingLocations) do
            table.insert(ALL_LOCATIONS, #ALL_LOCATIONS + 1, value)
        end

        for _, value in pairs(Archipelago.CheckedLocations) do
            table.insert(ALL_LOCATIONS, #ALL_LOCATIONS + 1, value)
        end
        -- HINTS_ID = "_read_hints_"..TEAM_NUMBER.."_"..PLAYER_ID
        -- Archipelago:SetNotify({HINTS_ID})
        -- Archipelago:Get({HINTS_ID})
    end


    -- print(Archipelago.Seed)
    local storage_item = Tracker:FindObjectForCode("manual_location_storage")
    local SEED_BASE = (Archipelago.Seed or tostring(#ALL_LOCATIONS)).."_"..Archipelago.TeamNumber.."_"..Archipelago.PlayerNumber

    if ROOM_SEED == "default" or ROOM_SEED ~= SEED_BASE then -- seed is default or from previous connection

        ROOM_SEED = SEED_BASE
        if #storage_item.ItemState.MANUAL_LOCATIONS > 10 then
            storage_item.ItemState.MANUAL_LOCATIONS[storage_item.ItemState.MANUAL_LOCATIONS_ORDER[1]] = nil
            table.remove(storage_item.ItemState.MANUAL_LOCATIONS_ORDER, 1)
        end
        if storage_item.ItemState.MANUAL_LOCATIONS[ROOM_SEED] == nil then
            storage_item.ItemState.MANUAL_LOCATIONS[ROOM_SEED] = {}
            table.insert(storage_item.ItemState.MANUAL_LOCATIONS_ORDER, ROOM_SEED)
        end
    else -- seed is from previous connection
    end
end

function onClear(slot_data)
    MANUAL_CHECKED = false
    local storage_item = Tracker:FindObjectForCode("manual_location_storage")
    if storage_item == nil then
        CreateLuaManualStorageItem("manual_location_storage")
        storage_item = Tracker:FindObjectForCode("manual_location_storage")
    end
    preOnClear()
    ScriptHost:RemoveWatchForCode("StateChanged")
    ScriptHost:RemoveOnLocationSectionHandler("location_section_change_handler")
    --SLOT_DATA = slot_data
    CUR_INDEX = -1
    -- reset locations
    for _, location_array in pairs(LOCATION_MAPPING) do
        for _, location in pairs(location_array) do
            if location then
                local location_obj = Tracker:FindObjectForCode(location)
                if location_obj then
                    if location:sub(1, 1) == "@" then
                        if storage_item.ItemState.MANUAL_LOCATIONS[ROOM_SEED][location_obj.FullID] then
                            location_obj.AvailableChestCount = storage_item.ItemState.MANUAL_LOCATIONS[ROOM_SEED][location_obj.FullID]
                        else
                            location_obj.AvailableChestCount = location_obj.ChestCount
                        end
                    else
                        location_obj.Active = false
                    end
                end
            end
        end
    end
    -- reset items
    for _, item_array in pairs(ITEM_MAPPING) do
        for _, item_pair in pairs(item_array) do
            item_code = item_pair[1]
            item_type = item_pair[2]
            -- print("on clear", item_code, item_type)
            local item_obj = Tracker:FindObjectForCode(item_code)
            if item_obj then
                if item_obj.Type == "toggle" then
                    item_obj.Active = false
                elseif item_obj.Type == "progressive" then
                    item_obj.CurrentStage = 0
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
        if #ALL_LOCATIONS > 0 then
            ALL_LOCATIONS = {}
        end
        for _, value in pairs(Archipelago.MissingLocations) do
            table.insert(ALL_LOCATIONS, #ALL_LOCATIONS + 1, value)
        end

        for _, value in pairs(Archipelago.CheckedLocations) do
            table.insert(ALL_LOCATIONS, #ALL_LOCATIONS + 1, value)
        end

        HINTS_ID = "_read_hints_"..TEAM_NUMBER.."_"..PLAYER_ID
        Archipelago:SetNotify({HINTS_ID})
        Archipelago:Get({HINTS_ID})
    end
    ScriptHost:AddOnFrameHandler("load handler", OnFrameHandler)
    MANUAL_CHECKED = true
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
                item_obj.CurrentStage = item_obj.CurrentStage + 1
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
    MANUAL_CHECKED = false
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
    MANUAL_CHECKED = true
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
        Tracker.BulkUpdate = true
        for _, hint in ipairs(value) do
            if hint.finding_player == Archipelago.PlayerNumber then
                if not hint.found then
                    updateHints(hint.location, hint.status)
                elseif hint.found then
                    updateHints(hint.location, hint.status)
                end
            end
        end
        Tracker.BulkUpdate = false
    end
end

function onNotifyLaunch(key, value)
    if key == HINTS_ID then
        Tracker.BulkUpdate = true
        for _, hint in ipairs(value) do
            if hint.finding_player == Archipelago.PlayerNumber then
                if not hint.found then
                    updateHints(hint.location, hint.status)
                else if hint.found then
                    updateHints(hint.location, hint.status)
                end end
            end
        end
        Tracker.BulkUpdate = false
    end
end

function updateHints(locationID, status) -->
    if Highlight then
        print(locationID, status)
        local location_table = LOCATION_MAPPING[locationID]
        for _, location in ipairs(location_table) do
            if location:sub(1, 1) == "@" then
                local obj = Tracker:FindObjectForCode(location)

                if obj then
                    obj.Highlight = HIGHTLIGHT_LEVEL[status]
                else
                    print(string.format("No object found for code: %s", location))
                end
            end
        end
    end
end


-- ScriptHost:AddWatchForCode("settings autofill handler", "autofill_settings", autoFill)
-- Archipelago:AddClearHandler("clear handler", onClearHandler)
-- Archipelago:AddItemHandler("item handler", onItem)
-- Archipelago:AddLocationHandler("location handler", onLocation)

-- Archipelago:AddSetReplyHandler("notify handler", onNotify)
-- Archipelago:AddRetrievedHandler("notify launch handler", onNotifyLaunch)



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
        with open(path + "/scripts/init.lua", "w", encoding="utf-8") as init_lua:
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
end

function OnFrameHandler()
    ScriptHost:RemoveOnFrameHandler("load handler")
    -- stuff
    ScriptHost:AddWatchForCode("StateChanged", "*", StateChanged)
    ScriptHost:AddOnLocationSectionChangedHandler("location_section_change_handler", LocationHandler)
    CreateLuaManualStorageItem("manual_location_storage")
    ForceUpdate()
end
require("scripts/luaitems")
require("scripts/watches")
ScriptHost:AddOnFrameHandler("load handler", OnFrameHandler)
"""
            )
    if not os.path.exists(path + "/scripts/luaitems.lua"):
        with open(path + "/scripts/luaitems.lua", "w", encoding="utf-8") as init_lua:
            init_lua.write(
                """
local function CanProvideCodeFunc(self, code)
    return code == self.Name
end

local function OnLeftClickFunc(self)
    -- your custom handling for clicks here
    -- return true
end

local function OnRightClickFunc(self)
    -- your custom handling for clicks here
    -- return true
end

local function OnMiddleClickFunc(self)
    -- your custom handling for clicks here
    -- return true
end

local function ProvidesCodeFunc(self, code)
    if CanProvideCodeFunc(self, code) then
    
            return 1
        end
    return 0
end

local function SaveManualLocationStorageFunc(self)
    return {
        -- save everything from ItemState in here separately
        MANUAL_LOCATIONS = self.ItemState.MANUAL_LOCATIONS,
        MANUAL_LOCATIONS_ORDER = self.ItemState.MANUAL_LOCATIONS_ORDER,
        Target = self.ItemState.Target,
        Name = self.Name,
        Icon = self.Icon
    }
end

local function LoadManualLocationStorageFunc(self, data)
    if data ~= nil and self.Name == data.Name then
        -- load everything from ItemState in here separately
        self.ItemState.MANUAL_LOCATIONS = data.MANUAL_LOCATIONS
        self.ItemState.MANUAL_LOCATIONS_ORDER = data.MANUAL_LOCATIONS_ORDER
        self.Icon = ImageReference:FromPackRelativePath(data.Icon)
    else
    end
end

function CreateLuaManualStorageItem(name)
    local self = ScriptHost:CreateLuaItem()
    -- self.Type = "custom"
    self.Name = name --code --
    self.Icon = ImageReference:FromPackRelativePath("/images/items/closed_Chest.png")
    self.ItemState = {
        MANUAL_LOCATIONS = {
            ["default"] = {}
        },
        MANUAL_LOCATIONS_ORDER = {}
        -- you can add many more custom stuff in here
    }
   
    self.CanProvideCodeFunc = CanProvideCodeFunc
    self.OnLeftClickFunc = OnLeftClickFunc -- your_custom_leftclick_function_here
    self.OnRightClickFunc = OnRightClickFunc -- your_custom_rightclick_function_here
    self.OnMiddleClickFunc = OnMiddleClickFunc -- your_custom_middleclick_function_here
    self.ProvidesCodeFunc = ProvidesCodeFunc
    self.SaveFunc = SaveManualLocationStorageFunc
    self.LoadFunc = LoadManualLocationStorageFunc
    return self
end
"""
            )

    if not os.path.exists(path + "scripts/items_import.lua"):
        with open(path + "/scripts/items_import.lua", "w", encoding="utf-8") as items_lua:
            items_lua.write(
                """
Tracker:AddItems("items/items.json")
Tracker:AddItems("items/location_items.json")
Tracker:AddItems("items/labels.json")
                """
            )
    if not os.path.exists(path + "/scripts/layouts_import.lua"):
        with open(path + "/scripts/layouts_import.lua", "w", encoding="utf-8") as layouts_lua:
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
        with open(path + "/scripts/settings.lua", "w", encoding="utf-8") as settings_lua:
            settings_lua.write(
                """
------------------------------------------------------------------
-- Configuration options for scripted systems in this pack
------------------------------------------------------------------
AUTOTRACKER_ENABLE_ITEM_TRACKING = true
AUTOTRACKER_ENABLE_LOCATION_TRACKING = true"""
            )
    if not os.path.exists(path + "/scripts/autotracking.lua"):
        with open(path + "/scripts/autotracking.lua", "w", encoding="utf-8") as auto_lua:
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
    if not os.path.exists(path + "/scripts/watches.lua"):
        with open(path + "/scripts/watches.lua", "w", encoding="utf-8") as auto_lua:
            auto_lua.write(
                """
-- Archipelago:AddClearHandler("clear handler", onClear)
Archipelago:AddClearHandler("clear handler", onClearHandler)
Archipelago:AddItemHandler("item handler", onItem)
Archipelago:AddLocationHandler("location handler", onLocation)

Archipelago:AddSetReplyHandler("notify handler", onNotify)
Archipelago:AddRetrievedHandler("notify launch handler", onNotifyLaunch)


        """
            )
    if not os.path.exists(path + "manifest.json"):
        game_name_lua = game_name.lower().replace(' ', '_')
        with open(path + "/manifest.json", "w", encoding="utf-8") as manifest:
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
                "min_poptracker_version": "0.31.0",
            }
            # manifest["platform"] = "snes"
            # manifest["versions_url"] = "https://raw.githubusercontent.com/<username>/<repo_name>/versions/versions.json"
            manifest.write(json.dumps(manifest_json, indent=4))
    if not os.path.exists(path + "/scripts/logic/logic_main.lua"):
        with open(path + "/scripts/logic/logic_main.lua", "w", encoding="utf-8") as logic_lua:
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
    [7] = "cleared",
    [false] = "none",
    [true] = "normal",
\u007d

-- Table to store named locations
NAMED_LOCATIONS = \u007b\u007d
local stale = true
local accessibilityCache = \u007b\u007d
local accessibilityCacheComplete = false
local currentParent = nil
local currentLocation = nil
local indirectConnections = \u007b\u007d


--
function Table_insert_at(er_table, key, value)
    if er_table[key] == nil then
        er_table[key] = \u007b\u007d
    end
    table.insert(er_table[key], value)
end

-- 
function CanReach(name)
    -- if type(name) == "table" then
    --     -- print("-----------")
    --     -- print("start CanREach for", name.name)
    -- -- else
    --     -- print("start CanREach for", name)
    -- end
    local location
    if stale then
        stale = false
        accessibilityCacheComplete = false
        accessibilityCache = \u007b\u007d
        indirectConnections = \u007b\u007d
        while not accessibilityCacheComplete do
            accessibilityCacheComplete = true
            entry_point:discover(ACCESS_NORMAL, 0, nil)
            for dst, parents in pairs(indirectConnections) do
                if dst:accessibility() < ACCESS_NORMAL then
                    for parent, src in pairs(parents) do
                        -- print("Checking indirect " .. src.name .. " for " .. parent.name .. " -> " .. dst.name)
                        parent:discover(parent:accessibility(), parent.keys, parent.worldstate)
                    end
                end
            end
        end
        --entry_point:discover(ACCESS_NORMAL, 0) -- since there is no code to track indirect connections, we run it twice here
        --entry_point:discover(ACCESS_NORMAL, 0)
    end
    
    location = NAMED_LOCATIONS[name]
    
    if location == nil then
        return ACCESS_NONE
    end
    return location:accessibility()
end

-- creates a lua object for the given name. it acts as a representation of a overworld region or indoor location and
-- tracks its connected objects via the exit-table
function {game_name_lua}_location.new(name)
    local self = setmetatable(\u007b\u007d, {game_name_lua}_location)
    if name then
        NAMED_LOCATIONS[name] = self
        self.name = name
    else
        NAMED_LOCATIONS[name] = self
        self.name = tostring(self)
    end
    if string.find(self.name, "_inside") then
        self.side = "inside"
    elseif string.find(self.name, "_outside") then
        self.side = "outside"
    else
        self.side = nil
    end
    -- print("------")
    -- print(origin)
    self.worldstate = origin
    -- print(self.worldstate)
    -- print("------")
    self.exits = \u007b\u007d
    self.keys = math.huge

    return self
end

local function always()
    return ACCESS_NORMAL
end

-- marks a 1-way connections between 2 "locations/regions" in the source "locations" exit-table with rules if provided
function {game_name_lua}_location:connect_one_way(exit, rule)
    if type(exit) == "string" then
        local existing = NAMED_LOCATIONS[exit]
        if existing then
            print("Warning: " .. exit .. " defined multiple times")  -- not sure if it's worth fixing in data or simply allowing this
            exit = existing
        else
            exit = {game_name_lua}_location.new(exit)
        end
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

-- technically redundant but well
-- creates a connection between 2 locations that is traversable in both ways but each connection follow different rules.
-- acts as a shortcut for 2 connect_one_way-calls
function {game_name_lua}_location:connect_two_ways_stuck(exit, rule1, rule2)
    self:connect_one_way(exit, rule1)
    exit:connect_one_way(self, rule2)
end

-- checks for the accessibility of a region/location given its own exit requirements
function {game_name_lua}_location:accessibility()
    -- only executed when run from a rules within a connection
    if currentLocation ~= nil and currentParent ~= nil then
        if indirectConnections[currentLocation] == nil then
            indirectConnections[currentLocation] = \u007b\u007d
        end
        indirectConnections[currentLocation][currentParent] = self
    end
    -- up to here
    local res = accessibilityCache[self] -- get accessibilty lvl set in discover for a given location
    if res == nil then
        res = ACCESS_NONE
        accessibilityCache[self] = res
    end
    return res
end

-- 
function {game_name_lua}_location:discover(accessibility, keys)
    -- checks if given Accessbibility is higer then last stored one
    -- prevents walking in circles
    
    if accessibility > self:accessibility() then
        self.keys = math.huge -- resets keys used up to this point
        accessibilityCache[self] = accessibility
        accessibilityCacheComplete = false -- forces CanReach tu run again/further
    end
    if keys < self.keys then
        self.keys = keys -- sets current amout of keys used
    end

    if accessibility > 0 then -- if parent-location was accessible
        for _, exit in pairs(self.exits) do -- iterate over current watched locations exits
            local location

            -- local exit_name = exit[1].name
            local location_name = self.name

            if location == nil then
                location = exit[1] or empty_location-- exit name
            end
            
            local oldAccess = location:accessibility() -- get most recent accessibilty level for exit
            local oldKey = location.keys or 0
            
            if oldAccess < accessibility then -- if new accessibility from above is higher then currently stored one, so is more accessible then before
                local rule = exit[2] -- get rules to check

                currentParent, currentLocation = self, location -- just set for ":accessibilty()" check within rules
                local access, key = rule(keys)
                local parent_access = currentParent:accessibility()
                if type(access) == "boolean" then --
                    access = A(access)
                end
                -- print(self.name, type(access), type(parent_access), location.name)
                if access > parent_access then
                    access = parent_access
                end
                currentParent, currentLocation = nil, nil -- just set for ":accessibilty()" check within rules

                if access == nil then
                    print("Warning: " .. self.name .. " -> " .. location.name .. " rule returned nil")
                    access = ACCESS_NONE
                end
               
                if key == nil then
                    key = keys
                end
                if access > oldAccess or (access == oldAccess and key < oldKey) then -- not sure about the <
                    -- print(self.name, "to", location.name)
                    -- print(accessLVL[self:accessibility()], "from", self.name, "to", location.name, ":", accessLVL[access])
                    location:discover(access, key)
                end
            end
        end
    end
end

entry_point = {game_name_lua}_location.new("entry_point")

-- 
function StateChanged()
    stale = true
    -- entry_point:discover(AccessibilityLevel.Normal, 0)
end

ScriptHost:AddWatchForCode("StateChanged", "*", StateChanged)
        """
            )
    if not os.path.exists(path + "/scripts/logic/logic_helper.lua"):
        with open(path + "/scripts/logic/logic_helper.lua", "w", encoding="utf-8") as logic_helper_lua:
            logic_helper_lua.write(
                """
ACCESS_NONE = AccessibilityLevel.None
ACCESS_PARTIAL = AccessibilityLevel.Partial
ACCESS_INSPECT = AccessibilityLevel.Inspect
ACCESS_SEQUENCEBREAK = AccessibilityLevel.SequenceBreak
ACCESS_NORMAL = AccessibilityLevel.Normal
ACCESS_CLEARED = AccessibilityLevel.Cleared

local bool_to_accesslvl = {
    [true] = ACCESS_NORMAL,
    [false] = ACCESS_NONE
}
                
function A(result)
    if result then
        return ACCESS_NORMAL
    end
    return ACCESS_NONE
end

function ALL(...)
    local args = { ... }
    local min = ACCESS_NORMAL
    for _, v in ipairs(args) do
        if type(v) == "function" then
            v = v()
        elseif type(v) == "string" then
            v = Has(v)
        end
        if type(v) == "boolean" then
            v = bool_to_accesslvl[v]
        end
        if v < min then
            if v == ACCESS_NONE then
                return ACCESS_NONE
            end
            min = v
        end
    end
    return min
end

function ANY(...)
    local args = { ... }
    local max = ACCESS_NONE
    for _, v in ipairs(args) do
        if type(v) == "function" then
            v = v()
        elseif type(v) == "string" then
            v = Has(v)
        end
        if type(v) == "boolean" then
            v = bool_to_accesslvl[v]
            -- v = A(v)
        end
        if v > max then
            if v == ACCESS_NORMAL then
                return ACCESS_NORMAL
            end
            max = v
        end
    end
    return max
end

function Has(item, amount, amountInLogic)
    local count = Tracker:ProviderCountForCode(item)

    -- print(item, count, amount, amountInLogic)
    if amountInLogic then
        if count >= amountInLogic then
            return ACCESS_NORMAL
        elseif count >= amount then
            return ACCESS_SEQUENCEBREAK
        end
        return ACCESS_NONE
    end
    if not amount then
        if count > 0 then
            return ACCESS_NORMAL
        end
        return ACCESS_NONE
    else
        if count >= amount then
            return ACCESS_SEQUENCEBREAK
        end
        return ACCESS_NONE
    end
end


-- ANy function added here and used in access rules should try to return an Accessibility Level if it is used inside 
-- the ANY() and ALL() functions
--
--"""
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
    if not (
        os.path.exists(path + "/scripts/autotracking/item_mapping.lua")
        and os.path.exists(path + "/scripts/autotracking/location_mapping.lua")
    ):
        _create_mappings(path=path, game_data=game_dict[game_name], test_state=test_state)
        return exit()


def _create_mappings(path: str, game_data: dict[str, int], test_state: bool = False):
    """
    writes the 2 mapping files needed for location and item tracking via AP
    :param game_data:
    :return:
    """
    items_data = game_data["item_name_to_id"]
    locations_data = game_data["location_name_to_id"]
    item_name_data = {**items_data, **locations_data}
    _write_mapping(path=path, file_name="item_mapping", data=items_data, type="items", test_state=test_state)
    _write_mapping(
        path=path, file_name="location_mapping", data=locations_data, type="locations"
    )
    _write_mapping(
        path=path, file_name="item_names", data=item_name_data, type="item_names"
    )
    pass


def _write_mapping(path: str, file_name: str, data: dict[str, int], type: str, test_state: bool = False):
    """
    writes the corresponding mapping file if AP-ID's to names.
    searches for the most common delimiters used in locationnames to possibly preselect/-create some regions.
    Item-types need to be adjusted after that step.
    Defaults to "toggle", randomizes it if Test-flag is set
    :param path:
    :param file_name:
    :param data:
    :param type:
    :return:
    """
    delimiter = [" - ", ": ", ") "]
    replacement = ["/", "/", ")/"]
    escape = ["\\", "\'", "\""]
    forbidden = ["<", ">", ":", "|", "?", "*"]
    item_states = ["toggle", "consumable", "static", "progressive", "progressive_toggle"]

    with open(path + "/scripts/autotracking/" + file_name + ".lua", "w", encoding="utf-8") as mapping:
        mapping.write(f"{file_name.upper()} = \u007b\n")
        match type:
            case "items":
                for name, ids in data.items():
                    for escape_char in escape:
                        if escape_char in name:
                            # name = name.replace(f"{escape_char}", f"\\{escape_char}")
                            name = name.replace(f"{escape_char}", "")
                    mapping.write(
                        f'\t[{ids}] = \u007b\u007b"{name.replace(" ", "").lower()}", '
                        f'"{random.choice(item_states) if test_state else "toggle" }"\u007d\u007d,'
                        f'\n'
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
                    for forbidden_char in forbidden:
                        name = name.replace(f"{forbidden_char}", "")
                    for escape_char in escape:
                        if escape_char in name:
                            # name = name.replace(f"{escape_char}", f"\\{escape_char}")
                            name = name.replace(f"{escape_char}", "")
                    mapping.write(f'\t[{ids}] = \u007b"@{name}"\u007d,\n')
            case "item_names":
                for name, ids in data.items():
                    for escape_char in escape:
                        if escape_char in name:
                            # name = name.replace(f"{escape_char}", f"\\{escape_char}")
                            name = name.replace(f"{escape_char}", "")
                    mapping.write(
                        f'\t["{name.replace(" ", "").lower()}"] = "{name}",'
                        f"\n"
                    )
        mapping.write("\u007d")


if __name__ == "__main__":
    import argparse
    root = tk.Tk()
    root.withdraw()

    print(
        """
    Please select the Directory the pack should be created in
    If there is no file called 'datapackage_url.json' already present please provide the requested information.
    """
    )
    read_file_path = tk.filedialog.askdirectory()
    if not os.path.exists(read_file_path + "/datapackage_url.json"):
        with open(read_file_path + "/datapackage_url.json", "w", encoding="utf-8") as base_file:
            url = (
                    input("datapackage source (url): ")
                    or "https://archipelago.gg"
            )
            game_name = input("Game name from Datapackage: ")
            dp_json = {
                "url": f"{url}/datapackage",
                "game_name": f"{game_name}"
            }
            base_file.write(json.dumps(dp_json, indent=4))
    with open(f"{read_file_path}/datapackage_url.json") as args_json:
        dp_json = json.load(args_json)
        datapackage_path = dp_json["url"]
        game_name = dp_json["game_name"]

    games_dict = requests.get(datapackage_path).json()["games"]

    create_base_structure(
        path=read_file_path, game_name=game_name, game_dict=games_dict
    )

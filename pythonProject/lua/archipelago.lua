require("scripts.autotracking.item_mapping")
require("scripts.autotracking.location_mapping")

CUR_INDEX = -1
--SLOT_DATA = nil

ALL_LOCATIONS = {}
SLOT_DATA = {}

MANUAL_CHECKED = true
ROOM_SEED = "default"
TROLL_PLAYER = false

if Highlight then
    HIGHLIGHT_LEVEL= {
        [0] = Highlight.Unspecified,
        [10] = Highlight.NoPriority,
        [20] = Highlight.Avoid,
        [30] = Highlight.Priority,
        [40] = Highlight.None,
        [100] = Highlight.Unspecified, --Filler
        [101] = Highlight.Priority, --Progression
        [102] = Highlight.NoPriority, --Useful
        [103] = Highlight.Priority, -- Prog + Useful
        [104] = Highlight.Avoid, --Trap
        [105] = Highlight.Priority, -- Prog + Trap
        [106] = Highlight.NoPriority, -- Useful + Trap
        [107] = Highlight.Priority, -- Prog + Useful + Trap
    }
end

Troll_Lookup = {
    ["solarcell"] = true,
    ["earthor"] = true,
}

---function to build a pretty-printable representation of a provided table
---@param o table
---@param depth? integer
---@return string
function DumpTable(o, depth)
    if depth == nil then
        depth = 0
    end
    if type(o) == 'table' then
        local tabs = ('\t'):rep(depth)
        local tabs2 = ('\t'):rep(depth + 1)
        local s = '{\n'
        for k, v in pairs(o) do
            if type(k) ~= 'number' then
                k = '"' .. k .. '"'
            end
            s = s .. tabs2 .. '[' .. k .. '] = ' .. DumpTable(v, depth + 1) .. ',\n'
        end
        return s .. tabs .. '}'
    else
        return tostring(o)
    end
end

---helper function that gets called when a LocationSection has changed state.
---checks if the interaction was from the server or manual.
---if manual, puts it into a cache for keeping that LocationSection toggled when reconnecting
---@param location LocationSection
function LocationHandler(location)
    if MANUAL_CHECKED then
        local custom_storage_item = Tracker:FindObjectForCode("manual_location_storage").ItemState
        if not custom_storage_item then
            return
        end
        if Archipelago.PlayerNumber == -1 then -- not connected
            if ROOM_SEED ~= "default" then -- seed is from previous connection
                ROOM_SEED = "default"
                custom_storage_item.MANUAL_LOCATIONS["default"] = {}
            else -- seed is default
            end
        end
        local full_path = location.FullID
        if not custom_storage_item.MANUAL_LOCATIONS[ROOM_SEED] then
            custom_storage_item.MANUAL_LOCATIONS[ROOM_SEED] = {}
        end
        if location.AvailableChestCount < location.ChestCount then --add to list
            -- print("add to list")
            custom_storage_item.MANUAL_LOCATIONS[ROOM_SEED][full_path] = location.AvailableChestCount
        else --remove from list of set back to max chestcount
            -- print("remove from list")
            custom_storage_item.MANUAL_LOCATIONS[ROOM_SEED][full_path] = nil
        end
    end
    -- local custom_storage_item = Tracker:FindObjectForCode("manual_location_storage").ItemState
    -- print(DumpTable(storage_item.ItemState.MANUAL_LOCATIONS))
    ForceUpdate() --
end

--function to force an update even if the interaction within poptracker noramlly would not call for a state update
function ForceUpdate()
    local update = Tracker:FindObjectForCode("update")
    if update == nil then
        return
    end
    update.Active = not update.Active
end


---resets a given item back to default or what's saved for the given seed in the pseuso-cache LuaItems
---@param item_type string table of the ItemCode and extra parameters from the Item_Mapping.lau
---@param item_obj JsonItem Tracker:FindObjectForCode(item) return object
---@param item_code string Reference for the custom LuaItem CachesItems
local function ItemReset(item_type, item_obj, item_code)
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

---resets a given location back to default or whats saved for the gives seed in the pseuso-cache LuaItems
---@param location string String of the Location or LocatioSection to reset
---@param location_obj JsonItem|LocationSection Tracker:FindObjectForCode(location) return object
---@param custom_storage_item table Reference for the custom LuaItem CachesItems
local function LocationReset(location, location_obj, custom_storage_item)
    if location:sub(1, 1) == "@" then
        ---@cast location_obj LocationSection
        if custom_storage_item.MANUAL_LOCATIONS[ROOM_SEED][location_obj.FullID] then
            location_obj.AvailableChestCount = custom_storage_item.MANUAL_LOCATIONS[ROOM_SEED][location_obj.FullID]
        else
            location_obj.AvailableChestCount = location_obj.ChestCount
        end
        location_obj.Highlight = HIGHLIGHT_LEVEL[40]
    else
        ---@cast location_obj JsonItem
        location_obj.Active = false
    end
end


--- Function to prepare custom LuaItems for caching, check for mischieve/traps, subscribe to datastorage
local function PreOnClear()
    PLAYER_ID = Archipelago.PlayerNumber or -1
	TEAM_NUMBER = Archipelago.TeamNumber or 0
    if PLAYER_ID > -1 then
        for key, _ in pairs(Troll_Lookup) do
            if string.find(string.lower(Archipelago:GetPlayerAlias(PLAYER_ID)), key, 1, true) ~= nil then
                TROLL_PLAYER = true
                break
            end
        end

        --- example for how to build a date object and how to check current user's date against it
        --local start_day_range = BuildTimeObj(nil, 3 , 31)
        --local end_day_range = BuildTimeObj(nil, 4 , 5)
        --DATE_CHECK_PASSED = CheckDateRange(start_day_range, end_day_range, os.time())
        --if TROLL_PLAYER == false and DATE_CHECK_PASSED then
        --    TROLL_PLAYER = true
        --end

        if #ALL_LOCATIONS > 0 then
            ALL_LOCATIONS = {}
        end
        for _, value in pairs(Archipelago.MissingLocations) do
            table.insert(ALL_LOCATIONS, #ALL_LOCATIONS + 1, value)
        end

        for _, value in pairs(Archipelago.CheckedLocations) do
            table.insert(ALL_LOCATIONS, #ALL_LOCATIONS + 1, value)
        end
        ---add more of those for other datastorage keys
        HINTS_ID = "_read_hints_"..TEAM_NUMBER.."_"..PLAYER_ID
        Archipelago:SetNotify({HINTS_ID}) --{HINTS_ID, other vars, ...}
        Archipelago:Get({HINTS_ID}) --{HINTS_ID, other vars, ...}
    end


    -- print(Archipelago.Seed)
    local seed_base = (Archipelago.Seed or tostring(#ALL_LOCATIONS)).."_"..Archipelago.TeamNumber.."_"..Archipelago.PlayerNumber
    if ROOM_SEED == "default" or ROOM_SEED ~= seed_base then -- seed is default or from previous connection

        ROOM_SEED = seed_base --something like 2345_0_12
        for _, custom_item_code in pairs({"manual_location_storage"}) do -- add more to the table if you created more storage cache items
            local custom_storage_item = Tracker:FindObjectForCode(custom_item_code).ItemState
            if custom_storage_item then
                if #custom_storage_item.MANUAL_LOCATIONS > 10 then
                    custom_storage_item.MANUAL_LOCATIONS[custom_storage_item.MANUAL_LOCATIONS_ORDER[1]] = nil
                    table.remove(custom_storage_item.MANUAL_LOCATIONS_ORDER, 1)
                end
                if custom_storage_item.MANUAL_LOCATIONS[ROOM_SEED] == nil then
                    custom_storage_item.MANUAL_LOCATIONS[ROOM_SEED] = {}
                    table.insert(custom_storage_item.MANUAL_LOCATIONS_ORDER, ROOM_SEED)
                end
            end
        end
    else -- seed is from previous connection
        -- do nothing
    end
end

---function that gets called when the pack connects to an AP server
---@param slot_data? table Slotdata send from AP server for the specific user/slot
function OnClear(slot_data)
    MANUAL_CHECKED = false
    local custom_storage_item = Tracker:FindObjectForCode("manual_location_storage").ItemState
    if custom_storage_item == nil then
        CreateLuaManualStorageItem("manual_location_storage")
        custom_storage_item = Tracker:FindObjectForCode("manual_location_storage").ItemState
    end
    -- repeat that here for every cache-storage item you create just to be safe

    PreOnClear()

    ScriptHost:RemoveWatchForCode("StateChanged")
    ScriptHost:RemoveOnLocationSectionHandler("location_section_change_handler")
    --SLOT_DATA = slot_data
    CUR_INDEX = -1
    -- reset locations
    for _, location_array in pairs(LOCATION_MAPPING) do
        for _, location in pairs(location_array) do
            if location then
				---@type LocationSection
                local location_obj = Tracker:FindObjectForCode(location)
                if location_obj then
                    LocationReset(location, location_obj, custom_storage_item)
                end
            end
        end
    end
    -- reset items
    for _, item_array in pairs(ITEM_MAPPING) do
        for _, item_pair in pairs(item_array) do
            local item_code = item_pair[1]
            local item_type = item_pair[2]
            -- print("on clear", item_code, item_type)
			---@type JsonItem
            local item_obj = Tracker:FindObjectForCode(item_code)
            if item_obj then
                ItemReset(item_type, item_obj, item_code)
            end
        end
    end
    PLAYER_ID = Archipelago.PlayerNumber or -1
    TEAM_NUMBER = Archipelago.TeamNumber or 0
    SLOT_DATA = slot_data
    -- if Tracker:FindObjectForCode("autofill_settings").Active == true then
    --     AutoFill(slot_data)
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

---Run every time an Item gets sent to the connected slot
---@param index integer running index for the items the connected slot has received so far
---@param item_id integer ID of the received item, matching the game's datapackage ID
---@param item_name string name of the item from the datapackage for the given itemID
---@param player_number integer slotnumber of the player who picked up the item
function OnItem(index, item_id, item_name, player_number)
    if index <= CUR_INDEX then
        return
    end
    local is_local = player_number == Archipelago.PlayerNumber
    CUR_INDEX = index;
    local item = ITEM_MAPPING[item_id]
    if not item or not item[1] then
        --print(string.format("OnItem: could not find item mapping for id %s", item_id))
        return
    end
    for _, item_pair in pairs(item) do
        local item_code = item_pair[1]
        local item_type = item_pair[2]
        local consumable_multiplier = tonumber(item_pair[3]) or 1

        local item_obj = Tracker:FindObjectForCode(item_code)
        if item_obj then
            if item_obj.Type == "toggle" then
                -- print("toggle")
                item_obj.Active = true
            elseif item_obj.Type == "progressive" then
                -- print("progressive")
                if item_obj.Active == true then
                    item_obj.CurrentStage = item_obj.CurrentStage + 1
                else
                    item_obj.Active = true
                end
            elseif item_obj.Type == "consumable" then
                -- print("consumable")
                item_obj.AcquiredCount = item_obj.AcquiredCount + item_obj.Increment * consumable_multiplier
            elseif item_obj.Type == "progressive_toggle" then
                -- print("progressive_toggle")
                if item_obj.Active then
                    item_obj.CurrentStage = item_obj.CurrentStage + 1
                else
                    item_obj.Active = true
                end
            end
        else
            print(string.format("OnItem: could not find object for code %s", item_code))
        end
    end
end

---called when a location gets cleared
---@param location_id integer ID of the location cleared from the datapackage
---@param location_name string name of the location cleared from the datapackage
function OnLocation(location_id, location_name)
    MANUAL_CHECKED = false
    local location_array = LOCATION_MAPPING[location_id]
    if not location_array or not location_array[1] then
        print(string.format("OnLocation: could not find location mapping for id %s", location_id))
        return
    end

    for _, location in pairs(location_array) do
        local location_obj = Tracker:FindObjectForCode(location)
        -- print(location, location_obj)
        if location_obj then
            if location:sub(1, 1) == "@" then
                (location_obj --[[@as LocationSection]]).AvailableChestCount = location_obj.AvailableChestCount - 1
            else
                (location_obj --[[@as JsonItem]]).Active = true
            end
        else
            print(string.format("OnLocation: could not find location_object for code %s", location))
        end
    end
    MANUAL_CHECKED = true
end

-- this Autofill function is meant as an example on how to do the reading from slot_data
-- and mapping the values to your own settings
-- ---@param slot_data table
-- function AutoFill(slot_data)
--     -- print(DumpTable(slot_data))

--     mapToggle={[0]=0,[1]=1,[2]=1,[3]=1,[4]=1}
--     mapToggleReverse={[0]=1,[1]=0,[2]=0,[3]=0,[4]=0}
--     mapTripleReverse={[0]=2,[1]=1,[2]=0}

--     slotCodes = {
--         map_name = {code="", mapping=mapToggle...}
--     }
--     -- print(Tracker:FindObjectForCode("autofill_settings").Active)
--     if Tracker:FindObjectForCode("autofill_settings").Active == true then
--         for settings_name, settings_value in pairs(slot_data) do
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

---@class APHintMessage
---@field receiving_player integer
---@field finding_player integer
---@field location integer
---@field item integer
---@field found boolean
---@field entrance string
---@field item_flags 0|1|2|3|4|5|6|7
---@field status 0|10|20|30|40

---function to update the Highlight of a LocationSection to represent the status of the hint that is present
---for that LocationSection
---@param locationID integer ID of the locations the hint is being given for
---@param status 0|10|20|30|40|100|101|102|103|104|105|106|107 status to determine the color of the hint glow
local function UpdateHints(locationID, status) -->
    if Highlight then
        -- print(locationID, status)
        local location_table = LOCATION_MAPPING[locationID]
        for _, location in ipairs(location_table) do
            if location:sub(1, 1) == "@" then
				---@type LocationSection
                local obj = Tracker:FindObjectForCode(location)

                if obj then
                    if TROLL_PLAYER and HIGHLIGHT_LEVEL[status] == Highlight.Avoid then
                        obj.Highlight = HIGHLIGHT_LEVEL[30]
                    else
                        obj.Highlight = HIGHLIGHT_LEVEL[status]
                    end
                else
                    print(string.format("No object found for code: %s", location))
                end
            end
        end
    end
end

---triggers as AP sends live updates from the server using a given key we subscribed to in Archipelago:SetNotify
---@param key string Name of the key that was used to send the message
---@param value table<integer, APHintMessage>
---@param old_value table<integer, APHintMessage>
function OnNotify(key, value, old_value)
    print("OnNotify", key, value, old_value)
    if value ~= old_value and key == HINTS_ID then
        Tracker.BulkUpdate = true
        for _, hint in ipairs(value) do
            if hint.finding_player == Archipelago.PlayerNumber then
                if hint.status == 0 then
                    UpdateHints(hint.location, 100+hint.item_flags)
                else
                    UpdateHints(hint.location, hint.status)
                end
            end
        end
        Tracker.BulkUpdate = false
    end
end

---triggers on connecting to AP when we receive this message from the server after providing a given key to Archipelago:Get
---@param key string Name of the key that was used to send the message
---@param value table<integer, APHintMessage>
function OnNotifyLaunch(key, value)
    if key == HINTS_ID then
        Tracker.BulkUpdate = true
        for _, hint in ipairs(value) do
            if hint.finding_player == Archipelago.PlayerNumber then
                if hint.status == 0 then
                    UpdateHints(hint.location, 100+hint.item_flags)
                else
                    UpdateHints(hint.location, hint.status)
                end
            end
        end
        Tracker.BulkUpdate = false
    end
end

-------------------
---this section is only for special things that are time of day or day of year dependant if you really want to do stuff
---stuff like this

---@param start_date number BuildTimeObj() return aka unix timestamp
---@param end_date number BuildTimeObj() return aka unix timestamp
---@param target_date number BuildTimeObj() return aka unix timestamp
function CheckDateRange(start_date, end_date, target_date)
    local one_day = 86400
    local check_result = false
    for day_obj = start_date, end_date, one_day do
        check_result = CheckDate(day_obj, target_date)
        if check_result then
            return true
        end
    end
end

---@param target_date number BuildTimeObj() return aka unix timestamp
---@param reference_time number? BuildTimeObj() return aka unix timestamp
function CheckDate(reference_time, target_date)
    local today = os.date("*t")
    local reference_day =  os.date("*t", target_date)
    if reference_time then
        today = os.date("*t", reference_time)
    end
    return today.year == reference_day.year and
    today.month == reference_day.month and
    today.day == reference_day.day
end

---helper function to return a date object for the provided day
---@param year number?
---@param month number?
---@param day number?
---@param hour number?
---@param minute number?
---@param second number?
---@return integer
function BuildTimeObj(year, month, day, hour, minute, second)
    local today = os.date("*t", os.time())
    return os.time(
        {
            year = year or today.year,
            month = month or today.month,
            day = day or today.day,
            hour = hour or 0,
            min = minute or 0,
            sec = second or 0
        }
    )
end
-------------------


--doc
--hint layout
-- {
--     ["receiving_player"] = 1,
--     ["class"] = Hint,
--     ["finding_player"] = 1,
--     ["location"] = 67361,
--     ["found"] = false,
--     ["item_flags"] = 2, --bitflag --> 0=filler, 1=progression, 2=useful, 4=trap
--     ["status"] = 40, --bitflag --> 0=Unspecified, 10=NoPriority, 20=Avoid, 30=Priority, 40=None
--     ["entrance"] = ,
--     ["item"] = 66062,
-- }


----------
---remnant from when poptracker had issues loading some larger/heavy packs
--function OnClearHandler(slot_data)
--    local clear_timer = os.clock()
--
--    ScriptHost:RemoveWatchForCode("StateChange")
--    -- Disable tracker updates.
--    Tracker.BulkUpdate = true
--    -- Use a protected call so that tracker updates always get enabled again, even if an error occurred.
--    local ok, err = pcall(OnClear, slot_data)
--    -- Enable tracker updates again.
--    if ok then
--        -- Defer re-enabling tracker updates until the next frame, which doesn't happen until all received items/cleared
--        -- locations from AP have been processed.
--        local handlerName = "AP OnClearHandler"
--        local function frameCallback()
--            ScriptHost:AddWatchForCode("StateChange", "*", StateChanged)
--            ScriptHost:RemoveOnFrameHandler(handlerName)
--            Tracker.BulkUpdate = false
--            ForceUpdate()
--            print(string.format("Time taken total: %.2f", os.clock() - clear_timer))
--        end
--        ScriptHost:AddOnFrameHandler(handlerName, frameCallback)
--    else
--        Tracker.BulkUpdate = false
--        print("Error: OnClear failed:")
--        print(err)
--    end
--end
-- if you want to use the graph based logic you need to create lua representations of your region/connectors/location wit the `.new()` function
-- connect multiple of these representations with the provided one_way/two_ways() methods.
-- this will build a graph that gets traveres via the :discover() method.

--To-Do: add a tutorial for the grpah absed logic into the README

-- ScriptHost:AddWatchForCode("ow_dungeon details handler", "ow_dungeon_details", owDungeonDetails)


{game_name_lua}_location = {}
{game_name_lua}_location.__index = {game_name_lua}_location

accessLVL= {
    [0] = "none",
    [1] = "partial",
    [3] = "inspect",
    [5] = "sequence break",
    [6] = "normal",
    [7] = "cleared",
    [false] = "none",
    [true] = "normal",
}

-- Table to store named locations
---@type table<string, {game_name_lua}_new_return>
NAMED_LOCATIONS = {}
local stale = true
local accessibilityCache = {}
local accessibilityCacheComplete = false
local currentParent = nil
local currentLocation = nil
local indirectConnections = {}


---simple helper to insert into tables and create them if not already present
---@param er_table table table to insert into
---@param key string|integer|boolean key to use to insert into the table
---@param value any value to insert into the table
function Table_insert_at(er_table, key, value)
    if er_table[key] == nil then
        er_table[key] = {}
    end
    table.insert(er_table[key], value)
end

--- checks if a given location is reacable in any way from any of the starting points and returns an accessibilityLevel
--- @param name string
--- @return accessibilityLevel
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
        accessibilityCache = {}
        indirectConnections = {}
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


---@class {game_name_lua}_new_return
---@field accessibility function
---@field connect_one_way function
---@field connect_one_way_entrance function
---@field connect_two_ways function
---@field connect_two_ways_entrance function
---@field connect_two_ways_entrance_door_stuck function
---@field connect_two_ways_stuck function
---@field discover function
---@field name string
---@field side string?
---@field baseWorldstate "light"|"dark"|""
---@field worldstate "light"|"dark"|""
---@field exits table<integer, {[1]:alttp_location_new_return, [2]:function}>
---@field keys integer
--you can add more stuff here for sure

-- creates a lua object for the given name. it acts as a representation of a overworld region or indoor location and
-- tracks its connected objects via the exit-table

-- creates a lua object for the given name. it acts as a representation of an overworld region or indoor location and tracks its connected objects via the exit-table
--add as many things as you like, just make sure to fill and use them properly. and maybe typehint it like shown above
---@param name string
---@return alttp_location_new_return
function {game_name_lua}_location.new(name)
    local self = setmetatable({}, {game_name_lua}_location)
    if name then
        NAMED_LOCATIONS[name] = self
        self.name = name
    else
        NAMED_LOCATIONS[name] = self
        self.name = tostring(self)
    end


    -------
    -- tyes help to denote if its interior or exterior/OW location/region
    if string.find(self.name, "_inside") then
        self.side = "inside"
    elseif string.find(self.name, "_outside") then
        self.side = "outside"
    else
        self.side = ""
    end

    --only usefull for ER stuff
    self.baseWorldstate = origin
    self.worldstate = origin
    -------


    self.exits = {}
    self.keys = math.huge

    return self
end

---function to give a default value during rule evaluations of no other rule got specified.
---@return integer
local function always()
    return ACCESS_NORMAL
end

---marks a 1-way connections between 2 "locations/regions" in the source "locations" exit-table with rules if provided
---@param exit string|alttp_location_new_return alttp_location_new_return or code/name
---@param rule? function
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
    self.exits[#self.exits + 1] = { exit, rule }
end

---marks a 2-way connection between 2 locations. acts as a shortcut for 2 connect_one_way-calls
---@param exit string|alttp_location_new_return alttp_location_new_return or code/name
---@param rule? function
function {game_name_lua}_location:connect_two_ways(exit, rule)
    self:connect_one_way(exit, rule)
    exit:connect_one_way(self, rule)
end

-- creates a 1-way connection from a region/location to another one via a 1-way connector like a ledge, hole,
-- self-closing door, 1-way teleport, ...
---@param name string arbitrary name for the connection. isnt used anywhere
---@param exit string|alttp_location_new_return alttp_location_new_return or code/name
---@param rule? function
function {game_name_lua}_location:connect_one_way_entrance(name, exit, rule)
    if rule == nil then
        rule = always
    end
    self.exits[#self.exits + 1] = { exit, rule }
end

-- creates a connection between 2 locations that is traversable in both ways using the same rules both ways
-- acts as a shortcut for 2 connect_one_way_entrance-calls
---@param name string arbitrary name for the connection. isnt used anywhere
---@param exit string|alttp_location_new_return alttp_location_new_return or code/name
---@param rule? function
function {game_name_lua}_location:connect_two_ways_entrance(name, exit, rule)
    if exit == nil then -- for ER
        return
    end
    self:connect_one_way_entrance(name, exit, rule)
    exit:connect_one_way_entrance(name, self, rule)
end

-- creates a connection between 2 locations that is traversable in both ways but each connection follow different rules.
-- acts as a shortcut for 2 connect_one_way_entrance-calls
---@param name string arbitrary name for the connection. isnt used anywhere
---@param exit string|alttp_location_new_return alttp_location_new_return or code/name
---@param rule1? function
---@param rule2? function
function {game_name_lua}_location:connect_two_ways_entrance_door_stuck(name, exit, rule1, rule2)
    self:connect_one_way_entrance(name, exit, rule1)
    exit:connect_one_way_entrance(name, self, rule2)
end

-- technically redundant but well
-- creates a connection between 2 locations that is traversable in both ways but each connection follow different rules.
-- acts as a shortcut for 2 connect_one_way-calls
---@param exit string|alttp_location_new_return alttp_location_new_return or code/name
---@param rule1? function
---@param rule2? function
function {game_name_lua}_location:connect_two_ways_stuck(exit, rule1, rule2)
    self:connect_one_way(exit, rule1)
    exit:connect_one_way(self, rule2)
end

---checks for the accessibility of a regino/location given its own exit requirements
---@return 0|1|2|3|4|5|6|7
function {game_name_lua}_location:accessibility()
    -- only executed when run from a rules within a connection
    if currentLocation ~= nil and currentParent ~= nil then
        if indirectConnections[currentLocation] == nil then
            indirectConnections[currentLocation] = {}
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

---function to start walking the graph them this location
---@param accessibility 0|1|2|3|4|5|6|7
---@param keys integer
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

Entry_point = {game_name_lua}_location.new("Entry_point")

---helperfunction that is used to force a grpah update on every state change within poptracker.
function StateChanged()
    stale = true
    -- entry_point:discover(AccessibilityLevel.Normal, 0)
end

ScriptHost:AddWatchForCode("StateChanged", "*", StateChanged)
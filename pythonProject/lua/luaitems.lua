---function to check if the item can provide a given code.
---you can have it check and return true for multiple codes but for simplicity only the name is
---a valid code by default from the builder
---@param self LuaItem
---@param code string
---@return boolean
local function CanProvideCodeFunc(self, code)
    return code == self.Name
end

---function that get triggered when left clicking a lua items as hosted item or in an itemgrid
---will do whatever you want it to
---@param self LuaItem
local function OnLeftClickFunc(self)
    -- your custom handling for clicks here
    -- return true
end

---function that get triggered when right clicking a lua items as hosted item or in an itemgrid
---will do what ever you want it to
---@param self LuaItem
local function OnRightClickFunc(self)
    -- your custom handling for clicks here
    -- return true
end

---function that get triggered when middle clicking a lua items as hosted item or in an itemgrid
---will dp whatever you want it to
---@param self LuaItem
local function OnMiddleClickFunc(self)
    -- your custom handling for clicks here
    -- return true
end

---function to check if, depending on the current state of the item, a certain code will be provided
---this can be much more complex but since we only use 1 code and this one should always be returned
---if you dont return a code here the item will be "disabled" in the maps/itemgrid
---and "enabled" if it provides the code
---@param self LuaItem
---@param code string
---@return integer
local function ProvidesCodeFunc(self, code)
    if CanProvideCodeFunc(self, code) then

            return 1
        end
    return 0
end

---save function triggered on closing popotracker to have a state to restore later on. specific to custom preudo-cache LuaItems
---@param self LuaItem
---@return table
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

---function triggered on loading the pack to restore the lat saves state. specific to custom preudo-cache LuaItems
---@param self LuaItem
---@param data table
local function LoadManualLocationStorageFunc(self, data)
    if data ~= nil and self.Name == data.Name then
        -- load everything from ItemState in here separately
        self.ItemState.MANUAL_LOCATIONS = data.MANUAL_LOCATIONS
        self.ItemState.MANUAL_LOCATIONS_ORDER = data.MANUAL_LOCATIONS_ORDER
        self.Icon = ImageReference:FromPackRelativePath(data.Icon)
    else
    end
end

-------
---there are more functions present by default that are unused in the example
--local function PropertyChangedFunc()
--    -- print("PropertyChangedFunc")
--end
--local function ItemState()
--end
--local function Name()
--end
--local function Icon ()--> ImageReference:FromPackRelativePath()
--end
--local function Type()
--end

------

---creates an empty pseudo cache item to store various states for up to 10 seeds to restroe when reconncing to those.
---mainly intended for manually marked off locations like shops or inspected locations OR for item states that have been
---manually set because they are hard to infer from game/server state
---@param name string
---@return LuaItem
function CreateLuaManualStorageItem(name)
    local self = ScriptHost:CreateLuaItem()
    -- self.Type = "custom"
    self.Name = name --code --
    self.Icon = ImageReference:FromPackRelativePath("/images/items/closed_Chest.png")
    self.ItemState = {
        MANUAL_LOCATIONS = {
            ["default"] = {}
        }, --[[@as table<string, string[]>]]
        MANUAL_LOCATIONS_ORDER = {}
        -- you can add many more custom stuff in here
    } --[[@as table<string, any>]]

    self.CanProvideCodeFunc = CanProvideCodeFunc
    self.OnLeftClickFunc = OnLeftClickFunc -- your_custom_leftclick_function_here
    self.OnRightClickFunc = OnRightClickFunc -- your_custom_rightclick_function_here
    self.OnMiddleClickFunc = OnMiddleClickFunc -- your_custom_middleclick_function_here
    self.ProvidesCodeFunc = ProvidesCodeFunc
    self.SaveFunc = SaveManualLocationStorageFunc
    self.LoadFunc = LoadManualLocationStorageFunc
    return self
end
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
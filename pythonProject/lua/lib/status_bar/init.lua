Tracker:AddItems("scripts/lib/status_bar/items.json")

local function PopulateStatusBar(slot_data)
    -- If the slot data contains the version of the apworld used for generation
    -- you can uncomment the below line of code and provide the appropriate
    -- slot data key to show it in the status bar alongside the game name

    --local version = slot_data["apworld_version"]

    local game = Archipelago:GetPlayerGame(Archipelago.PlayerNumber)
    local game_version = "Game: "..game
    if version ~= nil then
        game_version = game_version.." ("..version..")"
    end

    local clear = #Archipelago.CheckedLocations
    local missing = #Archipelago.MissingLocations
    local locations = "Locations (on connection): "..clear.."/"..(clear + missing)

    local seed = Archipelago.Seed
    seed = "Seed: "..seed
    
    local status = game_version.."        "..locations.."        "..seed

    local status_bar = Tracker:FindObjectForCode("status_bar")
    status_bar.BadgeText = status
    
    if game ~= "{game_name}" then
        status_bar.BadgeTextColor = '#ff0000'
        status_bar.BadgeText = 'Incorrect slot for game! '..status
    else
        status_bar.BadgeTextColor = '#ffffff'
    end
end
Archipelago:AddClearHandler("PopulateStatusBar", PopulateStatusBar)
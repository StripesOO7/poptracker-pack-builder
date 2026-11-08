Tracker:AddItems("scripts/lib/recent_items/items.json")
Tracker:AddLayouts("scripts/lib/recent_items/layout.json")

function ResetRecentItemFeed()
    for i = 1,6 do
        local recent_item_obj = Tracker:FindObjectForCode('recent-item-'..i)
        recent_item_obj:SetOverlayAlign("left")
        recent_item_obj.BadgeText = ""
        recent_item_obj.Icon = "scripts/lib/recent_items/empty.png"
    end
end

function AddToRecentItemFeed(item_code, item_id, item_name)
    local item_obj = Tracker:FindObjectForCode(item_code)
    if not item_obj then
        print(string.format("AddToRecentItemFeed: could not find object for code %s", item_code))
        return
    end
    
    for i = 6,2,-1 do
        local prev_item = Tracker:FindObjectForCode('recent-item-'..i)
        local next_item = Tracker:FindObjectForCode('recent-item-'..(i - 1))
        prev_item.BadgeText = next_item.BadgeText
        prev_item.Icon = next_item.Icon
    end
    
    local newest_item = Tracker:FindObjectForCode('recent-item-1')
    newest_item.BadgeText = "         "..item_name
    newest_item.Icon = item_obj.Icon:match("([^:]+):?")
end

ResetRecentItemFeed()
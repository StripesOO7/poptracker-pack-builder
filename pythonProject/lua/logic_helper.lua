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

---helper to convert boolean return values to accessibility values for graph evaluation
---@param result boolean
---@return accessibilityLevel
function A(result)
    if result then
        return ACCESS_NORMAL
    end
    return ACCESS_NONE
end

---Takes in an arbitrary amount of arguments which are accessibilityLevels, booleans, item codes,
---or functions that will return one of the previous three, and combines these values and
---returns the minimum shared accessibility</br>
---basically evaluates "are all requirements met?"
---@param ... function|string|boolean|accessibilityLevel
---@return accessibilityLevel
function ALL(...)
    local args = { ... }
    local min = ACCESS_NORMAL
    for _, v in ipairs(args) do
        if type(v) == "function" then
            v = v()
        elseif type(v) == "string" then
            v = HAS(v)
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

---Takes in an arbitrary amount of arguments which are accessibilityLevels, booleans, item codes,
---or functions that will return one of the previous three, and combines these values and
---returns the maximum accessibility of any provided argument</br>
---basically evaluates "is any 1 of the requirements met?"
---@param ... function|string|boolean|accessibilityLevel
---@return accessibilityLevel
function ANY(...)
    local args = { ... }
    local max = ACCESS_NONE
    for _, v in ipairs(args) do
        if type(v) == "function" then
            v = v()
        elseif type(v) == "string" then
            v = HAS(v)
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

---function to determine if a given item has been obtained/is active or has the needed amount
---@param item string
---@param amount? integer
---@param amountInLogic? integer
---@return accessibilityLevel
function HAS(item, amount, amountInLogic)
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

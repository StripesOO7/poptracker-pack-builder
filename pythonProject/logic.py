import json
import os
import tkinter as tk

from typing import Literal

DEFAULT_RULES = {
    "True_": True,
    "False_": False,
    # "AtLeast": Has,
    # "And": ALL,
    # "Or": ANY,
    # "Has": HAS,
    # "HasAll": ALL(Has),
    # "HasAny": ANY(Has),
    # "HasAllCounts": ALL(Has),
    # "HasAnyCount": ANY(Has),
    "HasFromList": True,
    "HasFromListUnique": True,
    "HasGroup": True,
    "HasGroupUnique": True,
    "CanReachLocation": True,
    "CanReachRegion": True,
    "CanReachEntrance": True,
}
DEFAULT_OPERATORS = {
    "eq": "==",
    "ne": "!=",
    "gt": ">",
    "lt": "<",
    "ge": ">=",
    "le": "<=",
    "contains": "contains",
    "in": "in"
}


def read_json_rules(path:str) -> dict:
    with open(path, "r") as rule_builder:
        rules = json.load(rule_builder)
    for rule in rules:
        rule["name"] = normalize_names(rule["name"], "location")
    return rules

def normalize_names(name:str, case:Literal["location", "item"]) -> str:
    delimiter = [" - ", ": ", ") "]
    replacement = ["/", "/", ")/"]
    escape = ["\\", "\'", "\""]
    forbidden = ["<", ">", ":", "|", "?", "*"]
    match case:
        case "location":
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
        case "item":
            for escape_char in escape:
                if escape_char in name:
                    # name = name.replace(f"{escape_char}", f"\\{escape_char}")
                    name = name.replace(f"{escape_char}", "")
    return name
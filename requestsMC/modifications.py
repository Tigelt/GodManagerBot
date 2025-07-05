import json
from difflib import get_close_matches


# JSON с товарами модификациями открываю и чекаю умное сходство 
def load_modifications():
    with open("modifications.json", "r", encoding='utf-8') as f:
        return json.load(f)

def find_closest_modification(name, variants_dict, cutoff=0.75):
    name = name.lower().strip()
    matches = get_close_matches(name, variants_dict.keys(), n=1, cutoff=cutoff)
    if matches:
        return matches[0], variants_dict[matches[0]]
    else:
        return None, None


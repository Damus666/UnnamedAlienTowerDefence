import os
import json
import typing

objects: dict[str] = {}
types_objects: dict[str, list] = {}
types_types: dict[str, type] = {}
types_counter: dict[str, int] = {}
types_names_objects: dict[str, dict[str]] = {}
types_ids_objects: dict[str, dict[int]] = {}

class Scriptable:
    type: str
    name: str
    id: int
    
    def __init_subclass__(cls) -> None:
        global types_objects, types_types, types_counter, types_names_objects, types_ids_objects
        types_objects[cls.__name__] = []
        types_types[cls.__name__] = cls
        types_counter[cls.__name__] = 0
        types_names_objects[cls.__name__] = {}
        types_ids_objects[cls.__name__] = {}
     
    def __str__(self):
        return f"{self.name}: {self.type}"
    
    def __repr__(self):
        res = "\n{ "+f"{self.name}: {self.type}\n"
        for varname in dir(self):
            if not varname.startswith("__") and not varname.endswith("__") and varname not in ["name", "type"]:
                varvalue = getattr(self, varname)
                if not callable(varvalue):
                    res += f"\t{varname} = {varvalue}\n"
        return res+"}"
    
    def optional(self, name):
        return not hasattr(self, name)
    
    def init(self):
        ...
        
    def cmp(self, other: "Scriptable"):
        return self.type == other.type and self.id == other.id
    
    def cmp_type(self, other: "Scriptable"):
        return self.type == other.type
    
    @classmethod
    def get(cls, name)->typing.Self:
        return get_of(cls.__name__, name)
    
    @classmethod
    def get_all(cls)->list[typing.Self]:
        return get_all(cls.__name__)

def load(folder: str):
    global objects, types_objects
    for dirpath, _, files in os.walk(folder):
        for file in files:
            file_name, extension = file.split(".")
            if extension == "json":
                with open(dirpath+"/"+file, "r") as file_buffer:
                    json_data = json.load(file_buffer)
                    scriptable = types_types[json_data["type"]]()
                    scriptable.type = json_data["type"]
                    scriptable.name = file_name
                    scriptable.id = types_counter[json_data["type"]]
                    types_counter[json_data["type"]] += 1
                    for attrname, attrvalue in json_data.items():
                        setattr(scriptable, attrname, attrvalue)
                    objects[file_name] = scriptable
                    types_objects[json_data["type"]].append(scriptable)
                    types_names_objects[json_data["type"]][scriptable.name] = scriptable
                    types_ids_objects[json_data["type"]][scriptable.id] = scriptable
                    scriptable.init()
                    
def get_from_name(name: str):
    return objects[name]

def get_of(type_name: str, name: str):
    return types_names_objects[type_name][name]
    
def get_of_id(type_name: str, id_: int):
    return types_ids_objects[type_name][id_]

def get_all(type_name: str):
    return types_objects[type_name]
                    
"""
Special thanks to PyFish for most of the UCI code.
"""
from typing import *


class Option:
    """Types:
    check (on/off), spin (numerical value), combo (choice), button, string

    All types can accept a function, to be called when the option is changed.

    Note that the UCI protocal specifies that invalid inputs are ignored:
    so we do nothing if the user inputs an invalid value."""
    
    class Check:
        """Value true/false."""
        
        def __init__(self, name: str, default: bool, func: callable = None):
            self.name = name
            self.default = default
            self.value = default
            self.func = func
        
        def set(self, value: str):
            value = bool(value.lower())
            self.value = value
            if self.func:
                self.func(value)
        
        def __str__(self):
            return f"option name {self.name} type check default {self.default}"
    
    class Spin:
        """Numerical value."""
        
        def __init__(self, name: str, default: int, min_value: int, max_value: int, func: callable = None):
            self.name = name
            self.default = default
            self.value = default
            self.min_value = min_value
            self.max_value = max_value
            self.func = func
        
        def set(self, value: str):
            value = int(value)
            if value < self.min_value or value > self.max_value:
                return
            
            self.value = value
            if self.func:
                self.func(value)
        
        def __str__(self):
            return f"option name {self.name} type spin default {self.default} min {self.min_value} max {self.max_value}"
    
    class Combo:
        """One choice from many."""
        
        def __init__(self, name: str, default: str, choices: list, func: callable = None):
            self.name = name
            self.default = default
            self.value = default
            self.choices = choices
            self.func = func
        
        def set(self, value: str):
            if value not in self.choices:
                raise ValueError(f"Invalid choice: '{value}'")
            self.value = value
            if self.func:
                self.func(value)
        
        def __str__(self):
            return f"option name {self.name} type combo default {self.default} var {' '.join(self.choices)}"
    
    class Button:
        """Carries out an action.
        A function must be passed as argument, to be called when the button is pressed."""
        
        def __init__(self, name: str, func: callable):
            self.name = name
            self.func = func
        
        def set(self, value):
            self.func(value)
        
        def __str__(self):
            return f"option name {self.name} type button"
    
    class String:
        """A string."""
        
        def __init__(self, name: str, default: str, func: callable = None):
            self.name = name
            self.default = default
            self.value = default
            self.func = func
        
        def set(self, value: str):
            self.value = value
            if self.func:
                self.func(value)
        
        def __str__(self):
            return f"option name {self.name} type string default {self.default}"
    
    class SpinOrCombo:
        """Either a Spin or a Combo. Automatically detects type."""
        
        def __init__(self, name: str, default: Union[int, str], min_value: int, max_value: int, choices: list,
                     func: callable = None):
            self.name = name
            self.default = default
            self.value = default
            self.min_value = min_value
            self.max_value = max_value
            self.choices = choices
            self.func = func
        
        def set(self, value: str):
            if value in self.choices:
                self.value = value
            else:
                try:
                    value = int(value)
                except ValueError:
                    return
                if value < self.min_value or value > self.max_value:
                    return
                self.value = value
            if self.func:
                self.func(value)
        
        def __str__(self):
            # We register this as type string in order to please UCI interfaces.
            return f"option name {self.name} type string default {self.default} " \
                   f"min {self.min_value} max {self.max_value} var {' '.join(self.choices)}"


""" -------------------- """


# Option specific functions
def on_engine_param_change(unused):
    """Called when the engine parameters are changed."""
    from engine_engine import setoptions_engine
    setoptions_engine()

def on_max_depth_change(unused):
    import engine_search_h
    engine_search_h.MAX_DEPTH = option("MAX_DEPTH")

def on_max_horizon_change(unused):
    import engine_search_h
    engine_search_h.MAX_HORIZON = option("MAX_HORIZON")

def parse_engine_option_str(option_str):
    """Format: setoption name {ADD_OPTION/REMOVE_OPTION} value {option_name} value {option_value}"""
    # split by 'name', then get the part of {option_name} and {option_value}
    # option_str here is just "{option_name} value {option_value}"
    option_name = option_str.split("value")[0].strip()
    option_value = option_str.split("value")[1].strip()
    return option_name, option_value

def on_add_engine_option(option_str):
    """Called when an engine option is added."""
    import engine_engine
    option_name, option_value = parse_engine_option_str(option_str)
    engine_engine.engine_options[option_name] = option_value
    
def on_remove_engine_option(option_str):
    """Called when an engine option is removed."""
    import engine_engine
    option_name, _ = parse_engine_option_str(option_str)
    del engine_engine.engine_options[option_name]
    

# UCI Options
options = {
    "ENGINE_PATH": Option.String("ENGINE_PATH", "stockfish"),
    "MAX_MOVES": Option.Spin("MAX_MOVES", 2, 1, 100),
    "Nodes": Option.SpinOrCombo("Nodes", "auto", 0, 1 << 32, ["auto"]),
    "Nodes scale": Option.Spin("Nodes scale", 750, 0, 1000),
    "MAX_DEPTH": Option.Spin("MAX_DEPTH", 256, 64, 1 << 16, on_max_depth_change),
    "MAX_HORIZON": Option.Spin("MAX_HORIZON", 30, 2, 1024, on_max_horizon_change),
    "debug": Option.Check("debug", False),
    
    # Default engine options
    "Threads": Option.Spin("Threads", 1, 1, 1024, func=on_engine_param_change),
    "Hash": Option.Spin("Hash", 256, 1, 1 << 25, func=on_engine_param_change),
    "MultiPV": Option.Spin("MultiPV", 1, 1, 500, func=None),
    
    # Command to add/remove engine options
    "ADD_OPTION": Option.String("ADD_OPTION", "", on_add_engine_option),
    "REMOVE_OPTION": Option.String("REMOVE_OPTION", "", on_remove_engine_option),
    
    "Move Overhead": Option.Spin("Move Overhead", 100, 0, 5000),
}


def setoption(name: str, value: str = None):
    """Set an option."""
    if name not in options:
        raise KeyError
    options[name].set(value)


def option(name: str):
    """Get value of an option."""
    if name not in options:
        return
    return options[name].value


def options_str():
    """Return a string of all options."""
    return "\n".join([str(_) for _ in options.values()])

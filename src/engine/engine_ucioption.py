"""
Special thanks to PyFish for most of the UCI code.
"""
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
                self.func()
        
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
            try:
                value = int(value)
            except ValueError:
                return
            if value < self.min_value or value > self.max_value:
                return
            
            self.value = value
            if self.func:
                self.func()
        
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
                return
            self.value = value
            if self.func:
                self.func()
        
        def __str__(self):
            return f"option name {self.name} type combo default {self.default} var {' '.join(self.choices)}"
    
    class Button:
        """Carries out an action.
        A function must be passed as argument, to be called when the button is pressed."""
        
        def __init__(self, name: str, func: callable):
            self.name = name
            self.func = func
        
        def set(self, value):
            self.func()
        
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
                self.func()
        
        def __str__(self):
            return f"option name {self.name} type string default {self.default}"

"""
--------------------
"""

# Option specific functions
def on_engine_param_change():
    from engine_engine import init_engine
    init_engine()
    
# UCI Options
options = {
    "ENGINE_PATH": Option.String("ENGINE_PATH", "stockfish"),
    "MAX_MOVES": Option.Spin("MAX_MOVES", 5, 1, 100),
    "Nodes": Option.Spin("Nodes", 100000, 0, 1<<32),
    "debug": Option.Check("debug", False),
    
    "Threads": Option.Spin("Threads", 1, 1, 1024, func=on_engine_param_change),
    "Hash": Option.Spin("Hash", 16, 1, 1<<25, func=on_engine_param_change),
    
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
    
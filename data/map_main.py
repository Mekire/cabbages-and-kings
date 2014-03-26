from . import map_prepare, tools
from .map_states import edit


def main():
    """Add states to control here."""
    app = tools.Control(map_prepare.ORIGINAL_CAPTION)
    state_dict = {"WORLD" : None,
                  "EDIT" : edit.Edit()
                  }
    app.state_machine.setup_states(state_dict, "EDIT")
    app.main()

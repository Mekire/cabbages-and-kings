from . import map_prepare,tools
from .map_states import edit


def main():
    """Add states to control here."""
    run_it = tools.Control(map_prepare.ORIGINAL_CAPTION)
    state_dict = {"WORLD" : None,
                  "EDIT" : edit.Edit()
                  }
    run_it.setup_states(state_dict,"EDIT")
    run_it.main()

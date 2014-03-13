"""
The main function is defined here. It simply creates an instance of
tools.Control and adds the game states to its dictionary using
tools.Control.setup_states.  There should be no need (theoretically) to edit
the tools.Control class.  All modifications should occur in this module
and in the prepare module.
"""

from . import prepare,tools
from .states import title, splash, select, game


def main():
    """Add states to control here."""
    app = tools.Control(prepare.ORIGINAL_CAPTION)
    state_dict = {"SPLASH" : splash.Splash(),
                  "TITLE"  : title.Title(),
                  "SELECT"  : select.Select(),
                  "GAME"   : game.Game(),
##                  'REGISTER'  : register.Register()
                  }
    app.setup_states(state_dict, "SPLASH")
    app.main()

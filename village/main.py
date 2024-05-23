from village.app.data import data
from village.app.utils import utils
from village.gui.gui import Gui

# start the GUI
gui = Gui()

# write the start message
utils.log("VILLAGE Started", destinations=[data.events])

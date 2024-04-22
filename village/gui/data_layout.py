from village.gui.layout import Layout


class DataLayout(Layout):
    def __init__(self, window):
        super().__init__(window)
        self.draw()

    def draw(self):
        self.disable(self.data_button)

        self.label = self.create_and_add_label(
            text="DATA", row=10, column=10, width=30, height=2, color="black"
        )

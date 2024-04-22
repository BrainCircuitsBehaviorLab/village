from village.gui.layout import Layout


class MainLayout(Layout):
    def __init__(self, window):
        super().__init__(window)
        self.draw()

    def draw(self):
        self.disable(self.main_button)

        self.image = self.create_and_add_image(
            row=10,
            column=10,
            width=192,
            height=30,
            file="mouse_village.png",
        )

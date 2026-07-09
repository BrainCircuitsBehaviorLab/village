from village.custom_classes.task_base import TaskBase


class DirectFunctionsBase:
    """
    Override this class in your project to define functions triggered directly.
    For example, you can trigger these functions from the behaviour controller, the
    camera trigger, or the GUI buttons.
    These functions can not accept arguments because they are triggered directly, but
    they can use self.task and then use some of the variables or settings of the
    task.

    Example:
        class DirectFunctions(DirectFunctionsBase):
            def function1(self):
                sound_device.load(
                    left=self.task.stimulus_sound, right=self.task.stimulus_sound
                    )
                sound_device.play()

            def function2(self):
                duration = self.task.stimulus_duration
                x_pos = self.task.stimulus_x_pos
                y_pos = self.task.stimulus_y_pos
                image_file = self.task.image_file
                draw_function = draw_image_generator(screen, duration, x_pos, y_pos)
                screen.load_draw_function(draw_function)
                screen.load_image(image_file)
    """

    def __init__(self) -> None:
        self.task: TaskBase = TaskBase()

from village.custom_classes.scale_trigger_base import ScaleTriggerBase


class ScaleTrigger(ScaleTriggerBase):
    """Records when the animal steps on and off the box scale, in the trial
    data of any running task.

    The weight is read every self.period seconds. When it goes above
    ON_GRAMS, a "ScaleOn" event is registered; when it drops back below
    OFF_GRAMS, a "ScaleOff" event. The gap between the two thresholds keeps a
    weight that wobbles around one value from producing a burst of events.

    They are Raspberry Pi events (saved with the Raspberry Pi clock whether or
    not the task uses a controller), and those arriving between trials are not
    recorded. The heaviest weight seen while on the scale is written on the box
    camera when the animal steps off.

    Adjust both thresholds to your animals and to where the scale is (under a
    small platform, under the whole floor of the box...).
    """

    ON_GRAMS = 10.0
    OFF_GRAMS = 5.0

    def __init__(self) -> None:
        super().__init__()
        self.period = 0.1  # seconds between readings
        self.on_scale = False
        self.max_weight = 0.0
        self.last_task = self.task

    def on_weight(self, weight: float, timestamp: float) -> None:
        # The same ScaleTrigger is reused from session to session: start over
        # when a new task begins.
        if self.task is not self.last_task:
            self.last_task = self.task
            self.on_scale = False
            self.max_weight = 0.0

        if not self.on_scale and weight > self.ON_GRAMS:
            self.on_scale = True
            self.max_weight = weight
            self.task.register_raspberry_event("ScaleOn", timestamp)
        elif self.on_scale and weight < self.OFF_GRAMS:
            self.on_scale = False
            self.task.register_raspberry_event("ScaleOff", timestamp)
            self.task.cam_box.write_text(f"SCALE: {self.max_weight:.1f} g")
        elif self.on_scale:
            self.max_weight = max(self.max_weight, weight)

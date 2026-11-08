## raspberry_stimulus_menu.py

No controller: a demo of the screen stimuli, not a training task. Every trial shows a menu of rectangles on the touchscreen; touching one shows a different stimulus for a few seconds. The touches are reacted to in [touch_trigger.py](touch_trigger.md).

The image, the image with alpha (transparent background) and the video come with the example project, in its `media` folder:

```{image} media/image.png
:alt: image.png, a cartoon mouse
:width: 150px
```
```{image} media/image_alpha.png
:alt: image_alpha.png, a cheese wedge with a transparent background
:width: 150px
```

{download}`image.png <media/image.png>`, {download}`image_alpha.png <media/image_alpha.png>`, {download}`video.mp4 <media/video.mp4>` (5 seconds of Conway's Game of Life, with a short melody).

{download}`Download raspberry_stimulus_menu.py <files/raspberry_stimulus_menu.py>`

```{literalinclude} files/raspberry_stimulus_menu.py
:language: python
```

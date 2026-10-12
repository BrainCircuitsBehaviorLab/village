## Detailed System Description

The Training Village (TV) trains rodents (mice or rats) in behavioral tasks
automatically, with no experimenter present: each animal, identified by its RFID
tag, walks from its home cage through a corridor into an operant box, runs a
training session, and goes back home. Animals go to the box whenever they want,
within the schedule you set for each one, and the system moves each of them through
the training stages on its own.

The system is built upon a lightweight aluminum framework and an acrylic base, which
securely supports the animal home cages and a connecting corridor that leads into an
operant box.

```{figure} /_static/corridor.png
:class: zoomable
:alt: Training Village Overview

Home cages and corridor.
```

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item}
:columns: 12 12 8 8

The entire ecosystem is centralized around a **Raspberry Pi 5** running Python code.
The Raspberry Pi directly manages the following primary peripherals:

- **Dual Camera System:** Two
  [Raspberry Pi Camera Module 3 (NoIR, Wide-Angle)](https://www.raspberrypi.com/products/camera-module-3/?variant=camera-module-3-noir-wide)
  cameras — one integrated directly into the corridor and another to be positioned inside the operant box.
- **Audio System (Optional):** A
  [Raspberry Pi DAC Pro](https://www.raspberrypi.com/products/dac-pro/) can be
  attached to deliver acoustic stimuli during behavioral tasks.
- **Interactive Interface (Optional):** A touchscreen can be integrated to present
  visual stimuli and record the animals' touch responses.
:::

:::{grid-item}
:columns: 12 12 4 4

```{image} /_static/raspberry.png
:alt: Raspberry Pi 5
:width: 100%
```
:::
::::

The system is compatible with any operant box. It works natively with
[**Bpod**](https://sanworks.io/). An [**Arduino**](https://www.arduino.cc/) or any
other microcontroller can also be used by communicating with it over
a serial port. The same approach can be used for other behavioral
controllers, such as [**Harp**](https://harp-tech.org/) or
[**PyControl**](https://pycontrol.readthedocs.io/).

Thanks to high-speed communication between the Raspberry Pi and the behavioral
controller (if used), experimental workloads are efficiently split between the two
devices:

- **The Raspberry Pi** handles heavy computational and multimedia tasks, such as
  real-time position monitoring via video-tracking, triggering localized sound or
  video playback based on events or animal coordinates, and managing LEDs and servo
  motors.
- **The Behavioral Controller (Bpod/Arduino)** can be used for time-critical or
  high-precision events, such as photogate detection, delivering water rewards at a
  behavioral port, or sending rapid TTL signals to external hardware like
  optogenetic lasers.

A custom main HAT is mounted onto the Raspberry Pi 5 to handle power and data
distribution. It receives a 5V power supply and connects to two specialized
satellite boards using Ethernet cables for data and separate jack-connector cables
for power. All the parts are listed in [List of Parts & Design Files](../resources/list_of_parts.md),
and the [Assembly Guide](../resources/hardware.md) shows how to put them together.

---

### Satellite Board 1: The Corridor Board

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item}
:columns: 12 12 8 8

Controls the following peripherals installed in the corridor:

- **RFID Reader:** Used in tandem with the video camera to reliably identify
  individual animals.
- **Weighing Scale:** Features an integrated load cell within the corridor to
  automatically weigh animals every time they return to their home cages.
- **Visible & Infrared (IR) Lighting:** Manages a day/night cycle to safeguard animal welfare while providing IR night-vision for the cameras during dark phases.
- **2 Servo Motors:** To control the corridor doors, providing automated access to
  the operant box. Two additional connectors on the board allow up to two more servo
  motors to be added — for example, to raise or lower a water bottle in the home
  cage.
- **Integrated Temperature & Humidity Sensor:** Continuously monitors the corridor
  environment.
:::

:::{grid-item}
:columns: 12 12 4 4

```{image} /_static/corridor_board.png
:alt: Corridor Board
:width: 100%
```
:::
::::

---

### Satellite Board 2: The Box Board

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item}
:columns: 12 12 8 8

Features optional connectors for the user to utilize as needed:

- **7 Servo Motor Connectors:** For managing mechanisms inside the box.
- **Internal Visible & Infrared (IR) Lighting Connectors:** To provide illumination
  inside the box.
- **Addressable/Programmable LED Connector:** To connect programmable LED strips or
  matrices, specifically dedicated to delivering precise visual stimuli during tasks.
- **Load Cell Connector:** Allows a load cell or force sensor to be installed inside
  the operant box.
- **Switch Connector:** Allows a mechanical switch to be connected. It is wired to
  the GPIO input pin, which goes ON when the switch is activated and OFF
  when it is released.
:::

:::{grid-item}
:columns: 12 12 4 4

```{image} /_static/box_board.png
:alt: Box Board
:width: 100%
```
:::
::::

```{figure} /_static/hardware.png
:class: zoomable
:alt: Hardware

The Raspberry Pi with the main HAT, and the two satellite boards with their
connectors. Click to enlarge.
```

---

### Software & Experimental Workflow

The Training Village software is written in Python and runs on the Raspberry Pi.
It is usually operated remotely from a laptop or PC, and it can also be monitored and
controlled from a phone through a [Telegram bot](../preparation/telegram.md).

To run and manage experiments, the user creates a
[project folder](../protocols/project_structure.md) containing two essential Python
components:

- **Task Scripts:** User-defined scripts that govern the behavioral tasks, handle communication with the underlying controller (Bpod, Arduino, etc.), and log data in the standardized format required by the TV ecosystem.
- **Training Protocol Script:** A master automation script that dictates the
  animal's learning progression. It evaluates performance metrics after sessions,
  updates task variables, and automatically transitions the subject to advanced
  training stages once pre-set benchmarks are met.

Below is a summary of the standard operational cycle:

```{figure} /_static/workflow.png
:class: zoomable
:alt: Standard Operational Cycle Workflow

The standard operational cycle. Click to enlarge.
```

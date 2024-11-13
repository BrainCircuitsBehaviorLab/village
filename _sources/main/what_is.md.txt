The Training Village is a system designed for the continuous automated training of rodents in complex cognitive tasks. In the system, RFID-tagged animals live in groups and access individually the behavioral box (e.g. an operant chamber) to perform tasks at any time, rain or shine.

The Training Village is  designed to wrap around your own task protocols and integrate with your behavioral control system although we provide it in tandem with a general-purpose touchscreen chamber and some standard task protocols run by BPod (by [Sanworks][SANWORKS]).

Because the system is running 24/7, it is designed to be remotely controlled. It can be accessed at any time to check on the system's status or to monitor the state of the animals through various cameras viewing the entry corridor and the inside of the behavioral box. Additionally, a configurable alert system integrated with Telegram allows users to receive real-time notifications regarding system status or the conditions of the animals.

By completely removing direct human intervention in the behavioral testing, the Training Village can decrease the stress of the animals caused by transportation and handling, providing the stable and predictable conditions that are optimal for animal cognitive testing. Moreover, the automatisation of the full process can impact positively in the work of the researchers carrying out these experiments which can be very repetitive and boring.

The Training Village is freely available, and legally protected by [GPL version 3][GPL] and [OSHW version 1][OSHW] licenses.

<video controls width="100%">
  <source src="_static/video.m4v" type="video/mp4">
</video>

## How Does It Work?

![training_village](_static/training_village.png)

The system is composed of several key components: the housing where the animals live, the behavioral box where tasks are performed, and the corridor that regulates access to the behavioral box.

###The Housing
The animals live together in one or more cages, which promotes better welfare. Any type of cage can be used, as long as it is connected to the corridor via a tube. We offer a solution with 2 or 4 cages connected by transparent acrylic tubes, which can serve different purposes (e.g., one cage with food, another for nesting). Optionally, RFID sensors can be installed in the tubes connecting the cages ([Eco-HAB][ECO]) to gather more data on the animals’ social behavior.

### The Behavioral Box
Any type of behavioral box can be used. We provide two design options: one with auditory stimuli and three behavioral ports, and another with a touchscreen and one reward port. The system is designed to interact with behavioral boxes controlled by Bpod (using Python). Integration with other controllers, such as Bcontrol or Bonsai, is currently under development.

### The Corridor
This is the central part of the system, consisting of a plastic corridor equipped with an RFID sensor, a weight scale, and a camera. Using a mechanism with two doors, animals can enter the behavioral box under certain conditions. The corridor sizes, shape and the motorized doors have been exhaustively tested and improved to efficiently control single-animal entrances using the minimum space possible. The entire system is controlled by a Raspberry Pi, which handles sending and receiving signals from electronic devices, controls the cameras, and runs the software that controls the whole system.
Most of the elements in the mouse version of the corridor are 3D-printed, except for the doors and the corridor lid, which are made of white laser-cut acrylic. The design files are shared in the How to build the training village (link) section. We also share the rat version, which includes more laser-cut parts and fewer printed components due to its larger size and the increased strength required.

![Corridor](_static/corridor.png)

## The Controller
The software that controls the system runs reliably 24/7 while monitoring the animals, regulating their access to the behavioral box, initiating tasks, and updating data.

We determined that the best option for running this system is the Raspberry Pi, due to its reliability, low power consumption, and cost-effectiveness. These mini-computers are designed to excel in tasks like these, come equipped with specialized video cameras, and can interact with a wide range of electronic devices.

To simplify interaction with the hardware components, we have designed a custom Raspberry Pi HAT (Hardware Attached on Top). This HAT provides the necessary connectors to control two servo motors, an RFID reader, a weight sensor, and a temperature sensor. This setup ensures seamless device connectivity, delivering a plug-and-play experience.

![controller](_static/raspberry_hat.png)

## System usage
The Training Village has been rigorously tested in the [Brain Circuits and Behavior Lab][LAB] with different groups of mice and two different behavioral tasks: a multi-choice delayed response task and a foraging task. Recently, the system has been adapted to rats in the [Animal Minds Lab][RAT].

The Training Village can work continuously for months, allowing the automatic collection of large datasets of cognitive-demanding tasks that often require long training periods (e.g. 20-40 sessions). It automatically adjusts training difficulty, timing, and session duration based on each animal’s motivation and needs,  letting subjects learn at their own pace while ensuring a balanced usage of the behavioral box. On average, mice in the Training Village perform about three sessions per day, with a significant preference for the nighttime. Behavioral box occupancy depends on the group size. With groups of 14 animals housed together in the system, the average occupancy is around 70% of the total daytime (i.e. 16.8 hours of training per day), indicating a high usage at this capacity. Subjects' performance and motivation are comparable to the manual training, yet with a significant reduction in the experimenter involvement.

![plots](_static/plots.png)

## Open Source
Training Village is an open-source project. You can find the code in our [GitHub repository][REPO] and all the necessary resources to build it in the [resources section][RESOURCES].

Developed by:

<a href="https://braincircuitsbehavior.org"
style="color:#8B00FF; font-size:24px; font-weight:normal;
font-family:'Futura', sans-serif; text-decoration:none;">
BRAIN CIRCUITS AND BEHAVIOR LAB
</a>

Contact: [marinraf@gmail.com](mailto:marinraf@gmail.com)

[SANWORKS]: https://sanworks.io
[GPL]: https://www.gnu.org/licenses/quick-guide-gplv3.pdf
[OSHW]: https://www.oshwa.org/definition/
[ECO]: https://elifesciences.org/articles/19532
[LAB]: https://braincircuitsbehavior.org
[RAT]: https://www.uab.cat/en/incuab/fx-animalmindslab-en
[REPO]: https://github.com/BrainCircuitsBehaviorLab/village/
[RESOURCES]: /resources_index.rst

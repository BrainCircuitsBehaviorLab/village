## The Controller

The software that controls the system must run reliably 24/7 while monitoring the animals, regulating their access to the behavioral box, initiating tasks, and updating data.

We determined that the best option for running this system is the Raspberry Pi, due to its reliability, low power consumption, and cost-effectiveness. These mini-computers are designed to excel in tasks like these, come equipped with specialized video cameras, and can interact with a wide range of electronic devices.

To simplify interaction with the hardware components, we have designed a custom Raspberry Pi HAT (Hardware Attached on Top). This HAT provides the necessary connectors to control two servo motors, an RFID reader, a weight sensor, and a temperature sensor. This setup ensures seamless device connectivity, delivering a plug-and-play experience.

![controller](_static/raspberry_hat.png)

<br>

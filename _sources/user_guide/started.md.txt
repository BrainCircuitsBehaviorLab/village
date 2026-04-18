## Getting Started

### Preliminary Steps
If you have purchased a Training Village from us, you will receive all the necessary parts for assembly, which requires only a screwdriver. Assembly is straightforward and can be easily completed by following these [instructions][INSTRUCTIONS].

We provide the Raspberry Pi along with an SD card that contains both the operating system (Raspberry Pi OS) and all required software pre-installed.

Once assembled, simply insert the SD card into the Raspberry Pi, and you can proceed with the system [configuration][CONFIGURE], including setting up remote access over the internet and backups.

### Build-It-Yourself
If you prefer to build the Training Village yourself, start by reviewing the complete list of required parts and the plans for all 3D-printable pieces [here][PLANS]. Once you have your own Raspberry Pi, you can either [download][ISO] an image of the SD card to copy onto your device or [install everything from scratch][SOFTWARE].

### Launching the System
Once the system is built and remote access is configured, the keyboard, mouse, and screen can be disconnected, unless a screen is needed in the behavioral box. From this point on, the system will be managed entirely from an external computer connected remotely.
Now, the Training Village is ready to start. Simply open a terminal window and type:

```
run_village
```

This command activates a Python environment (.env) and runs the file `/home/raspberry/village/village/main.py` which will start the program and display the GUI.


[INSTRUCTIONS]: /how_to_build/assembly_instructions.md
[CONFIGURE]: /initial_configuration_index.rst
[PLANS]: /how_to_build/list_of_parts.md
[ISO]: /resources/ISO.md
[SOFTWARE]: /how_to_build/software_installation.md

If you have purchased a Training Village from us, you will receive all the necessary parts for assembly, which requires only a screwdriver. Assembly is straightforward and can be easily completed by following these [instructions][INSTRUCTIONS].

We provide the Raspberry Pi along with an SD card that contains both the operating system (Raspberry Pi OS) and all required software pre-installed.

Once assembled, simply insert the SD card into the Raspberry Pi, and you can proceed with the system [configuration][CONFIGURE], including setting up remote access over the internet and backups.

Now you are ready to start the Training Village, simply open a terminal window and type:
```
run_village
```

This command activates a Python environment (.env) and runs the file `/home/raspberry/village/village/main.py`.

When the GUI launches, the system automatically checks connections with essential components (such as cameras, temperature sensors, weight sensors, etc.). If any connection cannot be established, a warning message will display, and the Training Village will enter debug mode. For help resolving connection issues, refer to the [troubleshooting section][TROUBLE].

After that, refer to the [user guide][GUIDE] to learn how to implant the animals with RFID capsules and how to operate the system effectively.

### Build-It-Yourself
If you prefer to build the Training Village yourself, start by checking the complete list of required parts and the plans for all 3D-printable pieces [here][PLANS]. Once you have your own Raspberry Pi, you can either [download][ISO] an image of the SD card to copy onto your device or [install everything from scratch][SOFTWARE].

[INSTRUCTIONS]: /how_to_build/assembly_instructions.md
[CONFIGURE]: /initial_configuration_index.rst
[GUIDE]: /user_guide_index.rst
[PLANS]: /how_to_build/list_of_parts.md
[ISO]: /resources/ISO.md
[SOFTWARE]: /how_to_build/software_installation.md

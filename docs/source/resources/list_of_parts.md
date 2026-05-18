## List of Parts

Below are the detailed component lists required to print, source, and assemble the Training Village system.

The estimated total cost of materials ranges between **€1,200 and €1,500** (or equivalent currency). This estimate varies depending on the local cost of 3D printing and custom laser-cutting or CNC machining services for the acrylic components.

---

### Raspberry Pi Components

*   1 x [Raspberry Pi 5 (8GB RAM)](https://www.raspberrypi.com/products/raspberry-pi-5/?variant=raspberry-pi-5-8gb)
*   1 x [Raspberry Pi Active Cooler](https://www.raspberrypi.com/products/active-cooler/)
*   1 x [Official Raspberry Pi 27W USB-C Power Supply](https://www.raspberrypi.com/products/power-supply/)
*   1 x High-Speed microSD Card (256 GB)
*   2 x [Raspberry Pi Camera Module 3 (NoIR, Wide-Angle)](https://www.raspberrypi.com/products/camera-module-3/?variant=camera-module-3-noir-wide)
*   2 x [Official Raspberry Pi Camera Cable (50 cm, Standard-to-Mini)](https://www.raspberrypi.com/products/camera-cable/?variant=camera-cable-std-mini-500)
*   *(Optional — required only for acoustic stimuli tasks):* 1 x [Raspberry Pi DAC Pro](https://www.raspberrypi.com/products/dac-pro/)

---

### Corridor Components

*   1 x Dedicated 5V, 3A Power Supply (for the Main HAT)
*   1 x 1 kg Load Cell (Note: The custom Corridor Board integrates the HX711 amplifier onboard; only the physical load cell sensor is needed)
*   2 x TowerPro MG995 Servo Motors (11 kg/cm torque, 5V)
*   1 x [SparkFun RFID Reader ID-20LA (125 kHz)](https://www.sparkfun.com/rfid-reader-id-20la-125-khz.html)
*   1 x Set of RFID Glass Transponder Capsules (125 kHz) for animal identification
*   1 x Complete set of 3D-printed structural components
*   1 x 3mm Matte White Acrylic Base (laser-cut or CNC-machined)
*   2 x 3mm Matte White Acrylic Doors (laser-cut or CNC-machined)
*   1 x 4mm Transparent Acrylic Lid (laser-cut or CNC-machined)
*   4 x 4mm Transparent Acrylic Lid Stops (laser-cut or CNC-machined)

#### Small Setup Configuration (2 Home Cages)
*   2 x Standard Home Cages (modified with custom cutouts to host the connecting tubes)
*   2 x Transparent Acrylic Connection Tubes (30 mm internal diameter, 34 mm external diameter, 16 cm length)
*   1 x Set of 20x20 mm Aluminum T-Slot Profiles (Slot 6 mm), cut to the following lengths:
    *   2 x 55 cm length
    *   4 x 45 cm length
    *   6 x 34 cm length

#### Large Setup Configuration (4 Home Cages / EcoHab Compatible)
*   4 x Standard Home Cages (modified with custom cutouts to host the connecting tubes)
*   3 x Transparent Acrylic Connection Tubes (30 mm internal diameter, 34 mm external diameter, 26 cm length)
*   1 x Transparent Acrylic Connection Tube (30 mm internal diameter, 34 mm external diameter, 10 cm length)
*   1 x Set of 20x20 mm Aluminum T-Slot Profiles (Slot 6 mm), cut to the following lengths:
    *   2 x 55 cm length
    *   4 x 65 cm length
    *   6 x 38 cm length

---

### Custom PCB Boards & Electronics

*   1 x Custom Main HAT Board
*   1 x Custom Corridor Board
*   1 x Custom Box Board
*   2 x Standard Ethernet Cables (used to interface the Corridor and Box satellite boards to the Main HAT)
*   2 x 5x20 mm Fuses (250V, 5A)
*   1 x Extra-tall GPIO Header Spacer/Extension (for vertical clearance between the Pi and the Main HAT)

---

### Illumination & Accessories

*   4 x [OPB100-EZ IR Emitter][https://www.digikey.es/es/products/detail/tt-electronics-optek-technology/OPB100-EZ/1636778?srsltid=AfmBOooF1n3jWZgLVXz4OcnRL9aMCuzfMDHeN47At1cGJwLUa2YQTyzU]
*   1 x 5V White LED Strip
*   1 x Home Cage Water Bottle
*   1 x Automated Food Dispenser Module

---

### Open-Source Design Files

*   📦 **[Download 3D Printing Files (.STL)][3D]**
*   🛠️ **[Download CAD/CNC Machining Files (.DXF)][CAD]**
*   🔌 **[Download PCB Gerber & Schematics Files][PCB]**

---

For a comprehensive, step-by-step walkthrough on assembling these components, please refer to the [System Assembly Guide][ASSEMBLY].

[3D]: /_static_3d.zip/
[CAD]: /_static/cad.zip
[PCB]: /_static/pcb_boards.zip
[ASSEMBLY]: /resources/hardware.md

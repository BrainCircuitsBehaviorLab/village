## Temperature or Weight Sensor Connection Error

The system is configured to work with address = 0x45 for the temperature sensor (DFRobot HX711) and address = 0x64 for the weight sensor (CQRobot SHT31). If you are using different models or if the devices are not recognized, follow these steps to verify that the addresses are correct:

1. Check that the devices are correctly connected to the raspberry.
2. Install the detection tools:
```
sudo apt-get install -y i2c-tools
```
3. Run the tools:
```
i2cdetect -y 1
```
4. Change the addresses in the python code by modifying the corresponding settings in
`village/settings.py` (extra_settings).


<br><br><br>

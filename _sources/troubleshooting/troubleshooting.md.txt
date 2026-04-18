### Temperature or Weight Sensor Connection Error

The system is configured to work with address = 0x45 for the temperature sensor (DFRobot HX711) and address = 0x48 for the weight sensor (CQRobot SHT31). If you are using different models or if the devices are not recognized, follow these steps to verify that the addresses are correct:

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


### Wrong numpy version

If you get an error about an incompatible NumPy version, it may be because installing another package that depends on NumPy automatically pulled NumPy 2 via pip.
If NumPy 2 was installed by mistake, you can remove it with:

```
pip uninstall numpy
```

This removes only the pip-installed version (NumPy 2), while keeping the system version (NumPy 1) that was installed via apt.
Next, run:
```
pip uninstall package-name
```
to remove the package that caused NumPy 2 to be installed.
Then install a specific version of that package that is compatible with NumPy 1, for example:
```
pip install package-name==<version>
```

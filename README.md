# meross-adapter

Meross smart plug adapter for Mozilla WebThings Gateway.

# Supported Devices

## Tested and Working

* MSS110
* MSS310

## Untested but _Should Work_

* MSS210
* MSS425
* MSS620

# Requirements

If you're running this add-on outside of the official gateway image for the Raspberry Pi, i.e. you're running on a development machine, you'll need to do the following (adapt as necessary for non-Ubuntu/Debian):

```
sudo apt install python3-dev libnanomsg-dev
sudo pip3 install nnpy
sudo pip3 install git+https://github.com/mozilla-iot/gateway-addon-python.git
```

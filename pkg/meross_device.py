"""Meross adapter for Mozilla WebThings Gateway."""

from gateway_addon import Device
import threading
import time

from .meross_property import MerossProperty


_POLL_INTERVAL = 5


class MerossDevice(Device):
    """Meross device type."""

    def __init__(self, adapter, _id, meross_dev, channel=None):
        """
        Initialize the object.

        adapter -- the Adapter managing this device
        _id -- ID of this device
        meross_dev -- the meross device object to initialize from
        channel -- the channel index of this plug
        """
        Device.__init__(self, adapter, _id)
        self._type = ['OnOffSwitch', 'SmartPlug']
        self.type = 'onOffSwitch'

        self.meross_dev = meross_dev
        self.name = meross_dev._name
        self.description = meross_dev._type
        if not self.name:
            self.name = self.description

        if channel is not None:
            self.channel = channel
            self.name = '{} ({})'.format(self.name, channel)
        else:
            self.channel = 0

        self.properties['on'] = MerossProperty(
            self,
            'on',
            {
                '@type': 'OnOffProperty',
                'label': 'On/Off',
                'type': 'boolean',
            },
            self.on)

        if self.meross_dev.supports_electricity_reading():
            self._type.append('EnergyMonitor')

            self.properties['power'] = MerossProperty(
                self,
                'power',
                {
                    '@type': 'InstantaneousPowerProperty',
                    'label': 'Power',
                    'type': 'number',
                    'unit': 'Watt',
                    'readOnly': True,
                },
                self.power)

            self.properties['voltage'] = MerossProperty(
                self,
                'voltage',
                {
                    '@type': 'VoltageProperty',
                    'label': 'Voltage',
                    'type': 'number',
                    'unit': 'volt',
                    'readOnly': True,
                },
                self.voltage)

            self.properties['current'] = MerossProperty(
                self,
                'current',
                {
                    '@type': 'CurrentProperty',
                    'label': 'Current',
                    'type': 'number',
                    'unit': 'ampere',
                    'readOnly': True,
                },
                self.current)

        t = threading.Thread(target=self.poll)
        t.daemon = True
        t.start()

    def poll(self):
        """Poll the device for changes."""
        while True:
            time.sleep(_POLL_INTERVAL)

            for prop in self.properties.values():
                prop.update()

    @property
    def on(self):
        """Determine whether or not the device is on."""
        return self.meross_dev.get_status(channel=self.channel)

    @property
    def power(self):
        """Determine current power usage."""
        return self.meross_dev.get_electricity()['electricity']['power']

    @property
    def voltage(self):
        """Determine current voltage."""
        return self.meross_dev.get_electricity()['electricity']['voltage']

    @property
    def current(self):
        """Determine current current."""
        return self.meross_dev.get_electricity()['electricity']['current']

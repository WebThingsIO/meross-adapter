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
        self.name = meross_dev.name
        self.description = meross_dev.type
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
            False)

        if self.meross_dev.supports_electricity_reading():
            self._type.append('EnergyMonitor')

            self.properties['power'] = MerossProperty(
                self,
                'power',
                {
                    '@type': 'InstantaneousPowerProperty',
                    'label': 'Power',
                    'type': 'number',
                    'unit': 'watt',
                    'readOnly': True,
                },
                0)

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
                0)

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
                0)

        t = threading.Thread(target=self.poll)
        t.daemon = True
        t.start()

    def poll(self):
        """Poll the device for changes."""
        while True:
            if not self.meross_dev.online:
                self.connected_notify(False)
                continue

            try:
                on = self.meross_dev.get_status(channel=self.channel)
                self.properties['on'].update(on)

                if self.meross_dev.supports_electricity_reading():
                    e = self.meross_dev.get_electricity()
                    self.properties['power'].update(e['power'])
                    self.properties['voltage'].update(e['voltage'])
                    self.properties['current'].update(e['current'])

                self.connected_notify(True)
            except:  # noqa: E722
                # catching the exceptions from meross_iot just lead to more
                # exceptions being thrown. cool.
                self.connected_notify(False)

            time.sleep(_POLL_INTERVAL)

    def handle_toggle(self, value):
        """Handle a switch toggle."""
        self.properties['on'].update(value)

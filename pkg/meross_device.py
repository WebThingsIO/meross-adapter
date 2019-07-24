"""Meross adapter for Mozilla WebThings Gateway."""

from gateway_addon import Device
import threading
import time

from .meross_property import (
    MerossBulbProperty,
    MerossOpenerProperty,
    MerossPlugProperty,
)


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


class MerossBulb(MerossDevice):
    """Meross smart bulb type."""

    def __init__(self, adapter, _id, meross_dev, channel=None):
        """
        Initialize the object.

        adapter -- the Adapter managing this device
        _id -- ID of this device
        meross_dev -- the meross device object to initialize from
        channel -- the channel index of this plug
        """
        MerossDevice.__init__(self, adapter, _id, meross_dev, channel=channel)

        self._type = ['OnOffSwitch', 'Light']
        self.type = 'onOffLight'

        self.properties['on'] = MerossBulbProperty(
            self,
            'on',
            {
                '@type': 'OnOffProperty',
                'label': 'On/Off',
                'type': 'boolean',
            },
            False)

        if self.meross_dev.supports_light_control():
            self._type.append('ColorControl')

            color = self.meross_dev.get_light_color(channel=self.channel)
            if 'rgb' in color and color['rgb'] != -1:
                self.properties['color'] = MerossBulbProperty(
                    self,
                    'color',
                    {
                        '@type': 'ColorProperty',
                        'label': 'Color',
                        'type': 'string',
                    },
                    '#{:02x}'.format(color['rgb']))
            else:
                if 'temperature' in color and color['temperature'] != -1:
                    self.properties['colorTemperature'] = MerossBulbProperty(
                        self,
                        'colorTemperature',
                        {
                            '@type': 'ColorTemperatureProperty',
                            'label': 'Color Temperature',
                            'type': 'integer',
                            'unit': 'kelvin',
                            'minimum': 2700,
                            'maximum': 6500,
                        },
                        color['temperature'])

                if 'luminance' in color and color['luminance'] != -1:
                    self.properties['brightness'] = MerossBulbProperty(
                        self,
                        'brightness',
                        {
                            '@type': 'BrightnessProperty',
                            'label': 'Brightness',
                            'type': 'integer',
                            'unit': 'percent',
                            'minimum': 0,
                            'maximum': 100,
                        },
                        color['luminance'])

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
                status = self.meross_dev.get_status(channel=self.channel)
                self.properties['on'].update(status['onoff'])

                if self.meross_dev.supports_light_control():
                    color = \
                        self.meross_dev.get_light_color(channel=self.channel)

                    if 'color' in self.properties:
                        self.properties['color'].update(
                            '#{:02x}'.format(color['rgb'])
                        )
                    else:
                        if 'colorTemperature' in self.properties:
                            self.properties['colorTemperature'].update(
                                color['temperature'] *
                                (6500 - 2700) / 100 +
                                2700
                            )

                        if 'brightness' in self.properties:
                            self.properties['brightness'].update(
                                color['luminance']
                            )

                self.connected_notify(True)
            except:  # noqa: E722
                # catching the exceptions from meross_iot just lead to more
                # exceptions being thrown. cool.
                self.connected_notify(False)

            time.sleep(_POLL_INTERVAL)

    def handle_toggle(self, value):
        """Handle a switch toggle."""
        self.properties['on'].update(value)

    def handle_light_state(self, value):
        """Handle a color change."""
        if 'color' in self.properties:
            self.properties['color'].update(
                '#{:02x}'.format(value['rgb'])
            )
        else:
            if 'colorTemperature' in self.properties:
                self.properties['colorTemperature'].update(
                    value['temperature'] * (6500 - 2700) / 100 + 2700
                )

            if 'brightness' in self.properties:
                self.properties['brightness'].update(
                    value['luminance']
                )


class MerossOpener(MerossDevice):
    """Meross smart garage door opener type."""

    def __init__(self, adapter, _id, meross_dev, channel=None):
        """
        Initialize the object.

        adapter -- the Adapter managing this device
        _id -- ID of this device
        meross_dev -- the meross device object to initialize from
        channel -- the channel index of this plug
        """
        MerossDevice.__init__(self, adapter, _id, meross_dev, channel=channel)

        self._type = ['DoorSensor']
        self.type = 'binarySensor'

        self.properties['open'] = MerossOpenerProperty(
            self,
            'open',
            {
                '@type': 'OpenProperty',
                'label': 'Open',
                'type': 'boolean',
                'readOnly': True,
            },
            False)

        self.add_action('open', {})
        self.add_action('close', {})

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
                state = self.meross_dev.get_status()
                self.properties['open'].update(state)
                self.connected_notify(True)
            except:  # noqa: E722
                # catching the exceptions from meross_iot just lead to more
                # exceptions being thrown. cool.
                self.connected_notify(False)

            time.sleep(_POLL_INTERVAL)

    def handle_state(self, value):
        """Handle an open/close event."""
        self.properties['open'].update(value)

    def perform_action(self, action):
        """
        Perform the requested action.

        action -- the action object
        """
        action.start()

        try:
            if action.name == 'open':
                self.meross_dev.open_door()
                action.finish()
            elif action.name == 'close':
                self.meross_dev.close_door()
                action.finish()
            else:
                action.status = 'error'
                self.action_notify(action)
        except:  # noqa: E722
            action.status = 'error'
            self.action_notify(action)


class MerossPlug(MerossDevice):
    """Meross smart plug type."""

    def __init__(self, adapter, _id, meross_dev, channel=None):
        """
        Initialize the object.

        adapter -- the Adapter managing this device
        _id -- ID of this device
        meross_dev -- the meross device object to initialize from
        channel -- the channel index of this plug
        """
        MerossDevice.__init__(self, adapter, _id, meross_dev, channel=channel)

        self._type = ['OnOffSwitch', 'SmartPlug']
        self.type = 'onOffSwitch'

        self.properties['on'] = MerossPlugProperty(
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

            self.properties['power'] = MerossPlugProperty(
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

            self.properties['voltage'] = MerossPlugProperty(
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

            self.properties['current'] = MerossPlugProperty(
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

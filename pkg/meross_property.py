"""Meross adapter for Mozilla WebThings Gateway."""

from gateway_addon import Property


class MerossProperty(Property):
    """Meross property type."""

    def __init__(self, device, name, description, value):
        """
        Initialize the object.

        device -- the Device this property belongs to
        name -- name of the property
        description -- description of the property, as a dictionary
        value -- current value of this property
        """
        Property.__init__(self, device, name, description)
        self.set_cached_value(value)

    def update(self, value):
        """Update the current value, if necessary."""
        if value != self.value:
            self.set_cached_value(value)
            self.device.notify_property_changed(self)


class MerossBulbProperty(MerossProperty):
    """Meross bulb property type."""

    def set_value(self, value):
        """
        Set the current value of the property.

        value -- the value to set
        """
        if self.name == 'on':
            success = False
            if value:
                success = self.device.meross_dev.turn_on(
                    channel=self.device.channel
                )
            else:
                success = self.device.meross_dev.turn_off(
                    channel=self.device.channel
                )

            if success:
                self.update(value)
        elif self.name == 'color':
            rgb = int(value[1:], 16)
            self.device.meross_dev.set_light_color(
                channel=self.device.channel,
                capacity=5,
                rgb=rgb,
                luminance=100,
            )
            self.update(value)
        elif self.name == 'colorTemperature':
            temperature = int((value - 2700) / (6500 - 2700) * 100)

            luminance = 100
            if 'brightness' in self.device.properties:
                luminance = self.device.properties['brightness'].value

            self.device.meross_dev.set_light_color(
                channel=self.device.channel,
                capacity=6,
                temperature=temperature,
                luminance=luminance,
            )
            self.update(value)
        elif self.name == 'brightness':
            capacity = 4
            temperature = -1

            if 'colorTemperature' in self.device.properties:
                capacity = 6
                temperature = int(
                    (self.device.properties['colorTemperature'].value - 2700) /
                    (6500 - 2700) *
                    100
                )

            self.device.meross_dev.set_light_color(
                channel=self.device.channel,
                capacity=capacity,
                luminance=value,
                temperature=temperature,
            )
            self.update(value)


class MerossPlugProperty(MerossProperty):
    """Meross plug property type."""

    def set_value(self, value):
        """
        Set the current value of the property.

        value -- the value to set
        """
        if self.name == 'on':
            success = False
            if value:
                success = self.device.meross_dev.turn_on(
                    channel=self.device.channel
                )
            else:
                success = self.device.meross_dev.turn_off(
                    channel=self.device.channel
                )

            if success:
                self.update(value)


class MerossOpenerProperty(MerossProperty):
    """Meross garage door opener property type."""

    pass

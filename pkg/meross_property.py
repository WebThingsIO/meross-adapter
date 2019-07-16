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
                self.set_cached_value(value)
                self.device.notify_property_changed(self)

    def update(self, value):
        """Update the current value, if necessary."""
        if value != self.value:
            self.set_cached_value(value)
            self.device.notify_property_changed(self)

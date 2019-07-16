"""Meross adapter for Mozilla WebThings Gateway."""

from gateway_addon import Adapter, Database
from meross_iot.manager import MerossManager
from meross_iot.meross_event import MerossEventType
from meross_iot.cloud.devices.light_bulbs import GenericBulb
from meross_iot.cloud.devices.power_plugs import GenericPlug
from meross_iot.cloud.devices.door_openers import GenericGarageDoorOpener
import threading
import time

from .meross_device import MerossDevice


class MerossAdapter(Adapter):
    """Adapter for Meross smart home devices."""

    def __init__(self, verbose=False):
        """
        Initialize the object.

        verbose -- whether or not to enable verbose logging
        """
        self.name = self.__class__.__name__
        Adapter.__init__(self,
                         'meross-adapter',
                         'meross-adapter',
                         verbose=verbose)

        self.manager = None
        self.pairing = False

        database = Database(self.package_name)
        if database.open():
            config = database.load_config()

            if 'username' in config and len(config['username']) > 0 and \
                    'password' in config and len(config['password']) > 0:
                self.manager = MerossManager(
                    meross_email=config['username'],
                    meross_password=config['password']
                )

                self.manager.register_event_handler(self.event_handler)
                self.manager.start()

            database.close()

        self.start_pairing()

    def start_pairing(self, timeout=None):
        """
        Start the pairing process.

        timeout -- Timeout in seconds at which to quit pairing
        """
        if self.manager is None or self.pairing:
            return

        self.pairing = True

        for bulb in self.manager.get_devices_by_kind(GenericBulb):
            pass

        for plug in self.manager.get_devices_by_kind(GenericPlug):
            if not plug.online:
                continue

            n_channels = len(plug.get_channels())

            if n_channels > 1:
                for channel in range(0, len(plug.get_channels())):
                    _id = 'meross-{}-{}'.format(plug.uuid, channel)
                    if _id not in self.devices:
                        device = MerossDevice(self, _id, plug, channel=channel)
                        self.handle_device_added(device)
            else:
                _id = 'meross-{}'.format(plug.uuid)
                if _id not in self.devices:
                    device = MerossDevice(self, _id, plug)
                    self.handle_device_added(device)

        for opener in self.manager.get_devices_by_kind(GenericGarageDoorOpener):  # noqa: E501
            pass

        self.pairing = False

    def cancel_pairing(self):
        """Cancel the pairing process."""
        self.pairing = False

    def event_handler(self, obj):
        """Handle events from devices."""
        if not hasattr(obj, 'device'):
            return

        _id = 'meross-{}'.format(obj.device.uuid)

        devices = []
        if _id in self.devices:
            devices.append(self.devices[_id])
        elif hasattr(obj, 'channel_id'):
            _id = '{}-{}'.format(_id, obj.channel_id)

            if _id in self.devices:
                devices.append(self.devices[_id])
            else:
                return
        else:
            for k in self.devices.keys():
                if k.startswith('{}-'.format(_id)):
                    devices.append(self.devices[k])

        if len(devices) == 0:
            # If the device wasn't found, but this is an online event, try to
            # pair with it.
            if obj.event_type == MerossEventType.DEVICE_ONLINE_STATUS and \
                    obj.status == 'online':

                def delayed_pair(self):
                    time.sleep(5)
                    self.start_pairing()

                t = threading.Thread(target=delayed_pair, args=(self,))
                t.daemon = True
                t.start()

            return

        if obj.event_type == MerossEventType.DEVICE_ONLINE_STATUS:
            for device in devices:
                device.connected_notify(obj.status == 'online')
        elif obj.event_type == MerossEventType.DEVICE_SWITCH_STATUS:
            for device in devices:
                device.handle_toggle(obj.switch_state)
        elif obj.event_type == MerossEventType.DEVICE_BULB_SWITCH_STATE:
            pass
        elif obj.event_type == MerossEventType.DEVICE_BULB_STATE:
            pass
        elif obj.event_type == MerossEventType.GARAGE_DOOR_STATUS:
            pass

"""Meross adapter for Mozilla WebThings Gateway."""

from gateway_addon import Adapter, Database
from meross_iot.api import MerossHttpClient

from .meross_device import MerossDevice


_TIMEOUT = 3


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

        self.client = None

        database = Database(self.package_name)
        if database.open():
            config = database.load_config()

            if 'username' in config and len(config['username']) > 0 and \
                    'password' in config and len(config['password']) > 0:
                self.client = MerossHttpClient(
                    email=config['username'],
                    password=config['password']
                )

            database.close()

        self.pairing = False
        self.start_pairing(_TIMEOUT)

    def start_pairing(self, timeout):
        """
        Start the pairing process.

        timeout -- Timeout in seconds at which to quit pairing
        """
        if self.client is None or self.pairing:
            return

        self.pairing = True

        for dev in self.client.list_supported_devices():
            if not self.pairing:
                break

            n_channels = len(dev.get_channels())

            if n_channels > 1:
                for channel in range(0, len(dev.get_channels())):
                    _id = 'meross-{}-{}'.format(dev.device_id(), channel)
                    if _id not in self.devices:
                        device = MerossDevice(self, _id, dev, channel=channel)
                        self.handle_device_added(device)
            else:
                _id = 'meross-{}'.format(dev.device_id())
                if _id not in self.devices:
                    device = MerossDevice(self, _id, dev)
                    self.handle_device_added(device)

        self.pairing = False

    def cancel_pairing(self):
        """Cancel the pairing process."""
        self.pairing = False

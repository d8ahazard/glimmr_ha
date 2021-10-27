"""Helpers for Glimmr."""

from glimmr import GlimmrConnectionError, GlimmrError

from .const import LOGGER


def glimmr_exception_handler(func):
    """Decorate Glimmr calls to handle Glimmr exceptions.

    A decorator that wraps the passed in function, catches Glimmr errors,
    and handles the availability of the device in the data coordinator.
    """

    async def handler(self, *args, **kwargs):
        try:
            await func(self, *args, **kwargs)
            self.coordinator.update_listeners()

        except GlimmrConnectionError as error:
            LOGGER.error("Error communicating with API: %s", error)
            self.coordinator.last_update_success = False
            self.coordinator.update_listeners()

        except GlimmrError as error:
            LOGGER.error("Invalid response from API: %s", error)

    return handler

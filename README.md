![Lint](https://github.com/d8ahazard/glimmr_ha/workflows/Lint/badge.svg) ![Pylint](https://github.com/d8ahazard/glimmr_ha/workflows/Pylint/badge.svg)

# :bulb: glimmr_ha - V 0.1.1 (out for testing)

Initial commit.

## :muscle: Cha
## Installation via HACS (Home Assistant Community Store)
[![Hacs Installtion](http://img.youtube.com/vi/_LTA07ENpBE/0.jpg)](http://www.youtube.com/watch?v=_LTA07ENpBE "Wiz Lightbulbs and Home Assistant walkthrough - 2021 Phillips Hue Killer?")

## Install for testing

1. Logon to your HA or HASS with SSH
2. Got to the HA `custom_components` directory within the HA installation path (if this is not available - create this directory).
3. Run `cd custom_components`
4. Run `git clone https://github.com/d8ahazard/glimmr_ha` within the `custom_components` directory
5. Run `mv glimmr_ha/custom_components/glimmr_ha/* glimmr_ha/` to move the files in the correct diretory
6. Restart your HA/HASS service in the UI with `<your-URL>/config/server_control`
7. Add the bulbs either by:
   - HA UI by navigating to "Integrations" -> "Add Integration" -> "Glimmr"
   - Manually by adding them to `configuration.yaml`

Questions? Check out the github project [glimmr-python](https://github.com/d8ahazard/glimmr-python)

## Enable Debug
```YAML
logger:
    default: warning
    logs:
      homeassistant.components.glimmr_ha: debug
```

## HA config

## You can now use the HASS UI to add the devices/integration.

To enable the platform integration after installation add

```
light:
  - platform: glimmr_ha
    name: <Name of the device>
    host: <IP of the bulb>
  - platform: glimmr_ha
    name: <Name of the device#2>
    host: <IP of the bulb#2>
```

If you want to use the integration as switch

```
switch:
  - platform: glimmr_ha
    name: <Name of the device>
    host: <IP of the socket>
```

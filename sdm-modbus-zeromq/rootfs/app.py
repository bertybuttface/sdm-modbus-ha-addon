import json
import logging
import os
import sys

import paho.mqtt.client as mqtt

from sdm_modbus_zmq.client import Client

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MqttWrapper:
    def __init__(self, settings: dict = {}) -> None:
        """
        Validate the settings and setup the base discoverable object class
        Args:
            settings(dict): Settings for the sensor we want to create in Home Assistant.
            Mandatory Keys:
                client_name
                mqtt_server
                mqtt_prefix - defaults to homeassistant
                mqtt_user
                mqtt_password
                device_id
                device_name
            Optional Keys:
                unique_id
        """
        logging.warning("In Discoverable __init__")
        settings_error_base = f"You must specify a server and a client_name"

        assert "client_name" in settings, f"client_name is unset. {settings_error_base}"
        self.client_name = settings["client_name"]

        assert "mqtt_server" in settings, f"mqtt_server is unset. {settings_error_base}"
        self.mqtt_server = settings["mqtt_server"]

        assert "mqtt_prefix" in settings, f"mqtt_prefix is unset. {settings_error_base}"
        self.mqtt_prefix = settings["mqtt_prefix"]

        assert (
            "mqtt_password" in settings
        ), f"mqtt_password is unset. {settings_error_base}"
        self.mqtt_password = settings["mqtt_password"]

        assert "mqtt_user" in settings, f"mqtt_user is unset. {settings_error_base}"
        self.mqtt_user = settings["mqtt_user"]

        assert "device_id" in settings, f"device_id is unset. {settings_error_base}"
        self.device_id = settings["device_id"]

        assert "device_name" in settings, f"device_name is unset. {settings_error_base}"
        self.device_name = settings["device_name"]

        self.topic_prefix = f"{self.mqtt_prefix}/sensor/{self.device_name}"
        # self.config_topic = f"{self.topic_prefix}/config"
        self.state_topic = f"{self.topic_prefix}/state"
        logging.info(f"topic_prefix: {self.topic_prefix}")
        logging.info(f"self.state_topic: {self.state_topic}")
        self.wrote_configuration = False
        logging.warning("Finishing Discoverable __init__")

    def _connect(self) -> None:
        logging.debug(
            f"Creating mqtt client({self.client_name}) for {self.mqtt_server}"
        )
        self.mqtt_client = mqtt.Client(self.client_name)
        self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_password)

        logging.info(f"Connecting to {self.mqtt_server}...")
        self.mqtt_client.connect(self.mqtt_server)

    def _state_helper(self, state: str = None, topic: str = None) -> None:
        """
        Write a state to our MQTT state topic
        """
        if not hasattr(self, "mqtt_client"):
            logging.warning(f"Connecting to {self.mqtt_server}...")
            self._connect()
        if not self.wrote_configuration:
            logging.debug(f"Writing sensor configuration")
            self.write_config()
        if not topic:
            logging.debug(f"topic unset, using default of '{self.state_topic}'")
            topic = self.state_topic
        logging.debug(f"Writing '{state}' to {topic}")
        self.mqtt_client.publish(topic, state, retain=True)

    # def delete(self) -> None:
    #     """
    #     Delete a synthetic sensor from Home Assistant via MQTT message.
    #     Based on https://www.home-assistant.io/docs/mqtt/discovery/
    #     mosquitto_pub -r -h 127.0.0.1 -p 1883 -t "homeassistant/binary_sensor/garden/config" \
    #         -m '{"name": "emeter", "device_class": "motion", "state_topic": "homeassistant/binary_sensor/garden/state"}'
    #     """

    #     config_message = ""

    #     logging.info(
    #         f"Writing '{config_message}' to topic {self.config_topic} on {self.mqtt_server}"
    #     )
    #     self.mqtt_client.publish(self.config_topic, config_message, retain=True)

    def generate_config(self) -> list:
        """
        Generate dictionaries that we'll grind into JSON and write to MQTT.
        Will be used with the MQTT discovery protocol to make Home Assistant
        automagically ingest the new sensor.
        """
        sensors = [
            {
                "device_class": "voltage",
                "name": "Voltage",
                "unit_of_measurement": "V",
                "value_template": "{{value_json.voltage}}",
            },
            {
                "device_class": "current",
                "name": "Current",
                "unit_of_measurement": "A",
                "value_template": "{{ value_json.current}}",
            },
            {
                "device_class": "power",
                "name": "Power Active",
                "unit_of_measurement": "W",
                "value_template": "{{ value_json.power_active}}",
            },
            {
                "device_class": "power",
                "name": "Power Apparent",
                "unit_of_measurement": "VA",
                "value_template": "{{ value_json.power_apparent}}",
            },
            # {
            #     "device_class": "power",
            #     "name": "Power Reactive",
            #     "unit_of_measurement": "W",
            #     "value_template": "{{ value_json.power_reactive}}"
            # },
            # {
            #     "device_class": "power_factor",
            #     "name": "Power Factor",
            #     # "unit_of_measurement": "%",
            #     "value_template": "{{ value_json.power_factor}}"
            # },
            # {
            #     "device_class": "phase_angle",
            #     "name": "Phase Angle",
            #     # "unit_of_measurement": "%",
            #     "value_template": "{{ value_json.phase_angle}}"
            # },
            {
                "device_class": "frequency",
                "name": "Frequency",
                "unit_of_measurement": "Hz",
                "value_template": "{{ value_json.frequency}}",
            },
            {
                "device_class": "energy",
                "name": "Import Energy Active",
                "unit_of_measurement": "kWh",
                "value_template": "{{ value_json.import_energy_active}}",
            },
            {
                "device_class": "energy",
                "name": "Export Energy Active",
                "unit_of_measurement": "kWh",
                "value_template": "{{ value_json.export_energy_active}}",
            },
            # {
            #     "device_class": "energy",
            #     "name": "Import Energy Reactive",
            #     # "unit_of_measurement": "%",
            #     "value_template": "{{ value_json.import_energy_reactive}}"
            # },
            # {
            #     "device_class": "energy",
            #     "name": "Export Energy Reactive",
            #     # "unit_of_measurement": "%",
            #     "value_template": "{{ value_json.export_energy_reactive}}"
            # },
            {
                "device_class": "power",
                "name": "Total Demand Power Active",
                "unit_of_measurement": "W",
                "value_template": "{{ value_json.total_demand_power_active}}",
            },
            {
                "device_class": "power",
                "name": "Maximum Total Demand Power Active",
                "unit_of_measurement": "W",
                "value_template": "{{ value_json.maximum_total_demand_power_active}}",
            },
            {
                "device_class": "power",
                "name": "Import Demand Power Active",
                "unit_of_measurement": "W",
                "value_template": "{{ value_json.import_demand_power_active}}",
            },
            {
                "device_class": "power",
                "name": "Maximum Import Demand Power Active",
                "unit_of_measurement": "W",
                "value_template": "{{ value_json.maximum_import_demand_power_active}}",
            },
            {
                "device_class": "power",
                "name": "Export Demand Power Active",
                "unit_of_measurement": "W",
                "value_template": "{{ value_json.export_demand_power_active}}",
            },
            {
                "device_class": "power",
                "name": "Maximum Export Demand Power Active",
                "unit_of_measurement": "W",
                "value_template": "{{ value_json.maximum_export_demand_power_active}}",
            },
            {
                "device_class": "current",
                "name": "Total Demand Current",
                "unit_of_measurement": "A",
                "value_template": "{{ value_json.total_demand_current}}",
            },
            {
                "device_class": "current",
                "name": "Maximum Total Demand Current",
                "unit_of_measurement": "A",
                "value_template": "{{ value_json.maximum_total_demand_current}}",
            },
            {
                "device_class": "energy",
                "name": "Total Energy Active",
                "unit_of_measurement": "kWh",
                "value_template": "{{ value_json.total_energy_active}}",
            },
            # {
            #     "device_class": "energy",
            #     "name": "Total Energy Reactive",
            #     # "unit_of_measurement": "%",
            #     "value_template": "{{ value_json.total_energy_reactive}}"
            # },
        ]
        for sensor in sensors:
            sensor["state_topic"] = self.state_topic
        return sensors

    def write_config(self) -> None:
        """
        mosquitto_pub -r -h 127.0.0.1 -p 1883 -t "homeassistant/sensor/emeter/config" \
            -m '{"name": "Voltage", "device_class": "voltage", "unit_of_measurement": "V", "state_topic": "homeassistant/sensor/emeter/state"}'
        """
        for sensor_config in self.generate_config():
            unique_id = sensor_config["name"].lower().replace(" ", "_")
            sensor_config["unique_id"] = f"emeter_{unique_id}"
            config_message = json.dumps(sensor_config)
            config_topic = f"{self.topic_prefix}/{unique_id}/config"
            logging.debug(
                f"Writing config '{config_message}' to topic {config_topic} on {self.mqtt_server}"
            )
            if not hasattr(self, "mqtt_client"):
                logging.info(f"Connecting to {self.mqtt_server}...")
                self._connect()
            else:
                logging.debug("mqtt_client already set")
            self.mqtt_client.publish(config_topic, config_message, retain=True)
        self.wrote_configuration = True

    def update_state(self, state) -> None:
        """
        Update MQTT device state
        Override in subclasses
        """
        self._state_helper(state=state)


if __name__ == "__main__":
    ZEROMQ_HOST = sys.argv[1]
    ZEROMQ_PORT = sys.argv[2]
    ZEROMQ_TOPIC = sys.argv[3]
    MQTT_HOST = sys.argv[4]
    MQTT_USER = sys.argv[5]
    MQTT_PASSWORD = sys.argv[6]

    if not ZEROMQ_HOST:
        raise Exception("Invalid ZEROMQ_HOST null")
    if not MQTT_HOST:
        raise Exception("Invalid MQTT_HOST null")

    device = Client(
        host=ZEROMQ_HOST,
        port=ZEROMQ_PORT,
        topic=ZEROMQ_TOPIC,
    )

    mqtt_wrapper = MqttWrapper(
        {
            "mqtt_server": MQTT_HOST,
            "mqtt_prefix": "homeassistant",
            "mqtt_user": MQTT_USER,
            "mqtt_password": MQTT_PASSWORD,
            "client_name": "emeter",
            "device_id": "emeter",
            "device_name": "emeter",
        }
    )

    logging.debug("Fetching values")

    while True:
        values = device.get_data()
        logging.debug(values)
        mqtt_wrapper.update_state(json.dumps(values))

@monitoring.schema
class Temperature(dj.Manual):
    definition = """
    # room temperature
    -> common.Room
    tmst                     : timestamp                    # measurement timestamp
    ---
    celcius                  : float                        # in celcius
    """


@monitoring.schema
class Humidity(dj.Manual):
    definition = """
    # room temperature
    -> common.Room
    tmst                     : timestamp                    # measurement timestamp
    ---
    relative_humidity             : float            # in percent
    """


@monitoring.schema
class Motion(dj.Manual):
    definition = """
    # room temperature
    -> common.Room
    tmst                     : timestamp                    # measurement timestamp
    ---
    """


@monitoring.schema
class Light(dj.Manual):
    definition = """
    # room temperature
    -> common.Room
    tmst                     : timestamp                    # measurement timestamp
    ---
    r_lumens             : float            # in cd per sqm
    g_lumens             : float            # in cd per sqm
    b_lumens             : float            # in cd per sqm
    trigger="time"           : enum('time', 'light')    # Trigger 
    """


@monitoring.schema
class Camera(dj.Manual):
    definition = """
    # room temperature
    -> common.Room
    tmst                     : timestamp                    # measurement timestamp
    --- 
    image             : mediumblob            # in Image  uint8 format
    trigger="time"           : enum('time', 'motion', 'light', 'sound')    # Trigger 
    """
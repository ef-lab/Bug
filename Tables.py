@monitoring.schema
class Temperature(dj.Manual):
    definition = """
    # room temperature
    -> common.room
    tmst                     : timestamp                    # measurement timestamp
    ---
    celcius                  : float                        # in celcius
    """


@monitoring.schema
class Humidity(dj.Manual):
    definition = """
    # room temperature
    -> common.room
    tmst                     : timestamp                    # measurement timestamp
    ---
    relative_humidity             : float            # in percent
    """


@monitoring.schema
class Motion(dj.Manual):
    definition = """
    # room temperature
    -> common.room
    tmst                     : timestamp                    # measurement timestamp
    ---
    """


@monitoring.schema
class Light(dj.Manual):
    definition = """
    # room temperature
    -> common.room
    tmst                     : timestamp                    # measurement timestamp
    ---
    R_lumens             : float            # in cd per sqm
    G_lumens             : float            # in cd per sqm
    B_lumens             : float            # in cd per sqm
    trigger="time"           : enum('light')    # Trigger 
    """


@monitoring.schema
class Camera(dj.Manual):
    definition = """
    # room temperature
    -> common.room
    tmst                     : timestamp                    # measurement timestamp
    --- 
    image             : mediumblob            # in %
    trigger="time"           : enum('time', 'motion', 'light', 'sound')    # Trigger 
    """

gauges = [
            {'command': obd.commands.SPEED, 'title': 'speed', 'max': 200, 'warn': 135, 'alt_u': 'mph', 'titleunits': True},
            {'command': obd.commands.RPM, 'title': 'rpm', 'max': 6500, 'warn': 5900, 'alt_u': None, 'titleunits': False},
            {'command': obd.commands.ENGINE_LOAD, 'title': 'load %', 'max': 100, 'warn': 90, 'titleunits': False},
            {'command': obd.commands.COOLANT_TEMP, 'title': 'coolant temp', 'min': -40, 'max': 215, 'warn': 100, 'alt_u': 'degF', 'titleunits': True},
            {'command': obd.commands.INTAKE_TEMP, 'title': 'intake temp', 'min': -40, 'max': 215, 'warn': 50, 'alt_u': 'degF', 'titleunits': True},
            {'command': obd.commands.TIMING_ADVANCE, 'title': 'timing adv deg', 'min': -64, 'max': 64, 'titleunits': False},
        ]

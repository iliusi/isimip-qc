import numpy as np
from isimip_qc.config import settings
from isimip_qc.fixes import fix_set_variable_attr


def check_latlon_variable(file):
    for variable in  ['lat', 'lon']:
        var = file.dataset.variables.get(variable)
        var_definition = settings.DEFINITIONS['dimensions'].get(variable)

        if var is None:
            file.error('Variable "%s" is missing.', variable)
        elif not var_definition:
            file.error('Definition for variable "s%" is missing.', variable)
        else:
            # check dtype
            dtypes = ['float32', 'float64']
            if var.dtype not in dtypes:
                file.warn('Data type of "%s" is "%s". Should be float or double (one of %s).', variable, var.dtype, dtypes)

            # check axis
            axis = var_definition.get('axis')
            try:
                if var.axis != axis:
                    file.warn('"axis" attribute of "%s" is %s. Should be "%s".', variable, var.axis, axis, fix={
                        'func': fix_set_variable_attr,
                        'args': (file, variable, 'axis', axis)
                    })
            except AttributeError:
                file.warn('"axis" attribute of "%s" is missing. Should be "%s".', variable, axis, fix={
                    'func': fix_set_variable_attr,
                    'args': (file, variable, 'axis', axis)
                })

            # check standard_name
            standard_name = var_definition.get('standard_name')
            try:
                if var.standard_name != standard_name:
                    file.warn('"standard_name" attribute of "%s" is "%s". Should be "%s".', variable, var.standard_name, standard_name, fix={
                        'func': fix_set_variable_attr,
                        'args': (file, variable, 'standard_name', standard_name)
                    })
            except AttributeError:
                file.warn('"standard_name" attribute of "%s" is missing. Should be "%s".', variable, standard_name, fix={
                    'func': fix_set_variable_attr,
                    'args': (file, variable, 'standard_name', standard_name)
                })

            # check long_name
            long_names = var_definition.get('long_names', [])
            try:
                if var.long_name not in long_names:
                    file.warn('"long_name" attribute of "%s" is %s". Should be in %s.', variable, var.long_name, long_names, fix={
                        'func': fix_set_variable_attr,
                        'args': (file, variable, 'long_name', long_names[0])
                    })
            except AttributeError:
                file.warn('"long_name" attribute of "%s" is missing. Should be "%s".', variable, long_names[0], fix={
                    'func': fix_set_variable_attr,
                    'args': (file, variable, 'long_name', long_names[0])
                })

            # check units
            units = var_definition.get('units')
            try:
                if var.units != units:
                    file.warn('"units" attribute for "%s" is "%s". Should be "%s".', variable, var.units, units, fix={
                        'func': fix_set_variable_attr,
                        'args': (file, variable, 'units', units)
                    })
            except AttributeError:
                file.warn('"units" attribute for "%s" is missing. Should be "%s".', variable, units, fix={
                    'func': fix_set_variable_attr,
                    'args': (file, variable, 'units', units)
                })

            if settings.SECTOR not in ['marine-fishery_regional', 'water_regional']:
                # check minimum
                minimum = var_definition.get('minimum')
                if np.min(var) != minimum:
                    file.error('First value of variable "%s" is %s. Must be %s.', variable, np.min(var), minimum)

                # check maximum
                maximum = var_definition.get('maximum')
                if np.max(var) != maximum:
                    file.error('Last value of variable "%s" is %s. Must be %s.', variable, np.max(var), maximum)

                if variable == 'lat':
                    lat_first = file.dataset.variables.get('lat')[0]
                    lat_last = file.dataset.variables.get('lat')[-1]
                    if lat_first < lat_last:
                        file.warn('Latitudes in wrong order. Index should range from north to south. (found %s to %s)', lat_first, lat_last)
                    else:
                        file.info('Latitude index order looks good (N to S).')

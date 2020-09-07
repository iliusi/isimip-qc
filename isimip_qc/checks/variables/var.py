import math

from isimip_qc.config import settings


def check_variable(file):
    variable_name = file.specifiers.get('variable')
    variable = file.dataset.variables.get(variable_name)
    definition = settings.DEFINITIONS.get('variable', {}).get(variable_name)

    if not variable:
        file.error('Variable %s is missing.', variable_name)
    elif not definition:
        file.error('Definition for variable %s is missing.', variable_name)
    else:
        # check file name and NetCDF variable to match each other
        if variable.name != variable_name:
            file.error('File name variable (%s) does not match internal variable name (%s).', variable_name, variable.name)

        # check dtype
        if variable.dtype != 'float32':
            file.warn('%s.dtype="%s" should be "float32".', variable_name, variable.dtype)

        # check chunking
        chunking = variable.chunking()
        if chunking[0] != 1 or chunking[-2] != 360 or chunking[-1] != 720:
            file.warn('%s.chunking=%s should be [1, ... , 360, 720].', variable_name, chunking)
        else:
            file.info('Variable chunking looks good (%s)', chunking)

        # check dimensions
        definition_dimensions = tuple(definition.get('dimensions', []))
        default_dimensions = ('time', 'lat', 'lon')
        if definition_dimensions:
            if variable.dimensions not in [definition_dimensions, default_dimensions]:
                file.error('%s dimension %s must be %s or %s.', variable_name, variable.dimensions, definition_dimensions, default_dimensions)
        else:
            if variable.dimensions != default_dimensions:
                file.error('%s dimension %s must be %s.', variable_name, variable.dimensions, default_dimensions)

        # check variable units
        units = definition.get('units')
        if units is not None:
            try:
                if variable.units != units:
                    file.error('%s.units=%s should be %s.', variable_name, variable.units, units)
                else:
                    file.info('Variable unit matches protocol definition (%s)', variable.units)
            except AttributeError:
                file.error('%s.units is missing. Should be "%s".', variable_name, units)
        else:
            file.warn('No units information on %s in definition.', variable_name)

        # check dimension order
        dim_len = len(variable.dimensions)
        if dim_len == 3:
            if variable.dimensions[0] != 'time' or variable.dimensions[1] != 'lat' or variable.dimensions[2] != 'lon':
                file.warn('%s dimension order %s should be ["time", "lat", "lon"].', variable_name, variable.dimensions)
            else:
                file.info('Dimensions for variable "%s" look good: %s', variable_name, variable.dimensions)
        elif dim_len == 4:
            if variable.dimensions[0] != 'time' or variable.dimensions[1] not in ['depth'] or variable.dimensions[2] != 'lat' or variable.dimensions[2] != 'lon':
                file.warn('%s dimension order %s should be ["time", "depth" , "lat", "lon"].', variable_name, variable.dimensions)
            else:
                file.info('Dimensions for variable "%s" look good', variable_name)
        else:
            file.error('Variable "%s" neither holds 2d or 3d data. (dim=%s)', dim_len)

        # check _FillValue and missing_value
        for name in ['_FillValue', 'missing_value']:
            try:
                attr = variable.getncattr(name)
                if not math.isclose(attr, 1e+20, rel_tol=1e-6):
                    file.error('Missing values for variable "%s": %s=%s but should be 1e+20.', variable_name, name, attr)
                else:
                    file.info('Missing value attribute "%s" is properly set.', name)
            except AttributeError:
                file.error('Missing value attribute "%s" for variable "%s" is missing. Should be set to 1e+20.', name, variable_name)

        # check valid range
        if settings.MINMAX:
            valid_min = definition.get('valid_min')
            valid_max = definition.get('valid_max')
            if (valid_min is not None) and (valid_min is not None):
                file.info("Checking values for valid minimum and maximum range defined in the protocol. This could take some time...")
                var_min = variable[:].min()
                var_max = variable[:].max()
                if (var_min < float(valid_min)) or (var_max > float(valid_max)):
                    file.error('Min/Max values (%.2E/%.2E) of %s are outside the valid range (%.2E to %.2E).', var_min, var_max, variable_name, valid_min, valid_max)
                else:
                    file.info('Min/Max values within valid range (%.2E to %.2E).', valid_min, valid_max)
            else:
                file.info('No min and/or max definition found for variable "%s".', variable_name)
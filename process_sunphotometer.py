import pandas as pd
import datetime as dt
import numpy as np
from ncas_amof_netcdf_template import create_netcdf, util, remove_empty_variables


def get_data(csv_file, wavelengths):
    df = pd.read_csv(csv_file)
    
    dt_times = [dt.datetime.strptime(i, "%Y-%m-%d %H:%M:%S") for i in df["Timestamp"]]
    elevations = np.stack(df["Elevation (deg)"].to_numpy())
    azimuths = np.stack(df["Azimuth (deg)"].to_numpy())
    out_temp = np.stack(df["Ambient temperature (C)"].to_numpy())
    out_temp = np.array([float(i) for i in out_temp]) + 273.15
    pres = np.stack(df["Ambient pressure (kPa)"].to_numpy())
    pres = np.array([float(i) for i in pres]) * 10  # kPa to hPa
    inst_temp = np.stack(df["Internal temperature (C)"].to_numpy())
    inst_temp = np.array([float(i) for i in inst_temp]) + 273.15
    inst_rh = np.stack(df["Internal humidity (%)"].to_numpy())
    dni = np.stack(df["DNI (W/m2)"].to_numpy())

    aod = np.empty((len(dt_times), len(wavelengths)))
    for i, w in enumerate(wavelengths):
        aod[:,i] = [float(j) for j in df[f'AOD {w} nm'][:]]

    return dt_times, elevations, azimuths, out_temp, pres, inst_temp, inst_rh, dni, aod


def make_netcdf_aerosol_optical_depth(
        csv_file, metadata_file = None, ncfile_location = ".",
        verbose = False, local_tsv_file_loc = None,
        wavelengths = [368, 412, 500, 675, 862, 1024]
    ):
    """
    Make aerosol-optical-depth netCDF file using data in csv_file
    """
    if verbose: print("Makinng aerosol-optical-depth netCDF file\nReading data")

    dt_times, elevations, azimuths, out_temp, pres, inst_temp, inst_rh, dni, aod = get_data(csv_file, wavelengths)
    unix_times, doy, years, months, days, hours, minutes, seconds, time_coverage_start_dt, time_coverage_end_dt, file_date = util.get_times(dt_times)

    if verbose: print("Creating file")
    ncfile = create_netcdf.main(
        "ncas-sunphotometer-3",
        date = file_date,
        dimension_lengths = {"time": len(unix_times), "index": 6},
        loc = "land",
        file_location = ncfile_location,
        return_open = True,
        use_local_files = local_tsv_file_loc,
    )

    if verbose: print("Adding data to variables")
    util.update_variable(ncfile, "atmosphere_optical_thickness_due_to_ambient_aerosol_particles", aod)
    util.update_variable(ncfile, "instrument_channel_wavelength", wavelengths)

    util.update_variable(ncfile, "time", unix_times)
    util.update_variable(ncfile, "year", years)
    util.update_variable(ncfile, "month", months)
    util.update_variable(ncfile, "day", days)
    util.update_variable(ncfile, "hour", hours)
    util.update_variable(ncfile, "minute", minutes)
    util.update_variable(ncfile, "second", seconds)
    util.update_variable(ncfile, "day_of_year", doy)

    if verbose: print("Setting global attributes")
    ncfile.setncattr("time_coverage_start", dt.datetime.fromtimestamp(time_coverage_start_dt, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
    ncfile.setncattr("time_coverage_end", dt.datetime.fromtimestamp(time_coverage_end_dt, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
    
    util.add_metadata_to_netcdf(ncfile, metadata_file)
                
    # if lat and lon given, no need to also give geospatial_bounds
    # this works great for point deployment (e.g. ceilometer)
    lat_masked = ncfile.variables["latitude"][0].mask
    lon_masked = ncfile.variables["longitude"][0].mask
    geospatial_attr_changed = "CHANGE" in ncfile.getncattr("geospatial_bounds")
    if geospatial_attr_changed and not lat_masked and not lon_masked:
        geobounds = f"{ncfile.variables['latitude'][0]}N, {ncfile.variables['longitude'][0]}E"
        ncfile.setncattr("geospatial_bounds", geobounds)
    
    ncfile.close()
    
    if verbose: print('Removing empty variables')
    remove_empty_variables.main(f'{ncfile_location}/ncas-sunphotometer-3_iao_{file_date}_aerosol-optical-depth_v1.0.nc', verbose = verbose)

    if verbose: print('Complete')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description = 'Create AMOF-compliant netCDF file for ncas-sunphotometer-3 instrument.')
    parser.add_argument('input_csv', type=str, help = 'Raw csv data from instrument.')
    parser.add_argument('-v','--verbose', action='store_true', help = 'Print out additional information.', dest = 'verbose')
    parser.add_argument('-m','--metadata', type = str, help = 'csv file with global attributes and additional metadata. Default is None', dest='metadata')
    parser.add_argument('-o','--ncfile-location', type=str, help = 'Path for where to save netCDF file. Default is .', default = '.', dest="ncfile_location")
    parser.add_argument('-t','--tsv-location', type = str, help = "Path where local copy of AMF_CVs tsv files are, for 'offline' use. Default is None (for 'online' use).", default = None, dest = "tsv_location")
    parser.add_argument('-w','--wavelengths', type = float, nargs = "*", help = "Wavelength(s) in nanometres used by instrument. Default are 368, 412, 500, 675, 862, 1024.", default = [368, 412, 500, 675, 862, 1024])
    args = parser.parse_args()

    make_netcdf_aerosol_optical_depth(
        args.input_csv, metadata_file = args.metadata, ncfile_location = args.ncfile_location,
        verbose = args.verbose, local_tsv_file_loc = args.tsv_location,
        wavelengths = args.wavelengths
    )

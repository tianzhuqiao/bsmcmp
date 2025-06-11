# bsmcmp
**bsmcmp** is a tool to compare data files.

## Install
```
$ pip install bsmcmp
```

## Supported file formats
- ASCII
- CSV
- [HDF5](https://docs.h5py.org/en/stable/)
- Matlab (.mat)
- [netCDF](https://unidata.github.io/netcdf4-python/)

## Usage
For example, to compare two files:
```
$ bsmcmp netcdf --file1 file1.nc --file2 file2.nc
```

To compare all files in two folders (assume both folders have the same structure):
```
$ bsmcmp netcdf --folder1 file1.nc --folder file2.nc
```

See `bsmcmp --help` or `bsmcmp COMMAND --help` for details
```
Usage: bsmcmp [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  ascii
  csv
  hdf5
  matlab
  netcdf
  ```
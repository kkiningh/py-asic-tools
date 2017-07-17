# py-asic-tools

Author: Kevin Kiningham
License: MIT

## Setup

### Installing Verilator
In `./verilator` run

```
autoconf
./configure
make -j8 && sudo make install
```

### Installing pybind11
No setup needed since it's a header only library (in `pybind11/include/`)

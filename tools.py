from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

import subprocess
try:
    from subprocess import DEVNULL # py3k
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

import tempfile
import importlib

import shlex
import mako.template

def import_verilog(name, inputs, outputs, source=None, include=None, docstring=""):
    # Infer the source file from the name
    if source is None:
        source = name + '.v'

    # Create a directory to use for the files created
    tmp_dir = os.path.join(tempfile.gettempdir(), 'V' + name)
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Compile the Verilog using verilator
    flags = ['--cc', '-Wall', '-Mdir', tmp_dir]
    if include is not None:
        flags.extend(['-y', include])
    subprocess.call(['verilator', source] + flags)

    # C++ stub to interface between verilator and python
    template = mako.template.Template(
r"""
#include <pybind11/pybind11.h>
#include "V${name}.h"

namespace py = pybind11;

PYBIND11_MODULE(${name}, m) {
    m.doc() = "${docstring}";

    py::class_<V${name}>(m, "${name}")
        .def("__init__", [](V${name} &instance, std::string name) {
            new (&instance) V${name}();
        }, py::arg("name") = "TOP")
        .def("eval", &V${name}::eval)
        .def("final", &V${name}::final)
    % for input_name in inputs.keys():
        .def_readwrite("${input_name}", &V${name}::${input_name})
    % endfor
    % for output_name in outputs.keys():
        .def_readonly("${output_name}", &V${name}::${output_name})
    % endfor
    ;
}""")

    # Render the template and write it to a temp file
    with tempfile.NamedTemporaryFile(suffix='.cc') as fd:
        fd.write(template.render(
            docstring = docstring,
            name = name,
            inputs = inputs,
            outputs = outputs
        ))
        fd.flush()

        # Get cflags for python
        py_flags = shlex.split(subprocess.check_output(
                ['python-config', '--cflags', '--ldflags']))

        # Call g++
        obj_file = os.path.join(tmp_dir, '{name}.so'.format(name=name))
        subprocess.call(
          ['g++', '-O3', '-fPIC', '-shared', '-std=c++1z']
          + ['-I', tmp_dir]
          + ['-I', './bin/share/verilator/include']
          + ['-I', './pybind11/include']
          + py_flags
          + ['./obj_dir/V{name}.cpp'.format(name=name)]
          + ['./obj_dir/V{name}__Syms.cpp'.format(name=name)]
          + ['./bin/share/verilator/include/verilated.cpp']
          + [fd.name]
          + ['-o', obj_file]
        , stderr=DEVNULL)

    # Add the temp directory to the path
    sys.path.append(tmp_dir)

    # Finish by running the actual import
    return importlib.import_module(name)

def main(argv):
  # Import the verilog as if it were a module
  Adder = import_verilog('Adder',
    inputs={
      'a': Bits(32),
      'b': Bits(32)
    },
    outputs={
      'c': Bits(32)
    }
  )

  # Create a new Adder instance
  adder = Adder.Adder()

  # Tick the simulation for the adder, feeding it inputs
  adder.eval({'a': 1, 'b': 2})

  # Get the output values
  pass

if __name__ == '__main__':
    main(sys.argv)

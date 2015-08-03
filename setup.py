from setuptools import setup, find_packages

setup(name = "pyR2html",
      version = "1.0.0",
      py_modules = ["R2html"],
      entry_points = {
          "console_scripts" : [
              "pyR2html=R2html:_main"
              ]
      }
)


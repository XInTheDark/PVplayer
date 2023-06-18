# Build PVengine executable on Linux-based systems

# Delete current pvengine executable
rm pvengine

pyinstaller engine_main.py --onefile -n pvengine

# Path: src/dist/pvengine

# Delete the build folder and pvengine.spec
rm -rf build
rm pvengine.spec

# Move the pvengine executable to src folder
mv dist/pvengine pvengine

# Delete the dist folder
rm -rf dist
# Use cx_freeze to build a faster executable of pvengine

# Delete current pvengine executable
rm pvengine
rm build/pvengine

cxfreeze -c engine_main.py --target-dir=build --target-name=pvengine

# Delete frozen_application_license.txt
rm build/frozen_application_license.txt

# First startup is slow, so we run the executable once to activate it
echo "quit" | build/pvengine
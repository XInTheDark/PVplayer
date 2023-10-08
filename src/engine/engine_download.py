# This module downloads the Stockfish engine if it is not already present.
import os, platform, zipfile
import urllib.request

URL_WINDOWS = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-windows-x86-64-modern.zip"
URL_LINUX = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-ubuntu-x86-64-modern.tar"
URL_MACOS = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-macos-x86-64-modern.tar"

def download_stockfish():
    """downlaods stockfish and returns engine path"""
    # Check if already present
    if os.path.exists("stockfish16.exe"):
        return "stockfish16.exe"
    elif os.path.exists("stockfish16"):
        return "./stockfish16"
    
    # get system type
    system = platform.system()
    if system == "Windows":
        # download from https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-windows-x86-64-modern.zip
        # and extract to stockfish.exe
        
        # Download file
        print("Downloading...")
        filename = urllib.request.urlretrieve(URL_WINDOWS)[0]
        print("Extracting...")
        os.rename(filename, "stockfish16.zip")
        with zipfile.ZipFile("stockfish16", "r") as zip_ref:
            zip_ref.extractall("")
            
        # rename stockfish-windows-x86-64-modern.exe to stockfish16.exe
        os.rename("stockfish-windows-x86-64-modern.exe", "stockfish16.exe")
        return "stockfish16.exe"
    
    elif system == "Linux":
        # Download file
        print("Downloading...")
        filename = urllib.request.urlretrieve(URL_LINUX)[0]
        print("Extracting...")
        os.rename(filename, "stockfish16.tar")
        os.system("tar -xf stockfish16.tar --directory .")

        # rename stockfish-windows-x86-64-modern to stockfish16
        os.rename("stockfish/stockfish-ubuntu-x86-64-modern", "stockfish16")
        os.system("chmod +x stockfish16")
        return "./stockfish16"
        
    elif system == "Darwin":
        print("Downloading...")
        filename = urllib.request.urlretrieve(URL_MACOS)[0]
        print("Extracting...")
        os.rename(filename, "stockfish16.tar")
        os.system("tar -xf stockfish16.tar --directory .")
        
        os.rename("stockfish/stockfish-macos-x86-64-modern", "stockfish16")
        os.system("chmod +x stockfish16")
        return "./stockfish16"
    
    raise Exception("Unsupported system: " + system)
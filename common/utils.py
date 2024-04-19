""" Common/utility methods
# no logging in this file
"""

from enum import Enum
import pathlib
import sys
import ctypes
import time
import subprocess
import random
import string
from requests.exceptions import ConnectionError, ReadTimeout
from .lan_str import LanStr

# Constants
WEBSITE = "https://mjcopilot.com"

# read version string from file version
MODEL_FOLDER = "models"
BROWSER_DATA_FOLDER = "browser_data"
RES_FOLDER = 'resources'
LOG_DIR = 'log'
MITM_CONFDIR = 'mitm_config'
TEMP_FOLDER = 'temp'

# for automation
GAME_MODES = ['4E', '4S', '3E', '3S']

class GameMode(Enum):
    """ Game Modes for bots/models"""
    MJ4P = "4P"
    MJ3P = "3P"
    
class UiState(Enum):
    """ UI State for the game"""
    NOT_RUNNING = 0
    MAIN_MENU = 1
    IN_GAME = 10
    GAME_ENDING = 20
    
class ModelFileException(Exception):
    """ Exception for model file error"""

class MITMException(Exception):
    """ Exception for MITM error"""
    
class BotNotSupportingMode(Exception):
    """ Bot not supporting current mode"""
    def __init__(self, mode:GameMode):
        super().__init__(mode)

def error_to_str(error:Exception, lan:LanStr) -> str:
    """ Convert error to language specific string"""
    if isinstance(error, ModelFileException):
        return lan.MODEL_FILE_ERROR
    elif isinstance(error, MITMException):
        return lan.MITM_SERVER_ERROR
    elif isinstance(error, BotNotSupportingMode):
        return lan.MODEL_NOT_SUPPORT_MODE_ERROR + f' {error.args[0].value}'
    elif isinstance(error, ConnectionError):
        return lan.CONNECTION_ERROR + f': {error}'
    elif isinstance(error, ReadTimeout):
        return lan.CONNECTION_ERROR + f': {error}'        
    else:
        return str(error)

def sub_folder(folder_name:str) -> pathlib.Path:
    """ return the subfolder Path, create it if not exists"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = pathlib.Path(sys._MEIPASS).parent   # pylint: disable=W0212,E1101
    except Exception:  #pylint: disable=broad-except
        base_path = pathlib.Path('.')
        
    subfolder = base_path / folder_name
    if not subfolder.exists():
        subfolder.mkdir(exist_ok=True)
    return subfolder.resolve()

def sub_file(folder:str, file:str) -> str:
    """ return the file absolute path string, given folder and filename, create the folder if not exists"""
    subfolder = sub_folder(folder)
    file_str = str((subfolder / file).resolve())
    return file_str

def wait_for_file(file:str, timeout:int=5) -> bool:
    """ Wait for file creation (blocking until the file exists) for {timeout} seconds
    returns:
        bool: True if file exists within timeout, False otherwise
    """
    # keep checking if the file exists until timeout
    start_time = time.time()
    while not pathlib.Path(file).exists():
        if time.time() - start_time > timeout:
            return False
        time.sleep(0.5)
    return True

def install_root_cert(cert_file:str) -> tuple[bool, str]:
    """ Install Root certificate onto the system
    params:
        cert_file(str): certificate file to be installed
    Returns:
        (bool, str): True if the certificate is installed successfully, str is the stdout
    """
    # Install cert. If the cert exists, system will skip installation
    if sys.platform == "win32":
        result = subprocess.run(['certutil', '-addstore', 'Root', cert_file],
            capture_output=True, text=True, check=False)

    elif sys.platform == "darwin":
        # TODO Test on MAC system
        result = subprocess.run(['sudo', 'security', 'add-trusted-cert', '-d', '-r', 'trustRoot', '-k', '/Library/Keychains/System.keychain', cert_file],
            capture_output=True, text=True, check=True)
    else:
        print("Unknown Platform. Please manually install MITM certificate:", cert_file)
        return False, ""
    
    # Check if successful
    if result.returncode == 0:  # success     
        return True, result.stdout
    else:   # error        
        return False, result.stdout
    
def list_files(folder:str, full_path:bool=False) -> list[pathlib.Path]:
    """ return the list of files in the folder 
    params:
        folder(str): name of the folder
        full_path(bool): True to return the full path, while False to return only the file name"""
    try:
        files = [f for f in pathlib.Path(folder).iterdir() if f.is_file()]
        if full_path:
            return [str(f.resolve()) for f in files]
        else:
            return [f.name for f in files]
    except: #pylint:disable=bare-except
        return []
    
def random_str(length:int) -> str:
    """ Generate random string with specified length"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def set_dpi_awareness():
    """ Set DPI Awareness """
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # for Windows 8.1 and later
        except AttributeError:
            ctypes.windll.user32.SetProcessDPIAware()       # for Windows Vista and later
        except: #pylint:disable=bare-except
            pass
class FPSCounter:
    """ for counting frames and calculate fps"""
    def __init__(self):
        self._start_time = time.time()
        self._frame_count = 0
        self._fps = 0

    def frame(self):
        """Indicates that a frame has been rendered or processed. Updates FPS if more than 1 second has passed."""
        self._frame_count += 1
        current_time = time.time()
        elapsed_time = current_time - self._start_time

        if elapsed_time >= 1.0:
            self._fps = self._frame_count / elapsed_time
            self._start_time = current_time
            self._frame_count = 0

    def reset(self):
        """ reset the counter"""
        self.__init__()
        
    @property
    def fps(self):
        """Returns the current frames per second."""
        return self._fps

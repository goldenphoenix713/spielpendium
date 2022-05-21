"""Contains save and load functions for splz files.

Functions that save and load Spielpendium save files (.splz)
"""

__all__ = ['save_splz', 'load_splz', 'IMAGE_SIZE']

import datetime
import os
import zipfile
import json
from io import BytesIO
from typing import Dict, Union, Tuple

import pandas as pd
from PyQt5 import QtGui, QtCore

from spielpendium import log

IMAGE_SIZE = 512
_SPLZ_VERSION = '1.0'


@log.log(log.logger)
def save_splz(data: pd.DataFrame, metadata: Dict, filename: str) -> bool:
    """ Saves the internal user data in a Spielpendium program to a .splz file.

    The SPLZ file format is a JSON formatted text file containing the game
    data, another containing metadata, and a folder containing associated
    game images in a zipped folder.

    :param data: The data to save, as a Pandas Dataframe.
    :param metadata: The metadata associated with the DataFrame.
    :param filename: The path to the save file location.
    :return: True if successful, False otherwise.
    """
    ###########################################################################
    # Data setup
    ###########################################################################

    # Take the images out of the DataFrame, since they can't be
    # saved in the JSON data file.
    images_list = data['Image']
    images_list.index = data['BGG Id']
    images: Dict[Union[int, str], QtGui.QImage] = images_list.to_dict()

    # Replace the images in the DataFrame with the relative image path
    # in the .splz file.
    data_copy = data.copy()

    data_copy['Image'] = 'images/' + data['BGG Id'].astype(str) + '.png'

    data_dict = data_copy.to_dict(orient='index')

    # Add some additional metadata
    metadata_copy = metadata.copy()
    metadata_copy.update(
        {'version': _SPLZ_VERSION,
         'creation_date': datetime.datetime.utcnow().isoformat()+'Z'}
    )

    file_data = {'metadata': metadata_copy, 'data': data_dict, }
    # Convert the data in the DataFrame to a JSON string.
    json_data = json.dumps(file_data, indent=2)

    log.logger.debug('Games data converted to JSON.')

    ###########################################################################
    # Write the file
    ###########################################################################

    # Open or create the splz file.
    try:
        with zipfile.ZipFile(filename, 'w') as file:
            # Write the JSON files into the zip file
            file.writestr('data.json', json_data)

            # Loop through the "images" dict and add them into the file.
            # The images are stored in the "images" sub folder and are named
            # with the associated BGG ID (which is unique).
            for bgg_id, image in images.items():
                buffer = QtCore.QBuffer()
                buffer.open(QtCore.QBuffer.ReadWrite)
                image.save(buffer, "PNG")
                image_bytes = BytesIO(buffer.data())
                file.writestr(
                    data_copy.loc[
                        data_copy['BGG Id'] == bgg_id
                        ]['Image'].values[0],
                    image_bytes.getvalue()
                )
                buffer.close()

        log.logger.info(f'SPLZ file successfully saved at {filename}.')

        # Let the user know saving was successful
        return True
    # If there's any error, return False
    except (OSError, zipfile.LargeZipFile) as err:
        log.logger.error(f'SPLZ file was not saved at {filename}. {err}')
        return False


@log.log(log.logger)
def load_splz(filepath: str) -> Tuple[pd.DataFrame, Dict]:
    """ Loads data stored in a .splz file into Spielpendium.

    :param filepath: The path to the .splz file.
    :return: The data that was stored in the file.
    :raises FileNotFoundError: If the file can't be found.
    :raises IOError: If the file is unable to be read for any reason.
    """

    ###########################################################################
    # Check that the file is valid
    ###########################################################################

    # Get the filename from the full path
    filename: str = os.path.split(filepath)[1]

    # Check to see if the file exists
    if not os.path.exists(filepath):
        raise FileNotFoundError(f'Unable to find the file {filename}.')

    # Check that the file is a valid zipfile or that is has .splz extension
    if not zipfile.is_zipfile(filepath) or not filename.endswith('.splz'):
        raise IOError(f'Unable to read {filename}. It does not '
                      'seem to be a valid .splz file. or may '
                      'have become corrupted.') from None

    log.logger.debug(f'File to load found at {filepath}.')
    ###########################################################################
    # Extract the contents of the zipfile
    ###########################################################################

    try:
        with zipfile.ZipFile(filepath) as file:
            # Load the json file with the user data and convert to a DataFrame
            json_file = json.loads(file.read('data.json').decode())
            json_data = json_file['data']
            data: pd.DataFrame = pd.DataFrame(json_data).T

            # Read in the metadata
            metadata = json_file['metadata']
            metadata.pop('version')
            metadata.pop('creation_date')

            # Loop through the images and add them to the DataFrame
            for index, path in zip(data.index, data['Image']):
                image = QtGui.QImage()
                if not image.loadFromData(file.read(path)):
                    # If the image cannot be found, raise an error.
                    raise FileNotFoundError(
                        f'The image {os.path.split(path)[1]} '
                        f'was not found in {filename}.'
                    )
                data.loc[index, 'Image'] = image.scaled(
                    IMAGE_SIZE,
                    IMAGE_SIZE,
                    QtCore.Qt.KeepAspectRatio
                )
        log.logger.info(f'File at {filepath} successfully loaded.')

    # Raise a IOError if the file can't be read for any reason.
    except (KeyError, UnicodeDecodeError,
            ValueError, FileNotFoundError):
        log.logger.error(f'Unable to read {filename}.')
        raise IOError(f'Unable to read {filename}. It does not '
                      'seem to be a valid .splz file. or may '
                      'have become corrupted.') from None
    return data, metadata


if __name__ == '__main__':
    test_im = (QtGui.QImage('../../images/image.jpg')
               .scaled(IMAGE_SIZE, IMAGE_SIZE, QtCore.Qt.KeepAspectRatio))

    the_data = [{
        'BGG Id': 1,
        'Image': test_im,
        'Name': 'Test',
        'Version': 1,
        'Author': 'Author',
        'Artist': 'Artist',
        'Publisher': 'Publisher Games',
        'Release Year': 2021,
        'Category': 'Made Up',
        'Description': 'This is a test thing I''m doing.',
        'Minimum Players': 3,
        'Maximum Players': 5,
        'Recommended Players': 4,
        'Age': 20,
        'Minimum Play Time': 50,
        'Maximum Play Time': 120,
        'BGG Rating': 1.2,
        'BGG Rank': 504033,
        'Complexity': 1.2,
        'Related Games': 'None',
    }]

    the_data = pd.DataFrame(the_data, index=[1])

    the_metadata = {
        'name': 'User',
    }

    # the_data, the_metadata = load_splz('test.splz')
    print(the_data)
    print(the_data['Image'])
    print(the_metadata)

    save_splz(the_data, the_metadata, 'test.splz')

    data2, metadata2 = load_splz('test.splz')

    print(data2)
    print(metadata2)

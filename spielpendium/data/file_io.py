"""Contains save and load functions for splz files.

Functions that save and load Spielpendium save files (.splz)
"""

__all__ = ['save_splz', 'load_splz']

import os
import zipfile
import json
from io import BytesIO
from typing import Dict, Union, Tuple

import pandas as pd
from PIL import Image, UnidentifiedImageError
from PyQt5 import QtGui


def save_splz(data: pd.DataFrame, metadata: Dict, filename: str) -> bool:
    """ Saves the internal user data in a Spielpendium program to a .splz file.

    The SPLZ file format is a JSON formatted text file containing the user's
    information and a folder containing associated game images in a zipped
    folder.

    :param data: The data to save, as a Pandas Dataframe.
    :param metadata: The metadata associated with the DataFrame.
    :param filename: The path to the save file location.
    :return: True if successful, false otherwise.
    """
    ###########################################################################
    # Data setup
    ###########################################################################

    # Take the images out of the DataFrame, since they can't be
    # saved in the JSON data file.
    images_list = data['Image']
    images_list.index = data['BGG Id']
    images: Dict[Union[int, str], Image.Image] = images_list.to_dict()

    # Replace the images in the DataFrame with the relative image path
    # in the .splz file.
    data_copy = data.copy()

    data_copy['Image'] = 'images/' + data['BGG Id'].astype(str) + '.png'

    # Convert the data in the DataFrame to a JSON string.
    json_data = json.dumps(json.loads(data_copy.to_json(orient="index")),
                           indent=4)
    json_meta = json.dumps(metadata, indent=4)

    ###########################################################################
    # Write the file
    ###########################################################################

    # Open or create the splz file.
    try:
        with zipfile.ZipFile(filename, 'w') as file:
            # Write the JSONs into the file
            file.writestr('data.json', json_data)
            file.writestr('metadata.json', json_meta)

            # Loop through the "images" dict and add them into the file.
            # The images are stored in the "images" subfolder and are named
            # with the associated BGG Id (which is unique).
            for bgg_id, image in images.items():
                image_bytes = BytesIO()
                image.save(image_bytes, format="PNG")
                file.writestr(
                    data_copy.loc[data_copy['BGG Id'] == bgg_id]['Image'].values[0],
                    image_bytes.getvalue()
                )

        # Let the user know saving was successful
        return True
    # If there's any error, return False
    except (OSError, zipfile.LargeZipFile):
        return False


def load_splz(filepath: str) -> Tuple[pd.DataFrame, Dict]:
    """ Loads data stored in a .splz file into Spielpendium.

    :param filepath: The path to the .splz file.
    :return: The data that was stored in the file.
    :raises FileNotFoundError: If the file can't be found.
    :raises TypeError: If the file is unable to be read for any reason.
    """

    ###########################################################################
    # Check that the file is valid
    ###########################################################################

    # Get the filename from the full path
    filename: str = os.path.split(filepath)[1]

    # Check to see if the file exists
    if not os.path.exists(filepath):
        raise FileNotFoundError(f'Unable to find the file {filename}.')

    # Check that the file is a valid zipfile or that is have a .splz extension
    if not zipfile.is_zipfile(filepath) or not filename.endswith('.splz'):
        raise TypeError(f'Unable to read {filename}. It does not '
                        'seem to be a valid .splz file. or may '
                        'have become corrupted.') from None

    ###########################################################################
    # Extract the contents of the zipfile
    ###########################################################################

    try:
        with zipfile.ZipFile(filepath) as file:
            # Load the json file with the user data and convert to a DataFrame
            json_data = file.read('data.json').decode()
            data: pd.DataFrame = pd.read_json(json_data, orient='index')

            # Read in the metadata file
            metadata = json.loads(file.read('metadata.json').decode())

            # Loop through the images and add them to the DataFrame
            for ii, path in zip(data.index, data['Image']):
                image = QtGui.QImage()
                if not image.loadFromData(file.read(path)):
                    # If the image cannot be found, raise an error.
                    raise FileNotFoundError(f'The image {os.path.split(path)[1]} was not found in {filename}.')
                # image: Image.Image = Image.open(BytesIO(image_bytes))
                data.loc[ii, 'Image'] = image

    # Raise a TypeError if the file can't be read for any reason.
    except (KeyError, UnicodeDecodeError,
            ValueError, UnidentifiedImageError):
        raise TypeError(f'Unable to read {filename}. It does not '
                        'seem to be a valid .splz file. or may '
                        'have become corrupted.') from None
    return data, metadata


if __name__ == '__main__':
    the_data, the_metadata = load_splz('test.splz')
    print(the_data)
    print(the_metadata)

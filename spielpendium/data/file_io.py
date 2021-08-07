"""Contains save and load functions for splz files.

Functions that save and load Spielpendium save files (.splz)
"""

__all__ = ['save_splz', 'load_splz']

import zipfile
import json
from io import BytesIO

import pandas as pd


def save_splz(data: pd.DataFrame, filename: str) -> bool:
    """ Saves the internal user data in a Spielpendium program to a .splz file.

    The SPLZ file format is a JSON formatted text file containing the user's
    information and a folder containing associated game images in a zipped
    folder.

    :param data: The data to save, as a Pandas dataframe.
    :param filename: The path to the save file location.
    :return: True if successful, false otherwise.
    """
    ###########################################################################
    # Data setup
    ###########################################################################

    # Take the images out of the DataFrame, since they can't be
    # saved in the JSON data file.
    images = data['Image']
    images.index = data['BGG Id']
    images = images.to_dict()

    # Replace the images in the DataFrame with the relative image path
    # in the .splz file.
    data['Image'] = 'images/' + data['BGG Id'].astype(str) + '.png'

    # Convert the data in the DataFrame to a JSON string.
    json_data = json.dumps(json.loads(data.to_json(orient="index")), indent=4)

    ###########################################################################
    # Write the file
    ###########################################################################

    # Open or create the splz file.
    try:
        with zipfile.ZipFile(filename, 'w') as file:
            # Write the JSON into the file
            file.writestr('data.json', json_data)

            # Loop through the "images" dict and add them into the file.
            # The images are stored in the "images" subfolder and are named
            # with the associated BGG Id (which is unique).
            for bgg_id, image in images.items():
                image_bytes = BytesIO()
                image.save(image_bytes, "PNG")
                file.writestr(
                    data.loc[data['BGG Id'] == bgg_id]['Image'].values[0],
                    image_bytes.getvalue()
                )
    except OSError:  # Couldn't save the file
        return False
    except zipfile.LargeZipFile:  # The file is too big, requires ZIP64.
        return False
    return True


def load_splz(filename: str) -> pd.DataFrame:
    pass

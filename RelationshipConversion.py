import os
from glob import glob
from pathlib import Path

import pandas as pd
import numpy as np
from tqdm import tqdm


def symmetrize_dataframe(df: pd.DataFrame):
    values = df.to_numpy()
    assert values.ndim == 2 and values.shape[0] == values.shape[1], 'Something with the dataframe is not right.'
    values = 1/2*(values.T + values)
    df.loc[:, :] = values
    return df

def similarity2distance(df: pd.DataFrame):

    # get the minimum and maximum for min-max-normalization
    mini = df.min().min()
    maxi = df.max().max()

    # do the formula as described in
    # Lucas Weber and Richard Lenz
    # "Relationship Discovery for Heterogeneous Time Series Integration: A Comparative Analysis for Industrial
    # and Building Data."
    # Datenbanksysteme für Business, Technologie und Web (BTW 2025).
    # Gesellschaft für Informatik, Bonn, 2025.
    df = np.exp(-(df - mini) / (maxi - mini))
    return df


def transform_conditional_entropy(df: pd.DataFrame):
    """
    Conditional entropy is a pseudo-distance (the more entropy there is, the less related signals are).
    But it is not symmetric, therefore we need a transformation.

    Additionally, the minimal value is not zero but negative infinity (pseudo-distance).
    Therefore, we have to make the values positive.

    :param df: the dataframe containing the distance/similarity values
    :return: the dataframe containing the transformed values that correspond to the notion of a distance
    (large values -> unrelated signals)
    """
    df = symmetrize_dataframe(df)
    df = df.abs().max().max() + df
    return df


def transform_covariance(df: pd.DataFrame):
    """
    Covariance is a similarity (but already symmetrical). We therefore need to convert it into a distance.

    :param df: the dataframe containing the distance/similarity values
    :return: the dataframe containing the transformed values that correspond to the notion of a distance
    (large values -> unrelated signals)
    """
    df = similarity2distance(df)
    return df


def transform_euclidean_dist(df: pd.DataFrame):
    """
    Euclidean distance is a distance and symmetrical, therefore we do not have to do anything.

    :param df: the dataframe containing the distance/similarity values
    :return: the dataframe containing the transformed values that correspond to the notion of a distance
    (large values -> unrelated signals)
    """
    return df


def transform_pec(df: pd.DataFrame):
    """
    Power Envelope Correlation is neither a similarity nor a distance but is symmetrical.
    We therefore square it first.
    And then we need to convert it into a distance.

    :param df: the dataframe containing the distance/similarity values
    :return: the dataframe containing the transformed values that correspond to the notion of a distance
    (large values -> unrelated signals)
    """
    df = df**2
    df = similarity2distance(df)
    return df


def transform_prec(df: pd.DataFrame):
    """
    Precision square is a similarity, but already symmetrical.
    We therefore need to convert it into a distance.

    :param df: the dataframe containing the distance/similarity values
    :return: the dataframe containing the transformed values that correspond to the notion of a distance
    (large values -> unrelated signals)
    """
    df = similarity2distance(df)
    return df


def main():

    # create the folder for the data
    if not os.path.isdir("data"):
        os.mkdir("data")
    new_root = Path("data")

    # get all the folders for the csv similarities as currently in the folder
    folders = glob('csv_similarities_*')
    files = [Path(ele) for folder in folders for ele in glob(os.path.join(folder, '*.csv'))]

    # create the folders within the data folder
    update_folders = dict()
    for folder in folders:
        target_folder = folder.replace("similarities", "transformed")
        target_folder = new_root / target_folder
        update_folders[folder] = target_folder
        if not os.path.isdir(target_folder):
            os.mkdir(target_folder)
    print(update_folders)
    # define the transformations functions
    transformation_functions = {"ce_gaussian.csv": transform_conditional_entropy,
                                "cov-sq_EmpiricalCovariance.csv": transform_covariance,
                                "pdist_euclidean.csv": transform_euclidean_dist,
                                "pec.csv": transform_pec,
                                "prec-sq_ShrunkCovariance.csv": transform_prec}

    # go through the files, make the transformations and put them into the new folder
    for file in tqdm(files, desc='Transforming files'):

        # get the folder we are working with
        folder = file.parts[-2]
        file_name = file.parts[-1]

        # get the target path
        target_name = update_folders[folder] / file_name

        # guard clause so a transformation is defined
        if file_name not in transformation_functions:
            continue

        # read the file into memory
        df = pd.read_csv(file, index_col=0)

        # call the transformation function and save the result
        df = transformation_functions[file_name](df)
        df.to_csv(target_name)


if __name__ == '__main__':
    main()

import os
from glob import glob
import time

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np


def preprocess_data(target_folder: str = "data"):

    # go through the folders and collect the data
    files = glob(os.path.join(target_folder, "*", "*reordering_results.csv"))

    # read the csv data containing the results and read them into memory adding a column with the file name
    results = []
    for file in files:

        # read the csv file
        filet = pd.read_csv(file, header=0)

        # create an extra column with the filename
        filet["File"] = file
        results.append(filet)
    results = pd.concat(results)

    # save the results as a parquet file
    results.to_parquet(f"Result_{time.time()}.parquet")

def plot_matrix_reordering(save_figure=False):

    # load the results into memory
    results = pd.read_parquet("Result_1742399052.0165398.parquet")
    print(results.columns)

    # get the dataset name from the filename
    results["Dataset"] = results["File"].apply(lambda x: os.path.split(x)[-2].split("_")[-1])
    results["Measure"] = results["File"].apply(lambda x: "_".join(os.path.split(x)[-1].split("_")[:-2]))

    # drop the originals rows as we do not need them
    results = results.loc[results["Name"] != "Original", :]

    # check which methods did not terminate
    results.replace([np.inf, -np.inf], np.nan, inplace=True)
    unterminated_methods = results.groupby("Method").apply(lambda x: x.eq(-1).any().any() or pd.isnull(x).any().any(), include_groups=False)
    unterminated_methods = set(unterminated_methods[unterminated_methods == True].index)
    print(f"The following methods did not terminate for all cases: {unterminated_methods} and will be deleted.")
    results = results[~results["Method"].isin(unterminated_methods)]

    # go through each dataset, relationship measure, and permutation and get the random linear arrangement
    # for normalization of the values
    random_arrangement = dict()
    for row in results[results["Method"] == "Random"].itertuples():
        key = (row.Name, row.File)
        assert key not in random_arrangement, 'Something is off.'
        random_arrangement[(row.Name, row.File)] = row.LS

    # normalize all the linear arrangement value
    timer = time.perf_counter()
    results["Normalizer"] = results[["Name", "File"]].apply(lambda x: random_arrangement[tuple(x)], axis=1)
    results["Normalized Linear Arrangement"] = results["LS"]/results["Normalizer"]
    print(f"Fast normalization took: {time.perf_counter() - timer:.2f} seconds.")

    testing = False
    if testing:
        timer = time.perf_counter()
        for (name, file), value in random_arrangement.items():
            bool_mask = (results["Name"] == name) & (results["File"] == file)
            results.loc[bool_mask, "LS"] /= value
        print(f"Slow normalization took: {time.perf_counter() - timer:.2f} seconds.")
        assert (results["Normalized LA"] == results["LS"]).all(), "Something is off."

    # rework the method names
    results["Method"] = results["Method"].str.replace("_", " ")

    # find the best performing methods (using the median)
    best_performing = results.groupby("Method")["Normalized Linear Arrangement"].median().nsmallest(10)
    # print(f"Best performing methods: {best_performing}.")
    best_performing = list(best_performing.index)

    # only keep the best methods
    results = results.loc[results["Method"].isin(set(best_performing)), :]

    # check whether we want to save
    if save_figure:
        # use pgf backed
        matplotlib.use("pgf")
        matplotlib.rcParams.update({
            "pgf.texsystem": "pdflatex",
            'font.family': 'serif',
            'text.usetex': True,
            'pgf.rcfonts': False,
        })

    # make a seaborn bar plot
    plt.figure()
    plt1 = sns.boxplot(results, x="Normalized Linear Arrangement", y="Method", hue="Method", order=best_performing,
                       palette="vlag")
    plt.grid(axis="x")
    plt.tight_layout()

    # make the ax label alignment
    for ele in plt1.get_xticklabels():
        ele.set_horizontalalignment('right')
        # https://stackoverflow.com/a/65244211
        ele.set_verticalalignment("center")  # for some obscure reason, this fixes horizontal alignment in pgf
    if save_figure:
        plt.savefig('linear_arrangement.pgf')
    else:
        plt.show()


def main():
    # uncomment this if you want to create a new results parquet file from a fresh run
    # preprocess_data()

    # make the plots
    plot_matrix_reordering(True)


if __name__ == "__main__":
    main()

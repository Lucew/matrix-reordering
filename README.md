# Matrix Reordering for Time Series Data Integration

With the rise of the internet of things (IoT) and data-driven analysis of complex systems, there is an ever-increasing 
amount of time-series data. Experts can use this data to optimize buildings or industrial complexes like power 
plants. While these developments are of utter importance for cost, energy, and environmental efficiency, 
missing meta-data is named as a challenge across all approaches by the industry, researchers, and government agencies.
Since manually adding semantic information is time-consuming and cost-intensive, automatic approaches are becoming 
increasingly important [[Weber, Lenz]](https://dl.gi.de/items/1418dcec-1af7-4337-9474-1c5aa25e22a8)

While most  approaches compare their performance against a ground truth, there exists a considerable usability gap of
the methods.  Namely, how a practitioner can apply the methods to an unknown set of time series from arbitrary
buildings. To close this gap, we aim to find appropriate visualizations to make the results accessible for pracitioners.

Automated approaches for finding a functional location (e.g., all sensors in one room) mostly take the form of pairwise
relationship measures. In other words, the outcome of most approaches is a similarity/dissimilarity matrix. With
arbitrary orderings, existing clusters and related sensors are hard to extract. Matrix reordering, also termed
seriation, has a considerable community in visual data analytics. With this paper, we want to show how these algorithms
can be applied to time series data integration by reordering the distance matrices to enable pracitioners to interact
with the methods.

# Reproducibility
Clone the repository and install the dependencies in a working python environment (docker, conda, venv recommended).

## Generating the similarity matrices
We use a data collection used in a previous publication 
[[Weber, Lenz]](https://dl.gi.de/items/1418dcec-1af7-4337-9474-1c5aa25e22a8). The similarity matrices can be found in
the accompanying [Github repository](https://github.com/Lucew/relationship-discovery). 

In order to get the similarity matrices run the script 
[Similarities2CSV.py](https://github.com/Lucew/relationship-discovery/blob/master/Similarities2CSV.py) within the cloned
repository. If you don't want to install the dependencies, the repository contains a docker image with the right
configuration.

After the script is finished, copy all folders starting with `csv_similarities_spi_*` in the folder of this repository.

## Preprocessing

The [seriation package](https://cran.r-project.org/web/packages/seriation/index.html) that implements the reordering
methods used in this paper expects distance matrices. Unfortunately, not all the relationship measures for time series
integration are distances. Therefore, we need to transform the matrices into a pseudo-distance as described in the
paper.

The script [RelationshipConversion.py](./RelationshipConversion.py) implements these conversion. Run the script with
after you copied the csv files (see previous step) - `python RelationshipConversion.py`.

## Running the Reorderings

As the reordering algorithms require some time, we implemented a distributed evaluation over multiple processor cores.
Run the script [DeployCalculations.py](./DeployCalculations.py) with the following options to reproduce the paper
results `python DeployCalculations.py -mt 180 -rs 50` to reproduce the paper results.

#! /usr/bin/env python3

import json
from argparse import ArgumentParser
from datetime import datetime
from matplotlib import pyplot as plt

import clr
parser = ArgumentParser()
# The default value here will work if the .NET assembly "compartments" is in the PYTHONPATH.
# If you are using the pycms docker container, this will be the case. Note that the default value
# doesn't have ".exe" at the end of it.
parser.add_argument("-c", "--compartments", default="compartments", help="Specify full path to compartments.exe")
parser.add_argument("-p", "--png", action="store_true", help="Save output to a .png file")

args = parser.parse_args()

clr.AddReference(args.compartments)
from compartments.emodl import EmodlLoader
from compartments import Configuration as cfg
from compartments.emod.utils import SolverFactory as solvers

import cmsmodel

import pandas as pd

def main():

    config = {
        "solver": "SSA",
        "runs": 11,
        "duration": 180,
        "samples": 180,
        "prng_seed": datetime.now().microsecond
    }
    cfg.CurrentConfiguration = cfg.ConfigurationFromString(json.dumps(config))

    model_description = build_model()
    model_info = load_model(model_description, cleanup=False)

    solver = solvers.CreateSolver(config["solver"], model_info, 1, 180.0, 180)
    solver.Solve()
    data = solver.GetTrajectoryData()
    df = pd.DataFrame(columns=list(map(str, solver.GetTrajectoryLabels())))
    for index, label in enumerate(solver.GetTrajectoryLabels()):
        print(f"index={index}, label={label}")
        plt.plot([float(value) for value in data[index]], label=str(label))
        df[str(label)] = [float(value) for value in data[index]]
    plt.legend()
    if not args.png:
        plt.show()
    else:
        print("Saving plot to 'trajectory.png'")
        plt.savefig("trajectory.png")

    print(df.head())
    df.to_csv("trajectories.net.csv")

    return


def build_model():

    model = cmsmodel.CmsModel("seir")

    model.add_species("S", 990, observe=True)
    model.add_species("E", 0, observe=True)
    model.add_species("I", 10, observe=True)
    model.add_species("R", 0, observe=True)
    model.add_species("CI", 0)

    model.add_parameter("Ki", 0.5)
    model.add_parameter("Kl", 0.2)
    model.add_parameter("Kr", 1/7)
    model.add_parameter("Kw", 1/365)

    model.add_reaction("transmit", ["S"], ["E", "CI"], "(/ (* Ki S I) (+ S E I R))")
    model.add_reaction("shed", ["E"], ["I"], "(* Kl E)")
    model.add_reaction("recover", ["I"], ["R"], "(* Kr I)")
    model.add_reaction("waning", ["R"], ["S"], "(* Kw R)")

    model.add_observable("cumulative", "CI")
    model.add_observable("population", "(+ S E I R)")

    return model


def load_model(model, cleanup=True):

    model_info = EmodlLoader.LoadEMODLModel(str(model))

    return model_info


def sample_one():

    ## Sample load from fixed file and RunModel() - writes trajectories to file as specified in configuration
    # from compartments import Program as cms
    # model = cms.LoadModel("e:/src/ifdm/cms-test/models/idm/simplemodel/simplemodel.emodl")
    # cms.RunModel(model, config["solver"], config["duration"], config["runs"], config["samples"])

    return


def sample_two():

    ## Sample load from fixed file and ExecuteModel() - returns trajectories to caller
    # from compartments import Program as cms
    # model = cms.LoadModel("e:/src/ifdm/cms-test/models/idm/simplemodel/simplemodel.emodl")
    # results = cms.ExecuteModel(model, config["solver"], config["duration"], config["runs"], config["samples"])
    # for label in results.Labels:
    #     print(label)
    #
    # print(f"{len(results.Data)} trajectories in results.")
    #
    # for index in range(len(results.Data)):
    #     plt.plot([float(value) for value in results.Data[index]], label=str(results.Labels[index]))
    #
    # plt.show()

    return


if __name__ == "__main__":
    main()

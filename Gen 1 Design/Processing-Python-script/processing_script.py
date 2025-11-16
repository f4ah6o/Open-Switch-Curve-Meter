import marimo

__generated_with = "0.9.14"
app = marimo.App(width="medium")


@app.cell
def __():
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    return np, pd, plt


@app.cell
def __():
    # Configuration parameters
    switch_name = "Kailh Box Navy"  # switch_name is currently not used

    # File paths (update these to your actual paths)
    input_file = "Choc-Brown.csv"
    output_file = "Choc-Brown-processed.csv"

    graph = False  # Graphing still needs to be implemented
    graph_output_file = "Wherever.png"  # Graphing still needs to be implemented

    # Parameters used to find the start and end (adjust if they don't work well)
    start_step = 0.3  # Change in consecutive measurements that indicates the start point
    end_step = start_step  # Change in consecutive measurements that indicates the end point

    # Property of your force curve meter
    force_curve_meter_step_increment = 0.005  # Increments in mm

    # Properties of the actuation and release arrows
    arrow_length = 10  # Length for the actuation and release point arrows
    arrow_offset = 3  # How far the arrows should be from the actual force curve line, in gf

    return (
        switch_name,
        input_file,
        output_file,
        graph,
        graph_output_file,
        start_step,
        end_step,
        force_curve_meter_step_increment,
        arrow_length,
        arrow_offset,
    )


@app.cell
def __(input_file, pd):
    # Part 0 - Import data
    data = pd.read_csv(input_file)
    return data,


@app.cell
def __(data, force_curve_meter_step_increment, np, start_step):
    # Part 1 - Tare the data, and prepare the downstroke

    # Part 1a - Find the start point of the downstroke
    started = False
    index_start = 0

    while not started:
        index_start += 1
        if data["Raw Force (gf)"][index_start] - data["Raw Force (gf)"][index_start - 1] > start_step:
            started = True
        elif index_start > 3000:
            print("Error - unable to find start point - consider adjusting your start_step, or check your input file.")
            break

    # Part 1b - Tare the data
    zero_average = np.average(data["Raw Force (gf)"][0:index_start - 1])
    data["Force - Tared (gf)"] = data["Raw Force (gf)"] - zero_average

    # Part 1c - Create the corrected downstroke
    # Part 1c1 - Find the length of the downstroke (travel)
    peak_value = data["Force - Tared (gf)"].max()
    index_peak = data["Force - Tared (gf)"].idxmax()

    travel = (index_peak - index_start) * force_curve_meter_step_increment

    # Part 1c2 - Create the corrected downstroke X axis which starts from 0
    data["Corrected downstroke X (mm)"] = pd.Series(
        np.arange(0, travel + force_curve_meter_step_increment, force_curve_meter_step_increment)
    )

    # Part 1c3 - Create the corrected downstroke force readings
    downstroke_force = data["Force - Tared (gf)"][0:index_peak + 1]
    data["Corrected downstroke force (gf)"] = downstroke_force.shift(-1 * index_start)

    # Part 1c4 - Create the corrected downstroke actuation status
    downstroke_actuation = data["Actuated?"][0:index_peak + 1]
    data["Corrected downstroke actuated?"] = downstroke_actuation.shift(-1 * index_start)

    return (
        started,
        index_start,
        zero_average,
        peak_value,
        index_peak,
        travel,
        downstroke_force,
        downstroke_actuation,
    )


@app.cell
def __(data, end_step, force_curve_meter_step_increment, index_peak, np, travel):
    # Part 2 - Prepare the upstroke

    # Part 2a - Create the corrected upstroke X axis
    data["Corrected upstroke X (mm)"] = pd.Series(
        np.arange(travel, -1 * force_curve_meter_step_increment, -1 * force_curve_meter_step_increment)
    )

    # Part 2b - Find the endpoint of the measurement
    index_end = len(data) - 1
    ended = False

    while not ended:
        index_end -= 1
        if data["Force - Tared (gf)"][index_end] - data["Force - Tared (gf)"][index_end + 1] > end_step:
            ended = True
        elif index_end <= 0:
            print("Error - unable to find end point - consider adjusting your end_step")
            break

    # Part 2c - Create the corrected upstroke force
    upstroke_force = data["Force - Tared (gf)"][0:index_end + 1]
    data["Corrected upstroke force (gf)"] = upstroke_force.shift(-1 * (index_peak + 1))

    # Part 2d - Create the corrected upstroke actuation status
    upstroke_actuation = data["Actuated?"][0:index_end + 1]
    data["Corrected upstroke actuated?"] = upstroke_actuation.shift(-1 * (index_peak + 1))

    # Part 2e - Match length, by trimming from the top
    if data["Corrected upstroke force (gf)"].count() > data["Corrected upstroke X (mm)"].count():
        shift_amount = data["Corrected upstroke force (gf)"].count() - data["Corrected upstroke X (mm)"].count()
        data["Corrected upstroke force (gf)"] = data["Corrected upstroke force (gf)"].shift(-1 * shift_amount)
        data["Corrected upstroke actuated?"] = data["Corrected upstroke actuated?"].shift(-1 * shift_amount)
    elif data["Corrected upstroke force (gf)"].count() < data["Corrected upstroke X (mm)"].count():
        # Still need to write this code to fill in zeroes
        print("test")

    return index_end, ended, upstroke_force, upstroke_actuation


@app.cell
def __(arrow_length, arrow_offset, data, np):
    # Part 3 - Find and report the actuation and release points

    # Part 3a - Find the actuation point
    actuated = False
    index_actuation = 0
    actuation_point = 0
    actuation_force = 0

    while not actuated:
        index_actuation += 1
        if (data["Corrected downstroke actuated?"][index_actuation] > 0.5 and
            data["Corrected downstroke actuated?"][index_actuation - 1] < 0.5):
            actuated = True
            actuation_point = data["Corrected downstroke X (mm)"][index_actuation]
            actuation_force = data["Corrected downstroke force (gf)"][index_actuation]
        elif index_actuation > 6000:
            print("Error - unable to find actuation point")
            break

    # Part 3b - Find the release point
    released = False
    index_release = 0
    release_point = 0
    release_force = 0

    while not released:
        index_release += 1
        if (data["Corrected upstroke actuated?"][index_release] < 0.5 and
            data["Corrected upstroke actuated?"][index_release - 1] > 0.5):
            released = True
            release_point = data["Corrected upstroke X (mm)"][index_release]
            release_force = data["Corrected upstroke force (gf)"][index_release]
        elif index_release > 6000:
            print("Error - unable to find release point")
            break

    # Part 3c - Write the actuation points
    data["Actuation points"] = np.nan
    data.at[0, "Actuation points"] = actuation_point
    data.at[1, "Actuation points"] = actuation_point

    data["Actuation arrow points"] = np.nan
    data.at[0, "Actuation arrow points"] = actuation_force + arrow_offset
    data.at[1, "Actuation arrow points"] = actuation_force + arrow_offset + arrow_length

    # Part 3d - Write the release points
    data["Release points"] = np.nan
    data.at[0, "Release points"] = release_point
    data.at[1, "Release points"] = release_point

    data["Release arrow points"] = np.nan
    data.at[0, "Release arrow points"] = release_force - arrow_offset
    data.at[1, "Release arrow points"] = release_force - arrow_offset - arrow_length

    return (
        actuated,
        index_actuation,
        actuation_point,
        actuation_force,
        released,
        index_release,
        release_point,
        release_force,
    )


@app.cell
def __(data, output_file):
    # Part 4 - Write output file
    data_rounded = data.round(3)
    data_rounded.to_csv(output_file)
    return data_rounded,


@app.cell
def __(
    actuation_force,
    actuation_point,
    index_end,
    index_peak,
    index_start,
    release_force,
    release_point,
    travel,
):
    # Part 5 - Report findings
    print("Index start: ", index_start)
    print("Index peak: ", index_peak)
    print("Index end: ", index_end)
    print("Travel:", travel, "mm")
    print("Actuation point: ", actuation_point, "mm")
    print("Actuation force: ", actuation_force, "gf")
    print("Release point: ", release_point, "mm")
    print("Release_force: ", release_force, "gf")
    return


@app.cell
def __(data, graph, plt):
    # Part 6 - Graph (not yet implemented)
    if graph:
        plt.figure(figsize=(10, 6))
        plt.plot(data["Corrected downstroke X (mm)"], data["Corrected downstroke force (gf)"], label="Downstroke")
        plt.plot(data["Corrected upstroke X (mm)"], data["Corrected upstroke force (gf)"], label="Upstroke")
        plt.xlabel("Distance (mm)")
        plt.ylabel("Force (gf)")
        plt.title("Force Curve")
        plt.legend()
        plt.grid(True)
        plt.gca()
    return


if __name__ == "__main__":
    app.run()

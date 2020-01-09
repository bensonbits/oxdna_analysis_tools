#!/usr/bin/env python

import numpy as np
from os import environ, path
from sys import exit, stderr
import subprocess
import argparse
import matplotlib.pyplot as plt
from config import PROCESSPROGRAM
import time

if __name__ == "__main__":
    #handle commandline arguments
    #this program has no positional arguments, only flags
    parser = argparse.ArgumentParser(description="Finds the ensemble of distances between any two particles in the system")
    parser.add_argument('-i', '--input', nargs=4, action='append', help='An inputfile, trajectory, particle1, particle2 set.  Can call -i multiple times to plot multiple datasets.')
    parser.add_argument('-o', '--output', nargs=1, help='The name to save the graph file to')
    parser.add_argument('-f', '--format', nargs=1, help='Output format for the graphs.  Defaults to histogram.  Options are \"histogram\", \"trajectory\", and \"both\"')
    parser.add_argument('-d', '--data', nargs=1, help='If set, the output from DNAnalysis will be dumped to the specified filename')
    args = parser.parse_args()

    #-i requires 4 arguments, the input file used to run the simulation, the trajectory to analyze, and the two particles to compute the distance between.
    inputfiles = [i[0] for i in args.input]
    trajectories = [i[1] for i in args.input]
    p1s = [i[2] for i in args.input]
    p2s = [i[3] for i in args.input]

    #Make sure that the input is correctly formatted
    if(len(inputfiles) != len(trajectories) != len(p1s) != len(p2s)):
        print("ERROR: bad input arguments\nPlease supply an equal number of input, trajectory and particle pairs", file=stderr)
        exit(1)

    #-o names the output file
    if args.output:
        outfile = args.output[0]
    else: 
        print("INFO: No outfile name provided, defaulting to \"distance.png\"", file=stderr)
        outfile = "distance.png"

    #-f defines which type of graph to produce
    hist = False
    lineplt = False
    if args.format:
        if "histogram" in args.format:
            hist = True
        if "trajectory" in args.format:
            lineplt = True
        if "both" in args.format:
            hist = True
            lineplt = True
        if hist == lineplt == False:
            print("ERROR: unrecognized graph format\nAccepted formats are \"histogram\", \"trajectory\", and \"both\"", file=stderr)
            exit(1)
    else:
        print("INFO: No graph format specified, defaulting to histogram", file=stderr)
        hist = True

    distances = []

    #for each input, launch DNAnalysis to use the faster C++ distance calculator
    for i,inputfile, dat_file, particle_1, particle_2 in zip(range(len(inputfiles)), inputfiles, trajectories, p1s, p2s):
        command_for_data = 'analysis_data_output_1 = { \n name = stdout \n print_every = 1 \n col_1 = { \n type=step \n} \n col_2 = { \n type=distance \n particle_1='+str(particle_1)+'\n particle_2='+str(particle_2)+'\n PBC=true \n} \n}'

        launchargs = [PROCESSPROGRAM,inputfile ,'trajectory_file='+dat_file,command_for_data]
        print("INFO: running DNAnalysis on file {}...".format(dat_file), file=stderr)
        myinput = subprocess.run(launchargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        out = myinput.stdout
        err = myinput.stderr
        for line in err.split('\n'):
            if "CRITICAL" in line or "ERROR" in line:
                print("ERROR: DNAnalysis encountered an error", file=stderr)
                print(err, file=stderr)
        out = out.rstrip()
        distances.append([float(i.split()[1])*0.85 for i in out.strip().split('\n')]) # 1 simulation unit is 0.85 nm

    # -d will dump the DNAnalysis output to a text file.
    if args.data:
        datafile = args.data[0]
        if len(distances) > 1:
            for i, data in enumerate(distances):
                out = datafile[:datafile.find(".")]+str(i)+datafile[datafile.find("."):]
                with open(out, 'w+') as f:
                    print("INFO: Writing DNAnalysis output to file {}".format(out), file=stderr)
                    f.write(data)
        else:
            with open(datafile, 'w+') as f:
                f.write(data)

    #get some min/max values to make the plots pretty
    lower = min((min(l) for l in distances))
    upper = max((max(l) for l in distances))

    [print("mean_distance:", np.mean(l), "stdev:", np.std(l)) for l in distances]

    #from clustering import perform_DBSCAN
    #for l in distances:
    #    perform_DBSCAN(np.array(l), 10, dat_file, inputfile)

    print(hist, lineplt)
    #make a histogram
    if hist == True:
        if lineplt == True:
            #if making two plots, automatically append the plot type to the output file name
            out = outfile[:outfile.find(".")]+"_hist"+outfile[outfile.find("."):]
        else:
            out = outfile
        bins = np.linspace(np.floor(lower-(lower*0.1)), np.ceil(upper+(upper*0.1)), np.ceil(len(distances[0])/2))
        for i, dist_list in enumerate(distances):
            a = plt.hist(dist_list, bins, weights=np.ones(len(dist_list)) / len(dist_list),  alpha=0.5, label="{} from {} to {}".format(args.input[i][1], args.input[i][2], args.input[i][3]))
        plt.xlabel("Distance (nm)")
        plt.ylabel("Normalized frequency")
        plt.legend()
        #plt.show()
        print("INFO: Writing histogram to file {}".format(out), file=stderr)
        plt.savefig("{}".format(out))

    #make a trajectory plot
    if lineplt == True:
        if hist == True:
            #clear the histogram plot
            plt.clf()
            #if making two plots, automatically append the plot type to the output file name
            out = outfile[:outfile.find(".")]+"_traj"+outfile[outfile.find("."):]
        else:
            out = outfile
        for i, dist_list in enumerate(distances):
            a = plt.plot(dist_list, alpha=0.5, label="{} from {} to {}".format(args.input[i][1], args.input[i][2], args.input[i][3]))
        plt.xlabel("Simulation Steps")
        plt.ylabel("Distance (nm)")
        plt.legend()
        #plt.show()
        print("INFO: Writing trajectory plot to file {}".format(out), file=stderr)
        plt.savefig("{}".format(out))
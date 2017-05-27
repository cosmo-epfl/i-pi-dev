#!/usr/bin/env python2

""" 
Computes the velocity autocorrelation functions from i-pi outputs. 
Assumes the input files are in xyz format and atomic units.
"""


import argparse
import sys
import numpy as np
from ipi.utils.io import read_file


def compute_acf(input_file, output_prefix, maximum_lag, length_block, length_zeropadding, spectral_windowing, labels):

    # stores the arguments
    ifile = str(args.input_file[-1])
    ofile = str(args.output_prefix[-1])
    mlag = int(args.maximum_lag[-1])
    bsize = int(args.length_block[-1])
    npad = int(args.length_zeropadding[-1])
    ftbox = str(args.spectral_windowing[-1])
    labels = str(args.labels)

    #checks for errors
    if(mlag <= 0):
        raise ValueError("MAXIMUM_LAG should be a non-negative integer.")
    if(npad < 0):
        raise ValueError("LENGTH_ZEROPADDING should be a non-negative integer.")
    if(bsize <=2 * mlag):
        if(bsize == -1):
            bsize = 2 * mlag
        else:
            raise ValueError("LENGTH_BLOCK should be greater than or equal to 2 * MAXIMUM_LAG.")

    #reads one frame. 
    ff = open(ifile)
    rr = read_file("xyz", ff, output = "array")
    ff.close()

    #stores the indices of the "chosen" atoms.
    ndof = len(rr['data'])
    if( "*" in labels):
        labelbool = np.ones(ndof/3, bool)
    else:
        labelbool = np.zeros(ndof/3, bool)
        for l in labels:
            labelbool = np.logical_or(labelbool, rr['names'] == l)
    nspecies = labelbool.sum()

    #initializes variables.
    nblocks = 0
    dt = 1.0 / float(bsize)
    data = np.zeros((bsize, nspecies, 3) , float)
    fvvacf = np.zeros(bsize / 2 + 1, float)
    time = np.asarray(range(mlag + 1)) * dt
    omega = np.asarray(range(2 * (mlag + npad)))/float(2 * mlag + 2 * npad) * (2 * np.pi)

    #selects window function for fft.
    if(ftbox == "none"):
        win = np.ones(2 * mlag + 1, float)
    elif(ftbox == "cosine-hanning"):
        win = np.hanning(2 * mlag + 1)
    elif(ftbox == "cosine-hamming"):
        win = np.hamming(2 * mlag + 1)
    elif(ftbox == "cosine-blackman"):
        win = np.blackman(2 * mlag + 1)
    elif(ftbox == "triangle-bartlett"):
        win = np.bartlett(2 * mlag + 1)

    print win

    ff = open(ifile)
    while True:

        try :
            #Reads the data in blocks.
            for i in range(bsize):
                rr = read_file("xyz", ff, output="array")
                data[i] = rr['data'].reshape((ndof/3,3))[labelbool]

            #Computes the Fourier transform of the data.
            fdata = np.fft.rfft(data , axis = 0)

            #Computes the Fourier transform of the vvac applying the convolution theorem.
            tfvvacf = fdata * np.conjugate(fdata)

            #Averages over all species and sums over the x,y,z directions. Also multiplies with the time step and a prefactor of (2pi)^-1.
            fvvacf = fvvacf + 3.0 * np.real(np.mean(tfvvacf, axis = (1,2))) * dt / (2 * np.pi)
            nblocks +=  1

        except EOFError:
            break
    ff.close()

    #Performs the block average of the Fourier transform.
    fvvacf = np.real(fvvacf) / nblocks

    #Computes the inverse Fourier transform to get the vvac.
    vvacf = np.fft.irfft(fvvacf)[:mlag + 1]
    np.savetxt(ofile + "_vv.data" , np.vstack((time, vvacf)).T[:mlag + npad])

    #Applies window in one direction and pads the vvac with zeroes.
    pvvacf = np.append(vvacf * win[mlag:], np.zeros(npad))

    #Recomputes the Fourier transform assuming the data is an even function of time.
    fpvvacf = np.fft.hfft(pvvacf)
    np.savetxt(ofile + "_fvv.data" , np.vstack((omega, fpvvacf)).T[:mlag + npad])

if __name__ == "__main__":

   # adds description of the program.
    parser=argparse.ArgumentParser(description="Given the velocity of a system, computes the velocity-velocity autocorrelation function and its Fourier transform")

   # adds arguments.
    parser.add_argument("-ifile", "--input_file", required=True, nargs=1, type=str, default=None, help="the relative path to the xyz formatted velocity file")
    parser.add_argument("-mlag", "--maximum_lag", required=True, nargs=1, type=int, default=None, help="the maximum time lag for the autocorrelation function")
    parser.add_argument("-bsize", "--length_block", nargs=1, type=int, default=[-1],  help="the number of lines to be imported at once during ``chunk-by-chunk`` input; defaults to 2 * MAXIMUM_LAG")
    parser.add_argument("-ftpad", "--length_zeropadding", nargs=1, type=int, default=[0], help="number of zeroes to be padded at the end of the autocorrelation function before the Fourier transform is computed")
    parser.add_argument("-ftwin", "--spectral_windowing", nargs=1, type=str, choices=["none", "cosine-hanning", "cosine-hamming", "cosine-blackman", "triangle-bartlett"], default=["none"], help="if autocorrelation function should be multiplied by a window function before the Fourier transform is computed.")
    parser.add_argument("-labels", "--labels", nargs=1, type=str, default=["*"], help="labels of the species to be monitored")
    parser.add_argument("-oprefix", "--output_prefix", required=True, nargs=1, type=str, help="the prefix of the output file.")

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit()

    # Process everything.
    compute_acf(args.input_file, args.output_prefix, args.maximum_lag, args.length_block, args.length_zeropadding, args.spectral_windowing, args.labels)


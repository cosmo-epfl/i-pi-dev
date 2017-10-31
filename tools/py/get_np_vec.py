#!/usr/bin/env python2 
description = """
Computes the momentum distribution having as input the end-to-end vectors of the open path
in atomic units. The result is the 3D distribution in atomic units, with the format
px py pz n(p)
....
"""

import argparse
import numpy as np
import time
from scipy.interpolate import RegularGridInterpolator

def histo3d(data, dqxgrid, dqygrid, dqzgrid, ns, cut,invsigma, bsize):

    histo = np.zeros((ns,ns,ns))
    fx = np.zeros(ns); fy = np.zeros(ns); fz = np.zeros(ns); 

    dqxstep = np.abs(dqxgrid[1] - dqxgrid[0])
    dqystep = np.abs(dqygrid[1] - dqygrid[0])
    dqzstep = np.abs(dqzgrid[1] - dqzgrid[0])

    dqcutx = int(cut / invsigma / dqxstep)
    dqcuty = int(cut / invsigma / dqystep)
    dqcutz = int(cut / invsigma / dqzstep)

    nshalf = ns/2.
    halfinvsigma2 = 0.5 * invsigma**2

    for x,y,z in data:
        qx= int(x/dqxstep + nshalf)
        qy= int(y/dqystep + nshalf)
        qz= int(z/dqzstep + nshalf) 
        
        fx[qx-dqcutx:qx+dqcutx] = np.exp(-(x-dqxgrid[qx-dqcutx:qx+dqcutx])**2*halfinvsigma2)
        fy[qy-dqcuty:qy+dqcuty] = np.exp(-(y-dqygrid[qy-dqcuty:qy+dqcuty])**2*halfinvsigma2)
        fz[qz-dqcutz:qz+dqcutz] = np.exp(-(z-dqzgrid[qz-dqcutz:qz+dqcutz])**2*halfinvsigma2)
     
        histo[qx-dqcutx:qx+dqcutx,qy-dqcuty:qy+dqcuty,qz-dqcutz:qz+dqcutz] += outer3(fx[qx-dqcutx:qx+dqcutx], fy[qy-dqcuty:qy+dqcuty], fz[qz-dqcutz:qz+dqcutz])
    return histo * np.sqrt(1.0 / 2.0 / np.pi * invsigma**2)**3


def outer3(*vs):
    return reduce(np.multiply.outer, vs)
     
def get_np(fname, prefix, bsize, P, mamu, Tkelv, s, ns, cut):   

    start = time.clock()

    #Read the end to end distances from file
    delta= np.loadtxt(fname)
    step = np.shape(delta)[0] 

    #convert to atomic units
    T = 3.1668105e-06 * Tkelv
    m = 1822.8885 * mamu

    #set the default parameters for the grid in case they are not given
    if(s == 0): s = delta.max() * 5.
    if(ns == 0): ns = int(2 * s * np.sqrt(T * P * m) + 20.0)
    if(ns % 2 == 0): ns += 1

    dq = np.zeros((bsize,3) , float)
    dqxgrid = np.linspace(-s, s, ns)
    dqygrid = np.linspace(-s, s, ns)
    dqzgrid = np.linspace(-s, s, ns)
    qgrid = np.zeros((3,ns*ns*ns))
    dqx,dqy,dqz= np.meshgrid(dqxgrid, dqygrid, dqzgrid)
    qgrid[0,:] = (np.array(dqx)).flatten()
    qgrid[1,:] = (np.array(dqy)).flatten()
    qgrid[2,:] = (np.array(dqz)).flatten()

    dqxstep = np.abs(dqxgrid[0] - dqxgrid[1])
    dqystep = np.abs(dqygrid[0] - dqygrid[1])
    dqzstep = np.abs(dqzgrid[0] - dqzgrid[1])
 
    # Defines the final grid for momentum.
    pxi = -np.pi/(dqxgrid[1]-dqxgrid[0])
    pxf = +np.pi/(dqxgrid[1]-dqxgrid[0])
    pxstep = 2 * np.pi / np.abs(dqxgrid[-1]-dqxgrid[0])
    pxgrid = np.linspace(pxi,pxf,ns)
  

    pyi = -np.pi/(dqygrid[1]-dqygrid[0])
    pyf = +np.pi/(dqygrid[1]-dqygrid[0])
    pystep = 2 * np.pi / np.abs(dqygrid[-1]-dqygrid[0])
    pygrid = np.linspace(pyi,pyf,ns)

    pzi = -np.pi/(dqzgrid[1]-dqzgrid[0])
    pzf = +np.pi/(dqzgrid[1]-dqzgrid[0])
    pzstep = 2 * np.pi / np.abs(dqzgrid[-1]-dqzgrid[0])
    pzgrid = np.linspace(pzi,pzf,ns)
 
    if(ns%2 ==0):  pxgrid= pxgrid- pxstep/2.;  pygrid= pygrid- pystep/2.; pzgrid= pzgrid- pzstep/2.;

    px,py,pz= np.meshgrid(pxgrid, pygrid, pzgrid)
    pgrid= np.zeros((3,ns*ns*ns))
    pgrid[0,:] = (np.array(py)).flatten()
    pgrid[1,:] = (np.array(px)).flatten()
    pgrid[2,:] = (np.array(pz)).flatten() 
    dpstep= np.abs(pxgrid[1]-pxgrid[0])
    
    nplist3d = []
    h3dlist = []
    ftxlist = []
    ftylist = []
    ftzlist = []
    px2list = []
    py2list = []
    pz2list =[]

    n_block =int(step/bsize)
    if (n_block ==0):
             print 'not enough data to build a block'
             exit()
    for x in xrange(n_block):
        dq = delta[x*bsize : (x+1)*bsize]
        print "# Computing 3D histogram."
        h3d = histo3d(np.concatenate((dq, -dq)), dqxgrid, dqygrid, dqzgrid, ns, cut, np.sqrt(T * P * m), bsize)
        h3dlist.append(h3d) 

        # Computes the 3D Fourier transform of the convoluted histogram of the end-to-end distances.
        #npvec3d= np.abs(np.fft.fftshift(np.fft.fftn(h3d)))       
        #nplist3d.append(npvec3d.flatten())
        
        # Calculates px2, py2, pz2
        xgrid = dqxgrid
        ygrid = dqygrid
        zgrid = dqzgrid

        # Creates an interpolation function on a 3D grid 
        hxyz = RegularGridInterpolator((xgrid,ygrid,zgrid), h3d)

        # Calculates the histogram along the x,y,z directions
        hx00 = hxyz((xgrid,0,0)) 
        h0y0 = hxyz((0,ygrid,0)) 
        h00z = hxyz((0,0,zgrid)) 

        # Takes the Fourier transform to get the corresponding momentum distribution along the xyz directions.
        # Computes the Fourier transform of the end to end vector.
        fthx00 = hx00 * 0.0
        fth0y0 = h0y0 * 0.0
        fth00z = h00z * 0.0

        print "# computing FT for block #", x
        for i in range(len(fthx00)):
            fthx00[i] = (hx00 * np.cos(pxgrid[i] * dqxgrid)).sum()
            fth0y0[i] = (h0y0 * np.cos(pygrid[i] * dqygrid)).sum()
            fth00z[i] = (h00z * np.cos(pzgrid[i] * dqzgrid)).sum()

        # Calculates the average values of the second moments.
        px2list.append((fthx00 * pxgrid**2).sum())
        py2list.append((fth0y0 * pxgrid**2).sum())
        pz2list.append((fth00z * pxgrid**2).sum())

        ftxlist.append(fthx00)
        ftylist.append(fth0y0)
        ftzlist.append(fth00z)

    #avgnp3d= np.mean(np.asarray(nplist3d), axis = 0)
    #norm= sum(avgnp3d*dpstep**3)
    #avgnp3d= avgnp3d/norm
    #np.savetxt(str("output"+ prefix +".np3d"), np.c_[pgrid.T, avgnp3d])

    # Calculates the average histogram.
    h3d = np.sum(np.asarray(h3dlist), axis = 0)

    fthx00 = np.sum(np.asarray(ftxlist), axis = 0)
    fth0y0 = np.sum(np.asarray(ftylist), axis = 0)
    fth00z = np.sum(np.asarray(ftzlist), axis = 0)

    ftxnorm = (fthx00).sum()
    ftynorm = (fth0y0).sum()
    ftznorm = (fth00z).sum()
    
    # Calculates the average values of the second moments.
    print "px^2:", np.sum(np.asarray(px2list), axis = 0) / ftxnorm, "+/-", np.std(np.asarray(px2list) / ftxnorm) * np.sqrt(n_block)
    print "py^2:", np.sum(np.asarray(py2list), axis = 0) / ftynorm, "+/-", np.std(np.asarray(py2list) / ftynorm) * np.sqrt(n_block)
    print "pz^2:", np.sum(np.asarray(pz2list), axis = 0) / ftznorm, "+/-", np.std(np.asarray(pz2list) / ftznorm) * np.sqrt(n_block)

    print "# time taken (s)", time.clock() - start


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument( '-qfile', type=str, help = "name of the end-to-end distance vectors file")
    parser.add_argument('--prefix', type=str, default ="", help = 'prefix for the output files')
    parser.add_argument("-bsize", type=int, default = 50000, help = "specify the size of the blocks")
    parser.add_argument("-P", type=int, default = 1 , help = "specify the number of beads")
    parser.add_argument("-m", type=float, default = 1.007, help = "specify the mass of the atom in a.m.u. default is hydorgen")
    parser.add_argument("-T", type=float, default = 300, help = "specify the temperature of the system in kelvin")
    parser.add_argument("-dint", type=float, default = 0, help = "specify the positive extrema of the interval to build the histogram ([-dint,dint])")
    parser.add_argument("-ns", type=int, default = 0, help = "specify the number of point to use for the histogram")
    parser.add_argument("-cut", type=int, default = 6, help = "specify the size of the grid around a specific point in units of sigma")
    args = parser.parse_args()

    get_np(args.qfile, args.prefix, args.bsize, args.P, args.m, args.T,args.dint, args.ns, args.cut)


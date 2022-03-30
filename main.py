"""
Main code to run the radiative transfer calculation.
Created on 15. July 2021 by Andrea Gebek.
"""

import sys
import json
import numpy as np
from datetime import datetime
import os
import multiprocessing as mp
from functools import partial
SCRIPTPATH = os.path.realpath(__file__)
GITPATH = os.path.dirname(SCRIPTPATH)
PARENTPATH = os.path.dirname(GITPATH)
sys.path.append(GITPATH)
import prometheusScripts.constants as const

if __name__ == '__main__':

    N_arguments = len(sys.argv)

    if N_arguments == 1:

        import prometheusScripts.setup

        sys.exit(0)

    import prometheusScripts.fluxDecrease as flux

    startTime = datetime.now()

    """
    Read in the json parameters and perform the radiative transfer calculation
    """

    paramsFilename = sys.argv[1]

    with open(PARENTPATH + '/setupFiles/' + paramsFilename + '.txt') as file:
        param = json.load(file)

    fundamentalsDict = param['Fundamentals']
    scenarioDict = param['Scenarios']
    architectureDict = param['Architecture']
    speciesDict = param['Species']
    gridsDict = param['Grids']
    outputDict = param['Output']

    GRID, args = flux.prepareArguments(fundamentalsDict, architectureDict, scenarioDict, speciesDict, gridsDict, outputDict)

    N_cores = mp.cpu_count()

    RESULTS = []

    with mp.Pool(processes = N_cores) as pool:

        RESULTS = pool.map(partial(flux.evaluateChord, args = args), GRID)

    pool.close()
    pool.join()
    print(sys.getsizeof(RESULTS))
    R = np.sum(np.array(RESULTS).reshape((int(gridsDict['orbphase_steps']), int(gridsDict['phi_steps']) * int(gridsDict['rho_steps']), len(args[3]))), axis = 1).flatten() # Sum over rho and phi coordinates


    """
    Store the output in .txt files
    """

    orbphase_axis = flux.constructAxis(gridsDict, architectureDict, 'orbphase')
    wavelength_axis = flux.constructAxis(gridsDict, architectureDict, 'wavelength') * 1e8 # Conversion from cm to Angstrom

    wavelength, orbphase = np.meshgrid(wavelength_axis, orbphase_axis, indexing = 'ij')
    wavelength = wavelength.flatten()
    orbphase = orbphase.flatten()


    header = 'Wavelength grid (Å), Orbital phase grid [rad], R'

    np.savetxt(PARENTPATH + '/output/' + paramsFilename + '_lightcurve.txt', np.array([wavelength, orbphase, R]).T, header = header)


    if outputDict['benchmark']:

        R_benchmark = resultsDict['R_benchmark'].flatten()

        np.savetxt(PARENTPATH + '/output/' + paramsFilename + '_barometricBenchmark.txt', np.array([wavelength, orbphase, R_benchmark]).T, header = header)


    if outputDict['recordTau']:

        rho_axis = flux.constructAxis(gridsDict, architectureDict, 'rho')

        phi_axis = flux.constructAxis(gridsDict, architectureDict, 'phi')
        
        phi, rho = np.meshgrid(phi_axis, rho_axis, indexing = 'ij')
        phi = phi.flatten()
        rho = rho.flatten()

        tauDisk = resultsDict['tauDisk'].flatten()

        np.savetxt(PARENTPATH + '/output/' + paramsFilename + '_tau.txt', np.array([phi, rho, tauDisk]).T, header = 'phi grid [rad], rho grid [cm], tau')  

    elapsedTime = datetime.now() - startTime

    print("\nDISHOOM-PROMETHEUS finished, yay! Elapsed time is:", elapsedTime)

    print("The maximal flux decrease due to atmospheric/exospheric absorption in percent is:", np.abs(np.round(100 * (1 - np.min(R)), 5)))

    print("The minimal flux decrease due to atmospheric/exospheric absorption in percent is:", np.abs(np.round(100 * (1 - np.max(R)), 5)))


    print(r"""
    *******  *******           ,/MMM8&&&.         ****     **** ******** ********** **      ** ******** **     **  ********
    /**////**/**////**     _...MMMMM88&&&&..._    /**/**   **/**/**///// /////**/// /**     /**/**///// /**    /** **////// 
    /**   /**/**   /**   .:'''MMMMM88&&&&&&''':.  /**//** ** /**/**          /**    /**     /**/**      /**    /**/**       
    /******* /*******   :     MMMMM88&&&&&&     : /** //***  /**/*******     /**    /**********/******* /**    /**/*********
    /**////  /**///**    ':...MMMMM88&&&&&&....:  /**  //*   /**/**////      /**    /**//////**/**////  /**    /**////////**
    /**      /**  //**      `''MMMMM88&&&&'''`    /**   /    /**/**          /**    /**     /**/**      /**    /**       /**
    /**      /**   //**         'MMM8&&&'         /**        /**/********    /**    /**     /**/********//*******  ******** 
    //       //     //                            //         // ////////     //     //      // ////////  ///////  ////////  
    """)
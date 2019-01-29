#!/usr/bin/env python2
'''
    A python script example to create plot files to build a board:
    Gerber files
    Drill files
    Map dril files
    Important note:
        this python script does not plot frame references (page layout).
        the reason is it is not yet possible from a python script because plotting
        plot frame references needs loading the corresponding page layout file
        (.wks file) or the default template.
        This info (the page layout template) is not stored in the board, and therefore
        not available.
        Do not try to change SetPlotFrameRef(False) to SetPlotFrameRef(true)
        the result is the pcbnew lib will crash if you try to plot
        the unknown frame references template.
        Anyway, in gerber and drill files the page layout is not plot
'''

import sys
import os
import glob
import fnmatch
sys.path.insert(0,'/Applications/Kicad/kicad.app/Contents/Frameworks/python/site-packages')

from pcbnew import *


def rename_gerber_files(dir):
    # Make a list of .gbr and .drl files in the current directory.
    gerbers = glob.glob(os.path.join(dir, '*.gbr'))
    gerbers.extend(glob.glob(os.path.join(dir, '*.drl')))

    # File renaming rules.
    gerber_types = [
        {'from': '-SilkBottom.gbr',   'to': '.GBO'},
        {'from': '-MaskBottom.gbr',    'to': '.GBS'},
        {'from': '-CuBottom.gbr',      'to': '.GBL'},
        {'from': '-CuTop.gbr',      'to': '.GTL'},
        {'from': '-MaskTop.gbr',    'to': '.GTS'},
        {'from': '-SilkTop.gbr',   'to': '.GTO'},
        {'from': '-EdgeCuts.gbr', 'to': '.GKO'},
        {'from': '-PasteTop.gbr',   'to': '.GTP'},
        {'from': '-PasteBottom.gbr',   'to': '.GBP'},
        {'from': '.drl',           'to': '.TXT'},
    ]
    for g in gerbers:
        for t in gerber_types:
            if g.endswith(t['from']):
                # Strip the 'from' string from the old name and append the 'to' string to make the new name.
                new_g = g[:-len(t['from'])] + t['to']
                # Remove any existing file having the new name.
                try:
                    os.remove(new_g)
                except:
                    # An exception occurred because the file we tried to remove probably didn't exist.
                    pass
                # Rename the old file with the new name.
                os.rename(g, new_g)
                break

    if os.path.exists(dir + "-drl_map.pdf"):
        os.remove(dir + "-drl_map.pdf")

def generate_gerber(filename, output_dir):
    board = LoadBoard(filename)
    pctl = PLOT_CONTROLLER(board)
    popt = pctl.GetPlotOptions()
    popt.SetOutputDirectory(output_dir)

    # Set some important plot options (see pcb_plot_params.h):
    popt.SetPlotFrameRef(False)     #do not change it
    popt.SetLineWidth(FromMM(0.35))

    popt.SetAutoScale(False)        #do not change it
    popt.SetScale(1)                #do not change it
    popt.SetMirror(False)
    popt.SetUseGerberAttributes(True)
    popt.SetIncludeGerberNetlistInfo(True)
    popt.SetUseGerberProtelExtensions(False)
    popt.SetExcludeEdgeLayer(False);
    popt.SetScale(1)
    popt.SetUseAuxOrigin(True)

    # This by gerbers only
    popt.SetSubtractMaskFromSilk(False)
    # Disable plot pad holes
    popt.SetDrillMarksType( PCB_PLOT_PARAMS.NO_DRILL_SHAPE );
    # Skip plot pad NPTH when possible: when drill size and shape == pad size and shape
    # usually sel to True for copper layers
    popt.SetSkipPlotNPTH_Pads( False );

    # Once the defaults are set it become pretty easy...
    # I have a Turing-complete programming language here: I'll use it...
    # param 0 is a string added to the file base name to identify the drawing
    # param 1 is the layer ID
    # param 2 is a comment
    plot_plan = [
        ( "CuTop", F_Cu, "Top layer" ),
        ( "CuBottom", B_Cu, "Bottom layer" ),
        ( "PasteBottom", B_Paste, "Paste Bottom" ),
        ( "PasteTop", F_Paste, "Paste top" ),
        ( "SilkTop", F_SilkS, "Silk top" ),
        ( "SilkBottom", B_SilkS, "Silk top" ),
        ( "MaskBottom", B_Mask, "Mask bottom" ),
        ( "MaskTop", F_Mask, "Mask top" ),
        ( "EdgeCuts", Edge_Cuts, "Edges" ),
    ]


    for layer_info in plot_plan:
        if layer_info[1] <= B_Cu:
            popt.SetSkipPlotNPTH_Pads( True )
        else:
            popt.SetSkipPlotNPTH_Pads( False )

        pctl.SetLayer(layer_info[1])
        pctl.OpenPlotfile(layer_info[0], PLOT_FORMAT_GERBER, layer_info[2])
        print 'plot %s' % pctl.GetPlotFileName()
        if pctl.PlotLayer() == False:
            print "plot error"

    #generate internal copper layers, if any
    lyrcnt = board.GetCopperLayerCount();

    for innerlyr in range ( 1, lyrcnt-1 ):
        popt.SetSkipPlotNPTH_Pads( True );
        pctl.SetLayer(innerlyr)
        lyrname = 'inner%s' % innerlyr
        pctl.OpenPlotfile(lyrname, PLOT_FORMAT_GERBER, "inner")
        print 'plot %s' % pctl.GetPlotFileName()
        if pctl.PlotLayer() == False:
            print "plot error"


    # At the end you have to close the last plot, otherwise you don't know when
    # the object will be recycled!
    pctl.ClosePlot()

    # Fabricators need drill files.
    # sometimes a drill map file is asked (for verification purpose)
    drlwriter = EXCELLON_WRITER( board )
    drlwriter.SetMapFileFormat( PLOT_FORMAT_PDF )

    mirror = False
    minimalHeader = False
    offset = wxPoint(0,0)
    # False to generate 2 separate drill files (one for plated holes, one for non plated holes)
    # True to generate only one drill file
    mergeNPTH = True
    drlwriter.SetOptions( mirror, minimalHeader, offset, mergeNPTH )

    metricFmt = True
    drlwriter.SetFormat( metricFmt )

    genDrl = True
    genMap = True
    print 'create drill and map files in %s' % pctl.GetPlotDirName()
    drlwriter.CreateDrillandMapFilesSet( pctl.GetPlotDirName(), genDrl, genMap );

    # One can create a text file to report drill statistics
    rptfn = pctl.GetPlotDirName() + 'drill_report.rpt'
    print 'report: %s' % rptfn
    drlwriter.GenDrillReportFile( rptfn );

    rename_gerber_files(output_dir)


if __name__ == "__main__":
    basedir = "gerber"
    matches = list()

    if not os.path.exists(basedir):
        os.mkdir(basedir)

    for root, dirnames, filenames in os.walk("RFmodules"):
        for filename in fnmatch.filter(filenames, "*.kicad_pcb"):
            matches.append(os.path.join(root, filename))
    for pcb_file in matches:
        print(pcb_file)
        output_dir = os.path.join(os.path.abspath(basedir), os.path.basename(pcb_file).split(".")[0])
        generate_gerber(pcb_file, os.path.abspath(output_dir))

# Fiji-TNT-Counting
A Python script to allow for blind, standardized TNT counting in Fiji/ImageJ. 

# Installation

Download the provided TNT-Plugin_plgs.py file. Rename it if you'd like, but leave the _plgs.py ending. Drag this file directly into your /Fiji/Plugins folder on your computer. Restart Fiji; the plugin should be in your plugins bar.

# Outputs 
After analysis (clicking exit/continue), a row will be added to an automatically created/saved csv file in the folder you are analyzing. 
This analysis sheets will include:

  • Total number of cells. *Please note* this is only accurate if you do not have overlapping categorizations when counting cells. It is a simple sum of all subtypes of cells counter.
  
  • Total # of TNT-connected cells
  
  • Ratio of TNT-connected cells
  
  • Cell subtypes
  
  • # of TNT-Connected Cells for each subtype
  
  • TNT connection matrix (# of connections, categorized by type of cells connected)

  • All marked cell coords, cell type, if connected, type of connections (subtypes)
  
  • All marked line coords and which subtypes are being connected
  

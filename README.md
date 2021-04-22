# flopyVedo
(Working title) 

The intent is to share some tools that I have found useful in making groundwater models with flopy and visualizing them using the vedo package. 

Very much a work in progress, building out more examples as I go.

## Motivation/Goal
I was a hydrogeologist working in consulting for several years. I was frequently building models with the combination of ESRI ArcGIS, a paid-for model GUI (Visual Modflow or similar), and C-Tech's EVS. These are expensive wrappers for open source models. (for the record I love all these tools, particularly EVS is super, super cool.)

After that I learned how to write production code at a tech company as a UI person. Now I am a grad student back in hydrogeology, and I want to do what I did before but using free open source tools, and I want to share how.

## Requirements:

Python38
Vedo (only works with python38 at the time of this writing)
Flopy
pykrige (for some of it)
Some pandas and numpy

## Note
Sample data is from a site in Luxembourg that I may do my PhD work on.

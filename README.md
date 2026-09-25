# About
This is Add-on for Blender, to help calculate building materials needed for simple constructions.

# Installation
Simply download .py file and add it as Add-on to blender.

# Usage

1. Create construction premitives and rename them; <img src="screenshots/Screenshot From 2026-09-25 22-54-31.png"/>
1. Use created premitives to model desired construction; <img src="screenshots/Screenshot From 2026-09-25 22-54-47.png"/>
1. Use tool, provided by Add-on to select area, items and calculate pieces and their lengths;

 * tool provides several ways to select/filter scene objects:
  
  * perform calculation only among selected objects;
  * perform calculation only among objects located within box (box is imaginary and doesn't change the scene) of selected object;
    * here are option allowing to accept objects located within box partially. else partial objects will not be counted;
 * finally, perform calculation using corresponding button. as a result, new Text object created in blender and it's name written in field 'Result' - navigate to Blender's text editor and read result.

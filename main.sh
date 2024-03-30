#!/bin/bash

echo -e "\e[34m enter the asset 1 file path"
read asset1

echo -e "\e[34m enter the asset 2 file path"
read asset2

echo -e "\e[34m enter the asset 3 file path"
read asset3

echo -e "\e[34m enter the asset 4 file path"
read asset4

echo -e "\e[34m enter the asset 5 file path"
read asset5


#asset1
gnome-terminal -- bash -c "python3 $asset1; exec bash"

#asset2
gnome-terminal -- bash -c "python3 $asset2; exec bash"

#asset3
gnome-terminal -- bash -c "python3 $asset3; exec bash"

#asset4
gnome-terminal -- bash -c "python3 $asset4; exec bash"

#asset5
gnome-terminal -- bash -c "python3 $asset5; exec bash"


echo -e "\e[32m all 5 assets are running"


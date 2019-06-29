#!/bin/bash
cd database
git add -A
git commit -m  "$1" 
git push
cd ../website
git add -A
git commit -m  "$1" 
git push

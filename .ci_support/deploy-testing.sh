#!/bin/bash
cd database
git checkout testing
git add -A
git commit -m  "$1" 
git push

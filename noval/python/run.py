# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        NovalIDE.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-08
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------


from noval.launcher import run
import noval.model as model

def main():
    run(model.LANGUAGE_DEFAULT)


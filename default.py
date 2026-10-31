# -*- coding: utf-8 -*-
"""Lancé depuis Programmes, Extensions ou RunScript(script.module.jsruntime) :
installe ou met à jour le moteur JavaScript."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

import jsruntime  # noqa: E402

jsruntime.install_with_dialog()

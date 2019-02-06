#!/usr/bin/env python

'''
Validate a MAVLink protocol XML file against a schematron specification.

Schematron provides additional validation not enabled in XSD 1.0. 
'''

from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import object
import os
import re
import sys
from lxml import etree
from lxml import isoschematron

# Schematron schema file
schematronFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "schematron.map")


def load_validator():
    """Create schematron validator"""
    try: 
        with open(schematronFile, 'r') as f:
            schematron_root = etree.parse(f)
            schematron = isoschematron.Schematron(schematron_root,store_report=True)
            return schematron
    except Exception as e:
        print(e, file=sys.stderr)
    #except:
    #    print("WARNING: Unable to load schematron validator. XML validation will not be performed", file=sys.stderr)


def validation_report(report):
    """Generate readable report"""
    print("Validation report:")
    print(schematron.validation_report)


def validate(xmlfile):
    """Uses lxml to validate an XML file using schematron."""
    xmlvalid = True
    try:
        with open(xmlfile, 'r') as f:
            xmldocument = etree.parse(f)
            print(schematron)
            print(xmldocument)
            xmlvalid = schematron.validate(xmldocument)
            print('DEBUG:valid: %s' % xmlvalid)
            print("Validation report:")
            validation_report(schematron.validation_report)
            return xmlvalid
    except etree.XMLSchemaError:
        return False
    except etree.DocumentInvalid as err:
        sys.exit('ERROR: %s' % str(err.error_log))
    return xmlvalid




schematron=load_validator()


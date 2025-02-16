#!/usr/bin/env python

#
# Copyright 2021, by the California Institute of Technology.
# ALL RIGHTS RESERVED.
# United States Government sponsorship acknowledged.
# Any commercial use must be negotiated with the Office of Technology Transfer
# at the California Institute of Technology.
# This software may be subject to U.S. export control laws and regulations.
# By accepting this document, the user agrees to comply with all applicable
# U.S. export laws and regulations. User has the responsibility to obtain
# export licenses, or other export authority as may be required, before
# exporting such information to foreign countries or providing access to
# foreign persons.
#

"""
=================
test_run_utils.py
=================

Unit tests for the util/run_utils.py module.

"""
import os
import shutil
import tempfile
import unittest
from os.path import abspath, join

from pkg_resources import resource_filename

from opera.util.logger import PgeLogger
from opera.util.run_utils import create_sas_command_line
from opera.util.run_utils import time_and_execute


class RunUtilsTestCase(unittest.TestCase):
    """Base test class using unittest"""

    starting_dir = None
    working_dir = None
    data_dir = None
    test_dir = None

    @classmethod
    def setUpClass(cls) -> None:
        """
        Set up class variables:
        Initialize the number of times to exercise the module (currently 1000)

        """
        cls.starting_dir = abspath(os.curdir)
        cls.test_dir = resource_filename(__name__, "")
        cls.data_dir = join(cls.test_dir, "data")

        os.chdir(cls.test_dir)

        cls.working_dir = tempfile.TemporaryDirectory(
            prefix="test_run_utils_", suffix='temp', dir=os.curdir)

        cls.logger = PgeLogger()

    @classmethod
    def tearDownClass(cls) -> None:
        """
        At completion re-establish starting directory
        -------
        """
        cls.working_dir.cleanup()
        os.chdir(cls.starting_dir)

    def setUp(self) -> None:
        """Use the temporary directory as the working directory"""
        os.chdir(self.working_dir.name)

    def tearDown(self) -> None:
        """
        Return to starting directory
        -------
        """
        os.chdir(self.test_dir)

    def test_create_sas_command_line(self):
        """Tests for run_utils.create_sas_command_line()"""

        # Make a command from something locally available on PATH (findable
        # by a which call)
        cmd = 'echo'
        runconfig_path = '/path/to/runconfig'
        options = ['Hello from test_create_command_line function.', '--']

        command_line = create_sas_command_line(cmd, runconfig_path, options)

        self.assertIsInstance(command_line, list)
        self.assertEqual(len(command_line), 4)

        # Check that the executable was resolved to actual location on disk
        self.assertEqual(command_line[0], shutil.which(cmd))

        # Check that the runconfig path was appended as the final input argument
        self.assertEqual(command_line[-1], runconfig_path)

        # Check that each option made it into the command line
        for option in options:
            self.assertIn(option, command_line)

        # Make a command using python module name (not findable with which)
        cmd = 'unittest'
        options = ['--verbose', '--']

        command_line = create_sas_command_line(cmd, runconfig_path, options)

        self.assertIsInstance(command_line, list)
        self.assertEqual(len(command_line), 6)

        # Check that python3 was assigned as the executable
        self.assertEqual(command_line[0], 'python3')
        self.assertEqual(command_line[1], '-m')
        self.assertEqual(command_line[2], cmd)

        # Check that the runconfig path was appended as the final input argument
        self.assertEqual(command_line[-1], runconfig_path)

        # Check that each option made it into the command line
        for option in options:
            self.assertIn(option, command_line)

    def test_time_and_execute(self):
        """Tests for run_utils.time_and_execute()"""
        program_path = 'echo'
        program_options = ['Hello from test_time_and_execute function.', '--']
        runconfig_filepath = '/path/to/runconfig'

        command_line = create_sas_command_line(program_path, runconfig_filepath, program_options)

        # Execute a valid command
        elapsed_time = time_and_execute(command_line, self.logger, execute_via_shell=False)
        self.logger.info('test', 1, f'Elapsed time: {elapsed_time}.')

        # Execute an invalid command (non-zero return)
        program_path = 'bash'
        program_options = ['-c', 'exit 1']

        command_line = create_sas_command_line(program_path, runconfig_filepath, program_options)

        with self.assertRaises(RuntimeError):
            time_and_execute(command_line, self.logger, execute_via_shell=False)

        self.logger.close_log_stream()

        log_file = self.logger.get_file_name()

        self.assertTrue(os.path.exists(log_file))

        # Open the log file, and check for specific messages
        with open(log_file, 'r', encoding='utf-8') as infile:
            log = infile.read()

        # Check for the successful run
        self.assertIn('Hello from test_time_and_execute function.', log)
        self.assertIn(f'Elapsed time: {elapsed_time}', log)

        # Check for the erroneous run (note this test is generalized to work
        # on both linux and osx)
        self.assertIn('bash -c exit 1 /path/to/runconfig" failed with exit code 1', log)

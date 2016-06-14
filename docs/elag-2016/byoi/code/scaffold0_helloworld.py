#!/usr/bin/env python

"""
Part 0
======

Hello World.

----

To run:

    (vm) $ python scaffold0_helloworld.py

Run with less noise:

    (vm) $ python scaffold0_helloworld.py 2> /dev/null

"""
import luigi


class HelloWorldTask(luigi.Task):

    def run(self):
        """
        TODO:

        * Print 'HelloWorldTask says hello world' to stdout.
        """

if __name__ == '__main__':
    luigi.run(['HelloWorldTask', '--workers', '1', '--local-scheduler'])

# Vision

This file outlines the vision for the project.

## Overview

tutr (Tell Me How To) is an AI powered terminal assistant which assists users in discovering and executing terminal commands.

## Terminal

The `tutr` tool is mean to be run from the terminal command line as a quick, one shot, command which will produce a terminal command based on prompt.

### Invoking

The `tutr` tool will be invoked in the terminal via the `tutr` command.

Examples:
    - `> tutr git create and switch to new branch called 'testing'`
    - `> tutr sed replace all instances of 'something' with 'something else' in ~/some_file.txt`
    - `> tutr curl http://somewebsite.com and display all request headers`

## AI Power

At it's core `tutr` compiles a simple set of context, invokes an LLM, and returns a reponse to the user directly in the terminal.

## Context

When invoked `tutr` will receive a few key peices of context:

1. The command being investigated (if known).
Ex: 
    -`git`
    - `sed`
    - Any terminal command installed in the system

2. Documentation regarding the tool:
Ex: 
    - Man page for the command. Generated with `man $CMD`
    - Help argument for the command. Generated with `$CMD --help`
    - Other documentation sources



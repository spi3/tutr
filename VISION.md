# Vision

This file outlines the vision for the project.

## Overview

TMHT (Tell Me How To) is an AI powered terminal assistant which assists users in discovering and executing terminal commands.

## Terminal

The `tmht` tool is mean to be run from the terminal command line as a quick, one shot, command which will produce a terminal command based on prompt.

### Invoking

The `tmht` tool will be invoked in the terminal via the `tmht` command.

Examples:
    - `> tmht git create and switch to new branch called 'testing'`
    - `> tmht sed replace all instances of 'something' with 'something else' in ~/some_file.txt`
    - `> tmht curl http://somewebsite.com and display all request headers`

## AI Power

At it's core `tmht` compiles a simple set of context, invokes an LLM, and returns a reponse to the user directly in the terminal.

## Context

When invoked `tmht` will receive a few key peices of context:

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



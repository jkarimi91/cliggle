# Cliggle
A CLI for Kaggle Competitions.

## Why?
To have a more streamlined workflow especially 
when working over SSH.

## Installation
```
pip install cliggle
```

## Usage
### List
To list the current competitions by (shortened) title:
```
cliggle list
```
### Download
To download the data for a competition:
```
cliggle download <title>
```
### Submit
To make a submission:
```
cliggle submit <title> <filename>
```
### Help
To see the help strings for cliggle:
```
cliggle --help
```
To see the help strings for the commands:
```
cliggle <command> --help
```
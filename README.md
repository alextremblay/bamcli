## bamcli

bamcli is a CLI (Command Line Interface) to BAM (BlueCat Address Manager). It uses the BAM Python API.

## Installation

* Download the code from Github

<pre><code>
$ git clone https://github.com/quistian/bamcli.git
</code></pre>

* Set up the Python3 virtual environment for bamcli to run in:

<pre><code>
$ cd bamcli
$ python3 -m venv `pwd`/venv
$ . venv/bin/activate
$ pip install --upgrade pip
$ pip install click requests
$ pip install --editable .
</code></pre>


Customize your Unix shell (this documentation assumes /bin/sh, /bin/bash or /bin/zsh) environment to set the BAM URL, Username and Password

<pre><code>
$ cat .example_bamrc
export BAM_USER=fred
export BAM_PW='Flintstones_R_4ever!'
export BAM_API_URL='https://bam.bigcorp.ca/Services/REST/v1/'

$ mv .example_bamrc .bamrc
$ vi .bamrc
$ . .bamrc
</code></pre>

The BAM CLI interface will not work with out these SHELL variables being set


## Description

The CLI operates on one's DNS data Resource Records (RR) using four commands or actions:

* add
* delete
* update
* view

At present the CLI understands four types of DNS Resource Records:

* A records for mapping IP addresses
* CNAME records for creating aliases
* TXT records for adding text based information
* MX records for mail exchanger data

## Examples

<h3> Adding Resource Records</h3>
  
First we shall ADD some data to our zone: zip.bigcorp.ca to our network: 10.10.0.0/24

<pre><code>
$ bamcli add red.zip.bigcorp.ca  A 10.10.0.100
$ bamcli add blue.zip.bigcorp.ca A 10.10.10.10
$ bamcli add blue.zip.bigcorp.ca A 10.10.2.2
$ bamcli add zip.bigcorp.ca A 10.10.11
$ bamcli add smtp.zip.bigcorp.ca A 10.10.25.25
$ bamcli add rouge.zip.bigcorp.ca CNAME red.zip.bigcorp.ca
$ bamcli add note.zip.bigcorp.ca TXT "Superman and Batman"
$ bamcli add zip.bigcorp.ca MX 10,smtp.zip.bigcorp.ca
</code></pre>

Records can also be added to the top level:

<pre><code>
$ bamcli add zip.bigcorp.ca MX 10,smtp.zip.bigcorp.ca
$ bamcli add zip.bigcorp.ca A 10.10.1.1
</code></pre>

Time to Live values can be assigned on a per RR basis (the default being 86400 seconds/1 day) by adding a numeric value as the last argument:

<pre><code>
$ bamcli add tmp.zip.bigcorp.ca A 10.10.7.7 3600
</code></pre>

<h3> Viewing DNS data </h3>

Now we can VIEW the data we have added. To see the entire zone use the top level domain name followed by a dot. (The output is in BIND format).

* bamcli view zip.bigcorp.ca.

<pre><code>
zip.bigcorp.ca       IN       A      10.10.1.1
zip.bigcorp.ca       IN       MX     10 smtp.zip.bigcorp.ca
blue.zip.bigcorp.ca  IN       A      10.10.10.10
blue.zip.bigcorp.ca  IN       A      10.10.2.2
red.zip.bigcorp.ca   IN       A      10.10.0.100
tmp.zip.bigcorp.ca   IN  3600 A      10.10.7.7
rouge.zip.bigcorp.ca IN       CNAME  red.zip.bigcorp.ca
note.zip.bigcorp.ca  IN       TXT    "Superman and Batman"
</code></pre>

To see only the data at the top of the zone drop the trailing dot:

* bamcli view zip.bigcorp.ca

<pre><code>
zip.bigcorp.ca       IN   A      10.10.1.1
zip.bigcorp.ca       IN   MX     10 smtp.zip.bigcorp.ca
</code></pre>

To see all data of the same RR type the value can be dropped from the argument list:

* bamcli view blue.zip.bigcorp.ca A

<pre><code>
blue.zip.bigcorp.ca       IN   A    10.10.10.10
blue.zip.bigcorp.ca       IN   A    10.10.2.2
</code></pre>

can be created/deleted/changed and viewed
via this intereface.

At the present time bulk operations are managed by creating a file of bamcli commands and reading the file into the shell

#!/usr/bin/perl 
#===============================================================================
#
#         FILE:  core.pl
#
#        USAGE:  ./core.pl  
#
#  DESCRIPTION:  Core for PoCo-IRC bot
#
#      OPTIONS:  ---
# REQUIREMENTS:  ---
#         BUGS:  ---
#        NOTES:  ---
#       AUTHOR:  Kyle Isom (coder@kyleisom.net)
#      COMPANY:  
#      VERSION:  1.0
#      CREATED:  06/25/2010 12:31:26 AM
#     REVISION:  ---
#===============================================================================

use strict;
use warnings;

use POE;
use POE::Component::IRC;
use POE::Component::IRC::State;
use POE::Component::IRC::Plugin::AutoJoin;

# create session and list event handlers
POE::Session -> create(
    package_states => [
        main => [ qw( _start _ircjoin ) ]
    ]
);


